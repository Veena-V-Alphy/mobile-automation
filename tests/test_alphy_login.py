import allure
import pytest
from Config.DesiredCap import DesiredCap
from tests.BaseTest import BaseTest
from tests.PersonalMobileLogin import PersonalMobileLoginPage
from tests.AlphyWebLogin import *


class TestLogin(BaseTest):
    NEEDS = {"mobile", "web"}
    # Set by test_login_tc5 - tells tc6-tc8 whether the student registration
    registration_page_displayed = None

    # TC1: Company alloted license has exceeded
    @allure.title("Company alloted license has exceeded")
    @pytest.mark.hybrid
    def test_login_tc1(self):
        self.web_page.goto(DesiredCap.WEB_URLS["alphylogin"])
        AlphyWebLoginPage(self.web_page, self.mobile_driver).exceeded_license()
        self.web_page.goto(DesiredCap.WEB_URLS["deactivation"])
        DeactivationPage(self.web_page, self.mobile_driver).deactivate()
        PersonalMobileLoginPage(self.mobile_driver).tc1()

    # TC2: Alphy Personal-----Correct Login
    @allure.title(
        "Check whether the user registration page is displayed if the user is logging in first time otherwise intro pages should be displayed")
    @pytest.mark.hybrid
    def test_login_tc2(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        TestLogin.registration_page_displayed = login.tc2()
        if not TestLogin.registration_page_displayed:
            pytest.fail("Student registration page not displayed for this login")

    # TC3: Alphy Personal login----Mandatory validation in student registration page
    @allure.title("Alphy Personal login----Mandatory validation in student registration page")
    @pytest.mark.hybrid
    def test_login_tc3(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc3()


    # TC4: Alphy Personal login----Email validation in student registration page
    @allure.title("Alphy Personal login----Email validation in student registration page")
    @pytest.mark.hybrid
    def test_login_tc4(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc4()

    # TC5: Alphy Personal Login---- Duplicate email validation in the user registration page
    @allure.title("Alphy Personal login----Duplicate email  validation in user registration page")
    @pytest.mark.hybrid
    def test_login_tc5(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc5()

    # TC6: In the user registration check whether inactive role is visible in the dropdown
    @allure.title("In the user registration check whether inactive role is visible in the dropdown")
    @pytest.mark.hybrid
    def test_login_tc6(self):
        login = PersonalMobileLoginPage(self.mobile_driver, self.web_page)
        login.tc6()

    # TC7: In the user registration check whether inactive hierarchy is visible in the dropdown
    @allure.title("In the user registration check whether inactive hierarchy is visible in the dropdown")
    @pytest.mark.hybrid
    def test_login_tc7(self):
        login = PersonalMobileLoginPage(self.mobile_driver, self.web_page)
        login.tc7()

    # TC8: In the user registration complete the student registration page
    @allure.title("Alphy Personal login----complete the student registration page")
    @pytest.mark.hybrid
    def test_login_tc8(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc8()


    #TC9: Alphy Personal-----Keeping the mobile number field blank
    @allure.title("Alphy Personal login----Blank mobile number shows 'Please enter mobile number' message")
    @pytest.mark.hybrid
    def test_login_tc9(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc9()

    #TC10: Alphy Personal-----mobile number less than 10 digits
    @allure.title("Alphy Personal login----Mobile number less than 10 digits shows validation error")
    @pytest.mark.hybrid
    def test_login_tc10(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc10()

    # TC11: Mobile + Web - Inactive login
    @allure.title("Web and mobile----Check for inactive login")
    @pytest.mark.hybrid
    def test_login_tc11(self):

        with allure.step("Open the web login page and change the status of the user to inactive"):
            self.web_page.goto(DesiredCap.WEB_URLS["alphylogin"])
            AlphyWebLoginPage(self.web_page,self.mobile_driver).inactivate_user()

    #TC12: Alphy Personal-----Blank OTP Validation
    @allure.title("Alphy Personal login----Blank OTP shows 'Enter OTP first' toast")
    @pytest.mark.hybrid
    def test_login_tc12(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc12()

    #TC13: Alphy Personal-----Invalid OTP
    @allure.title("Alphy Personal login----Login with Invalid OTP")
    @pytest.mark.hybrid
    def test_login_tc13(self):
        login = PersonalMobileLoginPage(self.mobile_driver)
        login.tc13()

    #TC14: Mobile + Web Company license expired
    @allure.title("Check mobile login if the company license has expired")
    @pytest.mark.hybrid
    def test_login_tc14(self):
        try:
            with allure.step("Open the web login page and change the company license to current date-1"):
                self.web_page.goto(DesiredCap.WEB_URLS["alphylogin"])
                AlphyWebLoginPage(self.web_page,self.mobile_driver).expired_license()
        finally:
            with allure.step("Open the superadmin login page and change the company license to say 10/12/2030"):
                self.web_page.context.clear_cookies()
                self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
                SuperAdminLoginPage(self.web_page,self.mobile_driver).change_license_date()

    # TC15: Super admin- Product is made as Inactive
    @allure.title("Superadmin- Product is made inactive")
    @pytest.mark.hybrid
    def test_login_tc15(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page,self.mobile_driver).inactivate_product()

    # TC16: Super admin- Company status is made as Inactive
    @allure.title("Superadmin- Company is made inactive")
    @pytest.mark.hybrid
    def test_login_tc16(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_company()

    # TC17: Super admin- User status is made as Inactive
    @allure.title("Superadmin- User is made inactive")
    @pytest.mark.hybrid
    def test_login_tc17(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_user()

    # TC18: Super admin- Access to Login to Alphy App is made inactive
    @allure.title("Superadmin-Access to Login to Alphy App is made inactive")
    @pytest.mark.hybrid
    def test_login_tc18(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_alphy_app_access()

    # TC19: Superadmin-In the roles remove the " Access to Login to Alphy App" activity from the student role
    @allure.title("Superadmin-In the roles remove the 'Access to Login to Alphy App' activity from the student role")
    @pytest.mark.hybrid
    def test_login_tc19(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).remove_app_access_from_student_role()

    # TC20: Superadmin-  In the roles, make the Student role as inactive
    @allure.title("Superadmin-  In the roles, make the Student role as inactive")
    @pytest.mark.hybrid
    def test_login_tc20(self):
        self.web_page.goto(DesiredCap.WEB_URLS["superadminlogin"])
        SuperAdminLoginPage(self.web_page, self.mobile_driver).inactivate_student_role()

    #TC21: Remove the app access in the Alphy access control and try to login in the mobile application
    @pytest.mark.hybrid
    @allure.title("Remove the app access in the Alphy access control and try to login in the mobile application")
    def test_login_tc21(self):
        self.web_page.goto(DesiredCap.WEB_URLS["alphylogin"])
        AlphyWebLoginPage(self.web_page,self.mobile_driver).remove_app_access_control()
        PersonalMobileLoginPage(self.mobile_driver).tc17()




"""
    # TC7: Download video from content screen (includes login flow)
    @allure.title("Download a video from the content screen")
    def test_7_download_video_from_content_screen(self):
        login = LoginTest(self.mobile_driver)
        login.tc7()

    # TC8: Add counsellor and assign the package


    @allure.title("Successful package payment")
    def test_5_payment_page(self):
        subscription = PaymentGatewayTest(self.mobile_driver)
        subscription.success_payment()


    @allure.title("Add counsellor and assign a package")
    def test_8_add_user(self):
       add_user=AddUSer(self.mobile_driver)
       add_user.add_counsellor()"""
