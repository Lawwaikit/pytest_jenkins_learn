"""模拟交易场景测试（调用已生成的 API 代码）。

不再依赖 fastapi.testclient；被测服务通过 requests + ApiSession 访问。
登录后用户由 conftest 的 active_user fixture 每例动态注册，trader fixture 负责充值初始资金。
价格从行情接口动态获取，不再硬编码。
"""
from __future__ import annotations

import pytest
import allure

from api.generated.trade_api import TradeAPI
from api.generated.user_api import UserAPI
from api.generated.wallet_api import WalletAPI
from keywords.wallet_kw import new_idempotency_key

INITIAL_BALANCE = 1_000_000  # ¥10,000.00


@pytest.fixture
def trader(active_user):
    """场景准备：给当前登录用户充值初始资金。"""
    response = WalletAPI().deposit(body={"amount_cents": INITIAL_BALANCE})
    assert response.status_code == 200, response.text
    return active_user


@pytest.fixture
def prices(trader) -> dict[str, int]:
    """从行情接口读取标的价格，避免用例里硬编码。"""
    response = TradeAPI().list_instruments()
    assert response.status_code == 200, response.text
    return {item["symbol"]: item["price_cents"] for item in response.data}


def _balance() -> int:
    response = WalletAPI().get_balance()
    assert response.status_code == 200, response.text
    return response.data["available_balance"]


def _positions() -> dict:
    response = TradeAPI().list_positions()
    assert response.status_code == 200, response.text
    return response.data

@allure.epic("交易模块")
class TestTrading:

    @allure.feature("行情查询")
    @allure.story("查询模拟行情")

    @allure.title("查询模拟行情")
    def test_list_instruments(self):
        """查看模拟行情。"""
        response = TradeAPI().list_instruments()
        assert response.status_code == 200, response.text
        items = response.data
        assert isinstance(items, list) and len(items) >= 1
        assert all(item["price_cents"] > 0 for item in items)


    @allure.feature("交易执行")
    @allure.story("买入扣减现金并新建持仓")

    @allure.title("买入扣减现金并新建持仓")
    def test_buy_deducts_cash_and_opens_position(self, trader, prices):
        """买入扣减现金并新建持仓。"""
        price = prices["600519"]
        response = TradeAPI().buy(body={"symbol": "600519", "quantity": 2})
        assert response.status_code == 200, response.text
        trade = response.data
        assert trade["side"] == 1
        assert trade["symbol"] == "600519"
        assert trade["price_cents"] == price
        assert trade["amount_cents"] == price * 2
        assert _balance() == INITIAL_BALANCE - price * 2

        positions = _positions()
        assert positions["total"] == 1
        assert positions["items"][0]["quantity"] == 2
        assert positions["items"][0]["avg_cost_cents"] == price
        assert positions["items"][0]["profit_cents"] == 0


    @allure.feature("交易执行")
    @allure.story("余额不足时买入被拒绝")

    @allure.title("余额不足时买入被拒绝")
    def test_buy_insufficient_balance_rejected(self, trader, prices):
        """余额不足时买入被拒绝。"""
        quantity = INITIAL_BALANCE // prices["600519"] + 1
        response = TradeAPI().buy(
            body={"symbol": "600519", "quantity": quantity}
        )
        assert response.status_code == 422, response.text
        assert _balance() == INITIAL_BALANCE


    @allure.feature("交易执行")
    @allure.story("相同幂等键的买入只成交一次")

    @allure.title("相同幂等键的买入只成交一次")
    def test_buy_with_same_idempotency_key_only_once(self, trader, prices):
        """相同幂等键的买入只成交一次。"""
        key = new_idempotency_key("trade")
        body = {"symbol": "300750", "quantity": 1, "idempotency_key": key}
        api = TradeAPI()
        first = api.buy(body=body)
        second = api.buy(body=body)
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert second.data["trade_no"] == first.data["trade_no"]
        assert _balance() == INITIAL_BALANCE - prices["300750"]
        assert _positions()["items"][0]["quantity"] == 1


    @allure.feature("交易执行")
    @allure.story("卖出回款并减少持仓，全部卖出后删除持仓记录")

    @allure.title("卖出回款并减少持仓，全部卖出后删除持仓记录")
    def test_sell_returns_cash_and_reduces_position(self, trader, prices):
        """卖出回款并减少持仓，全部卖出后删除持仓记录。"""
        price = prices["000001"]
        buy = TradeAPI().buy(body={"symbol": "000001", "quantity": 10})
        assert buy.status_code == 200, buy.text

        sell = TradeAPI().sell(body={"symbol": "000001", "quantity": 4})
        assert sell.status_code == 200, sell.text
        assert sell.data["side"] == 2
        assert sell.data["amount_cents"] == price * 4
        assert _balance() == INITIAL_BALANCE - price * 6
        assert _positions()["items"][0]["quantity"] == 6

        all_out = TradeAPI().sell(body={"symbol": "000001", "quantity": 6})
        assert all_out.status_code == 200, all_out.text
        assert _positions()["total"] == 0


    @allure.feature("交易执行")
    @allure.story("持仓不足时卖出被拒绝")

    @allure.title("持仓不足时卖出被拒绝")
    def test_sell_insufficient_position_rejected(self, trader):
        """持仓不足时卖出被拒绝。"""
        response = TradeAPI().sell(body={"symbol": "000001", "quantity": 1})
        assert response.status_code == 422, response.text
        assert _balance() == INITIAL_BALANCE


    @allure.feature("交易执行")
    @allure.story("成交历史分页查询")

    @allure.title("成交历史分页查询")
    def test_trade_history_pagination(self, trader):
        """成交历史分页查询。"""
        api = TradeAPI()
        for _ in range(2):
            response = api.buy(body={"symbol": "000001", "quantity": 1})
            assert response.status_code == 200, response.text
        response = api.list_history(query={"page": 1, "size": 1})
        assert response.status_code == 200, response.text
        data = response.data
        assert data["total"] == 2
        assert len(data["items"]) == 1


    @allure.feature("交易执行")
    @allure.story("注销时持仓未平仓被拒绝")

    @allure.title("注销时持仓未平仓被拒绝")
    def test_deactivate_rejected_when_position_open(self, trader, prices):
        """持仓未平仓时注销被拒绝。"""
        price = prices["000001"]
        buy = TradeAPI().buy(body={"symbol": "000001", "quantity": 1})
        assert buy.status_code == 200, buy.text
        withdraw = WalletAPI().withdraw(
            body={"amount_cents": INITIAL_BALANCE - price}
        )
        assert withdraw.status_code == 200, withdraw.text
        response = UserAPI().delete_me()
        assert response.status_code == 409, response.text
        assert response.data["detail"] == "All positions must be closed before deactivation"
