import subprocess

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
