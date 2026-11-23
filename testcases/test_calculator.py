# flake8: noqa
import allure

from app.calculator import add, sub
import pytest

@allure.epic("计算模块")
@allure.feature("加减模块")
class TestCalculator:
    """计算器模块的测试用例"""

    # 使用参数化测试覆盖多种输入情况
    @pytest.mark.parametrize("a, b, expected", [
        (2, 3, 5),
        (0, 0, 0),
        (-1, 1, 0),
        (10, 20, 30),
        (100, 200, 300),
    ])
    @pytest.mark.smoke
    @allure.title("title 加法")
    @allure.description("""description 加法
    验证加法功能是否正常
    前置条件：
    测试步骤：
    预期结果：
    """)
    @allure.story("story 加法")
    def test_add(self, a, b, expected):
        allure.dynamic.title(f"{a}+{b}={expected}")
        """测试加法功能"""
        assert add(a, b) == expected

    @pytest.mark.parametrize("a, b, expected", [
        (5, 2, 3),
        (0, 0, 0),
        (10, 5, 5),
        (-1, -1, 0),
        (100, 50, 50),
    ])
    @allure.title("title 减法")
    @allure.description("""description 减法
    验证减法功能是否正常
    前置条件：
    测试步骤：
    预期结果：
    """)
    @allure.story("story 减法")
    def test_sub(self, a, b, expected):
        """测试减法功能"""
        allure.dynamic.title(f"{a}-{b}={expected}")
        assert sub(a, b) == expected
