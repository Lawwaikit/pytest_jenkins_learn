# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 连通性探测
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class ProbeAPI(BaseAPI):
    """连通性探测 相关接口。

    MySQL / Redis 连通性探测，纯读无副作用；不可达时返回 503。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = ProbeAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def probe_mysql(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """MySQL 连通性探测 GET /probe/mysql
        
        建立连接并执行 SELECT 1，纯探测无副作用；返回延迟毫秒数，失败时返回 503。
        """
        return self._request(
            'GET', '/probe/mysql',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='MySQL 连通性探测',
        )


    def probe_redis(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """Redis 连通性探测 GET /probe/redis
        
        执行 PING，纯探测无副作用；返回延迟毫秒数，失败时返回 503。
        """
        return self._request(
            'GET', '/probe/redis',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='Redis 连通性探测',
        )
