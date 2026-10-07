import subprocess
import pytest
import allure

import report_export


def pytest_sessionfinish(session, exitstatus):
    try:
        report_export.export_to_excel("allure-results", "allure-report-summary.xlsx")
        report_export.export_to_html("allure-results", "allure-report-summary.html")
    except Exception as export_error:
        print(f"Could not export Allure results summary: {export_error}")

    try:
        subprocess.run(
            ["allure", "generate", "allure-results", "-o", "allure-report", "--clean"],
            shell=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as generate_error:
        print(f"Could not generate Allure report: {generate_error}")
        return

    try:
        # non-blocking: "allure open" runs a live server and would hang pytest if awaited.
        # stdout/stderr are discarded (not inherited) so the server can't hold a redirected
        # output file open and block whatever launched this process.
        subprocess.Popen(
            ["allure", "open", "allure-report"],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as open_error:
        print(f"Could not open Allure report: {open_error}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        mobile_driver = getattr(item.instance, "mobile_driver", None)
        if mobile_driver is not None:
            try:
                allure.attach(
                    mobile_driver.get_screenshot_as_png(),
                    name="screenshot (mobile_driver)",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as screenshot_error:
                print(f"Could not capture mobile_driver screenshot: {screenshot_error}")

        web_page = getattr(item.instance, "web_page", None)
        if web_page is not None:
            try:
                allure.attach(
                    web_page.screenshot(),
                    name="screenshot (web_page)",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as screenshot_error:
                print(f"Could not capture web_page screenshot: {screenshot_error}")

