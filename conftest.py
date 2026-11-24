"""pytest 全局 fixture：会话管理、每例用户、临时匿名客户端。

base_url 统一取自 api.session.DEFAULT_BASE_URL，后续接入 env.yaml / --env 时只改那一处即可。
"""
from __future__ import annotations

import uuid
from typing import Callable

import pytest

from api.generated.auth_api import AuthAPI
from api.session import (
    DEFAULT_BASE_URL,
    ApiSession,
    SessionManager,
    new_username,
    set_default_manager,
)
from keywords.auth_kw import DEFAULT_PASSWORD


@pytest.fixture(scope="session")
def sessions() -> SessionManager:
    """整轮测试共享一个 SessionManager；默认管理入口在此注册。"""
    manager = SessionManager(base_url=DEFAULT_BASE_URL, auto_login=True)
    set_default_manager(manager)
    yield manager
    manager.clear()
    set_default_manager(None)


@pytest.fixture
def anonymous_client() -> ApiSession:
    """带 base_url 但不自动登录的会话，用于注册、匿名/负向请求。"""
    session = ApiSession(base_url=DEFAULT_BASE_URL, auto_login=False)
    yield session
    session.close()


def _register(username: str, password: str, client: ApiSession, **fields) -> None:
    """通过生成的 AuthAPI 注册用户，状态码由 fixture 层校验。"""
    response = AuthAPI(client=client).register(
        body={"username": username, "password": password, **fields}
    )
    assert response.status_code == 201, (
        f"动态注册失败：{response.status_code} {response.text}"
    )


@pytest.fixture(autouse=True)
def active_user(sessions: SessionManager, anonymous_client: ApiSession) -> ApiSession:
    """每个用例动态注册并登录一个用户，结束后自动登出并清理。"""
    username = new_username("case")
    password = DEFAULT_PASSWORD
    _register(username, password, anonymous_client)
    session = sessions.add_user("main", username, password, auto_login=True)
    sessions.use("main")
    yield session
    sessions.clear()


@pytest.fixture
def make_user(
    sessions: SessionManager, anonymous_client: ApiSession
) -> Callable[..., ApiSession]:
    """按需创建额外用户，例如 buyer / seller，默认自动登录并登记。"""

    def _make(
        alias: str | None = None,
        password: str = DEFAULT_PASSWORD,
        **fields,
    ) -> ApiSession:
        alias = alias or f"u_{uuid.uuid4().hex[:8]}"
        username = new_username("extra")
        _register(username, password, anonymous_client, **fields)
        return sessions.add_user(alias, username, password, auto_login=True)

    return _make
