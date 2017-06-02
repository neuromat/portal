from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver

from experiments.tests.tests_helper import global_setup_ft, apply_setup


@apply_setup(global_setup_ft)
class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        global_setup_ft()
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()
