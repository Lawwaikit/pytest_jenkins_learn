"""用户管理场景测试（调用已生成的 API 代码）。

被测 APP 与 pytest 不在同一个项目或环境：本文件不导入 main.app，也不使用
fastapi.testclient.TestClient，而是通过 api/generated 下的类走 HTTP 请求。
登录用户由 conftest 的 active_user fixture 每例动态注册并自动登录。
"""
from __future__ import annotations

from api.generated.auth_api import AuthAPI
from api.generated.user_api import UserAPI
from api.session import new_username
from keywords.auth_kw import DEFAULT_PASSWORD


def test_register_success(anonymous_client):
    """新用户注册。"""
    username = new_username("reg")
    response = AuthAPI(client=anonymous_client).register(
        body={
            "username": username,
            "password": DEFAULT_PASSWORD,
            "email": "reg@example.com",
            "nickname": "reg",
        }
    )
    assert response.status_code == 201, response.text
    data = response.data
    assert data["username"] == username
    assert data["status"] == 1
    assert data["email"] == "reg@example.com"
    assert data["nickname"] == "reg"


def test_register_duplicate_rejected(active_user, anonymous_client):
    """重复用户名注册被拒绝。"""
    response = AuthAPI(client=anonymous_client).register(
        body={
            "username": active_user.user.username,
            "password": "Other@123456",
        }
    )
    assert response.status_code == 409, response.text


def test_login_success(active_user, anonymous_client):
    """登录成功并返回 token。"""
    response = AuthAPI(client=anonymous_client).login(
        body={
            "username": active_user.user.username,
            "password": active_user.user.password,
        }
    )
    assert response.status_code == 200, response.text
    data = response.data
    assert data["token_type"] == "Bearer"
    assert data["user"]["id"] == UserAPI().get_me().data["id"]
    assert data["expires_in"] > 0


def test_login_wrong_password(active_user, anonymous_client):
    """错误密码登录被拒绝。"""
    response = AuthAPI(client=anonymous_client).login(
        body={
            "username": active_user.user.username,
            "password": "Wrong@123456",
        }
    )
    assert response.status_code == 401, response.text


def test_protected_route_requires_token(anonymous_client):
    """未登录访问受保护接口被拒绝。"""
    response = UserAPI(client=anonymous_client).get_me()
    assert response.status_code == 401, response.text


def test_get_profile(active_user):
    """查看个人信息。"""
    response = UserAPI().get_me()
    assert response.status_code == 200, response.text
    assert response.data["username"] == active_user.user.username


def test_update_profile():
    """修改个人信息。"""
    response = UserAPI().patch_me(
        body={"email": "new@example.com", "nickname": "new-nick"}
    )
    assert response.status_code == 200, response.text
    assert response.data["email"] == "new@example.com"
    assert response.data["nickname"] == "new-nick"


def test_logout_revokes_token():
    """退出登录使 token 立即失效。"""
    response = AuthAPI().logout()
    assert response.status_code == 200, response.text
    me = UserAPI().get_me()
    assert me.status_code == 401, me.text


def test_deactivate_success():
    """注销账户成功（余额为 0 且无持仓）。"""
    response = UserAPI().delete_me()
    assert response.status_code == 200, response.text
    assert response.data["status"] == "deactivated"


def test_deactivate_blocks_access():
    """注销后 token 再访问业务接口返回 404。"""
    deleted = UserAPI().delete_me()
    assert deleted.status_code == 200, deleted.text
    response = UserAPI().get_me()
    assert response.status_code == 404, response.text
