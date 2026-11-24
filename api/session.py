"""会话管理：基于 requests 的自动登录与多用户切换。

ApiSession 是 requests.Session 的子类，重写 request() 后自动完成：
  1. 相对路径拼 base_url；
  2. token 为空时按需自动登录；
  3. 为业务接口注入 Authorization，单次调用的 headers 优先级最高；
  4. 登录/登出本身记录 Allure step 与附件。

SessionManager 负责管理多个 ApiSession，并通过 active 指针切换当前用户。
"""
from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import allure
import requests

DEFAULT_BASE_URL = "http://localhost:30080"
DEFAULT_LOGIN_PATH = "/api/v1/auth/login"
DEFAULT_REGISTER_PATH = "/api/v1/auth/register"
DEFAULT_LOGOUT_PATH = "/api/v1/auth/logout"
DEFAULT_TOKEN_KEY = "access_token"
DEFAULT_TOKEN_PREFIX = "Bearer"


def new_username(prefix: str = "u") -> str:
    """生成带前缀的随机用户名，供每例动态注册使用。"""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass
class UserContext:
    """一个登录用户的身份与 token。"""

    alias: str
    username: str
    password: str
    token: str | None = None

    def auth_headers(self, prefix: str = DEFAULT_TOKEN_PREFIX) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"{prefix} {self.token}"}


class ApiSession(requests.Session):
    """具备自动登录与用户切换能力的 requests.Session。"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        alias: str = "main",
        username: str | None = None,
        password: str | None = None,
        auto_login: bool = True,
        login_path: str = DEFAULT_LOGIN_PATH,
        register_path: str = DEFAULT_REGISTER_PATH,
        logout_path: str = DEFAULT_LOGOUT_PATH,
        token_key: str = DEFAULT_TOKEN_KEY,
        token_prefix: str = DEFAULT_TOKEN_PREFIX,
        timeout: float = 10,
    ) -> None:
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auto_login = auto_login
        self.login_path = login_path
        self.register_path = register_path
        self.logout_path = logout_path
        self.token_key = token_key
        self.token_prefix = token_prefix
        self.user = UserContext(alias=alias, username=username or "", password=password or "")
        self.headers.update({"Accept": "application/json"})
        if auto_login and self.user.username and self.user.password:
            self.login()

    def absolute_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}/{url.lstrip('/')}" if self.base_url else url

    @staticmethod
    def _has_authorization(headers: dict | None) -> bool:
        return any(str(key).lower() == "authorization" for key in (headers or {}))

    def request(
        self,
        method: str | bytes,
        url: str | bytes,
        *,
        params: Any = None,
        data: Any = None,
        json: Any = None,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """补 base_url、按需登录并注入 Authorization，然后调用 requests.Session.request。"""
        full_url = self.absolute_url(url.decode() if isinstance(url, bytes) else str(url))
        call_headers = dict(headers or {})
        path = url.decode() if isinstance(url, bytes) else str(url)
        public_paths = {self.login_path, self.register_path}

        if path not in public_paths:
            if (
                not self.user.token
                and self.auto_login
                and self.user.username
                and self.user.password
            ):
                self.login()
            if not self._has_authorization(call_headers):
                call_headers.update(self.user.auth_headers(self.token_prefix))

        kwargs.setdefault("timeout", self.timeout)
        return super().request(
            method.upper() if isinstance(method, (str, bytes)) else method,
            full_url,
            params=params,
            data=data,
            json=json,
            headers=call_headers or None,
            **kwargs,
        )

    def login(self) -> requests.Response:
        """登录并把 access_token 保存到 UserContext。"""
        if not self.user.username or not self.user.password:
            raise RuntimeError(f"会话 {self.user.alias!r} 缺少用户名或密码，无法自动登录")

        url = self.absolute_url(self.login_path)
        with allure.step(f"自动登录: {self.user.username}"):
            allure.attach(
                json.dumps(
                    {
                        "method": "POST",
                        "url": url,
                        "body": {
                            "username": self.user.username,
                            "password": "***",
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                name="登录请求",
                attachment_type=allure.attachment_type.JSON,
            )
            response = super().request(
                "POST",
                url,
                json={"username": self.user.username, "password": self.user.password},
                timeout=self.timeout,
            )
            text = response.text or ""
            try:
                payload = response.json()
            except Exception:
                payload = None
            allure.attach(
                json.dumps(
                    {"status_code": response.status_code, "body": payload if payload is not None else text},
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                name="登录响应",
                attachment_type=allure.attachment_type.JSON,
            )

        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"自动登录失败：{response.status_code} {text}")
        if not isinstance(payload, dict) or not payload.get(self.token_key):
            raise RuntimeError(f"登录响应缺少 {self.token_key!r}：{payload}")
        self.user.token = str(payload[self.token_key])
        return response

    def logout(self) -> requests.Response | None:
        """登出并清空本地 token；未登录时直接返回 None。"""
        if not self.user.token:
            return None
        token = self.user.token
        try:
            url = self.absolute_url(self.logout_path)
            with allure.step(f"自动登出: {self.user.username}"):
                response = super().request(
                    "POST",
                    url,
                    headers={"Authorization": f"{self.token_prefix} {token}"},
                    timeout=self.timeout,
                )
                allure.attach(
                    json.dumps(
                        {"status_code": response.status_code, "body": response.text or ""},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    name="登出响应",
                    attachment_type=allure.attachment_type.JSON,
                )
                return response
        finally:
            self.user.token = None


class SessionManager:
    """管理多个已登录用户，并在用例中切换 active 会话。"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        auto_login: bool = True,
        **session_options: Any,
    ) -> None:
        self.base_url = base_url
        self.auto_login = auto_login
        self.session_options = session_options
        self._sessions: dict[str, ApiSession] = {}
        self._active_alias: str | None = None

    def add_user(
        self,
        alias: str,
        username: str,
        password: str,
        *,
        auto_login: bool | None = None,
        **options: Any,
    ) -> ApiSession:
        """创建并登记一个用户会话；第一个加入的用户自动成为 active。"""
        session = ApiSession(
            self.base_url,
            alias=alias,
            username=username,
            password=password,
            auto_login=self.auto_login if auto_login is None else auto_login,
            **{**self.session_options, **options},
        )
        self._sessions[alias] = session
        if self._active_alias is None:
            self._active_alias = alias
        return session

    def use(self, alias: str) -> ApiSession:
        """切换当前用户。"""
        if alias not in self._sessions:
            raise KeyError(f"未登记的用户别名 {alias!r}，请先 add_user()")
        self._active_alias = alias
        return self._sessions[alias]

    def current(self) -> ApiSession:
        if self._active_alias is None:
            raise RuntimeError("SessionManager 还没有 active 用户，请先 add_user() 或 use()")
        return self._sessions[self._active_alias]

    def get(self, alias: str) -> ApiSession:
        if alias not in self._sessions:
            raise KeyError(f"未登记的用户别名 {alias!r}")
        return self._sessions[alias]

    @contextmanager
    def using(self, alias: str) -> Iterator[ApiSession]:
        """临时切换用户，退出上下文后恢复原 active。"""
        previous = self._active_alias
        session = self.use(alias)
        try:
            yield session
        finally:
            if previous is not None:
                self._active_alias = previous

    def logout(self, alias: str | None = None) -> None:
        target = alias or self._active_alias
        if target is None:
            return
        session = self.get(target)
        session.logout()

    def logout_all(self) -> None:
        for session in self._sessions.values():
            session.logout()

    def clear(self) -> None:
        """登出所有用户、关闭底层连接并清空注册表。"""
        self.logout_all()
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        self._active_alias = None


_DEFAULT_MANAGER: SessionManager | None = None


def set_default_manager(manager: SessionManager | None) -> None:
    """设置全局默认 SessionManager，通常由 conftest 的 session fixture 调用。"""
    global _DEFAULT_MANAGER
    _DEFAULT_MANAGER = manager


def get_default_manager() -> SessionManager:
    if _DEFAULT_MANAGER is None:
        raise RuntimeError(
            "没有可用的 SessionManager：请在 conftest 中调用 set_default_manager(manager)，"
            "或在 API 构造时显式传入 client=..."
        )
    return _DEFAULT_MANAGER
