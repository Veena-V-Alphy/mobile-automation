from datetime import datetime, timedelta
from urllib.parse import urljoin
import allure
from playwright.sync_api import expect

from Config.DesiredCap import DesiredCap
from tests.WebBasePage import WebBasePage
from tests.DGMobileLogin import DGMobileLoginPage

TEST_MOBILE_NUMBER = "9902985281"


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
        self._wait_for_postback()
        self.enter_text("#ContentPlaceHolder1_txttitle1", TEST_MOBILE_NUMBER, clear=True)
        user_row = self.page.locator(f"xpath=//tr[td[normalize-space(.)='{TEST_MOBILE_NUMBER}']]")
        # The search is an async UpdatePanel postback (ContentPlaceHolder1_upd1)
        # that re-renders the search field and grid in place, with no page load.
        # Mark the current search field and wait until it's been replaced and
        # the postback has finished - otherwise the row check runs against the
        # old grid. The postback regularly takes 8s+, so the old must_exist
        # check (a plain expect with the 5s default) gave up before the results
        # arrived. Both branches now wait for the postback the same way.
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
        if must_exist:
            try:
                expect(user_row).to_have_count(1, timeout=15000)
            except AssertionError as error:
                # Put what the grid actually contains into the error itself, so
                # it shows in the CI log without opening the Allure report
                allure.attach(self.page.screenshot(full_page=True),
                              name=f"User list - {TEST_MOBILE_NUMBER} not found",
                              attachment_type=allure.attachment_type.PNG)
                raise AssertionError(
                    f"User {TEST_MOBILE_NUMBER} not found in the user list.\n"
                    f"Page: {self.page.url}\n"
                    f"Grid rows after the search: {self._grid_rows()}\n"
                    f"Messages on the page: {self._page_messages()}"
                ) from error
        return user_row

    def _grid_rows(self, limit=5):
        # First few table rows, so a log shows e.g. "No records found" or a
        # renamed "9902985281_x" user instead of just "count 0"
        try:
            rows = self.page.locator("table tr").all_inner_texts()
            rows = [" | ".join(r.split()) for r in rows if r.strip()]
            return rows[:limit] or "no table rows"
        except Exception as exc:
            return f"could not read the grid ({exc})"

    def _page_messages(self):
        # Visible alert / validation / toast texts (success or error) on the page
        try:
            return self.page.evaluate(
                """() => [...document.querySelectorAll(
                        '.alert, .toast, .toast-message, .swal2-popup, .jq-toast-single, '
                        + '.text-danger, .error, .validation-summary-errors, [id*="lblMsg"], [id*="lblmsg"]')]
                    .filter(e => e.offsetParent !== null && e.innerText.trim())
                    .map(e => e.innerText.trim().replace(/\\s+/g, ' '))
                    .slice(0, 10)"""
            ) or "none"
        except Exception as exc:
            return f"could not read messages ({exc})"

    def _wait_for_postback(self, timeout=60000):
        # Wait until no ASP.NET async postback (search, Quick Add save) is running
        self.page.wait_for_function(
            """() => typeof Sys === 'undefined'
                || !Sys.WebForms.PageRequestManager.getInstance().get_isInAsyncPostBack()""",
            timeout=timeout,
        )

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

    def reactivate_user(self):
        # Search the user again rather than reusing a dropdown captured before a
        # long mobile step - the grid may have re-rendered in the meantime.
        self.wait_for_user_list()
        self.change_user_status(self.search_user().locator("select"))

    def inactivate_user(self):
        # The deactivation in tc22 renames the user to 9902985281_x, so make
        # sure an active 9902985281 exists before inactivating it.
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
            DGMobileLoginPage(self.driver).tc36()


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
            if user_row.count() == 0:
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
                mobile_number.fill(TEST_MOBILE_NUMBER)
                with allure.step("Save the Quick Add form"):
                    allure.attach(self.page.screenshot(), name="Quick Add before save",
                                  attachment_type=allure.attachment_type.PNG)
                    self.page.locator("#ContentPlaceHolder1_A2").click()
                    # Wait for the save to finish before going on. Without this the
                    # test moved straight to the mobile app, the save never
                    # completed, and the institutional login never reached the OTP
                    # screen because the number wasn't registered.
                    expect(mobile_number).to_be_hidden(timeout=60000)
                    self._wait_for_postback()
                    # Records any success/validation message the save showed;
                    # print() lands in "Captured stdout" of the CI log on failure
                    messages = self._page_messages()
                    print(f"[add_user] Quick Add saved. Messages on the page: {messages}")
                    allure.attach(str(messages), name="Quick Add messages",
                                  attachment_type=allure.attachment_type.TEXT)
                    allure.attach(self.page.screenshot(), name="Quick Add after save",
                                  attachment_type=allure.attachment_type.PNG)
            else:
                print(f"[add_user] {TEST_MOBILE_NUMBER} already in the list - Quick Add skipped")

        # Fails here with a clear error if the user still doesn't exist, and
        # moves a new (Draft) user to Active so the mobile login is accepted.
        #self.activate_user()

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
                edit_url = urljoin(self.page.url, f"usermaster.aspx?userid={user_id}")
                self.page.goto(edit_url)
                self.page.wait_for_load_state("load")
                # Make sure the edit form itself is there before touching its
                # fields, so a page that didn't open fails with a clear message.
                try:
                    self.page.get_by_role("button", name="Save & Activate").wait_for(
                        state="visible", timeout=60000)
                except Exception as error:
                    allure.attach(self.page.screenshot(full_page=True),
                                  name="User edit page did not open",
                                  attachment_type=allure.attachment_type.PNG)
                    raise AssertionError(
                        f"User edit page for user {user_id} did not show 'Save & Activate'.\n"
                        f"Opened: {edit_url}\nNow on: {self.page.url}\n"
                        f"Messages on the page: {self._page_messages()}"
                    ) from error
                # Quick Add leaves Parent Name / Parent Number empty, and both are
                # required for a Student - without them Save & Activate stays on
                # this page and the user remains in Draft (seen 13 Oct, local run).
                # Not every form has them, though: on 15 Oct CI the "Enter parent
                # name" field was missing (tc29-tc31) and input_value() waited
                # 20s and failed. Fill them only when they're there; if they were
                # needed, _save_and_activate reports the page's message.
                for placeholder, value in (("Enter parent name", "Test Parent"),
                                           ("Enter parent number", "9876543210")):
                    field = self.page.get_by_placeholder(placeholder).first
                    try:
                        field.wait_for(state="visible", timeout=5000)
                    except Exception:
                        with allure.step(f"'{placeholder}' field not on this form - skipped"):
                            print(f"[activate_user] '{placeholder}' field not found on {self.page.url} - skipped")
                        continue
                    if not field.input_value():
                        field.fill(value)
                self._save_and_activate()
                user_row = self.search_user()
                expect(user_row.locator("select")).to_have_attribute("statusname", "Active")

    def _save_and_activate(self):
        # Even with every required field filled, Save & Activate posts back to
        # usermaster.aspx (to a malformed "usermaster.aspx?usermaster.aspx%3fencrypt=&userid=..."
        # action), assigns a license, but leaves the user in Draft - no dialog,
        # no visible error (13 Oct local probe). Accept any dialog the click
        # raises (Playwright would otherwise dismiss it and cancel the save) and
        # report what the page showed if it doesn't return to the user list.
        dialogs = []

        def accept(dialog):
            dialogs.append(f"{dialog.type}: {dialog.message}")
            dialog.accept()

        self.page.on("dialog", accept)
        try:
            self.page.get_by_role("button", name="Save & Activate").click()
            try:
                self.wait_for_user_list()
            except Exception as error:
                # Still on the edit page: put what the page said into the error
                allure.attach(self.page.screenshot(full_page=True),
                              name="Save & Activate did not return to the user list",
                              attachment_type=allure.attachment_type.PNG)
                raise AssertionError(
                    "Save & Activate did not return to the user list.\n"
                    f"Page: {self.page.url}\n"
                    f"Dialogs: {dialogs or 'none'}\n"
                    f"Messages on the page: {self._page_messages()}"
                ) from error
        finally:
            self.page.remove_listener("dialog", accept)
        if dialogs:
            allure.attach("\n".join(dialogs), name="Save & Activate dialogs",
                          attachment_type=allure.attachment_type.TEXT)

    def inactivate_westfield_user(self):
        self.admin_login()
        self.activate_user()
        status_dropdown = self.inactivate_user_method()
        try:
            with allure.step("Check whether able to login from the inactive user"):
                DGMobileLoginPage(self.driver).tc30()
        finally:
            # Restore the Westfield user even if the mobile check failed
            self.change_user_status(status_dropdown)

    def login_to_institute(self, url_key):
        # Each institute is a separate site; clear the previous admin session
        # so Login.aspx shows the login form instead of redirecting past it.
        self.page.context.clear_cookies()
        self.page.goto(DesiredCap.WEB_URLS[url_key])
        self.admin_login()

    def inactivate_both_user(self):
        # Caller has already opened the DG login page.
        dg_inactivated = False
        westfield_inactivated = False
        try:
            with allure.step("Inactivate the user in the DG institute"):
                self.admin_login()
                self.activate_user()
                self.inactivate_user_method()
                dg_inactivated = True

            with allure.step("Inactivate the same user in the Westfield institute"):
                self.login_to_institute("Westfieldlogin")
                self.activate_user()
                self.inactivate_user_method()
                westfield_inactivated = True

            with allure.step("Check whether able to login when the user is inactive in both institutes"):
                DGMobileLoginPage(self.driver).tc31()
        finally:
            # Restore both institutes - previously only DG was reactivated, so the
            # Westfield user stayed inactive for every later run.
            """if westfield_inactivated:
                with allure.step("Reactivate the user in the Westfield institute"):
                    # Still logged in to Westfield at this point
                    self.reactivate_user()"""
            if dg_inactivated:
                with allure.step("Reactivate the user in the DG institute"):
                    self.login_to_institute("dglogin")
                    self.reactivate_user()
