import time

from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from functional_tests.base import FunctionalTest


class TrusteeLoggedInTest(FunctionalTest):

    def test_trustee_can_view_initial_page(self):
        experiment = Experiment.objects.first()

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

        # She is redirected to home page but now logged in.
        # She sees a list of experiments that has to be analysed and
        # experiments that are under analysis. That statuses are displayed
        # in the column Status in the table.
        table = self.browser.find_element_by_id('id_experiments_table')
        row_headers = table.find_element_by_tag_name(
            'thead').find_element_by_tag_name('tr')
        col_headers = row_headers.find_elements_by_tag_name('th')
        self.assertTrue(col_headers[4].text == 'Status')
        rows = table.find_element_by_tag_name('tbody') \
            .find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[4].text ==
                experiment.get_status_display() for row in rows)
        )

        # Statuses table cells are links. She clicks in an experiment status
        # that has to be analysed and see a modal that display the modal
        # title that shows experiment title in quotes.
        experiment_id = self.browser.find_element_by_link_text(
            'To be analysed').get_attribute('data-experiment_id')
        experiment1 = Experiment.objects.get(id=experiment_id)
        self.browser.find_element_by_link_text('To be analysed').click()
        time.sleep(1)
        modal_status = self.browser.find_element_by_id('status_modal')
        modal_status_title = modal_status.find_element_by_id(
            'modal_status_title').text
        self.assertIn('Change status for experiment', modal_status_title)
        self.assertIn('"' + experiment1.title + '"', modal_status_title)
        # In modal body she sees that she can chose a new status for the
        # experiment.
        modal_status_body = modal_status.find_element_by_id(
            'status_body').text
        self.assertIn('Please select an option:', modal_status_body)
        self.assertIn('To be analised', modal_status_body)

        self.fail('Finish this test!')
