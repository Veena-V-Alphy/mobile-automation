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
            try:
                with allure.step("Check whether able to login from the inactive user"):
                    PersonalMobileLoginPage(self.driver).tc11()
            finally:
                # Always reactivate, even if the check failed - otherwise every
                # later test runs against an inactive user.
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
            # jQuery UI's datepicker plugin script loads asynchronously, so wait
            # for it - otherwise `$el.datepicker` is intermittently undefined.
            self.page.wait_for_function(
                "typeof jQuery !== 'undefined' && typeof jQuery.fn.datepicker !== 'undefined'"
            )
            datepicker_to.evaluate(
                """(el, [y, m, d]) => {
                    const $el = jQuery(el);
                    $el.datepicker('setDate', new Date(y, m, d));
                    $el.datepicker('update');
                    $el.trigger('change');
                }""",
                [previous_date.year, previous_date.month - 1, previous_date.day]
            )
            # The date field already shows the new value before Update is pressed,
            # so checking the field alone passed even when Update was never
            # clicked (14 Oct) - nothing was saved and the mobile login still
            # worked. Wait for the "Record updated" message instead, and press
            # Update once more if it doesn't show up.
            update_button = self.page.get_by_role("button", name="Update")
            record_updated = self.page.get_by_text("Record updated")
            update_button.click()
            try:
                expect(record_updated).to_be_visible(timeout=15000)
            except AssertionError:
                with allure.step("'Record updated' not shown - pressing Update again"):
                    update_button.click()
                expect(record_updated, "License expiry was not saved: 'Record updated' never appeared "
                                       "after pressing Update").to_be_visible(timeout=15000)

            expect(datepicker_to).to_have_value(previous_date.strftime("%m/%d/%Y"))

        with allure.step("Check whether able to login if the company license is expired"):
            PersonalMobileLoginPage(self.driver).tc14()

    def exceeded_license(self):
        """Set the allotted licenses equal to the used ones. Returns the original
        allotted value so the caller can pass it to restore_allotted_licenses."""
        self.admin_login()
        with allure.step("In the company settings change the allotted license to used license"):
            self.page.get_by_role("link", name="Company Settings").click()

            license_info_text = self.page.locator("#ContentPlaceHolder1_lblLicensesInfo").inner_text()
            used_licenses = re.search(r"Used Licenses\s*:\s*(\d+)", license_info_text).group(1)

            allotted_licenses_field = self.page.locator("#ContentPlaceHolder1_txtLicenses")
            original_allotted = allotted_licenses_field.input_value()
            allure.attach(original_allotted, name="Original allotted licenses",
                          attachment_type=allure.attachment_type.TEXT)
            allotted_licenses_field.fill(used_licenses)
            self.page.get_by_role("button", name="Update").click()
            self.page.wait_for_load_state("domcontentloaded")
        return original_allotted

    def restore_allotted_licenses(self, allotted):
        self.admin_login()
        with allure.step(f"In the company settings restore the allotted licenses to {allotted}"):
            self.page.get_by_role("link", name="Company Settings").click()
            allotted_licenses_field = self.page.locator("#ContentPlaceHolder1_txtLicenses")
            allotted_licenses_field.fill(allotted)
            self.page.get_by_role("button", name="Update").click()
            # Same as expired_license: this page never reaches "networkidle"
            self.page.wait_for_load_state("domcontentloaded")
            expect(allotted_licenses_field).to_have_value(allotted)

    def remove_app_access_control(self):
        self.admin_login()
        with allure.step("In the access control remove the app access"):
            self.page.get_by_role("link", name="Access Control").click()
            access_control=self.page.get_by_role("checkbox", name="App Access")
            if access_control.is_checked():
                access_control.uncheck()
                self.page.wait_for_load_state("networkidle")
                expect(access_control).not_to_be_checked()
                self.post_and_wait(lambda: self.page.get_by_role("button", name="Submit").click())

    def restore_app_access_control(self):
        self.admin_login()
        with allure.step("In the access control give the app access back"):
            self.page.get_by_role("link", name="Access Control").click()
            access_control=self.page.get_by_role("checkbox", name="App Access")
            if not access_control.is_checked():
                access_control.check()
                self.page.wait_for_load_state("networkidle")
                self.page.get_by_role("button", name="Submit").click()
                self.page.wait_for_load_state("networkidle")

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

    def change_license_date(self, attempts=3):
        # This is tc14's cleanup: if it fails, the company license stays expired
        # for every later test. The superadmin site is sometimes slow (seen 14 Oct:
        # the "Companies" click timed out), so start over from the login page and
        # try again before giving up.
        login_url = self.page.url
        for attempt in range(1, attempts + 1):
            try:
                return self._change_license_date_once()
            except Exception as error:
                if attempt == attempts:
                    raise
                with allure.step(f"Attempt {attempt} to extend the license failed ({type(error).__name__}) - retrying"):
                    self.page.context.clear_cookies()
                    self.page.goto(login_url)

    def _change_license_date_once(self):
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

    APP_ACCESS_ACTIVITY = "Access to Login to Alphy App"

    def _open_alphy_activities(self):
        with allure.step("Select the Products"):
            self.page.get_by_role("link", name="Products").click()
            self.page.get_by_role("searchbox", name="Search:").fill('Alphy')
            product_row = self.page.locator("xpath=//tr[td[normalize-space(.)='Alphy']]")
        with allure.step("Select the activities"):
            # "Activities" loads a new page whose search box looks the same as the
            # Products one - wait for it, or the activity name can be typed into
            # the old page's search box.
            with self.page.expect_navigation():
                product_row.locator("select").select_option("Activities")
        return self.page.url

    def _activity_status_select(self, list_url, activity_name):
        # Load the activity list fresh and filter it, so the row shows the status
        # the server has saved. The list is paged, so the row is only on the page
        # once it's filtered.
        self.page.goto(list_url)
        self.page.get_by_role("searchbox", name="Search:").fill(activity_name)
        status_dropdown = self.page.locator(
            f"xpath=//tr[td[normalize-space(.)='{activity_name}']]").locator("select")
        status_dropdown.wait_for()
        return status_dropdown

    def _set_activity_status(self, list_url, activity_name, wanted, attempts=3):
        # "Change Status" saves in the background (activitylist.aspx/change_status)
        # and reloads the list straight away without waiting for the answer, so
        # the reloaded list - and the old row's "name" attribute - can show the
        # old status (14 Oct, tc18: the revert read a stale status and the
        # activity stayed Inactive). Wait for that save itself, then reload the
        # list to confirm it, and try again if it didn't stick.
        with allure.step(f"Set '{activity_name}' to {wanted}"):
            for attempt in range(1, attempts + 1):
                status_dropdown = self._activity_status_select(list_url, activity_name)
                current = status_dropdown.get_attribute("name")
                if current == wanted:
                    return
                if attempt > 1:
                    allure.attach(f"Attempt {attempt}: still {current}", name="Status retry",
                                  attachment_type=allure.attachment_type.TEXT)
                with self.page.expect_response(lambda r: r.url.endswith("/change_status"), timeout=60000):
                    status_dropdown.select_option("Change Status")
                self.page.wait_for_load_state("domcontentloaded")
            current = self._activity_status_select(list_url, activity_name).get_attribute("name")
            if current != wanted:
                raise AssertionError(f"'{activity_name}' is still {current} after {attempts} attempts "
                                     f"to make it {wanted}")

    def _check_login_with_app_access_inactive(self, mobile_check):
        self.superadmin_login()
        list_url = self._open_alphy_activities()
        with allure.step("Change the status of the aphy app access activity"):
            try:
                self._set_activity_status(list_url, self.APP_ACCESS_ACTIVITY, "Inactive")
                with allure.step("Check whether able to login if the status of the 'Access to Login to Alphy App'is made inactive"):
                    mobile_check()
            finally:
                # Always set it back to Active, even if making it Inactive failed
                # partway - otherwise every later test runs without app access.
                with allure.step("Change the 'Access to Login to Alphy App' status back to Active"):
                    self._set_activity_status(list_url, self.APP_ACCESS_ACTIVITY, "Active")

    def inactivate_alphy_app_access(self):
        self._check_login_with_app_access_inactive(PersonalMobileLoginPage(self.driver).tc17)

    def inactivate_alphy_app_access_dg(self):
        self._check_login_with_app_access_inactive(DGMobileLoginPage(self.driver).tc37)

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
                expect(activity_check).not_to_be_checked()
                self.post_and_wait(lambda: self.page.get_by_role("button", name="Submit").click())

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
                expect(activity_check).not_to_be_checked()
                self.post_and_wait(lambda: self.page.get_by_role("button", name="Submit").click())

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





