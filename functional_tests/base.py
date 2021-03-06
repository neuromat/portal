import time

import os

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from experiments.models import Experiment
from experiments.tests.tests_helper import create_experiment, PASSWORD

# To test haystack using a new index, instead of the settings.py index
TEST_HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE':
            'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': settings.HAYSTACK_TEST_URL,
        'INDEX_NAME': 'test_haystack',
        'TIMEOUT': 60 * 10,
    }
}

MAX_WAIT = 10


class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='labor1', password=PASSWORD
        )
        self.experiment = create_experiment(1, self.owner, Experiment.APPROVED)

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

    @staticmethod
    def wait_for(fn):
        start_time = time.time()
        while True:
            try:
                return fn()
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)

    def wait_for_detail_page_load(self):
        ##
        # First we wait for the page completely charge. For this we
        # guarantee an element of the page is there. As any of the
        # statistics, groups, and settings tab is always there, we wait for
        # Group tab.
        ##
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_link_text('Groups').text,
            'Groups'
        ))


class FunctionalTestTrustee(StaticLiveServerTestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='labor1', password=PASSWORD
        )
        self.experiment = create_experiment(1, self.owner)

        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en')
        self.browser = webdriver.Firefox(profile)

        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'http://' + staging_server

        # Trustee Claudia visit the home page and click in "Log In"
        self.browser.get(self.live_server_url)
        self.wait_for(
            lambda: self.browser.find_element_by_link_text('Log In').click()
        )

        ##
        # give trustees permission to change slug
        ##
        group = Group.objects.get(name='trustees')
        permission = Permission.objects.get(codename='change_slug')
        group.permissions.add(permission)

        # The trustee log in Portal
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_username'
            ).send_keys('claudia')
        )
        self.browser.find_element_by_id('id_password').send_keys(PASSWORD)
        self.browser.find_element_by_id('id_submit').click()

    def tearDown(self):
        self.browser.quit()

    # TODO: same definition as in FunctionalTest class (remember moto: "three
    # TODO: strikes and refactor"). Second now.
    def wait_for(self, fn):
        start_time = time.time()
        while True:
            try:
                return fn()
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)
