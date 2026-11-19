# flake8: noqa
import allure
import pytest
import random

@allure.feature("随机模块")
class TestRandom:
    """随机模块的测试用例"""

    @allure.story("随机成功或失败")
    @pytest.mark.parametrize("run_index", range(1, 11), ids=[f"第{i}次" for i in range(1, 11)])
    def test_random(self, run_index):
        """随机成功或失败（执行10次）"""
        result = random.choice([True, False])
        with allure.step(f"第 {run_index} 次执行，随机结果：{'成功' if result else '失败'}"):
            assert result, f"第 {run_index} 次随机失败"