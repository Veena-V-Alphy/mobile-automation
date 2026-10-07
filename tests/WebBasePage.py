import random
import time

import allure


class WebBasePage:
    def __init__(self, page, timeout=20000):
        self.page = page
        self.page.set_default_timeout(timeout)

    def find(self, selector):
        locator = self.page.locator(selector)
        locator.first.wait_for(state="attached")
        return locator.first

    def find_all(self, selector):
        locator = self.page.locator(selector)
        locator.first.wait_for(state="attached")
        return locator

    def is_present(self, selector):
        try:
            self.page.locator(selector).first.wait_for(state="attached")
            return True
        except Exception:
            return False

    def click(self, selector):
        element = self.find(selector)
        element.click()
        return element

    def enter_text(self, selector, text, clear=False):
        element = self.find(selector)
        element.click()
        if clear:
            element.fill(text)
        else:
            element.type(text)
        return element

    def select_random_option(self, selector):
        options = self.find_all(selector)
        count = options.count()
        options.nth(random.randrange(count)).click()
        return options

    def change_status_if_active(self, row, attr_name="name", label=None):
        """Toggle a listing row's status dropdown to Inactive if it's currently Active.
        Idempotent: does nothing if the row is already Inactive (e.g. left that way
        by a prior run). Always returns the status <select> locator so the caller
        can pass it to revert_status afterward, regardless of whether a toggle
        happened here."""
        status_dropdown = row.locator("select")
        current_status = status_dropdown.get_attribute(attr_name)
        if label:
            allure.attach(str(current_status), name=label, attachment_type=allure.attachment_type.TEXT)
        if current_status == "Active":
            status_dropdown.select_option("Change Status")
            self.page.wait_for_load_state("networkidle")
            time.sleep(20)
        return status_dropdown


    def revert_status(self, status_dropdown, attr_name="name"):
        """Ensure a status dropdown ends up back on Active. Idempotent: does
        nothing if it's already Active, so this is safe to call unconditionally
        regardless of whether this test run was the one that made it Inactive -
        it also self-heals a row a prior (buggy) run left stuck Inactive."""
        current_status = status_dropdown.get_attribute(attr_name)
        if current_status == "Active":
            return
        status_dropdown.select_option("Change Status")
        self.page.wait_for_load_state("networkidle")
        time.sleep(20)


