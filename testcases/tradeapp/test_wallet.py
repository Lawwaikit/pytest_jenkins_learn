"""钱包管理场景测试（调用已生成的 API 代码）。

不再依赖 fastapi.testclient；被测服务通过 requests + ApiSession 访问。
登录用户由 conftest 的 active_user fixture 每例动态注册并自动登录。
"""
from __future__ import annotations

import pytest
import allure

from api.generated.user_api import UserAPI
from api.generated.wallet_api import WalletAPI
from keywords.wallet_kw import new_idempotency_key


def _balance() -> dict:
    response = WalletAPI().get_balance()
    assert response.status_code == 200, response.text
    return response.data

@allure.epic("钱包模块")
class TestWallet:

    @allure.feature("用户注册")
    @allure.story("注册后钱包余额为 0")
    @allure.title("注册后钱包余额为 0")
    def test_register_initializes_zero_balance(self):
        """注册后钱包余额为 0。"""
        balance = _balance()
        assert balance["currency"] == "CNY"
        assert balance["available_balance"] == 0
        assert balance["frozen_balance"] == 0


    @allure.feature("钱包充值")
    @allure.story("充值更新余额")
    @allure.title("充值更新余额并写入流水")
    def test_deposit_updates_balance_and_writes_transaction(self):
        """充值更新余额并写入流水。"""
        response = WalletAPI().deposit(
            body={"amount_cents": 12500, "remark": "test deposit"}
        )
        assert response.status_code == 200, response.text
        txn = response.data
        assert txn["type"] == 1
        assert txn["amount"] == 12500
        assert txn["balance_before"] == 0
        assert txn["balance_after"] == 12500
        assert _balance()["available_balance"] == 12500


    @allure.feature("钱包充值")
    @allure.story("相同幂等键的充值")
    @allure.title("相同幂等键的充值只入账一次")
    def test_deposit_with_same_idempotency_key_only_once(self):
        """相同幂等键的充值只入账一次。"""
        key = new_idempotency_key()
        body = {"amount_cents": 5000, "idempotency_key": key}
        api = WalletAPI()
        first = api.deposit(body=body)
        second = api.deposit(body=body)
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert second.data["id"] == first.data["id"]
        assert _balance()["available_balance"] == 5000


    @allure.feature("钱包提现")
    @allure.story("提现更新余额")
    @allure.title("提现更新余额")
    def test_withdraw_updates_balance(self):
        """提现更新余额。"""
        deposit = WalletAPI().deposit(body={"amount_cents": 10000})
        assert deposit.status_code == 200, deposit.text
        response = WalletAPI().withdraw(body={"amount_cents": 3000})
        assert response.status_code == 200, response.text
        assert response.data["type"] == 2
        assert response.data["balance_after"] == 7000
        assert _balance()["available_balance"] == 7000


    @allure.feature("钱包提现")
    @allure.story("余额不足")
    @allure.title("余额不足提现被拒绝")
    def test_withdraw_insufficient_balance_rejected(self):
        """余额不足提现被拒绝。"""
        response = WalletAPI().withdraw(body={"amount_cents": 1})
        assert response.status_code == 422, response.text
        assert _balance()["available_balance"] == 0


    @allure.feature("钱包管理")
    @allure.story("流水分页查询")
    @allure.title("流水分页查询")
    def test_transaction_pagination(self):
        """流水分页查询。"""
        api = WalletAPI()
        for amount in (100, 200):
            response = api.deposit(body={"amount_cents": amount})
            assert response.status_code == 200, response.text
        response = api.list_transactions(query={"page": 1, "size": 1})
        assert response.status_code == 200, response.text
        data = response.data
        assert data["total"] == 2
        assert len(data["items"]) == 1


    @allure.feature("钱包管理")
    @allure.story("注销账户")
    @allure.title("钱包余额非零时注销被拒绝")
    def test_deactivate_rejected_when_balance_nonzero(self):
        """钱包余额非零时注销被拒绝。"""
        deposit = WalletAPI().deposit(body={"amount_cents": 100})
        assert deposit.status_code == 200, deposit.text
        response = UserAPI().delete_me()
        assert response.status_code == 409, response.text


    @allure.feature("钱包管理")
    @allure.story("注销账户")
    @allure.title("钱包余额为 0 时注销成功")
    def test_deactivate_succeeds_when_balance_zero(self):
        """钱包余额为 0 时注销成功。"""
        response = UserAPI().delete_me()
        assert response.status_code == 200, response.text
