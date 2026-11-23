import json
import allure


@allure.epic("用户管理")
@allure.feature("用户登录")
@allure.story("正常登录")
@allure.title("正确账号密码登录成功")
@allure.description("验证用户使用正确账号密码登录后能够获取 Token。")
def test_login():

    with allure.step("准备登录参数"):
        request_data = {
            "username": "admin",
            "password": "123456"
        }

    with allure.step("模拟发送登录请求"):
        response_data = {
            "code": 0,
            "message": "success",
            "token": "abcdef123456"
        }

        allure.attach(
            json.dumps(
                request_data,
                ensure_ascii=False,
                indent=4
            ),
            name="请求参数",
            attachment_type=allure.attachment_type.JSON
        )

        allure.attach(
            json.dumps(
                response_data,
                ensure_ascii=False,
                indent=4
            ),
            name="响应数据",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("校验 HTTP 业务响应"):
        assert response_data["code"] == 0

    with allure.step("校验 Token"):
        assert response_data["token"]