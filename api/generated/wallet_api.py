# -*- coding: utf-8 -*-
"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。

API: FinTrade Simulator 1.0.0
标签: 钱包管理
重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated
"""
from __future__ import annotations

from api.base import ApiResponse, BaseAPI


class WalletAPI(BaseAPI):
    """钱包管理 相关接口。

    余额、充值、提现与流水。充值为模拟入账，不接真实支付或打款通道。

    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。
    未显式传 client 时自动使用 SessionManager 的当前登录会话。
    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；
    接口变更后重新运行生成脚本，不要直接编辑本文件。

    调用方式:
        api = WalletAPI()
        response = api.<method>(path_params=..., query=..., body=..., headers=...)
    """

    def get_balance(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查询余额 GET /api/v1/wallet/balance
        
        返回默认币种钱包的可用余额与冻结余额，金额单位为整数分。
        """
        return self._request(
            'GET', '/api/v1/wallet/balance',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查询余额',
        )


    def deposit(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """充值（模拟入账） POST /api/v1/wallet/deposit
        
        金额单位为整数分（BIGINT），例如 12500 表示 ¥125.00。相同 idempotency_key 的重复请求只会入账一次。 本接口为模拟入账，不接真实支付通道。
        
        参数:
            amount_cents (int, 必填, body): 金额，整数分；12500 表示 ¥125.00
            idempotency_key (Any, 可选, body): 幂等键；相同键的重复请求只入账一次
            remark (Any, 可选, body): 备注，可选
        """
        return self._request(
            'POST', '/api/v1/wallet/deposit',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='充值（模拟入账）',
        )


    def withdraw(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """提现（模拟出账） POST /api/v1/wallet/withdraw
        
        金额单位为整数分（BIGINT），例如 12500 表示 ¥125.00。相同 idempotency_key 的重复请求只会入账一次。 余额不足返回 422；本接口为模拟出账，不接真实打款通道。
        
        参数:
            amount_cents (int, 必填, body): 金额，整数分；12500 表示 ¥125.00
            idempotency_key (Any, 可选, body): 幂等键；相同键的重复请求只入账一次
            remark (Any, 可选, body): 备注，可选
        """
        return self._request(
            'POST', '/api/v1/wallet/withdraw',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='提现（模拟出账）',
        )


    def list_transactions(self, *, path_params: dict | None = None, query: dict | None = None, body: dict | None = None, headers: dict | None = None) -> ApiResponse:
        """查询交易流水 GET /api/v1/wallet/transactions
        
        分页返回当前用户的充值/提现流水，按创建时间与 id 倒序。type：1=充值，2=提现。
        
        参数:
            page (int, 可选, query): 页码，从 1 开始
            size (int, 可选, query): 每页条数，1–100
        """
        return self._request(
            'GET', '/api/v1/wallet/transactions',
            path_params=path_params,
            query=query,
            body=body,
            headers=headers,
            name='查询交易流水',
        )
