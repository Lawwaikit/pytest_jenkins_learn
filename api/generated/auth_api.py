# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 认证
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class AuthAPI(BaseAPI):
    """认证 相关接口。

    注册、登录、登出。登录返回的 token 用于 Authorize。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = AuthAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def register(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """注册用户 POST /api/v1/auth/register
        
        注册新用户并在同一事务内初始化 CNY 钱包（余额 0）。用户名 3–64 字符且全局唯一，密码 8–128 字符。
        
        参数:
            username (str, 必填, body): 用户名，3–64 字符，全局唯一
            password (str, 必填, body): 密码，8–128 字符，argon2 哈希存储
            email (Any, 可选, body): 邮箱，可选
            nickname (Any, 可选, body): 昵称，可选
        """
        return self._request(
            'POST', '/api/v1/auth/register',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='注册用户',
        )


    def login(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """登录并签发 JWT POST /api/v1/auth/login
        
        校验用户名密码，返回 access_token。在 Swagger 右上角 Authorize 中填入 `Bearer <access_token>` 即可调用后续接口。
        
        参数:
            username (str, 必填, body): 用户名
            password (str, 必填, body): 密码
        """
        return self._request(
            'POST', '/api/v1/auth/login',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='登录并签发 JWT',
        )


    def logout(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """登出并使 token 失效 POST /api/v1/auth/logout
        
        把当前 token 的 jti 写入 Redis 黑名单，旧 token 立即无法访问业务接口。
        """
        return self._request(
            'POST', '/api/v1/auth/logout',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='登出并使 token 失效',
        )
