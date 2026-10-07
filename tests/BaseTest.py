import pytest
import time
import requests
from Config.DesiredCap import DesiredCap
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from playwright.sync_api import sync_playwright
from Page.MobileBasePage import MobileBasePage

class BaseTest:
    mobile_driver = None
    web_page = None
    mobile_page = None
    appium_service = None
    playwright = None
    web_browser = None
    web_context = None
    wait = None
    web_urls = DesiredCap.WEB_URLS
    MOBILE_APP_ID = "com.winray.alphy"
# Setup the server and driver
    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup(cls, request):
        needs = getattr(cls, "NEEDS", {"mobile", "web"})
        try:
            if "mobile" in needs:
                cls.mobile_driver = cls._start_mobile_driver()

            if "web" in needs:
                cls.web_page = cls._start_web_page()
        except Exception:
            # Startup failed partway through: clean up whatever did start
            # (Appium service/driver, browser) so the port/process isn't
            # left dangling for the next run.
            cls._teardown()
            raise

        yield
        cls._teardown()

    # Relaunch the app fresh before every test so a test can't inherit UI
    # state (which screen is open, what's typed in a field) left behind by
    # whichever test ran before it.
    @pytest.fixture(autouse=True)
    def reset_mobile_app(self):
        needs = getattr(self, "NEEDS", {"mobile", "web"})
        if "mobile" in needs and self.mobile_driver:
            self.mobile_driver.terminate_app(self.MOBILE_APP_ID)
            self.mobile_driver.activate_app(self.MOBILE_APP_ID)
        yield

    # Same idea for the web side: clear cookies before every test so a test
    # can't inherit a logged-in session left behind by whichever test ran
    # before it. A test that needs to switch between two logged-in sessions
    # within itself (e.g. admin then superadmin) still clears cookies again
    # mid-test for that switch - this fixture only covers the inter-test gap.
    @pytest.fixture(autouse=True)
    def reset_web_page(self):
        needs = getattr(self, "NEEDS", {"mobile", "web"})
        if "web" in needs and self.web_page:
            self.web_page.context.clear_cookies()
        yield

    @classmethod
    def _teardown(cls):
        try:
            if cls.mobile_driver:
                # cls.mobile_driver.terminate_app(cls.MOBILE_APP_ID)
                cls.mobile_driver.quit()
        finally:
            try:
                if cls.appium_service:
                    cls.appium_service.stop()
            finally:
                cls._stop_web_page()

    @classmethod
    def _start_mobile_driver(cls):
        android_options = DesiredCap.emulator_caps()
        cls.appium_service = AppiumService()
        # Startup can exceed 20s when the machine is low on RAM (emulator running);
        # Appium's own output goes to appium.log so a failed start shows the real reason.
        cls.appium_service.start(args=["--port", "4725", "--log", "appium.log"], timeout_ms=60000)

        # Wait until the server is actually ready to accept connections
        BaseTest._wait_for_appium_ready("http://127.0.0.1:4725/status", timeout=60)

        driver = webdriver.Remote("http://127.0.0.1:4725", options=android_options)
        driver.activate_app(cls.MOBILE_APP_ID)
        return driver

    @classmethod
    def _start_web_page(cls, browser="chromium"):
        cls.playwright = sync_playwright().start()
        browser_type = getattr(cls.playwright, browser, None)
        if browser_type is None:
            raise ValueError(f"Unsupported browser: {browser}")

        cls.web_browser = browser_type.launch(headless=False)
        cls.web_context = cls.web_browser.new_context(no_viewport=True)
        return cls.web_context.new_page()

    @classmethod
    def _stop_web_page(cls):
        try:
            if cls.web_context:
                cls.web_context.close()
        finally:
            try:
                if cls.web_browser:
                    cls.web_browser.close()
            finally:
                if cls.playwright:
                    cls.playwright.stop()



#Check if the server is ready or not
    @staticmethod
    def _wait_for_appium_ready(url, timeout=20):
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.5)
        raise RuntimeError("Appium server did not become ready in time")








