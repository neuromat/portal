import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from experiments.tests.tests_helper import global_setup_ft, apply_setup


@apply_setup(global_setup_ft)
class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        global_setup_ft()
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()


@apply_setup(global_setup_ft)
class FunctionalTestTrustee(StaticLiveServerTestCase):

    def setUp(self):
        global_setup_ft()
        self.browser = webdriver.Firefox()

        # Trustee Claudia visit the home page and click in "Log In"
        self.browser.get(self.live_server_url)
        self.browser.find_element_by_link_text('Log In').click()
        time.sleep(1)

        # The trustee Claudia log in Portal
        inputbox_username = self.browser.find_element_by_id('id_username')
        inputbox_username.send_keys('claudia')
        inputbox_password = self.browser.find_element_by_id('id_password')
        inputbox_password.send_keys('passwd')
        login_button = self.browser.find_element_by_id('id_submit')
        login_button.send_keys(Keys.ENTER)
        time.sleep(1)

    def tearDown(self):
        self.browser.quit()
