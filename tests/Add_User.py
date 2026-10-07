from tests import Validation
from tests.MobileBasePage import MobileBasePage
from tests.Validation import ToastValidator
import allure
import random
import unittest
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

class AddUSer(MobileBasePage, unittest.TestCase):
    def __init__(self, driver):
        unittest.TestCase.__init__(self)
        MobileBasePage.__init__(self, driver)

    @staticmethod
    def random_mobile_number():
        return random.choice("6789") + "".join(str(random.randint(0, 9)) for _ in range(9))

    def add_counsellor(self):
        with allure.step("Open More tab"):
            more= self.wait.until(EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.Button[contains(@content-desc,"Tab 5 of 5")]')))
            more.click()

        with allure.step("Open Add User"):
            add_user_button= self.wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, 'Add User')
            ))
            add_user_button.click()

            add_button= self.wait.until(EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().className("android.widget.Button").instance(2)')
            ))
            add_button.click()

        with allure.step("Enter a fresh mobile number"):
            # stored so later steps in the flow (e.g. submit/verify) can reuse the same number
            self.mobile_number = self.random_mobile_number()
            allure.attach(self.mobile_number, name="mobile number", attachment_type=allure.attachment_type.TEXT)
            mobile_field = self.wait.until(EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.EditText')
            ))
            mobile_field.click()
            mobile_field.clear()
            self.driver.execute_script("mobile: type", {"text": self.mobile_number})

        with allure.step("Select Counsellor role"):
            counsellor_radio_button = self.wait.until(EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.RadioButton").instance(1)')
            ))
            counsellor_radio_button.click()

        with allure.step("Select a random package"):
            select_package= self.wait.until(EC.presence_of_element_located(
                (AppiumBy.XPATH, '//*[contains(@content-desc, "Choose a package")]')
            ))
            select_package.click()

            # locator is a placeholder for whatever class/container wraps the opened package rows
            package_items = self.wait.until(EC.presence_of_all_elements_located(
                (AppiumBy.CLASS_NAME, "android.widget.Button")
            ))
            random.choice(package_items).click()

        with allure.step("Submit the form"):
            submit=self.wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID,"Submit")
            ))
            submit.click()

        with allure.step("Validate success alert"):
            # expected_text is a placeholder for the actual alert copy shown on success
            Validation.AlertValidator.validate_alert(self.driver, "Package assigned successfully","Message", "OK")


