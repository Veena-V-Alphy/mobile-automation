import time
from datetime import datetime, timedelta
import re
import allure
from playwright.sync_api import expect

from tests.WebBasePage import WebBasePage
from tests.PersonalMobileLogin import PersonalMobileLoginPage
from tests.DGMobileLogin import DGMobileLoginPage


class AlphyWebLoginPage(WebBasePage):
    def __init__(self, page, driver):
        WebBasePage.__init__(self, page)
        self.driver = driver

    def admin_login(self):
        with allure.step("Login By OTP"):
            self.page.locator("#rdbOtp").click()
            username_field = self.enter_text("#txtusername","7777777777")
            self.page.get_by_text("Request OTP").click()
            password_field = self.enter_text("#txtpassword","2222")
            self.page.get_by_role("button",name="Login").click()

    def inactivate_user(self):
        self.admin_login()

        with allure.step("In user management search the user and change the status"):
            self.enter_text("#ContentPlaceHolder1_txttitle1","9902985281")
            self.page.keyboard.press("Enter")
            self.page.wait_for_load_state("load")
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='9902985281']]")
            status_dropdown = self.change_status_if_active(user_row, attr_name="statusname", label="User status")
            with allure.step("Check whether able to login from the inactive user"):
                PersonalMobileLoginPage(self.driver).tc11()
            with allure.step("Change the inactive user to active one"):
                self.revert_status(status_dropdown, attr_name="statusname")


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
            PersonalMobileLoginPage(self.driver).tc14()

    def exceeded_license(self):
        self.admin_login()
        with allure.step("In the company settings change the allotted license to used license"):
            self.page.get_by_role("link", name="Company Settings").click()

            license_info_text = self.page.locator("#ContentPlaceHolder1_lblLicensesInfo").inner_text()
            used_licenses = re.search(r"Used Licenses\s*:\s*(\d+)", license_info_text).group(1)

            allotted_licenses_field = self.page.locator("#ContentPlaceHolder1_txtLicenses")
            allotted_licenses_field.fill(used_licenses)
            self.page.get_by_role("button", name="Update").click()

    def remove_app_access_control(self):
        self.admin_login()
        with allure.step("In the access control remove the app access"):
            self.page.get_by_role("link", name="Access Control").click()
            access_control=self.page.get_by_role("checkbox", name="App Access")
            if access_control.is_checked():
                access_control.uncheck()
                self.page.wait_for_load_state("networkidle")
                time.sleep(20)
                self.page.get_by_role("button", name="Submit").click()

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



class SuperAdminLoginPage(WebBasePage):
    def __init__(self, page, driver):
        WebBasePage.__init__(self, page)
        self.driver = driver

    def superadmin_login(self):
        with allure.step("Login with username and password"):
            self.enter_text("#txtusername","admin")
            self.enter_text("#txtpassword","1")
            self.page.get_by_role("button",name="Login").click()

    def change_license_date(self):
        self.superadmin_login()
        with allure.step("Search for the company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box=self.page.locator(".dataTables_filter input")
            search_box.fill('Alphy Company')
            self.page.keyboard.press("Enter")
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy Company']]")

            status_dropdown = user_row.locator("select")
            # Selecting "Edit" triggers a full postback to the company edit page.
            # expect_navigation is needed (not wait_for_load_state) because the
            # navigation hasn't started yet at the instant select_option returns.
            with self.page.expect_navigation():
                status_dropdown.select_option("Edit")

        with allure.step("Extend the license expiry on the company edit page"):
            product_row = self.page.locator("xpath=//tr[.//label[normalize-space(.)='Alphy']]")
            datepicker_to = product_row.locator("input[id*='datepickerTo']")
            # jQuery UI's datepicker plugin script loads asynchronously after the
            # postback above, so wait for it to actually be available - otherwise
            # `$el.datepicker` is intermittently still undefined at this point.
            self.page.wait_for_function(
                "typeof jQuery !== 'undefined' && typeof jQuery.fn.datepicker !== 'undefined'"
            )
            datepicker_to.evaluate(
                """(el) => {
                    const $el = jQuery(el);
                    $el.datepicker('setDate', new Date(2030, 11, 10));
                    $el.datepicker('update');
                    $el.trigger('change');
                }"""
            )
            self.page.get_by_role("button", name="Submit").click()
            self.page.wait_for_load_state("networkidle")

            expect(datepicker_to).to_have_value('12/10/2030')

    def change_license_date_dg(self):
        self.superadmin_login()
        with allure.step("Search for the company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box = self.page.locator(".dataTables_filter input")
            search_box.fill('DG UAT')
            self.page.keyboard.press("Enter")
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='DG UAT']]")

            status_dropdown = user_row.locator("select")
            # Selecting "Edit" triggers a full postback to the company edit page.
            # expect_navigation is needed (not wait_for_load_state) because the
            # navigation hasn't started yet at the instant select_option returns.
            with self.page.expect_navigation():
                status_dropdown.select_option("Edit")

        with allure.step("Extend the license expiry on the company edit page"):
            product_row = self.page.locator("xpath=//tr[.//label[normalize-space(.)='Alphy']]")
            datepicker_to = product_row.locator("input[id*='datepickerTo']")
            # jQuery UI's datepicker plugin script loads asynchronously after the
            # postback above, so wait for it to actually be available - otherwise
            # `$el.datepicker` is intermittently still undefined at this point.
            self.page.wait_for_function(
                "typeof jQuery !== 'undefined' && typeof jQuery.fn.datepicker !== 'undefined'"
            )
            datepicker_to.evaluate(
                """(el) => {
                    const $el = jQuery(el);
                    $el.datepicker('setDate', new Date(2030, 11, 10));
                    $el.datepicker('update');
                    $el.trigger('change');
                }"""
            )
            self.page.get_by_role("button", name="Submit").click()
            self.page.wait_for_load_state("networkidle")

            expect(datepicker_to).to_have_value('12/10/2030')

    def inactivate_product(self):
        self.superadmin_login()
        with allure.step("Inactivate product"):
            self.page.get_by_role("link", name="Products").click()
            search_box=self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the product is made inactive"):
                PersonalMobileLoginPage(self.driver).tc14()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_product_dg(self):
        self.superadmin_login()
        with allure.step("Inactivate product"):
            self.page.get_by_role("link", name="Products").click()
            search_box=self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the product is made inactive"):
                DGMobileLoginPage(self.driver).tc37()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_company(self):
        self.superadmin_login()
        with allure.step("Inactivate company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box=self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy Company')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy Company']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the company is made inactive"):
                PersonalMobileLoginPage(self.driver).tc14()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_company_dg(self):
        self.superadmin_login()
        with allure.step("Inactivate company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box=self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('DG UAT')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='DG UAT']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the company is made inactive"):
                DGMobileLoginPage(self.driver).tc37()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_user(self):
        self.superadmin_login()
        with allure.step("Select the Alphy company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy Company')
            company_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy Company']]")
            status_dropdown = company_row.locator("select")

        with allure.step("Select the User-9902985281 user from alphy company"):
            status_dropdown.select_option("Users")
            user_search_box=self.page.get_by_role("searchbox", name="Search:")
            user_search_box.fill('9902985281')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='9902985281']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the user is made inactive"):
                PersonalMobileLoginPage(self.driver).tc11()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_user_dg(self):
        self.superadmin_login()
        with allure.step("Select the DG UAT company"):
            self.page.get_by_role("link", name="Companies").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('DG UAT')
            company_row = self.page.locator("xpath=//tr[td[normalize-space(.)='DG UAT']]")
            status_dropdown = company_row.locator("select")

        with allure.step("Select the User-9902985281 user from DG UAT company"):
            status_dropdown.select_option("Users")
            user_search_box=self.page.get_by_role("searchbox", name="Search:")
            user_search_box.fill('9902985281')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='9902985281']]")
            status_dropdown = self.change_status_if_active(user_row)

        try:
            with allure.step("Check whether able to login if the status of the user is made inactive"):
                DGMobileLoginPage(self.driver).tc34()
        finally:
            self.revert_status(status_dropdown)

    def inactivate_alphy_app_access(self):
        self.superadmin_login()
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the activities"):
            user_dropdown = user_row.locator("select")
            user_dropdown.select_option("Activities")
        with allure.step("Change the status of the aphy app access activity"):
            activity_search_box=self.page.get_by_role("searchbox", name="Search:")
            activity_search_box.fill('Access to Login to Alphy App')
            activity_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
            status_dropdown = self.change_status_if_active(activity_row)

            try:
                with allure.step("Check whether able to login if the status of the 'Access to Login to Alphy App'is made inactive"):
                    PersonalMobileLoginPage(self.driver).tc17()
            finally:
                self.revert_status(status_dropdown)

    def inactivate_alphy_app_access_dg(self):
        self.superadmin_login()
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the activities"):
            user_dropdown = user_row.locator("select")
            user_dropdown.select_option("Activities")
        with allure.step("Change the status of the aphy app access activity"):
            activity_search_box=self.page.get_by_role("searchbox", name="Search:")
            activity_search_box.fill('Access to Login to Alphy App')
            activity_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
            status_dropdown = self.change_status_if_active(activity_row)

            try:
                with allure.step("Check whether able to login if the status of the 'Access to Login to Alphy App'is made inactive"):
                    DGMobileLoginPage(self.driver).tc37()
            finally:
                self.revert_status(status_dropdown)



    def remove_app_access_from_student_role(self):
        self.superadmin_login()
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the roles"):
            user_dropdown = user_row.locator("select")
            user_dropdown.select_option("Roles")
        with allure.step("Remove the Access to Login to Alphy App from the student role"):
            role_search_box = self.page.get_by_role("searchbox", name="Search:")
            role_search_box.fill('Student')
            role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
            status_dropdown = role_row.locator("select")
            status_dropdown.select_option("Edit")
            activity_row=self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
            activity_check=activity_row.locator("input")
            if activity_check.is_checked():
                activity_check.uncheck()
                self.page.wait_for_load_state("networkidle")
                time.sleep(20)
                self.page.get_by_role("button", name="Submit").click()

        try:
            with allure.step("Check whether able to login if the status of the 'Access to Login to Alphy App'is removed from the student role"):
                PersonalMobileLoginPage(self.driver).tc17()
        finally:
            if self.page.get_by_text("Search Role"):
                role_search_box = self.page.get_by_role("searchbox", name="Search:")
                role_search_box.fill('Student')
                role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
                status_dropdown = role_row.locator("select")
                status_dropdown.select_option("Edit")
                activity_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
                activity_check = activity_row.locator("input")
            activity_check.check()
            self.page.get_by_role("button", name="Submit").click()
            self.page.wait_for_load_state("networkidle")

    def remove_app_access_from_student_role_dg(self):
        self.superadmin_login()
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the roles"):
            user_dropdown = user_row.locator("select")
            user_dropdown.select_option("Roles")
        with allure.step("Remove the Access to Login to Alphy App from the student role"):
            role_search_box = self.page.get_by_role("searchbox", name="Search:")
            role_search_box.fill('Student')
            role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
            status_dropdown = role_row.locator("select")
            status_dropdown.select_option("Edit")
            activity_row=self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
            activity_check=activity_row.locator("input")
            if activity_check.is_checked():
                activity_check.uncheck()
                self.page.wait_for_load_state("networkidle")
                time.sleep(20)
                self.page.get_by_role("button", name="Submit").click()

        try:
            with allure.step("Check whether able to login if the status of the 'Access to Login to Alphy App'is removed from the student role"):
                DGMobileLoginPage(self.driver).tc37()
        finally:
            if self.page.get_by_text("Search Role"):
                role_search_box = self.page.get_by_role("searchbox", name="Search:")
                role_search_box.fill('Student')
                role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
                status_dropdown = role_row.locator("select")
                status_dropdown.select_option("Edit")
                activity_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Access to Login to Alphy App']]")
                activity_check = activity_row.locator("input")
            activity_check.check()
            self.page.get_by_role("button", name="Submit").click()
            self.page.wait_for_load_state("networkidle")

    def student_role_status_change(self):
        self.superadmin_login()
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            search_box = self.page.get_by_role("searchbox", name="Search:")
            search_box.fill('Alphy')
            user_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the roles"):
            user_dropdown = user_row.locator("select")
            user_dropdown.select_option("Roles")
        with allure.step("Make the student role as inactive "):
            role_search_box = self.page.get_by_role("searchbox", name="Search:")
            role_search_box.fill('Student')
            role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
            return self.change_status_if_active(role_row)

    def inactivate_student_role(self):
        status=self.student_role_status_change()
        try:
            with allure.step("Check whether able to login if the status of the student role is inactive"):
                PersonalMobileLoginPage(self.driver).tc14()

        finally:
            self.change_status(status)

    def inactivate_student_role_dg(self):
        status=self.student_role_status_change()
        try:
            with allure.step("Check whether able to login if the status of the student role is inactive"):
                DGMobileLoginPage(self.driver).tc37()

        finally:
            self.change_status(status)

    def change_status(self, status):
        # `status` was captured before an unrelated, possibly long-running
        # flow (e.g. mobile-only steps) ran in between - by now the search
        # box may have reset and that locator can go stale. Re-search for
        # the Student role row fresh instead of trusting the old reference.
        role_search_box = self.page.get_by_role("searchbox", name="Search:")
        role_search_box.fill('Student')
        role_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Student']]")
        status_dropdown = role_row.locator("select")
        self.revert_status(status_dropdown)


class DeactivationPage(WebBasePage):
    def __init__(self, page, driver):
        WebBasePage.__init__(self, page)
        self.driver = driver

    def deactivate(self):
        with allure.step("Deactivate the number"):
            self.enter_text("#txtName", "veena v")
            self.enter_text("#txtMobile", "9902985281")
            self.page.get_by_role("link", name="Send OTP").click()
            self.enter_text("#txtOtp","2222")
            self.enter_text("#txtReason", "Deactivate the user")
            # Wait for the submit postback to finish - navigating away straight
            # after the click can abort it, leaving the old user un-deactivated
            # so add_user() finds it and skips creating a fresh one.
            with self.page.expect_response(
                lambda r: "UserDeactivationRequest.aspx" in r.url and r.request.method == "POST"
            ):
                self.page.get_by_role("button", name="Verify OTP & Submit").click()





