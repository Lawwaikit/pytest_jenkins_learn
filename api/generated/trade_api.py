# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 交易
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class TradeAPI(BaseAPI):
    """交易 相关接口。

    模拟行情、买入、卖出、持仓与成交历史。固定价格即时结算，不接真实市场。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = TradeAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def list_instruments(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查询模拟行情 GET /api/v1/market/instruments
        
        返回内置模拟标的与固定价格，价格为整数分。行情为演示数据，不接真实市场。
        """
        return self._request(
            'GET', '/api/v1/market/instruments',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查询模拟行情',
        )


    def buy(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """买入标的 POST /api/v1/trades/buy
        
        按当前模拟价格即时成交：扣减钱包可用余额、增加持仓，并写入成交记录与钱包流水。余额不足返回 422；相同 idempotency_key 的重复请求只成交一次。
        
        参数:
            symbol (str, 必填, body): 行情标的符号，如 600519
            quantity (int, 必填, body): 成交数量，正整数
            idempotency_key (Any, 可选, body): 幂等键；相同键的重复请求只成交一次
        """
        return self._request(
            'POST', '/api/v1/trades/buy',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='买入标的',
        )


    def sell(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """卖出标的 POST /api/v1/trades/sell
        
        按当前模拟价格即时成交：减少持仓、回款到钱包，并写入成交记录与钱包流水。持仓不足返回 422；数量归零时删除该持仓记录。
        
        参数:
            symbol (str, 必填, body): 行情标的符号，如 600519
            quantity (int, 必填, body): 成交数量，正整数
            idempotency_key (Any, 可选, body): 幂等键；相同键的重复请求只成交一次
        """
        return self._request(
            'POST', '/api/v1/trades/sell',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='卖出标的',
        )


    def list_positions(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查询持仓 GET /api/v1/trades/positions
        
        返回当前用户的持仓数量、平均成本、当前价、市值与浮动盈亏，金额均为整数分。
        """
        return self._request(
            'GET', '/api/v1/trades/positions',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查询持仓',
        )


    def list_history(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查询成交历史 GET /api/v1/trades/history
        
        分页返回当前用户的成交记录，按成交时间与 id 倒序。side：1=买入，2=卖出。
        
        参数:
            page (int, 可选, query): 页码，从 1 开始
            size (int, 可选, query): 每页条数，1–100
        """
        return self._request(
            'GET', '/api/v1/trades/history',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查询成交历史',
        )
