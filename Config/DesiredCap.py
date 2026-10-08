import os

from appium.options.android import UiAutomator2Options


class DesiredCap:
    WEB_URLS = {
        "alphylogin": os.environ.get("ALPHY_URL_ALPHYLOGIN", "https://webuat.myalphy.com/pages/Login.aspx"),
        "dglogin": os.environ.get("ALPHY_URL_DGLOGIN", "https://demo1uat.myalphy.com/pages/Login.aspx"),
        "superadminlogin": os.environ.get("ALPHY_URL_SUPERADMINLOGIN", "https://adminuat.myalphy.com/pages/Login.aspx"),
        "Westfieldlogin":os.environ.get("ALPHY_URL_WESTFIELDLOGIN", "https://demo2uat.myalphy.com/pages/Login.aspx"),
        "deactivation": os.environ.get("ALPHY_URL_DEACTIVATION", "https://webuat.myalphy.com/pages/UserDeactivationRequest.aspx")
    }

    @staticmethod
    def get_mi_caps():

        android_options = UiAutomator2Options()
        android_options.platform_name = "Android"
        android_options.automation_name = "UiAutomator2"
        android_options.device_name = os.environ.get("ALPHY_DEVICE_NAME", "Redmi Note 7 Pro")
        android_options.app= os.getenv("APP_PATH", r"F:\app-uat-release.apk")
        android_options.app_package = "com.winray.alphy"
        android_options.app_activity = "com.example.alphy.MainActivity"
        android_options.no_reset = True
        android_options.new_command_timeout = 300
        android_options.set_capability("disableWindowAnimation", True)
        android_options.set_capability("waitForIdleTimeout", 100)  # default is often 1000ms+
        android_options.set_capability("waitForSelectorTimeout", 5000)
        android_options.set_capability("actionAcknowledgmentTimeout", 3000)
        android_options.set_capability("keyInjectionDelay", 0)
        #android_options.set_capability("unicodeKeyboard", True)
        #android_options.set_capability("resetKeyboard", True)
        # Emulator responds slowly when RAM is tight; default 20s adb timeout is too short
        android_options.set_capability("adbExecTimeout", 60000)
        android_options.set_capability("uiautomator2ServerInstallTimeout", 90000)
        android_options.set_capability("uiautomator2ServerLaunchTimeout", 120000)
        return android_options

    @staticmethod
    def emulator_caps():

        android_options = UiAutomator2Options()
        android_options.platform_name= "Android"
        android_options.automation_name= "UiAutomator2"
        android_options.device_name= "emulator-5554"
        android_options.app_package= "com.winray.alphy"
        android_options.app_activity= "com.example.alphy.MainActivity"
        android_options.app = os.environ.get("APP_PATH") or os.environ.get("ALPHY_APK_PATH", "F:\\app-uat-release.apk")
        android_options.no_reset = True
        # A fresh install on Android 13+ shows the notification permission dialog
        # over the login screen, which hides the "Personal" option from tc1
        android_options.auto_grant_permissions = True
        android_options.new_command_timeout = 300
        android_options.set_capability("disableWindowAnimation", True)
        android_options.set_capability("waitForIdleTimeout", 100)  # default is often 1000ms+
        android_options.set_capability("waitForSelectorTimeout", 5000)
        android_options.set_capability("actionAcknowledgmentTimeout", 3000)
        android_options.set_capability("keyInjectionDelay", 0)

        # Emulator responds slowly when RAM is tight; default 20s adb timeout is too short
        android_options.set_capability("adbExecTimeout", 60000)
        android_options.set_capability("uiautomator2ServerInstallTimeout", 90000)
        android_options.set_capability("uiautomator2ServerLaunchTimeout", 120000)
        return android_options
