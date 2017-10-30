import time

import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from experiments.tests.tests_helper import global_setup_ft, apply_setup

# To test haystack using a new index, instead of the settings.py index
TEST_HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE':
            'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'test_haystack',
        'TIMEOUT': 60 * 10,
    }
}

MAX_WAIT = 10


@override_settings(HAYSTACK_CONNECTIONS=TEST_HAYSTACK_CONNECTIONS)
@apply_setup(global_setup_ft)
class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        global_setup_ft()

        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en')
        self.browser = webdriver.Firefox(profile)

        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'http://' + staging_server

        # A neuroscience researcher discovered a new site that
        # provides a data base with neuroscience experiments.
        # She goes to checkout its home page
        self.browser.get(self.live_server_url)

    def tearDown(self):
        self.browser.quit()

    def wait_for(self, fn):
        start_time = time.time()
        while True:
            try:
                return fn()
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)


@apply_setup(global_setup_ft)
class FunctionalTestTrustee(StaticLiveServerTestCase):

    def setUp(self):
        global_setup_ft()

        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en')
        self.browser = webdriver.Firefox(profile)

        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'http://' + staging_server

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

    # TODO: same definition as in FunctionalTest class (remember moto: "three
    # TODO: strikes and refactor". Second now.
    def wait_for(self, fn):
        start_time = time.time()
        while True:
            try:
                return fn()
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)
