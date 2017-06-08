import time

from django.contrib.auth.models import User
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from selenium.webdriver.common.keys import Keys
from functional_tests.base import FunctionalTest


class LoginPageTest(FunctionalTest):

    def test_can_view_login_page_and_login_in_the_system(self):
        self.browser.get(self.live_server_url)

        # The visitor is in home page and see that is a "Log In" link in up
        # right corner of the page. She clicks in that link.
        self.browser.find_element_by_link_text('Log In').click()
        time.sleep(1)

        # She sees the login page with login fields (username and password)
        # where she can enter her credentials.
        login_header = self.browser.find_element_by_tag_name('h3').text
        self.assertIn('Log In', login_header)

        # She enters her credentials and click in login button
        # Obs.: this id's isn't in template because the template form elements
        # came from django auth system. You can see them by inspecting
        # element in browser.
        inputbox_username = self.browser.find_element_by_id('id_username')
        inputbox_username.send_keys('claudia')
        inputbox_password = self.browser.find_element_by_id('id_password')
        inputbox_password.send_keys('passwd')

        # When she hits enter to make login.
        login_button = self.browser.find_element_by_id('id_submit')
        login_button.send_keys(Keys.ENTER)
        time.sleep(1)

        # She is redirected to home page, but now logged in. So, she sees a
        # message of welcome and your name (or username) in up right corner of
        # the screen.
        welcome_message = self.browser.find_element_by_id(
            'login-language').text
        user = User.objects.get(username='claudia')
        self.assertIn('Welcome, ' + user.first_name, welcome_message)

        # She checks the home page out and decides to log out.
        logout_link = self.browser.find_element_by_link_text(
            'Log Out')
        logout_url = logout_link.get_attribute('href')
        logout_link.click()
        # Obs.: after clicking in logout_link, we verifiy if we've been
        # correct redirected to home page
        response = self.client.get(logout_url)
        self.assertRedirects(response, reverse('home'))
        time.sleep(1)

        self.fail('Finish this test!')
