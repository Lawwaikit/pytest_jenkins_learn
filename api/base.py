"""API 请求基础封装。

api/generated/ 下由 Swagger/OpenAPI 自动生成的类继承本类：
生成的类只负责「把业务参数拼成 HTTP 参数」，本类统一负责：
  1. 路径参数替换、query/body 组装；
  2. Allure step + 请求/响应附件自动留痕；
  3. 返回结构统一的 ApiResponse，不强制断言状态码，便于测试 4xx 场景。

HTTP 客户端默认取 api.session.SessionManager.current()，因此切换 active 用户后，
同一个 API 实例会自动使用新用户的会话；也可以显式传 client 覆盖（例如匿名/错误 token 场景）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

import allure

# 用于区分「调用方没传」与「调用方显式传了 None」：
# 负向用例常常需要把字段置为 None 来验证 422，不能用 None 当默认值。
UNSET = object()


@dataclass
class ApiResponse:
    """一次 HTTP 调用的结果。"""

    status_code: int
    headers: Mapping[str, str]
    data: Any
    text: str
    raw: Any = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        return self.data


_DEFAULT_CLIENT: Any = None


def set_default_client(client: Any) -> None:
    """设置兼容用的全局默认客户端；新写法请改用 set_default_manager()。"""
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = client


def get_default_client() -> Any:
    return _DEFAULT_CLIENT


class BaseAPI:
    """所有生成类的基类。

    :param client: 具备 request(method, url, params, json, headers) 方法的对象，
                   例如 api.session.ApiSession 或 requests.Session；
                   不传时动态取 SessionManager.current()，切换 active 用户无需重建实例。
    :param headers: 实例级默认请求头；自动登录的 Authorization 由 ApiSession 注入。
    :param base_path: 统一前缀，生成类一般已包含完整路径，留空即可。
    """

    def __init__(self, client: Any = None, headers: dict | None = None, base_path: str = ""):
        self._client = client
        self._headers = dict(headers or {})
        self.base_path = base_path.rstrip("/")

    @property
    def client(self) -> Any:
        if self._client is not None:
            return self._client
        from api.session import get_default_manager

        try:
            manager = get_default_manager()
        except RuntimeError:
            manager = None
        if manager is not None:
            return manager.current()
        client = get_default_client()
        if client is None:
            raise RuntimeError(
                "没有可用的 HTTP 客户端：请 BaseAPI(..., client=...) 传入，"
                "或在 conftest 中调用 set_default_manager(manager)。"
            )
        return client

    def _build_path(self, path: str, path_params: dict | None) -> str:
        url = f"{self.base_path}{path}"

        def replace(match):
            name = match.group(1)
            if not path_params or name not in path_params:
                raise KeyError(f"路径参数 {name!r} 缺失，调用时需要传入 {name}=...")
            return quote(str(path_params[name]), safe="")

        import re

        return re.sub(r"\{([^{}]+)\}", replace, url)

    def _request(
        self,
        method: str,
        path: str,
        *,
        path_params: dict | None = None,
        query: dict | None = None,
        body: dict | None = None,
        headers: dict | None = None,
        name: str | None = None,
    ) -> ApiResponse:
        """统一请求入口。生成的 API 方法只把参数转交到这里。"""
        url = self._build_path(path, path_params)
        params = {} if query is None else {k: v for k, v in query.items() if v is not UNSET}
        payload = {} if body is None else {k: v for k, v in body.items() if v is not UNSET}
        request_headers = {**self._headers, **(headers or {})}

        request_info = {
            "method": method.upper(),
            "url": url,
            "params": params,
            "body": payload,
            "headers": {k: ("***" if k.lower() == "authorization" else v)
                        for k, v in request_headers.items()},
        }

        with allure.step(name or f"{method.upper()} {url}"):
            allure.attach(
                json.dumps(request_info, ensure_ascii=False, indent=2, default=str),
                name="请求参数",
                attachment_type=allure.attachment_type.JSON,
            )
            raw = self.client.request(
                method.upper(),
                url,
                params=params or None,
                json=payload or None,
                headers=request_headers or None,
            )
            text = getattr(raw, "text", "") or ""
            try:
                data = raw.json()
            except Exception:
                data = None
            allure.attach(
                json.dumps(
                    {"status_code": raw.status_code, "body": data if data is not None else text},
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                name="响应数据",
                attachment_type=allure.attachment_type.JSON,
            )

        response = ApiResponse(
            status_code=raw.status_code,
            headers=dict(getattr(raw, "headers", {}) or {}),
            data=data,
            text=text,
            raw=raw,
        )
        return response
