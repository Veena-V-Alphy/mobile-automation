from tests.BasePage import BasePage
import allure
import unittest
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

class PaymentGatewayTest(BasePage, unittest.TestCase):
    def __init__(self, driver):
        unittest.TestCase.__init__(self)
        BasePage.__init__(self, driver)

    def success_payment(self):
        with allure.step("Open Packages tab and start purchase"):
            package_tab = self.wait.until(EC.presence_of_element_located((AppiumBy.XPATH,'//android.widget.Button[contains(@content-desc, "Tab 4 of 5")]')))
            package_tab.click()

            buy_button1 = self.wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID,"Buy")))
            buy_button1.click()

            buy_button2 = self.wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID,"Buy")))
            buy_button2.click()

        with allure.step("Select Wallets payment option"):
            wallet_option=self.wait.until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR,'new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollIntoView(new UiSelector().description("Wallets"))')))
            wallet_option.click()

            test_wallet=self.wait.until(EC.presence_of_element_located((AppiumBy.XPATH,'//android.view.ViewGroup/android.webkit.WebView/android.webkit.WebView/android.view.View/android.view.View[2]/android.view.View')))
            test_wallet.click()

            proceed_to_pay=self.wait.until(EC.presence_of_element_located((AppiumBy.XPATH,'//android.widget.Button[@text="Proceed to Pay"]')))
            proceed_to_pay.click()

        with allure.step("Enter test wallet OTP"):
            otp=self.wait.until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().resourceId("basic-otp")')))
            otp.click()
            self.driver.execute_script("mobile: type", {"text": "111000"})

        with allure.step("Confirm successful payment"):
            success=self.wait.until(EC.presence_of_element_located((AppiumBy.XPATH,'//android.view.View[@resource-id="status-container"]/android.view.View[1]')))
            success.click()

            submit=self.wait.until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().text("Submit")')))
            submit.click()
