# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 用户管理
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class UserAPI(BaseAPI):
    """用户管理 相关接口。

    个人信息查询、修改与软注销。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = UserAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def get_me(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查看个人信息 GET /api/v1/users/me
        """
        return self._request(
            'GET', '/api/v1/users/me',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查看个人信息',
        )


    def delete_me(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """注销账户（软注销） DELETE /api/v1/users/me
        
        要求所有钱包的可用余额与冻结余额均为 0，否则返回 409。注销后 token 再访问业务接口返回 404。
        """
        return self._request(
            'DELETE', '/api/v1/users/me',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='注销账户（软注销）',
        )


    def patch_me(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """修改个人信息 PATCH /api/v1/users/me
        
        可修改 email 与 nickname，至少提供一项。
        
        参数:
            email (Any, 可选, body): 新邮箱
            nickname (Any, 可选, body): 新昵称
        """
        return self._request(
            'PATCH', '/api/v1/users/me',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='修改个人信息',
        )
