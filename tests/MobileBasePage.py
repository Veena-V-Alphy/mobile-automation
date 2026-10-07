import random

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MobileBasePage:
    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, timeout)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_all(self, by, value):
        return self.wait.until(EC.presence_of_all_elements_located((by, value)))

    def is_present(self, by, value):
        try:
            self.wait.until(EC.presence_of_element_located((by, value)))
            return True
        except TimeoutException:
            return False

    def click(self, by, value):
        element = self.find(by, value)
        element.click()
        return element

    def tap(self, accessibility_id):
        return self.click(AppiumBy.ACCESSIBILITY_ID, accessibility_id)

    def type_text(self, text):
        self.driver.execute_script("mobile: type", {"text": text})

    def enter_text(self, by, value, text, clear=False):
        element = self.find(by, value)
        element.click()
        if clear:
            element.clear()
        self.type_text(text)
        return element

    def scroll_to_and_click(self, description):
        return self.click(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollIntoView(new UiSelector().description("{description}"))'
        )

    def select_random_option(self, by, value):
        options = self.find_all(by, value)
        random.choice(options).click()
        return options
