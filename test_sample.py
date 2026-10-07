# Save this file in your repo as: tests/test_sample.py
# Works both locally (PyCharm + Android Studio emulator) and in GitHub Actions.
import os

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

APPIUM_URL = os.getenv("APPIUM_URL", "http://127.0.0.1:4723")
APP_PATH = os.getenv("APP_PATH", os.path.abspath("app/app-debug.apk"))


@pytest.fixture
def driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Android Emulator"
    options.udid = "emulator-5554"          # default name of the first emulator
    options.app = APP_PATH
    options.new_command_timeout = 300
    options.set_capability("appium:uiautomator2ServerInstallTimeout", 120000)
    options.set_capability("appium:adbExecTimeout", 120000)

    drv = webdriver.Remote(APPIUM_URL, options=options)
    drv.implicitly_wait(10)
    yield drv
    drv.quit()


def test_app_launches(driver):
    # Replace with a real element from your app
    assert driver.current_package is not None


# Example of a real interaction (edit the IDs to match your app):
# def test_login(driver):
#     driver.find_element(AppiumBy.ID, "com.example:id/username").send_keys("demo")
#     driver.find_element(AppiumBy.ID, "com.example:id/password").send_keys("secret")
#     driver.find_element(AppiumBy.ID, "com.example:id/login").click()
#     assert driver.find_element(AppiumBy.ID, "com.example:id/home_title").is_displayed()
