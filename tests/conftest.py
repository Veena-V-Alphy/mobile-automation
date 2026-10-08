# ---------------------------------------------------------------------------
# Failure capture: on every failed test, save what was on screen.
#   failure-screens/<test>_mobile.png   - emulator/phone screenshot
#   failure-screens/<test>_mobile.xml   - app screen layout (page source)
#   failure-screens/<test>_web.png      - browser screenshot (hybrid tests)
# The same files are attached to the Allure report.
#
# Paste this into tests/conftest.py (create the file if it doesn't exist;
# if it exists, add these lines at the end and merge the imports).
# ---------------------------------------------------------------------------
import os
import re

import pytest

try:
    import allure
except ImportError:  # allure is optional
    allure = None

FAILURE_DIR = "failure-screens"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # Only capture when the test itself (or its setup) failed
    if report.when not in ("setup", "call") or not report.failed:
        return

    cls = getattr(item, "cls", None)
    if cls is None:
        return

    os.makedirs(FAILURE_DIR, exist_ok=True)
    name = re.sub(r"[^\w.-]", "_", item.nodeid.split("::")[-1])

    mobile_driver = getattr(cls, "mobile_driver", None)
    if mobile_driver:
        try:
            png = mobile_driver.get_screenshot_as_png()
            with open(os.path.join(FAILURE_DIR, f"{name}_mobile.png"), "wb") as f:
                f.write(png)
            if allure:
                allure.attach(png, name="mobile screenshot",
                              attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            print(f"[failure-capture] mobile screenshot failed: {e}")
        try:
            xml = mobile_driver.page_source
            with open(os.path.join(FAILURE_DIR, f"{name}_mobile.xml"), "w", encoding="utf-8") as f:
                f.write(xml)
            if allure:
                allure.attach(xml, name="mobile page source",
                              attachment_type=allure.attachment_type.XML)
        except Exception as e:
            print(f"[failure-capture] mobile page source failed: {e}")

    web_page = getattr(cls, "web_page", None)
    if web_page:
        try:
            png = web_page.screenshot(full_page=True)
            with open(os.path.join(FAILURE_DIR, f"{name}_web.png"), "wb") as f:
                f.write(png)
            if allure:
                allure.attach(png, name="web screenshot",
                              attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            print(f"[failure-capture] web screenshot failed: {e}")