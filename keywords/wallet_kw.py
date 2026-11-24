"""钱包关键字：组合生成的 WalletAPI，提供业务语义的原子操作。

请求参数由本层组装成 body / query 后传给生成类；鉴权头由 ApiSession 自动注入，
关键字不再要求调用方传 headers。需要指定用户时用 sessions.get(alias) 构造 API 对象。
"""
from __future__ import annotations

import uuid

from api.generated.wallet_api import WalletAPI


def new_idempotency_key(prefix: str = "idem") -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def available_balance(api: WalletAPI) -> int:
    response = api.get_balance()
    assert response.status_code == 200, f"查询余额失败：{response.status_code} {response.text}"
    return response.data["available_balance"]


def deposit(api: WalletAPI, amount_cents: int, **fields) -> dict:
    """充值；fields 可传 idempotency_key、remark 或未来新增字段。"""
    response = api.deposit(body={"amount_cents": amount_cents, **fields})
    assert response.status_code == 200, f"充值失败：{response.status_code} {response.text}"
    return response.data


def withdraw(api: WalletAPI, amount_cents: int, **fields) -> dict:
    response = api.withdraw(body={"amount_cents": amount_cents, **fields})
    assert response.status_code == 200, f"提现失败：{response.status_code} {response.text}"
    return response.data


def list_transactions(api: WalletAPI, page: int = 1, size: int = 20) -> dict:
    response = api.list_transactions(query={"page": page, "size": size})
    assert response.status_code == 200, f"查询流水失败：{response.status_code} {response.text}"
    return response.data
