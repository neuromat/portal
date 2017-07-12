import re
import time

from django.core import mail
from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from functional_tests.base import FunctionalTestTrustee

RESEARCHER_TEST_EMAIL = 'gezilda@example.com'
SUBJECT_APPROVED = 'Your experiment was approved in ODEN portal'


class TrusteeTest(FunctionalTestTrustee):

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
        # She verifies that the first experiment is to be analysed,
        # and two are under analysis. There is one that has been approved and
        # one more that has not been approved - experiments list template
        # for trustees displays first experiments to be analysed,
        # then experiments under analysis and, at last, approved and not
        # approved ones.
        i = 0
        for row in rows:
            if i < 2:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[4].text ==
                    Experiment.STATUS_OPTIONS[1][1])  # 'To be analysed'
            if i == 2:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[4].text ==
                    Experiment.STATUS_OPTIONS[2][1])  # 'Under analysis'
            if i == 3:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[4].text ==
                    Experiment.STATUS_OPTIONS[2][1])  # 'Under analysis'
            if i == 4:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[4].text ==
                    Experiment.STATUS_OPTIONS[4][1])  # 'Not approved'
            if i == 5:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[4].text ==
                    Experiment.STATUS_OPTIONS[3][1])  # 'Approved'
            i = i + 1

    def test_trustee_when_viewing_stauses_to_change_can_see_only_status_allowed_to_change(self):
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
        self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia'] "
        ).click()
        time.sleep(1)
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        statuses = dict(Experiment.STATUS_OPTIONS)
        self.assertIn(statuses[Experiment.TO_BE_ANALYSED], form_status_choices.text)
        self.assertIn(statuses[Experiment.UNDER_ANALYSIS], form_status_choices.text)
        self.assertIn(statuses[Experiment.APPROVED], form_status_choices.text)
        self.assertIn(statuses[Experiment.NOT_APPROVED], form_status_choices.text)
        # She press ESC to quit modal and clicks in an experiment status
        # that is approved. As when the experiment is already approved or
        # rejected trustee can't change its status, clicking on it has no
        # effect, the modal doesn't pop up.
        form_status_choices.send_keys(Keys.ESCAPE)
        time.sleep(1)
        self.browser.find_element_by_link_text('Approved').click()
        time.sleep(1)
        modal_body = self.browser.find_element_by_id('status_body').text
        self.assertEqual('', modal_body)

        # Finally, she clicks in an experiment status that is NOT approved.
        # The same occurs as clicking in approved experiment. She can't
        # change its status.
        self.browser.find_element_by_link_text('Not approved').click()
        time.sleep(1)
        modal_body = self.browser.find_element_by_id('status_body').text
        self.assertEqual('', modal_body)

    def test_trustee_can_see_experiments_to_be_analysed_sign(self):
        experiments_to_be_analysed = Experiment.objects.filter(status=Experiment.TO_BE_ANALYSED)
        new_experiments = self.browser.find_element_by_id('new_experiments')
        # TODO: we are using a bad technique - badger is greater or equal zero or -1
        badger = new_experiments.get_attribute('class').find('badger')
        if experiments_to_be_analysed:
            self.assertLess(-1, badger)
        else:
            self.assertLess(badger, 0)

    def test_send_email_when_trustee_change_status(self):
        # Obs.: we are implementing for changing status to APPROVED
        # TODO: see if is worth to implements to changing to other status
        # Claudia clicks on a status "Under analysis" of an experiment and
        # change it to "Approved"
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        time.sleep(1)
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.APPROVED + '"]').click()
        submit_button = self.browser.find_element_by_id('id_submit')
        submit_button.send_keys(Keys.ENTER)
        time.sleep(1)
        # Then a message appears on screen, telling her that an email was
        # sent to the experiment study researcher to warning him his
        # experiment was approved
        self.assertIn('An email was sent to ' +
                      experiment.study.researcher.name +
                      ' warning that the experiment changed status to '
                      'Approved.',
                      self.browser.find_element_by_tag_name('body').text)
        # The work is done. She is satisfied and decides to log out from system
        self.browser.find_element_by_link_text('Log Out').click()
        time.sleep(3)
        # The email was sent to the researcher. The guy checks her email and
        # finds a message
        email = mail.outbox[0]
        self.assertIn(experiment.study.researcher.email, email.to)
        self.assertEqual(email.subject,
                         'Your experiment was approved in NEDP portal')
        # Inside it, there's a message with congratulations and a link to
        # the Portal
        self.assertIn('Congratulations, your experiment ' + experiment.title
                      + ' was approved by the Portal committee. Now it is '
                        'public available under Creative Commons '
                        'Share Alike license.\nYou can view your experiment '
                        'data in ' +
                        self.live_server_url, email.body)
        url_search = re.search(r'http://.+$', email.body)
        if not url_search:
            self.fail('Could not find url in email body:\n' + email.body)
        url = url_search.group(0)
        self.assertEqual(self.live_server_url, url)
        # She clicks on link and a new tab (or window) is open in portal
        # home page
        self.browser.get(url)
        self.assertEqual(self.live_server_url, url)

    def test_change_status_from_to_be_analysed_to_under_analysis(self):
        # Statuses table cells are links. She clicks in an experiment status
        # that has to be analysed and see a modal that display the modal
        # title that shows experiment title in quotes.
        experiment_link = self.browser.find_element_by_link_text(
            'To be analysed')
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(id=experiment_id)
        experiment_link.click()
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
        # The trustee Claudia is redirect to home page with a warning
        # message telling her that the experiment is now under analysis.
        # In table she sees that the experiment is "Under analysis".
        td_tag_status = self.browser.find_element_by_xpath(
            "//a[@data-experiment_id='" + str(experiment.id) + "']"
        ).text
        # Experiment.STATUS[2][1] == 'Under analysis'
        self.assertEqual(td_tag_status, Experiment.STATUS_OPTIONS[2][1])
        self.assertIn('An email was sent to ' +
                      experiment.study.researcher.name +
                      ' warning that the experiment is under analysis.',
                      self.browser.find_element_by_tag_name('body').text)

    def test_change_status_to_not_approved_prohibted_without_justification(self):
        # Claudia has examined an experiment that has not conditions to be
        # published in portal. So after her analysis, he decide to not
        # approved it.
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        time.sleep(1)
        # The modal to change experiment status pop up, so she can select
        # NOT_APPROVED to the experiment.
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.NOT_APPROVED + '"]').click()
        # As she's clicked in NOT_APPROVED choice, a html textarea opens
        # below the status choices asking her to enter a text explaining why
        # the experiment has been rejected.
        not_approved_box = self.browser.find_element_by_id('not_approved_box')
        self.assertEqual(
            'Please write a justification for rejecting this experiment',
            not_approved_box.get_attribute('placeholder')
        )
        # She's hurry, and tries to submit the form without justifying why
        # she is rejecting the experiment. As she is not allowed to reject
        # an experiment without gives a justification, required html
        # form attribute prevents her from submitting form.
        # TODO: implement this test!

        # Javascript is momentarily disable in her browser so she can submit
        # the form. But as she didn't write justification, she is redirected
        # to home page with a message warning that the status of the
        # experiment hasn't changed.
        # This test is required if javascript is disabled
        # TODO: is possible disable javascript in selenium driver?
        # submit_button = self.browser.find_element_by_id('id_submit')
        # submit_button.send_keys(Keys.ENTER)
        # time.sleep(1)
        # td_tag_status = self.browser.find_element_by_xpath(
        #     "//a[@data-experiment_id='" + str(experiment.id) + "']"
        # ).text
        # # Experiment.STATUS[2][1] == 'Under analysis'
        # self.assertEqual(td_tag_status, Experiment.STATUS_OPTIONS[2][1])
        # self.assertIn('The status of experiment ' + experiment.title +
        #               ' hasn\'t changed to "Not approved" because you have '
        #               'not given a justification. Please resubmit changing '
        #               'status.',
        #               self.browser.find_element_by_tag_name('body').text)

    def test_change_status_to_not_approved_with_justification_displays_warning_message(self):
        # Claudia has examined an experiment that has not conditions to be
        # published in portal. So after her analysis, he decide to not
        # approved it. She is aware that she has to fill a justification
        # message.
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia'] "
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(id=experiment_id)
        experiment_link.click()
        time.sleep(1)
        # The modal to change experiment status pop up, so she can select
        # NOT_APPROVED to the experiment.
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.NOT_APPROVED + '"]').click()
        # As she choose NOT_APPROVED a textarea appears in modal requesting
        # her to fill in a justification message. So she write the
        # justification and submit the form.
        not_approved_box = self.browser.find_element_by_id('not_approved_box')
        not_approved_box.send_keys('The data sent has some mistakes. Please '
                                   'correct them and send again.')
        submit_button = self.browser.find_element_by_id('id_submit')
        submit_button.send_keys(Keys.ENTER)
        time.sleep(1)
        td_tag_status = self.browser.find_element_by_xpath(
            "//a[@data-experiment_id='" + str(experiment.id) + "']"
        ).text
        # Experiment.STATUS[4][1] == 'Not approved'
        self.assertEqual(td_tag_status, Experiment.STATUS_OPTIONS[4][1])
        self.assertIn('An email was sent to ' +
                      experiment.study.researcher.name +
                      ' warning that the experiment was rejected.',
                      self.browser.find_element_by_tag_name('body').text)

    def test_change_status_to_the_same_status_doesnt_displays_warning_message(self):
        # Claudia clicks an experiment that has a given status, and submit
        # the modal form to change status with same status.
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        time.sleep(1)
        # The modal to change experiment status pop up, and she chooses
        # UNDER_ANALYSIS, the same status as before.
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.UNDER_ANALYSIS + '"]').click()
        self.browser.find_element_by_id('id_submit').send_keys(Keys.ENTER)
        time.sleep(1)
        td_tag_status = self.browser.find_element_by_xpath(
            "//a[@data-experiment_id='" + str(experiment.id) + "']"
        ).text
        # Experiment.STATUS[2][1] == 'Under analysis'
        self.assertEqual(td_tag_status, Experiment.STATUS_OPTIONS[2][1])
        self.assertNotIn('An email was sent to ' +
                         experiment.study.researcher.name +
                         ' warning that the experiment is under analysis.',
                         self.browser.find_element_by_tag_name('body').text)

    def test_change_status_from_under_analysis_to_to_be_analysed_displays_warning_message(self):
        # Claudia clicks an experiment that she is already analysing. She is
        # in doubt about some aspect of it, and wants to pass it to other
        # trustee.
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        time.sleep(1)
        # The modal to change experiment status pop up, and she chooses
        # TO_BE_ANALYSED to liberate the experiment to be analysed by other
        # trustee.
        form_status_choices = self.browser.find_element_by_id(
            'id_status_choices')
        form_status_choices.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.TO_BE_ANALYSED + '"]').click()
        self.browser.find_element_by_id('id_submit').send_keys(Keys.ENTER)
        time.sleep(1)
        td_tag_status = self.browser.find_element_by_xpath(
            "//a[@data-experiment_id='" + str(experiment.id) + "']"
        ).text
        # Experiment.STATUS[1][1] == 'To be analysed'
        self.assertEqual(td_tag_status, Experiment.STATUS_OPTIONS[1][1])
        self.assertIn('You have liberate the experiment ' + experiment.title
                      + ' to be analysed by other trustee.',
                      self.browser.find_element_by_tag_name('body').text)

    def test_can_change_status_from_under_analysis_to_other_only_if_trustee_is_the_owner(self):
        # Claudia see an experiment that is UNDER_ANALYSIS and
        # click on it. He sees a modal warning that the experiment has already
        # under analysis by other trustee.
        # Obs.:
        # 1) requires create user 'roque' to this test
        # 2) requires login in test with user different of 'roque'
        self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='roque'] "
        ).click()
        time.sleep(1)
        # The modal to change experiment status pop up, but it has only a
        # message telling Claudia that the experiment is already been
        # analysed by other trustee
        modal_body = self.browser.find_element_by_id('status_body').text
        self.assertIn('This experiment is already under analysis by '
                      'trustee roque.',
                      modal_body)

        self.fail('Finish this test!')
