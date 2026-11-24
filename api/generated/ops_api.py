# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 运维探针
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class OpsAPI(BaseAPI):
    """运维探针 相关接口。

    容器健康、就绪、排空、实例与版本探针；compose healthcheck 与 check_readiness.py 依赖，行为不可变更。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = OpsAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def health(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """容器存活探针 GET /health
        
        轻量存活检查，不访问 MySQL/Redis；compose healthcheck 与 nginx depends_on 依赖此接口。
        """
        return self._request(
            'GET', '/health',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='容器存活探针',
        )


    def readiness(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """就绪探针 GET /ready
        
        正常返回 200 ready；调用 /admin/drain 后返回 503 not_ready，用于摘除流量。
        """
        return self._request(
            'GET', '/ready',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='就绪探针',
        )


    def drain(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """排空当前实例 POST /admin/drain
        
        置进程内 ready=False，仅影响被请求的实例；多实例下需逐个调用，恢复需重启进程。
        """
        return self._request(
            'POST', '/admin/drain',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='排空当前实例',
        )


    def get_instance(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """实例标识 GET /instance
        
        返回容器 hostname，用于多实例场景定位具体实例。
        """
        return self._request(
            'GET', '/instance',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='实例标识',
        )


    def slow(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """慢请求模拟 GET /slow
        
        固定 sleep 1 秒后返回，用于验证超时控制与优雅关闭。
        """
        return self._request(
            'GET', '/slow',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='慢请求模拟',
        )


    def version(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """版本探针 GET /version
        
        返回 APP_VERSION，便于灰度与发布校验。
        """
        return self._request(
            'GET', '/version',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='版本探针',
        )
