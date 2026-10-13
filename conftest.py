import os
import shutil
import subprocess

import report_export

# On Windows the Allure CLI is "allure.bat", which only resolves through the
# shell. On Linux, shell=True with a list runs a bare "allure" (the remaining
# items become arguments to sh, not to allure), so the shell is Windows-only.
USE_SHELL = os.name == "nt"
# GitHub Actions sets CI=true. The workflow builds its own (single-file) report
# there, and a headless runner has no browser for "allure open" to show it in.
ON_CI = os.getenv("CI", "").lower() == "true"


def pytest_sessionfinish(session, exitstatus):
    # "pytest --collect-only" runs no tests: don't rebuild (and pop open) the
    # report, or add an empty run to its history.
    if session.config.option.collectonly:
        return

    try:
        report_export.export_to_excel("allure-results", "allure-report-summary.xlsx")
        report_export.export_to_html("allure-results", "allure-report-summary.html")
    except Exception as export_error:
        print(f"Could not export Allure results summary: {export_error}")

    if ON_CI:
        return

    # Carry the previous report's history into this run's results, so the new
    # report shows the Trend charts and each test's earlier results. The run
    # itself still starts from fresh results (--clean-alluredir).
    try:
        if os.path.isdir("allure-report/history") and os.path.isdir("allure-results"):
            shutil.copytree("allure-report/history", "allure-results/history", dirs_exist_ok=True)
    except OSError as history_error:
        print(f"Could not carry over Allure history: {history_error}")

    try:
        subprocess.run(
            ["allure", "generate", "allure-results", "-o", "allure-report", "--clean"],
            shell=USE_SHELL,
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
            shell=USE_SHELL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as open_error:
        print(f"Could not open Allure report: {open_error}")
