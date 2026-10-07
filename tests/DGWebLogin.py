import time
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin
import allure
from playwright.sync_api import expect

from Config.DesiredCap import DesiredCap
from Page.WebBasePage import WebBasePage
from Page.DGMobileLogin import DGMobileLoginPage


class DGWebLoginPage(WebBasePage):
    def __init__(self, page, driver):
        WebBasePage.__init__(self, page)
        self.driver = driver

    def admin_login(self):
        with allure.step("Login By OTP"):
            self.page.locator("#rdbOtp").click()
            self.enter_text("#txtusername","7777777777")
            self.page.get_by_text("Request OTP").click()
            self.enter_text("#txtpassword","2222")
            self.page.get_by_role("button",name="Login").click()

    def search_user(self, must_exist=True):
        # The user list is paged, so search for the user rather than assuming
        # the row is on the first page.
        self.enter_text("#ContentPlaceHolder1_txttitle1", "9902985281", clear=True)
        user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='9902985281']]")
        if must_exist:
            self.page.keyboard.press("Enter")
            expect(user_row).to_have_count(1)
        else:
            # The row may legitimately be absent, so there's nothing to wait
            # for on screen. The search is an async UpdatePanel postback
            # (ContentPlaceHolder1_upd1) that re-renders the search field and
            # grid in place, with no page load. Mark the current search field
            # and wait until it's been replaced and the postback has finished -
            # otherwise the row check could run against the old grid. The
            # postback regularly takes 8s+, so allow more than the default.
            self.page.evaluate(
                "document.querySelector('#ContentPlaceHolder1_txttitle1').dataset.stale = '1'"
            )
            self.page.keyboard.press("Enter")
            self.page.wait_for_function(
                """() => {
                    const field = document.querySelector('#ContentPlaceHolder1_txttitle1');
                    return field && !field.dataset.stale
                        && !Sys.WebForms.PageRequestManager.getInstance().get_isInAsyncPostBack();
                }""",
                timeout=60000,
            )
        return user_row

    def wait_for_user_list(self):
        # userlist.aspx renders early but takes ~25s to finish parsing, so even
        # "domcontentloaded" overruns the 20s default timeout. Only wait for the
        # navigation to commit and then for the search field itself.
        self.page.wait_for_url("**/userlist.aspx*", wait_until="commit")
        self.page.locator("#ContentPlaceHolder1_txttitle1").first.wait_for(state="visible")

    def inactivate_user_method(self):
        # Caller must already be logged in (admin_login) - calling it here again
        # fails because the login form is gone once we're on userlist.aspx.
        with allure.step("In user management search the user and change the status"):
            user_row = self.search_user()
            status_dropdown = self.change_status_if_active(user_row, attr_name="statusname", label="User status")
            return status_dropdown

    def change_user_status(self,status_dropdown):
        with allure.step("Change the inactive user to active one"):
            if status_dropdown is not None:
                self.revert_status(status_dropdown, attr_name="statusname")

    def inactivate_user(self):
        # A prior run's tc35 deactivation renames the user to 9902985281_x,
        # so make sure an active 9902985281 exists before inactivating it.
        self.admin_login()
        self.activate_user()
        status_dropdown=self.inactivate_user_method()
        try:
            with allure.step("Check whether able to login from the inactive user"):
                DGMobileLoginPage(self.driver).tc34()
        finally:
            self.change_user_status(status_dropdown)



    def expired_license(self):
        self.admin_login()
        with allure.step("In the company settings, change the license expiry to current date - 1"):
            self.page.get_by_role("link", name="Company Settings").click()
            datepicker_to = self.page.locator("#ContentPlaceHolder1_datepickerTo")

            today = datetime.now()
            previous_date = today - timedelta(days=1)
            # The datepicker is a jQuery UI widget backed by its own internal state;
            # a plain fill()/blur() updates the visible input but the server-side
            # postback silently ignores it (verified: value reverts on reload). The
            # datepicker's own API is required for the change to actually persist,
            # same as change_license_date() below.
            datepicker_to.evaluate(
                """(el, [y, m, d]) => {
                    const $el = jQuery(el);
                    $el.datepicker('setDate', new Date(y, m, d));
                    $el.datepicker('update');
                    $el.trigger('change');
                }""",
                [previous_date.year, previous_date.month - 1, previous_date.day]
            )
            self.page.get_by_role("button", name="Update").click()
            # This page keeps background network activity going (poller/widget),
            # so it never reaches "networkidle" - wait for the postback's DOM
            # instead, same signal companymaster.aspx actually delivers reliably.
            self.page.wait_for_load_state("domcontentloaded")

            expect(datepicker_to).to_have_value(previous_date.strftime("%m/%d/%Y"))
            time.sleep(20)

        with allure.step("Check whether able to login if the company license is expired"):
            DGMobileLoginPage(self.driver).tc37()


    def inactive_hierarchy(self):
        self.admin_login()
        with allure.step("In the hierarchy change the status to inactive"):
            self.page.get_by_role("link", name="Hierarchy").click()
            search_box=self.page.get_by_role("searchbox", name="Search:")
            search_box.fill("Automation hierarchy")
            hierarchy_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Automation hierarchy']]")
            self.change_status_if_active(hierarchy_row)

    def change_status(self):
        search_box = self.page.get_by_role("searchbox", name="Search:")
        search_box.fill("Automation hierarchy")
        hierarchy_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Automation hierarchy']]")
        status_dropdown = hierarchy_row.locator("select")
        self.revert_status(status_dropdown)

    def add_user(self):
        self.admin_login()
        with allure.step("In the user management add user"):
            self.wait_for_user_list()
            user_row = self.search_user(must_exist=False)
            if user_row.count()== 0:
                # userlist.aspx takes ~25s to finish parsing and the Quick Add
                # modal handler (data-plugin="custommodal") only binds ~16s in;
                # clicking before that just follows the "#custom-modal-quick"
                # href and no modal opens.
                self.page.wait_for_function(
                    "() => !!(jQuery._data(document.querySelector('#lnkQuickAdd'), 'events') || {}).click",
                    timeout=60000,
                )
                self.page.get_by_role("link", name="Quick Add").click()
                mobile_number = self.page.locator("#ContentPlaceHolder1_txtQuickMobileno")
                mobile_number.fill("9902985281")
                self.page.locator("#ContentPlaceHolder1_A2").click()

    def activate_user(self):
        # Caller must already be logged in (admin_login)
        with allure.step("Activate the user if it is in Draft"):
            self.wait_for_user_list()
            user_row = self.search_user()
            status=user_row.locator("select").get_attribute("statusname")
            if status == "Draft":
                # "Edit/View Details" opens usermaster.aspx in a new tab (target=_blank)
                # which never materialises under automation, so open it in this tab
                # directly. ddlval is "select_<userid>".
                user_id = user_row.locator("select").get_attribute("ddlval").split("_")[1]
                self.page.goto(urljoin(self.page.url, f"usermaster.aspx?userid={user_id}"))
                self.page.wait_for_load_state("load")
                # Quick Add leaves Roles empty, and it's required to activate.
                # select_option waits for the "Student" option to be present.
                self.page.get_by_role("button", name="Save & Activate").click()
                self.wait_for_user_list()
                user_row = self.search_user()
                expect(user_row.locator("select")).to_have_attribute("statusname", "Active")
            else:
                return

    def inactivate_westfield_user(self):
        self.admin_login()
        self.activate_user()
        status_dropdown = self.inactivate_user_method()
        with allure.step("Check whether able to login from the inactive user"):
            DGMobileLoginPage(self.driver).tc30()
        self.change_user_status(status_dropdown)

    def login_to_institute(self, url_key):
        # Each institute is a separate site; clear the previous admin session
        # so Login.aspx shows the login form instead of redirecting past it.
        self.page.context.clear_cookies()
        self.page.goto(DesiredCap.WEB_URLS[url_key])
        self.admin_login()

    def inactivate_both_user(self):
        # Caller has already opened the DG login page.
        self.admin_login()
        self.activate_user()
        self.inactivate_user_method()
        try:
            with allure.step("Inactivate the same user in the Westfield institute"):
                self.login_to_institute("Westfieldlogin")
                self.activate_user()
                westfield_status = self.inactivate_user_method()
                with allure.step("Check whether able to login when the user is inactive in both institutes"):
                    DGMobileLoginPage(self.driver).tc34()
        finally:
            with allure.step("Reactivate the user in the DG institute"):
                self.login_to_institute("dglogin")
                self.wait_for_user_list()
                self.change_user_status(self.search_user().locator("select"))




