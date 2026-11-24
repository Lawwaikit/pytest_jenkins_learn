"""用户管理场景测试（调用已生成的 API 代码）。

被测 APP 与 pytest 不在同一个项目或环境：本文件不导入 main.app，也不使用
fastapi.testclient.TestClient，而是通过 api/generated 下的类走 HTTP 请求。
登录用户由 conftest 的 active_user fixture 每例动态注册并自动登录。
"""
from __future__ import annotations

import pytest
import allure

from api.generated.auth_api import AuthAPI
from api.generated.user_api import UserAPI
from api.session import new_username
from keywords.auth_kw import DEFAULT_PASSWORD

@allure.epic("用户管理模块")
class TestUserManagement:
    @allure.feature("用户注册")
    @allure.story("新用户注册")

    @allure.title("新用户注册")
    def test_register_success(self, anonymous_client):
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


    @allure.feature("用户注册")
    @allure.story("重复用户名注册")

    @allure.title("重复用户名注册被拒绝")
    def test_register_duplicate_rejected(self, active_user, anonymous_client):
        """重复用户名注册被拒绝。"""
        response = AuthAPI(client=anonymous_client).register(
            body={
                "username": active_user.user.username,
                "password": "Other@123456",
            }
        )
        assert response.status_code == 409, response.text


    @allure.feature("用户登录")
    @allure.story("登录成功")

    @allure.title("登录成功并返回 token")
    def test_login_success(self, active_user, anonymous_client):
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


    @allure.feature("用户登录")
    @allure.story("登录失败")
    @allure.title("错误密码登录被拒绝")
    def test_login_wrong_password(self, active_user, anonymous_client):
        """错误密码登录被拒绝。"""
        response = AuthAPI(client=anonymous_client).login(
            body={
                "username": active_user.user.username,
                "password": "Wrong@123456",
            }
        )
        assert response.status_code == 401, response.text


    @allure.feature("用户访问")
    @allure.story("访问受保护接口")
    @allure.title("未登录访问受保护接口被拒绝")
    def test_protected_route_requires_token(self, anonymous_client):
        """未登录访问受保护接口被拒绝。"""
        response = UserAPI(client=anonymous_client).get_me()
        assert response.status_code == 401, response.text


    @allure.feature("用户访问")
    @allure.story("查看个人信息")
    @allure.title("查看个人信息")
    def test_get_profile(self, active_user):
        """查看个人信息。"""
        response = UserAPI().get_me()
        assert response.status_code == 200, response.text
        assert response.data["username"] == active_user.user.username


    @allure.feature("用户访问")
    @allure.story("修改个人信息")
    @allure.title("修改个人信息")
    def test_update_profile(self):
        """修改个人信息。"""
        response = UserAPI().patch_me(
            body={"email": "new@example.com", "nickname": "new-nick"}
        )
        assert response.status_code == 200, response.text
        assert response.data["email"] == "new@example.com"
        assert response.data["nickname"] == "new-nick"


    @allure.feature("用户访问")
    @allure.story("退出登录")
    @allure.title("退出登录_revokes_token")
    def test_logout_revokes_token(self):
        """退出登录使 token 立即失效。"""
        response = AuthAPI().logout()
        assert response.status_code == 200, response.text
        me = UserAPI().get_me()
        assert me.status_code == 401, me.text


    @allure.feature("用户访问")
    @allure.story("注销账户")
    @allure.title("注销账户成功")
    def test_deactivate_success(self):
        """注销账户成功（余额为 0 且无持仓）。"""
        response = UserAPI().delete_me()
        assert response.status_code == 200, response.text
        assert response.data["status"] == "deactivated"


    @allure.feature("用户访问")
    @allure.story("注销账户")
    @allure.title("注销账户后无法访问业务接口")
    def test_deactivate_blocks_access(self):
        """注销后 token 再访问业务接口返回 404。"""
        deleted = UserAPI().delete_me()
        assert deleted.status_code == 200, deleted.text
        response = UserAPI().get_me()
        assert response.status_code == 404, response.text
