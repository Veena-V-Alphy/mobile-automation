import time
import allure
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ToastValidator:
    @staticmethod
    def _matches(actual, expected_text, exact_match):
        return actual == expected_text if exact_match else expected_text in actual

    @staticmethod
    def validate_toast_message(driver, expected_text, timeout=60, poll_interval=0.2, exact_match=True):
        # Checks both places a message can show up: the app's own (Flutter)
        # toast, exposed as content-desc, and a native Android toast
        # (android.widget.Toast, exposed as text).
        #
        # Every near-miss is recorded, so a failure says what the app showed
        # instead. Previously every exception was swallowed and a
        # content-desc that contained the text but wasn't an exact match
        # (e.g. "Access denied." or a longer message) failed as "did not
        # appear" with no hint (15 Oct CI: tc1, tc18, tc21, tc34, tc40).
        seen = []
        last_error = None
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                for toast in driver.find_elements(
                        AppiumBy.XPATH, f'//*[contains(@content-desc, "{expected_text}")]'):
                    actual = toast.get_attribute("content-desc") or ""
                    if ToastValidator._matches(actual, expected_text, exact_match):
                        return actual
                    if actual not in seen:
                        seen.append(actual)
                for toast in driver.find_elements(AppiumBy.XPATH, "//android.widget.Toast"):
                    actual = toast.get_attribute("text") or ""
                    if ToastValidator._matches(actual, expected_text, exact_match):
                        return actual
                    if actual and actual not in seen:
                        seen.append(actual)
            except Exception as error:
                last_error = error
            time.sleep(poll_interval)

        try:
            allure.attach(driver.page_source, f"page source - toast '{expected_text}' not found",
                          allure.attachment_type.XML)
        except Exception:
            pass
        detail = (f" Toast/message texts seen instead: {seen}" if seen
                  else " No related or native toast text was seen.")
        if last_error is not None and not seen:
            detail += f" Last lookup error: {type(last_error).__name__}: {str(last_error).splitlines()[0][:200]}"
        raise AssertionError(f"Toast with text '{expected_text}' did not appear within {timeout}s.{detail}")


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