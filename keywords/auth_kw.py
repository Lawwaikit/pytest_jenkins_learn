"""认证关键字示例：调用生成的 AuthAPI，封装场景准备动作。

新写法下登录由 ApiSession 自动完成，conftest 负责每例注册与登录；
本文件的显式登录函数保留给旧用例或负向场景使用。接口入参统一在关键字层组装。
"""
from __future__ import annotations

from api.base import ApiResponse
from api.generated.auth_api import AuthAPI

DEFAULT_PASSWORD = "Test@123456"


def register(api: AuthAPI, username: str, password: str = DEFAULT_PASSWORD,
             **fields) -> ApiResponse:
    """注册一个用户，由关键字层判断业务期望状态码。"""
    body = {"username": username, "password": password, **fields}
    response = api.register(body=body)
    assert response.status_code == 201, f"注册失败：{response.status_code} {response.text}"
    return response


def login(api: AuthAPI, username: str, password: str = DEFAULT_PASSWORD) -> dict:
    """兼容旧写法：显式登录并返回 headers；新写法由 ApiSession 自动登录。"""
    response = api.login(body={"username": username, "password": password})
    assert response.status_code == 200, f"登录失败：{response.status_code} {response.text}"
    token = response.data["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_and_login(api: AuthAPI, username: str,
                       password: str = DEFAULT_PASSWORD) -> dict:
    """兼容旧写法：注册 + 登录，返回用户上下文；新写法请用 conftest fixtures。"""
    response = register(api, username, password)
    return {
        "id": response.data["id"],
        "username": username,
        "password": password,
        "headers": login(api, username, password),
    }
