from django.contrib.auth.models import User
from django.urls import reverse
from selenium.webdriver.common.keys import Keys
from functional_tests.base import FunctionalTest


class LoginTest(FunctionalTest):

    def test_can_view_login_page_and_login_in_the_system(self):
        user = User.objects.get(username='claudia')

        # The visitor is in home page and see that is a "Log In" link in up
        # right corner of the page. She clicks in that link.
        self.browser.find_element_by_link_text('Log In').click()

        # She sees the login page with login fields (username and password)
        # where she can enter her credentials.
        self.wait_for(lambda: self.assertIn(
            'Log In',
            self.browser.find_element_by_tag_name('h3').text
        ))

        # She enters her credentials and click in login button
        # Obs.: this id's isn't in template because the template form elements
        # came from django auth system. You can see them by inspecting
        # element in browser.
        inputbox_username = self.browser.find_element_by_id('id_username')
        inputbox_username.send_keys('claudia')
        inputbox_password = self.browser.find_element_by_id('id_password')
        inputbox_password.send_keys('passwd')

        # She hits enter to make login.
        login_button = self.browser.find_element_by_id('id_submit')
        login_button.send_keys(Keys.ENTER)

        # She is redirected to home page, but now logged in. So, she sees a
        # welcome message and your name (or username) in up right corner of
        # the screen.
        self.wait_for(lambda: self.assertIn(
            'Welcome, ' + user.first_name,
            self.browser.find_element_by_id('login-language').text
        ))

        # She checks the home page out and decides to log out.
        logout_link = self.browser.find_element_by_link_text(
            'Log Out')
        logout_url = logout_link.get_attribute('href')
        logout_link.click()
        # Obs.: after clicking in logout_link, we verifiy if we've been
        # correctly redirected to home page
        response = self.client.get(logout_url)
        self.assertRedirects(response, reverse('home'))


class ResetPasswordTest(FunctionalTest):

    def test_forget_password_recovery(self):
        # The visitor is in home page and see that is a "Log In" link in up
        # right corner of the page. She clicks in that link.
        self.browser.find_element_by_link_text('Log In').click()

        # Suddenly she sees that she has forgotten her password. There's a
        # link to forgotten password cases. She clicks in it.
        self.wait_for(
            lambda:
            self.browser.find_element_by_link_text('Forgot password?').click()
        )

        # A new page loads telling her to fill in her email for the system
        # to send a recovery password for her.
        self.wait_for(
            lambda: self.assertEqual(
                self.browser.find_element_by_tag_name('h3').text,
                'Password reset'
            )
        )
        self.assertEqual(
            self.browser.find_element_by_class_name('top-small').text,
            'Research, Innovation and Dissemination Center for '
            'Neuromathematics'
        )
        self.assertIn(
            'Forgotten your password? Enter your email address below, '
            'and we\'ll email instructions for setting a new one.',
            self.browser.find_element_by_id('forgotten_password').text
        )
        self.assertEqual(
            self.browser.find_element_by_xpath(
                "//label[@for='id_email']"
            ).text, "Email address:"
        )
        ##
        # Search form is supposed to be there too
        ##
        self.assertEqual(
            self.browser.find_element_by_id('id_q').get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )

        ##
        # As we are reusing the Django authentication system (with same
        # templates names) we test for an element that is in original
        # template but not in ours.
        ##
        self.assertNotEqual(
            self.browser.find_element_by_tag_name('h1').text,
            'Django administration'
        )

        # She fills in the input box with her email and clicks on "Reset my
        # password button". The page refreshes telling her that an email was
        # sent to her with instructions for setting her password.
        box = self.browser.find_element_by_id('id_email')
        box.send_keys('matilda@fsf.org')
        self.browser.find_element_by_xpath(
            "//input[@value='Reset my password']"
        ).click()
        self.wait_for(
            lambda:
            self.assertIn(
                'We\'ve emailed you instructions for setting your password, '
                'if an account exists with the email you entered. You should '
                'receive them shortly.',
                self.browser.find_element_by_class_name('nep-content').text
            )
        )
        ##
        # As we are reusing the Django authentication system (with same
        # templates names) we test for an element that is in original
        # template but not in ours.
        ##
        self.assertNotEqual(
            self.browser.find_element_by_tag_name('h1').text,
            'Django administration'
        )
