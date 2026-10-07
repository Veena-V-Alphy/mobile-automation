import allure
import pytest
from Config.DesiredCap import DesiredCap
from Page.BaseTest import BaseTest
from Page.DGMobileLogin import DGMobileLoginPage
from Page.DGWebLogin import *
from Page.AlphyWebLogin import SuperAdminLoginPage, AlphyWebLoginPage, DeactivationPage


class TestDGLogin(BaseTest):
    NEEDS = {"mobile", "web"}
    registration_page_displayed = None

    # TC35: Alphy Personal-----Correct Login
    @allure.title(
        "Check whether the user registration page is displayed if the user is logging in first time otherwise intro pages should be displayed")
    def test_login_tc22(self):
        self.web_page.goto(DesiredCap.WEB_URLS["deactivation"])
        DeactivationPage(self.web_page, self.mobile_driver).deactivate()
        self.web_page.goto(DesiredCap.WEB_URLS["dglogin"])
        DGWebLoginPage(self.web_page, self.mobile_driver).add_user()
        login = DGMobileLoginPage(self.mobile_driver)
        TestDGLogin.registration_page_displayed = login.tc22()
        if not TestDGLogin.registration_page_displayed:
            pytest.fail("Student registration page not displayed for this login")

    # TC36: Alphy Personal login----Mandatory validation in student registration page
    @allure.title("Alphy Personal login----Mandatory validation in student registration page")
    def test_login_tc23(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc23()

    # TC37: Alphy Personal login----Email validation in student registration page
    @allure.title("Alphy Personal login----Email validation in student registration page")
    def test_login_tc24(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc24()

    # TC38: Alphy Personal Login---- Duplicate email validation in the user registration page
    @allure.title("Alphy Personal login----Duplicate email  validation in user registration page")
    def test_login_tc25(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc25()

    # TC39: In the user registration check whether inactive role is visible in the dropdown
    @allure.title("In the user registration check whether inactive role is visible in the dropdown")
    def test_login_tc26(self):
        login = DGMobileLoginPage(self.mobile_driver, self.web_page)
        login.tc26()

    # TC40: In the user registration check whether inactive hierarchy is visible in the dropdown
    @allure.title("In the user registration check whether inactive hierarchy is visible in the dropdown")
    def test_login_tc27(self):
        login = DGMobileLoginPage(self.mobile_driver, self.web_page)
        login.tc27()

    # TC41: Institutional login----complete the student registration page
    @allure.title("Institutional login----complete the student registration page")
    def test_login_tc28(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc28()

    # TC42:Institutional login----User registered for multiple institute
    @allure.title("Institutional login----User registered for multiple institute")
    def test_login_tc29(self):
        self.web_page.goto(DesiredCap.WEB_URLS["Westfieldlogin"])
        DGWebLoginPage(self.web_page, self.mobile_driver).add_user()
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc29()

    # TC43: Institutional login----Inactive user for one institute and active in other institute
    @allure.title("Institutional login----Inactive user for one institute and active in other institute")
    def test_login_tc30(self):
        self.web_page.goto(DesiredCap.WEB_URLS["Westfieldlogin"])
        DGWebLoginPage(self.web_page, self.mobile_driver).inactivate_westfield_user()

    # TC44: Institutional login----Inactive user for both institute
    @allure.title("Institutional login----Inactive user for both institute")
    def test_login_tc31(self):
        self.web_page.goto(DesiredCap.WEB_URLS["dglogin"])
        DGWebLoginPage(self.web_page, self.mobile_driver).inactivate_both_user()

    #TC22: Institutional-----Keeping the mobile number field blank
    @allure.title("Institutional----Blank mobile number shows 'Please enter mobile number' message")
    def test_login_tc32(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc32()

    #TC23: Institutional-----mobile number less than 10 digits
    @allure.title("Institutional----Mobile number less than 10 digits shows validation error")
    def test_login_tc33(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc33()

    # TC24: Mobile + Web - Inactive login
    @allure.title("Web and mobile----Check for inactive login")
    def test_login_tc34(self):

        with allure.step("Open the web login page and change the status of the user to inactive"):
            self.web_page.goto(DesiredCap.WEB_URLS["dglogin"])
            DGWebLoginPage(self.web_page, self.mobile_driver).inactivate_user()

    #TC25: Institutional-----Blank OTP Validation
    @allure.title("Institutional----Blank OTP shows 'Enter OTP first' toast")
    def test_login_tc35(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc35()

    #TC26: Institutional-----Invalid OTP
    @allure.title("Institutional----Login with Invalid OTP")
    def test_login_tc36(self):
        login = DGMobileLoginPage(self.mobile_driver)
        login.tc36()

    #TC27: Mobile + Web Company license expired
    @allure.title("Check mobile login if the company license has expired")
    def test_login_tc37(self):
        try:
            with allure.step("Open the web login page and change the company license to current date-1"):
                self.web_page.goto(DesiredCap.WEB_URLS["dglogin"])
                DGWebLoginPage(self.web_page,self.mobile_driver).expired_license()
        finally:
            with allure.step("Open the superadmin login page and change the company license to say 10/12/2030"):
                self.web_page.context.clear_cookies()
                self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
                SuperAdminLoginPage(self.web_page,self.mobile_driver).change_license_date_dg()

    # TC28: Super admin- Product is made as Inactive
    @allure.title("Superadmin- Product is made inactive")
    def test_login_tc38(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page,self.mobile_driver).inactivate_product_dg()


    # TC29: Super admin- Company status is made as Inactive
    @allure.title("Superadmin- Company is made inactive")
    def test_login_tc39(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_company_dg()

    # TC30: Super admin- User status is made as Inactive
    @allure.title("Superadmin- User is made inactive")
    def test_login_tc40(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_user_dg()

    # TC31: Super admin- Access to Login to Alphy App is made inactive
    @allure.title("Superadmin-Access to Login to Alphy App is made inactive")
    def test_login_tc41(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_alphy_app_access_dg()

    # TC32: Superadmin-In the roles remove the " Access to Login to Alphy App" activity from the student role
    @allure.title("Superadmin-In the roles remove the 'Access to Login to Alphy App' activity from the student role")
    def test_login_tc42(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).remove_app_access_from_student_role_dg()

    # TC33: Superadmin-  In the roles, make the Student role as inactive
    @allure.title("Superadmin-  In the roles, make the Student role as inactive")
    def test_login_tc43(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_student_role_dg()

    #TC34: Remove the app access in the Alphy access control and try to login in the mobile application
    @allure.title("Remove the app access in the Alphy access control and try to login in the mobile application")
    def test_login_tc44(self):
        self.web_page.goto(DesiredCap.WEB_URLS["dglogin"])
        AlphyWebLoginPage(self.web_page,self.mobile_driver).remove_app_access_control()
        DGMobileLoginPage(self.mobile_driver).tc37()

















