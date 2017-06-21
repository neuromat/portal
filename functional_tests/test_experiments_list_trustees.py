import time

from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from functional_tests.base import FunctionalTestTrustee


class TrusteeLoggedInTest(FunctionalTestTrustee):

    def test_trustee_can_view_initial_page(self):
        experiment = Experiment.objects.first()

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

    def test_trustee_can_change_experiment_status(self):
        # Statuses table cells are links. She clicks in an experiment status
        # that has to be analysed and see a modal that display the modal
        # title that shows experiment title in quotes.
        experiment_id = self.browser.find_element_by_link_text(
            'To be analysed').get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(id=experiment_id)
        self.browser.find_element_by_link_text('To be analysed').click()
        time.sleep(1)
        modal_status = self.browser.find_element_by_id('status_modal')
        modal_status_title = modal_status.find_element_by_id(
            'modal_status_title').text
        self.assertIn('Change status for experiment', modal_status_title)
        self.assertIn('"' + experiment.title + '"', modal_status_title)
        # In modal body she sees that she can chose a new status for the
        # experiment. As she wants to analyse the experiment, she changes
        # the status to "Under analysis".
        modal_status_body = modal_status.find_element_by_id(
            'status_body').text
        self.assertIn('Please select an option:', modal_status_body)
        self.assertIn('To be analysed', modal_status_body)
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.UNDER_ANALYSIS + '"]').click()
        submit_button = self.browser.find_element_by_id('id_submit')
        submit_button.send_keys(Keys.ENTER)
        time.sleep(1)
        # The trustee Claudia is redirect to home page and see that the
        # experiment that she changed is now "Under analysis"
        # table = self.browser.find_element_by_id('id_experiments_table')
        table = self.browser.find_element_by_id('id_experiments_table')
        rows = table.find_element_by_tag_name(
            'tbody').find_elements_by_tag_name('tr')
        any(row.find_elements_by_tag_name('td')[0].text ==
            experiment.title for row in rows)

    def test_trustee_when_viewing_stauses_to_change_cant_see_only_status_allowed(self):
        # She clicks in an experiment status that has to be analysed and see a
        # modal that display the modal title that shows experiment title in quotes.
        self.browser.find_element_by_link_text('To be analysed').click()
        time.sleep(1)
        # She sees a modal with "To be analysed" and "Under analysis" status options
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        statuses = dict(Experiment.STATUS_OPTIONS)
        self.assertIn(statuses[Experiment.TO_BE_ANALYSED], form_status_choices.text)
        self.assertIn(statuses[Experiment.UNDER_ANALYSIS], form_status_choices.text)
        # She press ESC to quit modal and clicks in an experiment status that is under
        # analysis. Now a modal with all status options but "Receiving" appears
        form_status_choices.send_keys(Keys.ESCAPE)
        time.sleep(1)
        self.browser.find_element_by_link_text('Under analysis').click()
        time.sleep(1)
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        statuses = dict(Experiment.STATUS_OPTIONS)
        self.assertIn(statuses[Experiment.TO_BE_ANALYSED], form_status_choices.text)
        self.assertIn(statuses[Experiment.UNDER_ANALYSIS], form_status_choices.text)
        self.assertIn(statuses[Experiment.APPROVED], form_status_choices.text)
        self.assertIn(statuses[Experiment.NOT_APPROVED], form_status_choices.text)
        # She press ESC to quit modal and clicks in an experiment status that is approved.
        # Now a modal telling that she cannot change status appears.
        form_status_choices.send_keys(Keys.ESCAPE)
        time.sleep(1)
        self.browser.find_element_by_link_text('Approved').click()
        time.sleep(1)
        modal_body = self.browser.find_element_by_id('status_body').text
        self.assertIn('You can\'t change an experiment status' +
                      ' that has already been approved or rejected.', modal_body)

        # Finally, she press ESC to quit modal and clicks in an experiment
        # status that is NOT approved. Now a modal telling that she cannot
        # change status appears.
        self.browser.find_element_by_id('status_body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        self.browser.find_element_by_link_text('Not approved').click()
        time.sleep(1)
        modal_body = self.browser.find_element_by_id('status_body').text
        self.assertIn('You can\'t change an experiment status' +
                      ' that has already been approved or rejected.', modal_body)

        self.fail('Finish this test!')
