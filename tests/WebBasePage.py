import random

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

    def is_present(self, selector, timeout=5000):
        # Short default (ms): a "not there" answer otherwise costs the full
        # page timeout. Pass a longer timeout for slow-loading elements.
        try:
            self.page.locator(selector).first.wait_for(state="attached", timeout=timeout)
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

    def post_and_wait(self, action, timeout=60000):
        """Run an action that saves via a form post (a status dropdown change,
        a Submit click) and wait until the server has answered it and the page
        has settled - instead of sleeping a fixed time and hoping it's done."""
        with self.page.expect_response(lambda r: r.request.method == "POST", timeout=timeout):
            action()
        self.page.wait_for_load_state("networkidle")

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
            self.post_and_wait(lambda: status_dropdown.select_option("Change Status"))
        return status_dropdown


    def revert_status(self, status_dropdown, attr_name="name"):
        """Ensure a status dropdown ends up back on Active. Idempotent: does
        nothing if it's already Active, so this is safe to call unconditionally
        regardless of whether this test run was the one that made it Inactive -
        it also self-heals a row a prior (buggy) run left stuck Inactive."""
        current_status = status_dropdown.get_attribute(attr_name)
        if current_status == "Active":
            return
        self.post_and_wait(lambda: status_dropdown.select_option("Change Status"))


