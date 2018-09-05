import re
import time
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from selenium.webdriver.common.keys import Keys

from experiments.tests.tests_helper import PASSWORD, create_trustee_user
from functional_tests.base import FunctionalTest


class LoginTest(FunctionalTest):

    def test_can_view_login_page_and_login_in_the_system(self):
        trustee = create_trustee_user('claudia')

        # The trustee is in home page and see that is a "Log In" link in up
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
        inputbox_username.send_keys(trustee.username)
        inputbox_password = self.browser.find_element_by_id('id_password')
        inputbox_password.send_keys(PASSWORD)

        # She hits enter to make login.
        login_button = self.browser.find_element_by_id('id_submit')
        login_button.send_keys(Keys.ENTER)

        # She is redirected to home page, but now logged in. So, she sees a
        # welcome message and your name (or username) in up right corner of
        # the screen.
        self.wait_for(lambda: self.assertIn(
            'Welcome, ' + trustee.first_name,
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

    user = None

    def setUp(self):
        self.user = User.objects.create_user(
            username='elaine', email='elaine@example.com',
            password='elaine@example'
        )
        super(ResetPasswordTest, self).setUp()

    def test_forget_password_recovery(self):
        # Adriana is in home page and see that is a "Log In" link in up
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
        # sent to her, with instructions for setting her password.
        box = self.browser.find_element_by_id('id_email')
        box.send_keys(self.user.email)
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

        ##
        # take some sleep to guarantie mail.outbox[0]
        ##
        time.sleep(0.5)

        # She goes to her email client and see that a message is inbox
        email = mail.outbox[0]
        self.assertIn(self.user.email, email.to)
        self.assertEqual(
            email.subject,
            'Password reset on ' + self.live_server_url.split('http://')[1]
        )
        self.assertIn(
            'Please go to the following page and choose a new password:',
            email.body
        )

        # In email body there's a link to reset password
        url_search = re.search(r'http://localhost:.+', email.body)
        if not url_search:
            self.fail('Could not find url in email body:\n' + email.body)
        url = url_search.group(0)
        # She clicks on link and a new tab (or window) is opened in portal
        self.browser.get(url)

        # The page has a message and a form to change the user password
        block_content = self.wait_for(
            lambda: self.browser.find_element_by_class_name('nep-content')
        )
        self.assertIn(
            'Please enter your new password twice so we can verify you '
            'typed it in correctly.',
            block_content.text
        )
        self.assertIn('New password', block_content.text)

        # The page has the elements for the nep header too.
        self.assertEqual(
            self.browser.find_element_by_tag_name('h1').text,
            'Neuroscience Experiments Database'
        )
        self.assertEqual(
            self.browser.find_element_by_id('id_q').get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )
        self.assertEqual(
            self.browser.find_element_by_id('filter_box').get_attribute('title'),
            'Select one or more data collection types'
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

        # Now Adriana can type in her new password and confirm it.
        self.browser.find_element_by_id('id_new_password1').send_keys(
            'new_password'
        )
        self.browser.find_element_by_id('id_new_password2').send_keys(
            'new_password'
        )
        self.browser.find_element_by_xpath(
            "//input[@value='Change my password']"
        ).click()
        # necessary to wait for Django password reset complete redirections
        time.sleep(1)

        # The page is redirected to a page that tell her that her password
        # was changed successfully
        block_content = self.wait_for(
            lambda: self.browser.find_element_by_class_name('nep-content')
        )
        self.assertIn(
            'Your password has been set. You may go ahead and log in now.',
            block_content.text
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

        # The page has the elements for the nep header too.
        self.assertEqual(
            self.browser.find_element_by_tag_name('h1').text,
            'Neuroscience Experiments Database'
        )
        self.assertEqual(
            self.browser.find_element_by_id('id_q').get_attribute('placeholder'),
            'Type key terms/words to be searched'
        )
        self.assertEqual(
            self.browser.find_element_by_id('filter_box').get_attribute('title'),
            'Select one or more data collection types'
        )

        # Finally, she clicks in Log in link to be redirected to Log in page
        self.browser.find_element_by_link_text('Log in').click()
        self.wait_for(lambda: self.assertIn(
            'Log In',
            self.browser.find_element_by_tag_name('h3').text
        ))
