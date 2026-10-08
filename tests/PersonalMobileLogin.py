import unittest
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

from tests import Validation
from tests.MobileBasePage import MobileBasePage
from tests.Validation import ToastValidator

MOBILE_NUMBER_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
OTP_FIELD = (AppiumBy.XPATH,
             "//android.widget.FrameLayout[@resource-id='android:id/content']/android.widget.FrameLayout/"
             "android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/"
             "android.view.View/android.widget.EditText[2]")
REGISTRATION_PAGE = "Provide details to complete registration."
# The loader is drawn next to the registration form's container (the view that
# directly holds the page title). Use "*[...]" (direct child), not ".//*[...]"
# (any descendant): the descendant version also matched the outermost layout,
# whose sibling is the always-present navigation-bar view on the CI emulator,
# so the "loader" never disappeared and every registration test timed out.
REGISTRATION_LOADER = (AppiumBy.XPATH,
                       f'//*[*[@content-desc="{REGISTRATION_PAGE}"]]/following-sibling::android.view.View')
PERSONAL_TEST_NUMBER = "9902985281"
APP_ID = "com.winray.alphy"

# Screens the app can be on right after it is relaunched
PERSONAL_OPTION = (AppiumBy.ACCESSIBILITY_ID, "Personal")
HOME_MORE_TAB = (AppiumBy.XPATH, '//android.widget.Button[contains(@content-desc, "Tab 5 of 5")]')
INTRO_SKIP = (AppiumBy.ACCESSIBILITY_ID, "Skip")
REGISTRATION_HEADER = (AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
PERMISSION_ALLOW = (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_button")
# Android's "<app> isn't responding" popup (shows on slow emulators)
ANR_DIALOG = (AppiumBy.XPATH, '//*[contains(@text, "isn\'t responding")]')
# Registration form - found by their hint text, not by position: the app only
# exposes the fields currently on screen, so "8th EditText" breaks once the
# form scrolls (e.g. when the keyboard is open).
SUBMIT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Submit")
SCHOOL_FIELD = (AppiumBy.XPATH, '//android.widget.EditText[@hint="School/Institute Name *"]')


class PersonalMobileLoginPage(MobileBasePage, unittest.TestCase):
    def __init__(self, driver, page=None):
        unittest.TestCase.__init__(self)
        MobileBasePage.__init__(self, driver)
        self.page = page

    # ---- shared helpers -------------------------------------------------

    def _assert_error_message(self, locator, expected_text, by=AppiumBy.ACCESSIBILITY_ID,
                               fail_message="Expected validation error message did not appear"):
        try:
            error_element = self.wait.until(EC.visibility_of_element_located((by, locator)))
        except TimeoutException:
            self.fail(fail_message)

        actual_error_text = error_element.get_attribute("content-desc")
        self.assertTrue(error_element.is_displayed(), "Error message is not visible")
        self.assertEqual(actual_error_text, expected_text)

    def _current_screen(self):
        """Return which known screen is showing right now, or None if the app
        is still on its splash/loading screen."""
        d = self.driver
        if d.find_elements(*ANR_DIALOG):
            return "not-responding"
        if d.find_elements(*PERMISSION_ALLOW):
            return "permission"
        if d.find_elements(*PERSONAL_OPTION):
            return "chooser"
        if d.find_elements(*HOME_MORE_TAB):
            return "home"
        if d.find_elements(*INTRO_SKIP):
            return "intro"
        if d.find_elements(*REGISTRATION_HEADER):
            return "registration"
        return None

    def _reset_app_data(self):
        # Wipes the app's saved session so it starts at the login chooser again.
        self.driver.execute_script("mobile: clearApp", {"appId": APP_ID})
        self.driver.activate_app(APP_ID)

    def _dismiss_not_responding_popup(self):
        with allure.step("Dismiss Android's 'isn't responding' popup"):
            title = self.driver.find_element(*ANR_DIALOG).get_attribute("text") or ""
            # Another app (e.g. Pixel Launcher) froze: closing it is harmless.
            # Our own app froze: choose Wait so it isn't killed mid-test.
            button = "Close app" if "alphy" not in title.lower() else "Wait"
            self.driver.find_element(AppiumBy.XPATH, f'//*[@text="{button}"]').click()
            self.driver.activate_app(APP_ID)

    def _ensure_at_login_chooser(self):
        # The app keeps its data (no_reset=True), so after a relaunch it can be on
        # the splash screen, the login chooser, the home screen (previous login
        # survived), the intro pages, or the registration page a previous test
        # stopped on. Wait until it settles on one of them, then get back to the
        # chooser from there. Checking only once, straight after the relaunch,
        # sees the splash screen and wrongly assumes the user is logged in.
        for _ in range(5):
            try:
                screen = self.wait.until(lambda d: self._current_screen())
            except TimeoutException:
                screen = "unknown"

            if screen == "chooser":
                return
            if screen == "not-responding":
                self._dismiss_not_responding_popup()
            elif screen == "permission":
                self.driver.find_element(*PERMISSION_ALLOW).click()
            elif screen == "home":
                with allure.step("Previous session still active - log out to reach the login chooser"):
                    self.logout()
            elif screen == "intro":
                with allure.step("Previous login stopped on the intro pages - finish it and log out"):
                    self.skip_intro_pages()
                    self.selecting_preference()
                    self.logout()
            else:
                # Registration page (can't log out from there) or an unknown screen
                with allure.step(f"App on '{screen}' screen - clear app data to reach the login chooser"):
                    self._reset_app_data()

        # Final check - fails with a clear timeout if the chooser still isn't there
        self.find(*PERSONAL_OPTION)

    def _open_personal_login(self):
        self._ensure_at_login_chooser()
        with allure.step("Open Personal login"):
            self.tap("Personal")

    def _reach_personal_otp_screen(self, number=PERSONAL_TEST_NUMBER):
        # Every test relaunches the app fresh (see BaseTest.reset_mobile_app),
        # so each tc that needs the OTP screen must get there itself rather
        # than assuming a previous test already navigated it into place.
        self._open_personal_login()
        with allure.step(f"Enter mobile number {number} and continue"):
            self.enter_text(*MOBILE_NUMBER_FIELD, number, clear=True)
            self.tap("Continue")

    def _login_with_otp(self, otp_text=None, clear=False, step_label="Enter OTP and login"):
        with allure.step(step_label):
            otp = self.find(*OTP_FIELD)
            otp.click()
            if clear:
                otp.clear()
            if otp_text is not None:
                self.type_text(otp_text)
            self.tap("Login")

    def _complete_login_flow(self):
        with allure.step("Check whether the student registration page is displayed"):
            registration_page_displayed = self.is_present(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)

        # When the registration page is not shown, this login already reaches the
        # home screen, so continue straight through to the logout flow here -
        # otherwise tc6-tc8 handle the registration page and log out afterwards.
        if not registration_page_displayed:
            self.intro_pages()
            self.selecting_preference()
            self.logout()

        return registration_page_displayed

    def _scroll_until_present(self, by, value, max_swipes=4):
        # Scroll the form down a step at a time until the element is on screen.
        for _ in range(max_swipes):
            if self.driver.find_elements(by, value):
                return
            try:
                self.driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollForward()')
            except Exception:
                pass  # this call scrolls but never returns an element; also raises when nothing is scrollable

    def _click_submit(self):
        # With the keyboard closed, the whole registration form fits on the CI
        # emulator's tall screen, so there is nothing to scroll and
        # scroll_to_and_click("Submit") can fail to tap. Tap it directly when it
        # is already on screen; otherwise fall back to scrolling to it.
        buttons = self.driver.find_elements(*SUBMIT_BUTTON)
        if buttons:
            buttons[0].click()
        else:
            self.scroll_to_and_click("Submit")

    def _hide_keyboard(self):
        try:
            if self.driver.is_keyboard_shown():
                self.driver.hide_keyboard()
        except Exception:
            pass

    def _search_and_select(self, search_text, result_id):
        self.enter_text(*MOBILE_NUMBER_FIELD, search_text)
        self.tap(result_id)

    def _enter_registration_field(self, instance, text, clear=False):
        return self.enter_text(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().className("android.widget.EditText").instance({instance})',
            text, clear=clear
        )

    def _select_random_dropdown(self, field_index, search_text=None):
        self.click(AppiumBy.XPATH, f'(//android.widget.EditText)[{field_index}]')
        if search_text is not None:
            self.enter_text(*MOBILE_NUMBER_FIELD, search_text)
        self.select_random_option(AppiumBy.CLASS_NAME, "android.widget.Button")

    # ---- flows shared across login types ---------------------------------

    def skip_intro_pages(self):
        with allure.step("Skip through intro pages"):
            while self.is_present(AppiumBy.ACCESSIBILITY_ID, "Next", timeout=10):
                self.tap("Next")

            self.tap("Get Started")


    def selecting_preference(self):
        with allure.step("Search and select hierarchy"):
            self._search_and_select("Automation hierarchy", "Automation hierarchy")

        with allure.step("Search and select board"):
            self._search_and_select("MH Board", "MH Board")

        with allure.step("Search and select subject"):
            self._search_and_select("10th MH Board Science", "10th MH Board Science")

    def find_login_options(self):
        with allure.step("Locate the Personal and Institute login options"):
            personal_option = self.find(AppiumBy.ACCESSIBILITY_ID, "Personal")
            institute_option = self.find(AppiumBy.ACCESSIBILITY_ID, "Institute")

        self.assertTrue(personal_option.is_displayed(), "Personal login option is not visible")
        self.assertTrue(institute_option.is_displayed(), "Institute login option is not visible")

    def logout(self):
        with allure.step("Click on More"):
            self.click(AppiumBy.XPATH, '//android.widget.Button[contains(@content-desc, "Tab 5 of 5")]')
            self.scroll_to_and_click("Logout")

    def tc1(self):
        try:
            self.tc14()
        finally:
            if self.is_present(AppiumBy.ACCESSIBILITY_ID, "Skip", timeout=10):
                self.skip_intro_pages()
                self.selecting_preference()
                self.logout()

    def tc2(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Check whether the student registration page is displayed"):
            registration_page_displayed = self.is_present(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
        return registration_page_displayed

    def tc3(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))

        with allure.step("Click on the Submit button in the registration page"):
            self._click_submit()
            # The first tap can land before the freshly loaded form responds to it
            # (seen on the CI emulator: no errors at all after Submit). If no
            # "Required" message appears within 10s, tap Submit once more.
            if not self.is_present(AppiumBy.XPATH, '//android.view.View[@content-desc="Required"]', timeout=10):
                self._click_submit()

        with allure.step("Check for mandatory fields"):
            for i in range(6):
                self._assert_error_message(
                    f'(//android.view.View[@content-desc="Required"])[{i + 1}]',
                    "Required",
                    by=AppiumBy.XPATH,
                    fail_message=f"Required error element #{i + 1} not found",
                )

    def tc4(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))
        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena")
            self._enter_registration_field(1, "V")

        with allure.step("Enter improper email format"):
            self._enter_registration_field(2, "veena")
            self._click_submit()
            self._assert_error_message(
                '//android.view.View[@content-desc="Enter valid email"]',
                "Enter valid email",
                by=AppiumBy.XPATH,
                fail_message="Message not found",
            )

    def tc5(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))
        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena")
            self._enter_registration_field(1, "V")

        with allure.step("Select the duplicate email ID"):
            self._enter_registration_field(2, "ankush.winray@gmail.com", clear=True)
            # Close the keyboard first so the email field loses focus - on the
            # phone, scrolling to Submit did this; on the emulator nothing scrolls.
            self._hide_keyboard()
            self._click_submit()
            self._assert_error_message(
                '//android.view.View[@content-desc="Duplicate email"]',
                "Duplicate email",
                by=AppiumBy.XPATH,
                fail_message="Message not found",
            )

    def tc6(self):
        from tests.AlphyWebLogin import SuperAdminLoginPage
        from Config.DesiredCap import DesiredCap
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))
        self.page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        status=SuperAdminLoginPage(self.page, self.driver).student_role_status_change()

        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena", clear=True)
            self._enter_registration_field(1, "V", clear=True)

        with allure.step("Enter email ID"):
            self._enter_registration_field(2, "veena@gmail.com", clear=True)

        with allure.step("Select the random state"):
            self._select_random_dropdown(4, "maha")

        with allure.step("Select the random city"):
            self._select_random_dropdown(5, "mum")

        with allure.step("Check if the student role is present"):
            role=self.find(AppiumBy.XPATH,"//android.widget.FrameLayout[@resource-id='android:id/content']/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.EditText[6]")
            role.click()
            student_role_present = self.is_present(AppiumBy.ACCESSIBILITY_ID, "Student")
            try:
                self.assertFalse(student_role_present, "Inactive 'student' role is still visible in the dropdown")
            finally:
                SuperAdminLoginPage(self.page, self.driver).change_status(status)


    def tc7(self):
        from tests.AlphyWebLogin import AlphyWebLoginPage
        from Config.DesiredCap import DesiredCap
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))
        self.page.goto(DesiredCap.WEB_URLS["alphylogin"])
        AlphyWebLoginPage(self.page, self.driver).inactive_hierarchy()

        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena", clear=True)
            self._enter_registration_field(1, "V", clear=True)

        with allure.step("Enter email ID"):
            self._enter_registration_field(2, "veena@gmail.com", clear=True)

        with allure.step("Select the random state"):
            self._select_random_dropdown(4, "maha")

        with allure.step("Select the random city"):
            self._select_random_dropdown(5, "mum")

        with allure.step("Select the role"):
            self._select_random_dropdown(6)

        with allure.step("Select the Interested class"):
            hierarchy = self.find(AppiumBy.XPATH,
                             "//android.widget.FrameLayout[@resource-id='android:id/content']/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.EditText[7]")
            hierarchy.click()
            hierarchy_present = self.is_present(AppiumBy.ACCESSIBILITY_ID, "10th MH Board Science")
            try:
                self.assertFalse(hierarchy_present, "Inactive hierarchy role is still visible in the dropdown")
            finally:
                AlphyWebLoginPage(self.page, self.driver).change_status()

    def tc8(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Wait for the registration page to finish loading"):
            self.find(AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))

        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena", clear=True)
            self._enter_registration_field(1, "V", clear=True)

        with allure.step("Enter email ID"):
            self._enter_registration_field(2, "veena@gmail.com", clear=True)

        with allure.step("Select the random state"):
            self._select_random_dropdown(4, "maha")

        with allure.step("Select the random city"):
            self._select_random_dropdown(5, "mum")

        with allure.step("Select the role"):
            self._select_random_dropdown(6)

        with allure.step("Select the Interested class"):
            self._select_random_dropdown(7)

        with allure.step("Enter the school/institute name"):
            # Found by hint text, scrolling down only if it isn't on screen yet.
            self._scroll_until_present(*SCHOOL_FIELD)
            self.enter_text(*SCHOOL_FIELD, "XYZ School")

        with allure.step("Click on the Submit button"):
            self._click_submit()

        Validation.AlertValidator.validate_alert(self.driver, "Are you sure you want to proceed?", "Terms and Conditions", "I Agree")
        self.skip_intro_pages()
        self.selecting_preference()
        self.logout()

    # Personal Login Page
    def tc9(self):
        self._open_personal_login()
        with allure.step("Continue without entering a mobile number"):
            self.tap("Continue")

        with allure.step("Validate blank mobile number error is shown"):
            self._assert_error_message("Please enter mobile number", "Please enter mobile number")

    def tc10(self):
        self._open_personal_login()
        with allure.step("Enter mobile number shorter than 10 digits"):
            self.enter_text(*MOBILE_NUMBER_FIELD, "123")
            self.tap("Continue")

        with allure.step("Validate 10-digit mobile number error is shown"):
            self._assert_error_message("Please enter 10 digit mobile number", "Please enter 10 digit mobile number")

    def tc11(self):
        self._open_personal_login()
        with allure.step("Enter inactive mobile number"):
            self.enter_text(*MOBILE_NUMBER_FIELD, PERSONAL_TEST_NUMBER, clear=True)
            self.tap("Continue")

        with allure.step("Validate 10-digit mobile number error is shown"):
            ToastValidator.validate_toast_message(self.driver, "User is inactive. Please contact admin.")

    # Blank OTP
    def tc12(self):
        self._reach_personal_otp_screen()

        self._login_with_otp(step_label="Leave OTP blank and attempt login")

        with allure.step("Validate 'Enter OTP first' toast is shown"):
            ToastValidator.validate_toast_message(self.driver, "Enter OTP first")

    def tc13(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("111")

        with allure.step("Validate 'Invalid OTP' toast is shown"):
            ToastValidator.validate_toast_message(self.driver, "Invalid OTP")

    def tc14(self):
        self._reach_personal_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Validate 'Access denied' toast is shown"):
            ToastValidator.validate_toast_message(self.driver, "Access denied")

    def tc15(self):
        # A deactivated user is rejected right after Continue with the same
        # "User is inactive" toast as tc3, regardless of which admin panel
        # (company admin vs superadmin) performed the deactivation - the app
        # never lets the flow reach the OTP screen at all in this state.
        self.tc11()

    def tc16(self):
        self.tc14()

    def tc17(self):
        try:
            self.tc14()
        finally:
            if self.is_present(AppiumBy.ACCESSIBILITY_ID, "Skip", timeout=10):
                self.skip_intro_pages()
                self.selecting_preference()
                self.logout()




















"""    # TC7: Download a video from the content screen
    def tc117(self):
        with allure.step("Login and navigate to content screen"):
            # Login first, then navigate through intro and preference selection to reach the content screen
            self.tc1()
            self.tc2()
            self.tc3()
            self.tc4()

        with allure.step("Navigate to a video in the content list"):
            self.tap("10th MH Science")
            self.click(AppiumBy.XPATH, '//*[contains(@content-desc, "Physics")]')
            self.click(AppiumBy.XPATH, '//*[contains(@content-desc, "Chapter-Electricity")]')
            self.click(AppiumBy.XPATH, '//*[contains(@content-desc, "MCQ")]')
            self.click(AppiumBy.XPATH, '//*[contains(@content-desc, "Video")]')

        with allure.step("Download the video"):
            self.click(AppiumBy.XPATH, '//*[contains(@content-desc, "Download")]')
            self.find(AppiumBy.XPATH, '//*[contains(@content-desc, "Downloaded")]')

        with allure.step("Validate download confirmation toast"):
            ToastValidator.validate_toast_message(self.driver, "Video downloaded successfully", exact_match=False)

"""