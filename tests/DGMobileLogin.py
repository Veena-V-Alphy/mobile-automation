import time
import unittest
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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
# (any descendant): the descendant version also matches the outermost layout,
# whose sibling is the always-present navigation-bar view on the CI emulator,
# so the "loader" never disappears and every registration test times out.
REGISTRATION_LOADER = (AppiumBy.XPATH,
                       f'//*[*[@content-desc="{REGISTRATION_PAGE}"]]/following-sibling::android.view.View')
INSTITUTE_PICKER_TITLE = "Select your Institute to Login"
DG_TEST_NUMBER = "9902985281"
# Old name, kept so any existing imports keep working
PERSONAL_TEST_NUMBER = DG_TEST_NUMBER
APP_ID = "com.winray.alphy"

# Screens the app can be on right after it is relaunched
INSTITUTE_OPTION = (AppiumBy.ACCESSIBILITY_ID, "Institute")
HOME_MORE_TAB = (AppiumBy.XPATH, '//android.widget.Button[contains(@content-desc, "Tab 5 of 5")]')
INTRO_SKIP = (AppiumBy.ACCESSIBILITY_ID, "Skip")
INTRO_NEXT = (AppiumBy.ACCESSIBILITY_ID, "Next")
INTRO_GET_STARTED = (AppiumBy.ACCESSIBILITY_ID, "Get Started")
LOGOUT_OPTION = (AppiumBy.ACCESSIBILITY_ID, "Logout")
REGISTRATION_HEADER = (AppiumBy.ACCESSIBILITY_ID, REGISTRATION_PAGE)
INSTITUTE_PICKER = (AppiumBy.ACCESSIBILITY_ID, INSTITUTE_PICKER_TITLE)
DG_INSTITUTE_NAME = "DG UAT"
DG_INSTITUTE_OPTION = (AppiumBy.ACCESSIBILITY_ID, DG_INSTITUTE_NAME)
ACCESS_DENIED_TOAST = (AppiumBy.XPATH, '//*[contains(@content-desc, "Access denied")]')
PERMISSION_ALLOW = (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_button")
# Android's "<app> isn't responding" popup (shows on slow emulators)
ANR_DIALOG = (AppiumBy.XPATH, '//*[contains(@text, "isn\'t responding")]')
SUBMIT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Submit")
REQUIRED_MESSAGE = (AppiumBy.XPATH, '//android.view.View[@content-desc="Required"]')
# Registration fields in screen order (their hint/label text). Fields are found
# by hint, not by position: the app only exposes the fields currently on
# screen, so "6th EditText" breaks once the form scrolls (e.g. keyboard open).
REGISTRATION_FIELD_HINTS = [
    "First Name *",                           # 0
    "Last Name *",                            # 1
    "Email *",                                # 2
    "State *",                                # 3
    "City *",                                 # 4
    "You are signing up as? *",               # 5
    "Which Class are you interested in? *",   # 6
    "School/Institute Name *",                # 7
]


class DGMobileLoginPage(MobileBasePage, unittest.TestCase):
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
        if d.find_elements(*INSTITUTE_OPTION):
            return "chooser"
        if d.find_elements(*HOME_MORE_TAB):
            return "home"
        if d.find_elements(*INTRO_SKIP):
            return "intro"
        if d.find_elements(*REGISTRATION_HEADER):
            return "registration"
        if d.find_elements(*INSTITUTE_PICKER):
            return "institute-picker"
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
        # survived), the intro pages, the registration page, or the institute
        # picker a previous test stopped on. Wait until it settles on one of
        # them, then get back to the chooser from there.
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
                # Registration page / institute picker (no logout there) or unknown
                with allure.step(f"App on '{screen}' screen - clear app data to reach the login chooser"):
                    self._reset_app_data()

        # Final check - fails with a clear timeout if the chooser still isn't there
        self.find(*INSTITUTE_OPTION)

    def _open_institutional_login(self):
        self._ensure_at_login_chooser()
        with allure.step("Open Institutional login"):
            self.tap("Institute")

    def _reach_institution_otp_screen(self, number=DG_TEST_NUMBER):
        # Every test relaunches the app fresh (see BaseTest.reset_mobile_app),
        # so each tc that needs the OTP screen must get there itself rather
        # than assuming a previous test already navigated it into place.
        self._open_institutional_login()
        with allure.step(f"Enter mobile number {number} and continue"):
            self.enter_text(*MOBILE_NUMBER_FIELD, number, clear=True)
            self._tap_with_keyboard_closed("Continue")

    def _login_with_otp(self, otp_text=None, clear=False, step_label="Enter OTP and login"):
        with allure.step(step_label):
            otp = self.find(*OTP_FIELD)
            otp.click()
            if clear:
                otp.clear()
            if otp_text is not None:
                self.type_text(otp_text)
            self._tap_with_keyboard_closed("Login")

    def _wait_for_registration_page(self):
        with allure.step("Wait for the registration page to finish loading"):
            self.find(*REGISTRATION_HEADER)
            self.wait.until(EC.invisibility_of_element_located(REGISTRATION_LOADER))
            # Wait until the First Name field can actually be tapped - the loader
            # disappearing is not enough on the slower CI emulator.
            self.wait.until(EC.element_to_be_clickable(
                (AppiumBy.XPATH, f'//android.widget.EditText[@hint="{REGISTRATION_FIELD_HINTS[0]}"]')))
            time.sleep(1)

    def _wait_for_post_login_screen(self, timeout=60):
        """After tapping Login, wait until the app leaves the OTP screen and
        return where it went: "registration", "intro", "home",
        "institute-picker" (or "chooser"). Returns "unknown" if none of
        them shows within the timeout, e.g. still on the OTP screen."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            screen = self._current_screen()
            if screen == "not-responding":
                self._dismiss_not_responding_popup()
                continue
            if screen == "permission":
                self.driver.find_element(*PERMISSION_ALLOW).click()
                continue
            if screen is not None:
                return screen
            time.sleep(1)
        return "unknown"

    def _screen_after_login(self):
        # A user registered in more than one institute (tc29 adds the test number
        # to Westfield) gets the institute picker before anything else. Choose
        # DG there, so the check that follows looks at the DG login.
        screen = self._wait_for_post_login_screen()
        if screen == "institute-picker":
            dg_option = self.driver.find_elements(*DG_INSTITUTE_OPTION)
            if dg_option:
                with allure.step(f"Institute picker shown (user is in more than one institute) - "
                                 f"choose '{DG_INSTITUTE_NAME}'"):
                    dg_option[0].click()
                screen = self._wait_for_post_login_screen()
        return screen

    def _report_unexpected_screen(self, screen, expected):
        # print() lands in "Captured stdout" of the CI log, the page source in Allure
        message = f"Expected the {expected} after login, but the app is on the '{screen}' screen"
        print(f"[DG login] {message}")
        try:
            allure.attach(self.driver.page_source, f"page source - {screen} instead of {expected}",
                          allure.attachment_type.XML)
        except Exception:
            pass
        return message

    def _login_to_registration_page(self):
        self._reach_institution_otp_screen()
        self._login_with_otp("2222")
        # Fail straight away with the screen the app is actually on. Before,
        # every registration test (tc23-tc28) waited for the registration
        # header and failed with a bare TimeoutException (15 Oct CI).
        screen = self._screen_after_login()
        if screen != "registration":
            raise AssertionError(
                self._report_unexpected_screen(screen, "student registration page")
                + ". This test needs a first-time (unregistered) DG user - see tc22.")
        self._wait_for_registration_page()

    def _scroll_until_present(self, by, value, max_swipes=4):
        # Scroll the form down, then back up, a step at a time until the element
        # is on screen. Does nothing if it is already visible.
        for direction in ("scrollForward", "scrollBackward"):
            for _ in range(max_swipes):
                if self.driver.find_elements(by, value):
                    return
                try:
                    self.driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).{direction}()')
                except Exception:
                    pass  # this call scrolls but never returns an element; also raises when nothing is scrollable

    def _registration_field(self, hint):
        # Closing the keyboard first lets the whole form fit on a tall screen;
        # scrolling covers smaller screens.
        locator = (AppiumBy.XPATH, f'//android.widget.EditText[@hint="{hint}"]')
        self._hide_keyboard()
        self._scroll_until_present(*locator)
        return locator

    def _click_submit(self):
        # With the keyboard closed the whole form can fit on the screen, so there
        # is nothing to scroll and scroll_to_and_click("Submit") can fail to tap.
        # Tap it directly when it is on screen; otherwise scroll to it.
        self._hide_keyboard()
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

    def _tap_with_keyboard_closed(self, accessibility_id):
        # Close the keyboard before tapping a button that sits under it. Seen on
        # the Redmi (13 Oct, tc1): with the keyboard still open after typing the
        # OTP, the "Login" tap landed on the keyboard and opened Gboard settings,
        # so the login was never sent.
        self._hide_keyboard()
        return self.tap(accessibility_id)

    def _collect_required_fields(self, max_swipes=4):
        # Returns the labels of all fields showing a "Required" message, scrolling
        # from the top of the form to the bottom to see every field.
        required = (AppiumBy.XPATH, '//android.widget.EditText[android.view.View[@content-desc="Required"]]')
        self._hide_keyboard()
        self.find(*required)  # wait until the first error has appeared
        scroll = 'new UiScrollable(new UiSelector().scrollable(true).instance(0)).{}()'
        for _ in range(max_swipes):  # back to the top first
            try:
                self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, scroll.format("scrollBackward"))
            except Exception:
                pass
        found = set()
        for _ in range(max_swipes + 1):
            for field in self.driver.find_elements(*required):
                label = field.get_attribute("hint") or field.get_attribute("text") or field.id
                found.add(label)
            try:
                self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, scroll.format("scrollForward"))
            except Exception:
                pass
        return found

    def _search_and_select(self, search_text, result_id):
        self.enter_text(*MOBILE_NUMBER_FIELD, search_text)
        self.tap(result_id)

    def _wait_for_keyboard(self, timeout=5):
        # Typing before the keyboard has opened is lost on the CI emulator.
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(
                lambda d: d.is_keyboard_shown())
            return True
        except Exception:
            return False

    def _type_and_verify(self, locator, text, attempts=3):
        # Same as PersonalMobileLoginPage._type_and_verify: tap the field, wait
        # for the keyboard, type, then read the field back and retry if the
        # text didn't land (seen on CI for the first field on a fresh form).
        # Attempt 1 uses send_keys; later attempts type via the keyboard.
        actual = ""
        for attempt in range(1, attempts + 1):
            element = self.wait.until(EC.element_to_be_clickable(locator))
            element.click()
            self._wait_for_keyboard()
            try:
                element.clear()
            except Exception:
                pass
            if attempt == 1:
                element.send_keys(text)
            else:
                time.sleep(1)
                self.type_text(text)
            actual = self.find(*locator).get_attribute("text") or ""
            if actual == text:
                return element
            with allure.step(f"Attempt {attempt}: field {locator[1]} shows '{actual}', expected '{text}' - retrying"):
                pass
        raise AssertionError(f"Could not type '{text}' into {locator[1]} after {attempts} attempts "
                             f"(field shows '{actual}')")

    def _enter_registration_field(self, instance, text, clear=False):
        # instance: 0 = First Name, 1 = Last Name, 2 = Email ... (see REGISTRATION_FIELD_HINTS)
        # "clear" is kept for existing callers; _type_and_verify always clears first.
        locator = self._registration_field(REGISTRATION_FIELD_HINTS[instance])
        return self._type_and_verify(locator, text)

    def _recheck_text_fields(self, expected):
        # expected: {field index: text}. The app can clear First Name shortly
        # after the form loads (seen on CI, see PersonalMobileLoginPage), so
        # just before Submit, read each typed field again and re-type any that changed.
        for index, text in expected.items():
            locator = self._registration_field(REGISTRATION_FIELD_HINTS[index])
            actual = self.find(*locator).get_attribute("text") or ""
            if actual != text:
                with allure.step(f"'{REGISTRATION_FIELD_HINTS[index]}' was reset to '{actual}' - typing '{text}' again"):
                    self._type_and_verify(locator, text)
        self._hide_keyboard()

    def _select_random_dropdown(self, field_index, search_text=None):
        # field_index is 1-based: 4 = State, 5 = City, 6 = Role, 7 = Class
        self.click(*self._registration_field(REGISTRATION_FIELD_HINTS[field_index - 1]))
        if search_text is not None:
            self.enter_text(*MOBILE_NUMBER_FIELD, search_text)
        self.select_random_option(AppiumBy.CLASS_NAME, "android.widget.Button")

    def _fill_name_email_state_city(self):
        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena", clear=True)
            self._enter_registration_field(1, "V", clear=True)

        with allure.step("Enter email ID"):
            self._enter_registration_field(2, "veena@gmail.com", clear=True)

        with allure.step("Select the random state"):
            self._select_random_dropdown(4, "maha")

        with allure.step("Select the random city"):
            self._select_random_dropdown(5, "mum")

    def _complete_registration(self):
        """Fill and submit the registration form (app must already be on it),
        then go through intro pages and preferences and log out."""
        self._fill_name_email_state_city()

        with allure.step("Select the role"):
            self._select_random_dropdown(6)

        with allure.step("Select the Interested class"):
            self._select_random_dropdown(7)

        with allure.step("Enter the school/institute name"):
            self._enter_registration_field(7, "XYZ School")

        with allure.step("Re-check the typed fields before submitting"):
            self._recheck_text_fields({0: "Veena", 1: "V", 2: "veena@gmail.com", 7: "XYZ School"})

        with allure.step("Click on the Submit button"):
            self._click_submit()

        # timeout=30: the confirmation waits on the server, slower on the CI emulator
        Validation.AlertValidator.validate_alert(
            self.driver, "Are you sure you want to proceed?", "Terms and Conditions", "I Agree", timeout=30)
        self._wait_until_registration_done()
        self.skip_intro_pages()
        self.selecting_preference()
        self.logout()

    # ---- flows shared across login types ---------------------------------

    def skip_intro_pages(self, timeout=60):
        # Same as PersonalMobileLoginPage.skip_intro_pages: poll the screen
        # instead of giving up on "Next" after 10s - after registering, the app
        # can take a while to leave the form (tc28).
        with allure.step("Skip through intro pages"):
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                d = self.driver
                get_started = d.find_elements(*INTRO_GET_STARTED)
                if get_started:
                    get_started[0].click()
                    return
                if d.find_elements(*PERMISSION_ALLOW):
                    d.find_element(*PERMISSION_ALLOW).click()
                    continue
                if d.find_elements(*ANR_DIALOG):
                    self._dismiss_not_responding_popup()
                    continue
                next_buttons = d.find_elements(*INTRO_NEXT)
                if next_buttons:
                    try:
                        next_buttons[0].click()
                    except Exception:
                        pass  # the page changed while tapping - look again
                time.sleep(1)

            still_on_form = bool(self.driver.find_elements(
                AppiumBy.XPATH, f'//android.widget.EditText[@hint="{REGISTRATION_FIELD_HINTS[0]}"]'))
            reason = ("the app is still on the registration form - the registration was not completed"
                      if still_on_form else "the intro pages never appeared")
            raise AssertionError(f"'Get Started' not found within {timeout}s: {reason}")

    def _wait_until_registration_done(self, timeout=60):
        # Same as PersonalMobileLoginPage._wait_until_registration_done: after
        # "I Agree", wait for the intro pages, and if the server rejects the
        # registration fail with the app's own (short-lived toast) message.
        with allure.step("Wait for the registration to be accepted"):
            first_name = (AppiumBy.XPATH, f'//android.widget.EditText[@hint="{REGISTRATION_FIELD_HINTS[0]}"]')
            toasts_seen = []
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                d = self.driver
                if d.find_elements(*INTRO_NEXT) or d.find_elements(*INTRO_GET_STARTED) or d.find_elements(*INTRO_SKIP):
                    return
                for toast in d.find_elements(AppiumBy.XPATH, "//android.widget.Toast"):
                    text = toast.get_attribute("text") or ""
                    if text and text not in toasts_seen:
                        toasts_seen.append(text)
                if d.find_elements(AppiumBy.XPATH, '//android.view.View[@content-desc="Duplicate email"]'):
                    toasts_seen.append("Duplicate email")
                if toasts_seen and d.find_elements(*first_name):
                    break  # the app showed a message and is back on the form
                time.sleep(1)

            allure.attach(self.driver.page_source, "page source after I Agree", allure.attachment_type.XML)
            if toasts_seen:
                raise AssertionError(f"Registration was not accepted. App message: {' | '.join(toasts_seen)}")
            if self.driver.find_elements(*first_name):
                raise AssertionError(f"Registration was not accepted: still on the registration form {timeout}s "
                                     f"after 'I Agree', and the app showed no message")
            raise AssertionError("After 'I Agree' the app is neither on the form nor on the intro pages")

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

    def logout(self, attempts=2):
        # Tapping "Logout" while the More page is still loading can be ignored,
        # so check the login chooser actually appears and tap again if not.
        for attempt in range(1, attempts + 1):
            with allure.step("Click on More" if attempt == 1 else f"Logout attempt {attempt}"):
                # First time, wait for the home screen's More tab; on a retry we
                # may already be on the More page, where the tab isn't needed.
                if attempt == 1 or not self.driver.find_elements(*LOGOUT_OPTION):
                    self.click(*HOME_MORE_TAB)
                self.scroll_to_and_click("Logout")
            if self.is_present(*INSTITUTE_OPTION, timeout=15):
                return
        allure.attach(self.driver.page_source, "page source after Logout", allure.attachment_type.XML)
        raise AssertionError(f"Still logged in after tapping 'Logout' {attempts} times - login chooser not shown")

    # ---- test cases -------------------------------------------------------

    def tc22(self):
        self._reach_institution_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Check whether the student registration page is displayed"):
            screen = self._screen_after_login()
            registration_page_displayed = screen == "registration"
            if not registration_page_displayed:
                # Shows in the log which screen came up instead (intro = the user
                # was already registered, i.e. the deactivation didn't take
                # effect; unknown = login didn't get past the OTP screen)
                self._report_unexpected_screen(screen, "student registration page")
        return registration_page_displayed

    def tc23(self):
        self._login_to_registration_page()

        with allure.step("Click on the Submit button in the registration page"):
            self._click_submit()
            # The first tap can land before the freshly loaded form responds to it.
            # If no "Required" message appears within 10s, tap Submit once more.
            if not self.is_present(*REQUIRED_MESSAGE, timeout=10):
                self._click_submit()

        with allure.step("Check for mandatory fields"):
            # Collected while scrolling through the whole form: with every field
            # showing an error the form is taller than the screen, and the app
            # only lists what is on screen.
            fields_with_required = self._collect_required_fields()
            self.assertGreaterEqual(
                len(fields_with_required), 6,
                f"Expected 'Required' under at least 6 fields, found {len(fields_with_required)}: "
                f"{sorted(fields_with_required)}")

    def tc24(self):
        self._login_to_registration_page()

        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena")
            self._enter_registration_field(1, "V")

        with allure.step("Enter improper email format"):
            self._enter_registration_field(2, "veena")

        with allure.step("Re-check the typed fields before submitting"):
            # The app clears First Name shortly after the form loads (see
            # _recheck_text_fields) - re-type anything it reset.
            self._recheck_text_fields({0: "Veena", 1: "V", 2: "veena"})

        with allure.step("Click on the Submit button"):
            self._click_submit()

        with allure.step("Scroll back to the email field"):
            # Same as Personal tc4: after Submit the email field (and the error
            # under it) can be scrolled off screen.
            self._registration_field(REGISTRATION_FIELD_HINTS[2])

        with allure.step("Validate the 'Enter valid email' error is shown"):
            self._assert_error_message(
                '//android.view.View[@content-desc="Enter valid email"]',
                "Enter valid email",
                by=AppiumBy.XPATH,
                fail_message="'Enter valid email' message not found",
            )

    def tc25(self):
        self._login_to_registration_page()

        with allure.step("Enter the first and last name of the user"):
            self._enter_registration_field(0, "Veena")
            self._enter_registration_field(1, "V")

        with allure.step("Enter the duplicate email ID"):
            self._enter_registration_field(2, "ankush.winray@gmail.com", clear=True)
            # Re-type anything the app reset (First Name), then close the keyboard
            # so the email field loses focus and validates before Submit.
            self._recheck_text_fields({0: "Veena", 1: "V", 2: "ankush.winray@gmail.com"})
            self._click_submit()
            self._assert_error_message(
                '//android.view.View[@content-desc="Duplicate email"]',
                "Duplicate email",
                by=AppiumBy.XPATH,
                fail_message="'Duplicate email' message not found",
            )

    def tc26(self):
        from tests.AlphyWebLogin import SuperAdminLoginPage
        from Config.DesiredCap import DesiredCap
        # Make the role inactive BEFORE the app loads the registration form -
        # the form most likely fetches its dropdown options when it opens, so the
        # role changed afterwards was still listed (13 Oct local run).
        self.page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        status = SuperAdminLoginPage(self.page, self.driver).student_role_status_change()

        try:
            self._login_to_registration_page()
            self._fill_name_email_state_city()

            with allure.step("Check if the student role is present"):
                self.click(*self._registration_field("You are signing up as? *"))
                student_role_present = self.is_present(AppiumBy.ACCESSIBILITY_ID, "Student", timeout=15)
                self.assertFalse(student_role_present, "Inactive 'student' role is still visible in the dropdown")
        finally:
            # Restore the role even if filling the form failed part-way
            SuperAdminLoginPage(self.page, self.driver).change_status(status)

    def tc27(self):
        from tests.DGWebLogin import DGWebLoginPage
        from Config.DesiredCap import DesiredCap
        # Same as tc26: make the hierarchy inactive before the form loads.
        self.page.goto(DesiredCap.WEB_URLS["dglogin"])
        DGWebLoginPage(self.page, self.driver).inactive_hierarchy()

        try:
            self._login_to_registration_page()
            self._fill_name_email_state_city()

            with allure.step("Select the role"):
                self._select_random_dropdown(6)

            with allure.step("Check if the inactive hierarchy is present in Interested class"):
                self.click(*self._registration_field("Which Class are you interested in? *"))
                hierarchy_present = self.is_present(AppiumBy.ACCESSIBILITY_ID, "10th MH Board Science", timeout=15)
                self.assertFalse(hierarchy_present, "Inactive hierarchy is still visible in the dropdown")
        finally:
            # Restore the hierarchy even if filling the form failed part-way
            DGWebLoginPage(self.page, self.driver).change_status()

    def tc28(self):
        self._login_to_registration_page()
        self._complete_registration()

    def tc29(self):
        self._reach_institution_otp_screen()
        self._login_with_otp("2222")
        with allure.step("Check that the institute selection screen is displayed"):
            picker_displayed = self.is_present(*INSTITUTE_PICKER, timeout=10)
            self.assertTrue(picker_displayed,
                            f"'{INSTITUTE_PICKER_TITLE}' screen not shown for a user registered in multiple institutes")
        # The app is left on the institute picker; the next test's
        # _ensure_at_login_chooser clears app data to get back to the chooser.

    def tc30(self):
        # User is inactive in one institute and active in the other: login should
        # go straight into the active institute without the institute picker.
        self._reach_institution_otp_screen()
        self._login_with_otp("2222")

        with allure.step("Check that the institute selection screen is not displayed"):
            self.assertFalse(self.is_present(*INSTITUTE_PICKER, timeout=10),
                             "Institute picker shown although the user is active in only one institute")

        if self.is_present(*REGISTRATION_HEADER):
            # Already on the registration page - continue from here, don't log in again
            self._wait_for_registration_page()
            self._complete_registration()
        else:
            self.skip_intro_pages()
            self.selecting_preference()
            self.logout()

    def tc32(self):
        self._open_institutional_login()
        with allure.step("Continue without entering a mobile number"):
            self._tap_with_keyboard_closed("Continue")

        with allure.step("Validate blank mobile number error is shown"):
            self._assert_error_message("Please enter mobile number", "Please enter mobile number")

    def tc33(self):
        self._open_institutional_login()
        with allure.step("Enter mobile number shorter than 10 digits"):
            self.enter_text(*MOBILE_NUMBER_FIELD, "123")
            self._tap_with_keyboard_closed("Continue")

        with allure.step("Validate 10-digit mobile number error is shown"):
            self._assert_error_message("Please enter 10 digit mobile number", "Please enter 10 digit mobile number")

    def tc34(self):
        self._open_institutional_login()
        with allure.step("Enter inactive mobile number"):
            self.enter_text(*MOBILE_NUMBER_FIELD, DG_TEST_NUMBER, clear=True)
            self._tap_with_keyboard_closed("Continue")

        with allure.step("Validate inactive user error is shown"):
            ToastValidator.validate_toast_message(
                self.driver, "Mobile no. is not registered for any active institute account.")

    # Blank OTP
    def tc35(self):
        self._reach_institution_otp_screen()
        self._login_with_otp(step_label="Leave OTP blank and attempt login")

        with allure.step("Validate 'Enter OTP first' toast is shown"):
            ToastValidator.validate_toast_message(self.driver, "Enter OTP first")

    def tc36(self):
        self._reach_institution_otp_screen()
        self._login_with_otp("111")

        with allure.step("Validate 'Invalid OTP' toast is shown"):
            ToastValidator.validate_toast_message(self.driver, "Invalid OTP")

    def _wait_for_denied_or_picker(self):
        # After the OTP, a user registered in more than one institute (tc29 adds
        # the test user to Westfield) gets the institute picker first; others
        # get the toast straight away. Watch for both at once - the toast is
        # short-lived, so waiting for the picker first could miss it.
        return self.wait.until(
            lambda d: "picker" if d.find_elements(*INSTITUTE_PICKER)
            else "denied" if d.find_elements(*ACCESS_DENIED_TOAST)
            else False)

    def tc37(self):
        try:
            self._reach_institution_otp_screen()
            self._login_with_otp("2222")
            if self._wait_for_denied_or_picker() == "picker":
                dg_option = self.driver.find_elements(*DG_INSTITUTE_OPTION)
                if not dg_option:
                    # DG is left out of the picker (e.g. the DG company is
                    # inactive): the user can't log in to DG, which is the
                    # access-denied outcome this check is for.
                    with allure.step(f"'{DG_INSTITUTE_NAME}' not offered in the institute picker - DG access is blocked"):
                        return
                with allure.step(f"Choose '{DG_INSTITUTE_NAME}' in the institute picker"):
                    dg_option[0].click()
            with allure.step("Validate 'Access denied' toast is shown"):
                ToastValidator.validate_toast_message(self.driver, "Access denied")
        finally:
            # If access was wrongly granted, finish the login and log out so the
            # next test starts clean
            if self.is_present(*INTRO_SKIP, timeout=10):
                self.skip_intro_pages()
                self.selecting_preference()
                self.logout()