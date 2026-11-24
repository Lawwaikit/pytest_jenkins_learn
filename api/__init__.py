"""API 封装层。

- base.py：请求模板与 ApiResponse；
- session.py：基于 requests 的自动登录会话与多用户管理；
- generated/：由 OpenAPI 文档自动生成的接口类。
"""
from api.base import ApiResponse, BaseAPI
from api.session import (
    ApiSession,
    SessionManager,
    get_default_manager,
    new_username,
    set_default_manager,
)

__all__ = [
    "ApiResponse",
    "BaseAPI",
    "ApiSession",
    "SessionManager",
    "get_default_manager",
    "new_username",
    "set_default_manager",
]
