import time

from functional_tests.base import FunctionalTest


class LoginPageTest(FunctionalTest):

    def test_can_view_login_page(self):
        self.browser.get(self.live_server_url)

        # The visitor is in home page and see that is a "Log In" link in up
        # right corner of the page. She clicks in that link.
        self.browser.find_element_by_link_text('Log In').click()
        time.sleep(1)

        # She sees the login page with login fields (username and password)
        # where she can enter her credentials.
        login_header = self.browser.find_element_by_tag_name('h3').text
        self.assertIn('Log In', login_header)

        self.fail('Finish this test!')
