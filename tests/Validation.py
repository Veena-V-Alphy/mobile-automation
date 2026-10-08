import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ToastValidator:
    @staticmethod
    def validate_toast_message(driver, expected_text, timeout=60, poll_interval=0.2, exact_match=True):
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                toast = driver.find_element(
                    AppiumBy.XPATH, f'//*[contains(@content-desc, "{expected_text}")]'
                )
                actual = toast.get_attribute("content-desc")
                if exact_match:
                    if actual == expected_text:
                        return actual
                else:
                    if expected_text in actual:
                        return actual
            except Exception:
                pass
            time.sleep(poll_interval)
        raise AssertionError(f"Toast with text '{expected_text}' did not appear within {timeout}s")


class AlertValidator:
    @staticmethod
    def validate_alert(driver, expected_text,locator_value,button_value,timeout=10, exact_match=True, dismiss=True):
        wait = WebDriverWait(driver, timeout)
        try:
            message = wait.until(EC.presence_of_element_located(
                (AppiumBy.XPATH, f'//android.view.View[@content-desc="{locator_value}"]/following-sibling::*[1]//*[@content-desc]')
            ))
        except Exception:
            raise AssertionError(f"Alert dialog did not appear within {timeout}s")

        actual = message.get_attribute("content-desc")
        if exact_match:
            if actual != expected_text:
                raise AssertionError(f"Alert text mismatch: expected '{expected_text}', got '{actual}'")
        else:
            if expected_text not in actual:
                raise AssertionError(f"Alert text '{expected_text}' not found in '{actual}'")

        if dismiss:
            ok_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, button_value)
            ok_button.click()

        return actual