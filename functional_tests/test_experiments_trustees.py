import random
import re
import time

import sys
from unittest import skip

from django.core import mail
from django.core.management import call_command
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from experiments.models import Experiment
from experiments.tests.tests_helper import random_utf8_string, \
    global_setup_ft, apply_setup, create_trustee_user
from functional_tests.base import FunctionalTestTrustee


@apply_setup(global_setup_ft)
class TrusteeTest(FunctionalTestTrustee):

    def setUp(self):
        create_trustee_user('claudia')
        create_trustee_user('roque')
        global_setup_ft()
        super(TrusteeTest, self).setUp()

    def _access_experiment_detail_page(self, experiment):
        # The new visitor is in home page and see the list of experiments.
        # She clicks in a "View" link and is redirected to experiment
        # detail page
        self.wait_for(
            lambda: self.browser.find_element_by_xpath(
                "//a[@href='/experiments/" + experiment.slug + "/']"
            ).click()
        )

    def _access_change_slug_modal(self):
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).first()

        self._access_experiment_detail_page(experiment)

        # The trustee clicks in experiment url link to change the url
        self.wait_for(
            lambda: self.browser.find_element_by_class_name(
                'fa-pencil-square-o'
            ).click()
        )
        return experiment

    # TODO: repeated from test_search.SearchTest
    def search_for(self, string):
        search_box = self.browser.find_element_by_id('id_q')
        search_box.clear()
        search_box.send_keys(string)
        self.browser.find_element_by_id('submit_terms').click()
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_tag_name('h2').text,
            'Search Results'
        ))

    # TODO: repeated from test_search.SearchTest
    def verify_n_objects_in_table_rows(self, n, row_class):
        table = self.browser.find_element_by_id('search_table')
        count = len(table.find_elements_by_class_name(row_class))
        self.assertEqual(n, count)

    def test_trustee_can_view_initial_page(self):
        experiment = Experiment.objects.first()

        # She is redirected to home page but now logged in.
        # She sees a list of experiments that has to be analysed and
        # experiments that are under analysis. That statuses are displayed
        # in the column Status in the table.
        self.wait_for(
            lambda: self.browser.find_element_by_id('id_experiments_table')
        )
        table = self.browser.find_element_by_id('id_experiments_table')
        row_headers = table.find_element_by_tag_name(
            'thead'
        ).find_element_by_tag_name('tr')
        col_headers = row_headers.find_elements_by_tag_name('th')
        self.assertTrue(col_headers[5].text == 'Status')
        rows = table.find_element_by_tag_name(
            'tbody'
        ).find_elements_by_tag_name('tr')
        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[5].text ==
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
                    row.find_elements_by_tag_name('td')[5].text ==
                    Experiment.STATUS_OPTIONS[1][1])  # 'To be analysed'
            if i == 2:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[5].text ==
                    Experiment.STATUS_OPTIONS[2][1])  # 'Under analysis'
            if i == 3:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[5].text ==
                    Experiment.STATUS_OPTIONS[2][1])  # 'Under analysis'
            if i == 4:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[5].text ==
                    Experiment.STATUS_OPTIONS[4][1])  # 'Not approved'
            if i == 5:
                self.assertTrue(
                    row.find_elements_by_tag_name('td')[5].text ==
                    Experiment.STATUS_OPTIONS[3][1])  # 'Approved'
            i = i + 1

    def test_trustee_can_see_experiment_downloads_column(self):
        # She sees that fourth column is "Downloads". These column
        # displays the number of downloads of the last version of the
        # experiments.
        self.wait_for(
            lambda: self.browser.find_element_by_id('id_experiments_table')
        )
        table = self.browser.find_element_by_id('id_experiments_table')
        row_headers = table.find_element_by_tag_name(
            'thead'
        ).find_element_by_tag_name('tr')
        col_headers = row_headers.find_elements_by_tag_name('th')
        self.assertTrue(col_headers[4].text == 'Downloads')

        # She sees that all entries in "Downloads" column is zero, that is,
        # nobody has made any downloads yet. After all, no experiments has
        # been even approved yet.
        row_entries = table.find_element_by_tag_name(
            'tbody'
        ).find_elements_by_tag_name('tr')

        self.assertTrue(
            any(row.find_elements_by_tag_name('td')[4].text == '0'
                for row in row_entries)
        )

    def test_trustee_when_viewing_stauses_to_change_can_see_only_status_allowed_to_change(self):

        statuses = dict(Experiment.STATUS_OPTIONS)

        # She clicks in an experiment status that has to be analysed and see a
        # modal that display the modal title that shows experiment title in
        # quotes.
        self.wait_for(lambda: self.browser.find_element_by_link_text(
            'To be analysed'
        ).click())

        # She sees a modal with "To be analysed" and "Under analysis" status
        # options
        self.wait_for(lambda: self.assertIn(
            str(statuses[Experiment.TO_BE_ANALYSED]),
            self.browser.find_element_by_id('id_status_choices').text
        ))
        self.wait_for(lambda: self.assertIn(
            str(statuses[Experiment.UNDER_ANALYSIS]),
            self.browser.find_element_by_id('id_status_choices').text
        ))

        # She press ESC to quit modal and clicks in an experiment status
        # that is under analysis. Now a modal with all status options but
        # "Receiving" appears
        ##
        # Ok, by the last wait_for we know that modal has been activated.
        # But we need to wait for modal been visible, until we can ESCAPE it.
        ##
        time.sleep(0.5)
        self.browser.find_element_by_id('id_status_choices').send_keys(
            Keys.ESCAPE
        )
        ##
        # We have to wait again, for modal been completely escaped
        ##
        time.sleep(0.5)
        self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        ).click()
        self.wait_for(lambda: self.assertIn(
            str(statuses[Experiment.TO_BE_ANALYSED]),
            self.browser.find_element_by_id('id_status_choices').text
        ))
        ##
        # We wait again for modal been visible
        ##
        time.sleep(0.5)
        ##
        # Ok, the page has been loaded, so we get the put element in a variable
        ##
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices'
        )

        self.assertIn(
            str(statuses[Experiment.UNDER_ANALYSIS]), status_choices_form.text
        )
        self.assertIn(str(statuses[Experiment.APPROVED]),
                      status_choices_form.text)
        self.assertIn(
            str(statuses[Experiment.NOT_APPROVED]), status_choices_form.text
        )

        # She press ESC to quit modal and clicks in an experiment status
        # that is approved. As when the experiment is already approved or
        # rejected trustee can't change its status, clicking on it has no
        # effect, the modal doesn't pop up.
        status_choices_form.send_keys(Keys.ESCAPE)
        self.wait_for(
            lambda: self.browser.find_element_by_link_text('Approved').click()
        )
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_id('status_body').text,
            ''
        ))

        # Finally, she clicks in an experiment status that is NOT approved.
        # The same occurs as clicking in approved experiment. She can't
        # change its status.
        self.browser.find_element_by_link_text('Not approved').click()
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_id('status_body').text,
            ''
        ))

    def test_trustee_can_see_experiments_to_be_analysed_sign(self):
        experiments_to_be_analysed = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).count()
        self.wait_for(
            lambda: self.browser.find_element_by_id('new_experiments')
        )
        new_experiments = self.browser.find_element_by_id('new_experiments')
        # TODO: we are using a bad technique - badger is greater or equal to
        # TODO: zero or -1
        badger = new_experiments.get_attribute('class').find('badger')
        if experiments_to_be_analysed:
            self.assertLess(-1, badger)
        else:
            self.assertLess(badger, 0)

    def test_send_email_when_trustee_change_status(self):
        # Obs.: we are implementing for changing status to APPROVED
        # TODO: see if it's worth to implement changing to other status
        # Claudia clicks on a status "Under analysis" of an experiment and
        # change it to "Approved"
        self.wait_for(lambda: self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        ))
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        ##
        # We wait for modal pops up
        ##
        time.sleep(0.5)
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.APPROVED + '"]').click()
        submit_button = self.browser.find_element_by_id('submit')
        submit_button.send_keys(Keys.ENTER)
        # Then a message appears on screen, telling her that an email was
        # sent to the experiment study researcher to warning her her
        # experiment was approved
        self.wait_for(lambda: self.assertIn(
            'An email was sent to ' +
            experiment.study.researcher.first_name +
            ' ' + experiment.study.researcher.last_name +
            ' warning that the experiment changed status to Approved.',
            self.browser.find_element_by_tag_name('body').text
        ))

        ##
        # Take some sleep to guarantie mail.outbox[0]
        ##
        time.sleep(0.5)

        # The email was sent to the researcher. The guy checks her email and
        # finds a message
        email = mail.outbox[0]
        self.assertIn(experiment.study.researcher.email, email.to)
        self.assertEqual(email.subject,
                         'Your experiment was approved')
        # Inside it, there's a message with congratulations and a link to
        # the Portal
        self.assertIn('We are pleased to inform you that your experiment ' +
                      experiment.title +
                      ' was approved by Neuromat Open Database Evaluation '
                      'Committee. All data of the submitted experiment '
                      'will be available freely to the public '
                      'consultation and shared under Creative Commons Share '
                      'Alike license.\n You can access your experiment '
                      'data by clicking on the link below\n' +
                      self.live_server_url + '\n', email.body)
        self.assertIn('With best regards,\n The NeuroMat Open Database '
                      'Evaluation Committee.', email.body)
        url_search = re.search(r'http://localhost:\d+', email.body)
        if not url_search:
            self.fail('Could not find url in email body:\n' + email.body)
        url = url_search.group(0)
        self.assertEqual(self.live_server_url, url)
        # She clicks on link and a new tab (or window) is opened in portal
        # home page
        self.browser.get(url)
        self.assertEqual(self.live_server_url, url)

    def test_change_status_from_to_be_analysed_to_under_analysis(self):
        # Statuses table cells are links. She clicks in an experiment status
        # that has to be analysed and see a modal that display the modal
        # title that shows experiment title in quotes.
        self.wait_for(
            lambda: self.browser.find_element_by_link_text('To be analysed')
        )
        experiment_link = self.browser.find_element_by_link_text(
            'To be analysed')
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(id=experiment_id)
        experiment_link.click()
        time.sleep(0.5)
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
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.UNDER_ANALYSIS + '"]').click()
        submit_button = self.browser.find_element_by_id('submit')
        submit_button.send_keys(Keys.ENTER)

        # The trustee Claudia is redirect to home page with a warning
        # message telling her that the experiment is now under analysis.
        # In table she sees that the experiment is "Under analysis".
        # TODO:
        # some times Experiment.STATUS_OPTIONS[2][1] not equal what
        # we want?
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_xpath(
                "//a[@data-experiment_id='" + str(experiment.id) + "']"
            ).text,
            Experiment.STATUS_OPTIONS[2][1]
        ))
        self.wait_for(lambda: self.assertIn(
            'An email was sent to ' + experiment.study.researcher.first_name +
            ' ' + experiment.study.researcher.last_name +
            ' warning that the experiment is under analysis.',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_change_status_to_not_approved_prohibted_without_justification(self):
        # Claudia has examined an experiment that has not conditions to be
        # published in portal. So after her analysis, he decide to not
        # approved it.
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        ))
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        # experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        ##
        # Waiting for modal pops up
        ##
        time.sleep(0.5)
        # The modal to change experiment status pops up, so she can select
        # NOT_APPROVED to the experiment.
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
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
        # submit_button = self.browser.find_element_by_id('submit')
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
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Under analysis'
            ).find_element_by_xpath(
                "//a[@data-experiment_trustee='claudia'] "
            )
        )
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia'] "
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(id=experiment_id)
        experiment_link.click()
        ##
        # Waiting for modal pops up
        ##
        time.sleep(0.5)
        # The modal to change experiment status pop up, so she can select
        # NOT_APPROVED to the experiment.
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.NOT_APPROVED + '"]').click()
        # As she choose NOT_APPROVED a textarea appears in modal requesting
        # her to fill in a justification message. So she write the
        # justification and submit the form.
        not_approved_box = self.browser.find_element_by_id('not_approved_box')
        not_approved_box.send_keys('The data sent has some mistakes. Please '
                                   'correct them and send again.')
        submit_button = self.browser.find_element_by_id('submit')
        submit_button.send_keys(Keys.ENTER)
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_xpath(
                "//a[@data-experiment_id='" + str(experiment.id) + "']"
            ).text,
            Experiment.STATUS_OPTIONS[4][1]
        ))
        self.wait_for(lambda: self.assertIn(
            'An email was sent to ' +
            experiment.study.researcher.first_name +
            ' ' + experiment.study.researcher.last_name +
            ' warning that the experiment was rejected.',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_change_status_to_the_same_status_doesnt_displays_warning_message(self):
        # Claudia clicks an experiment that has a given status, and submit
        # the modal form to change status with same status.
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Under analysis'
            ).find_element_by_xpath(
                "//a[@data-experiment_trustee='claudia']"
            )
        )
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()

        # The modal to change experiment status pop up, and she chooses
        # UNDER_ANALYSIS, the same status as before.
        self.wait_for(
            lambda: self.browser.find_element_by_id('id_status_choices')
        )
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        self.wait_for(
            lambda: status_choices_form.find_element_by_xpath(
                '//input[@type="radio" and  @value=' + '"' +
                Experiment.UNDER_ANALYSIS + '"]'
            ).click()
        )
        self.browser.find_element_by_id('submit').send_keys(Keys.ENTER)
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_xpath(
                "//a[@data-experiment_id='" + str(experiment.id) + "']"
            ).text,
            Experiment.STATUS_OPTIONS[2][1]
        ))
        self.wait_for(lambda: self.assertNotIn(
            'An email was sent to ' +
            experiment.study.researcher.first_name +
            ' ' + experiment.study.researcher.last_name +
            ' warning that the experiment is under analysis.',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_change_status_from_under_analysis_to_to_be_analysed_displays_warning_message(self):
        # Claudia clicks an experiment that she is already analysing. She is
        # in doubt about some aspect of it, and wants to pass it to other
        # trustee.
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Under analysis'
            ).find_element_by_xpath(
                "//a[@data-experiment_trustee='claudia']"
            )
        )
        experiment_link = self.browser.find_element_by_link_text(
            'Under analysis').find_element_by_xpath(
            "//a[@data-experiment_trustee='claudia']"
        )
        experiment_id = experiment_link.get_attribute('data-experiment_id')
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_link.click()
        ##
        # Waiting for modal pops up
        ##
        time.sleep(0.5)

        # The modal to change experiment status pop up, and she chooses
        # TO_BE_ANALYSED to liberate the experiment to be analysed by other
        # trustee.
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.TO_BE_ANALYSED + '"]').click()
        self.browser.find_element_by_id('submit').send_keys(Keys.ENTER)
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_xpath(
                "//a[@data-experiment_id='" + str(experiment.id) + "']"
            ).text,
            Experiment.STATUS_OPTIONS[1][1]
        ))
        self.wait_for(lambda: self.assertIn(
            'The experiment data ' + experiment.title +
            ' was made available to be analysed by other trustee.',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_can_change_status_from_under_analysis_to_other_only_if_trustee_is_the_owner(self):
        # Claudia see an experiment that is UNDER_ANALYSIS and
        # click on it. He sees a modal warning that the experiment has already
        # under analysis by other trustee.
        # Obs.:
        # 1) requires create user 'roque' to this test
        # 2) requires login in test with user different of 'roque'
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Under analysis').find_element_by_xpath(
                "//a[@data-experiment_trustee='roque'] "
            ).click()
        )
        # The modal to change experiment status pop up, but it has only a
        # message telling Claudia that the experiment is already been
        # analysed by other trustee
        self.wait_for(lambda: self.assertIn(
            'This experiment is already under analysis by '
            'trustee roque.',
            self.browser.find_element_by_id('status_body').text
        ))

    def test_can_view_ethics_committee_info(self):
        # Last experiment approved has ethics committee info (tests helper)
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # The trustee click in the experiment of the list that has ethics
        # commitee info data
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'View'
            ).find_element_by_xpath(
                "//a[@href='/experiments/" + experiment.slug + "/']"
            ).click()
        )
        self.browser.find_element_by_link_text('View').find_element_by_xpath(
            "//a[@href='/experiments/" + experiment.slug + "/']"
        ).click()

        # Bellow experiment description there's a link to ethics committee
        # approval site, and a link to download the ethics committee file
        # (because this experiment has that data posted via api)
        self.wait_for(lambda: self.assertEqual(
            experiment.ethics_committee_url,
            self.browser.find_element_by_link_text(
                'Approval of the ethics committee'
            ).get_attribute('href')
        ))
        ##
        # Obs.: self.assertIn because
        # experiment.ethics_committee_info.file.url gives relative url
        # here in test, but prepends url in template system
        ##
        self.wait_for(lambda: self.assertIn(
            experiment.ethics_committee_file.url,
            self.browser.find_element_by_link_text(
                'Approval of the ethics committee file'
            ).get_attribute('href')
        ))

    def test_change_status_from_under_analysis_to_approved_reindex_haystack(self):

        # The trustee Claudia changes an experiment under analysis to approved
        self.wait_for(
            lambda: self.browser.find_element_by_link_text(
                'Under analysis'
            ).find_element_by_xpath(
                '//a[@data-experiment_trustee="claudia"]').click()
        )
        self.wait_for(
            lambda:
            self.browser.find_element_by_id('id_status_choices')
                .find_element_by_xpath(
                '//input[@type="radio" and  @value=' + '"' +
                Experiment.APPROVED + '"]'
            ).click()
        )
        status_choices_form = self.browser.find_element_by_id(
            'id_status_choices')
        status_choices_form.find_element_by_xpath(
            '//input[@type="radio" and  @value=' + '"' +
            Experiment.APPROVED + '"]').click()
        submit_button = self.browser.find_element_by_id('submit')
        submit_button.send_keys(Keys.ENTER)

        # TODO: we're running rebuild_index manually, because the celery
        # TODO: task is not beeing recognized by tests. See:
        # TODO: https://stackoverflow.com/questions/4055860/unit-testing-with
        # TODO: -django-celery
        # TODO: http://bwreilly.github.io/blog/2013/07/21/testing-search
        # TODO: -haystack-in-django/
        # TODO: https://buxty.com/b/2012/12/testing-django-haystack-whoosh/
        # Redirect sys.stderr to avoid display
        # "GET http://127.0.0.1:9200/haystack/_mapping"
        # during tests.
        # TODO: see:
        # https://github.com/django-haystack/django-haystack/issues/1142
        stderr_backup, sys.stderr = \
            sys.stderr, open('/tmp/haystack_errors.txt', 'w+')
        # First time calling call_command does not give time to create de
        # file '/tmp/haystack_errors.txt' (I guess), so we give some time to
        # file to be created.
        call_command('rebuild_index', verbosity=0, interactive=False)
        sys.stderr.close()
        sys.stderr = stderr_backup

        # Coincidentally a researcher arrives to the site, just a few moments
        # after Claudia logged out from Portal, and searches for
        # the experiment that Claudia has just changed from under analysis
        # to approved.
        self.search_for('\"Experiment analysed by Claudia\"')

        # When a trustee changes experiment status from under analysis to
        # approved the system makes search reindexing, so the researcher will
        # see one line that corresponds to the experiment with 'Experiment
        # 2' in experiment title and nothing more.
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        experiment_text = self.browser.find_element_by_class_name(
            'experiment-matches'
        ).text
        self.assertIn('Experiment analysed by Claudia', experiment_text)

    def test_hover_mouse_over_notification_bell_display_tooltip(self):
        ##
        # First we get the total of experiments to be analysed
        ##
        experiments = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).count()

        # When the trustee pass the mouse over the notification bell at top
        # of the page, she sees a tooltip that displays how many experiments
        # has to be analysed
        self.wait_for(
            lambda: self.browser.find_element_by_id('new_experiments')
        )
        notification_bell = self.browser.find_element_by_id('new_experiments')
        tooltip_toggle = notification_bell.get_attribute('data-toggle')
        self.assertEqual('tooltip', tooltip_toggle)
        tooltip_text = notification_bell.get_attribute('title')
        self.assertEqual(
            'There is(are) ' + str(experiments) +
            ' experiment(s) to be analysed',
            tooltip_text
        )

    def test_url_editor_modal_displays_correct_content(self):
        experiment = self._access_change_slug_modal()

        # In modal there are some content about the current url, a label for
        # an input text form that trustee type the new slug, a sentence
        # telling how the new slug will be
        self.wait_for(
            lambda: self.assertIn(
                'Change experiment url slug',
                self.browser.find_element_by_id('change_url_modal').text
            )
        )
        modal = self.browser.find_element_by_id('change_url_modal')
        self.assertIn(
                'Current url: ' + self.live_server_url + '/experiments/' +
                experiment.slug,
                modal.text
        )
        self.assertIn(
            'Current slug: ' + experiment.slug, modal.text

        )
        self.assertIn(
            'New slug (type only lowcase letters without accents, numbers, '
            'dash, and underscore signs):',
            modal.text
        )
        self.assertEqual(
            'Type new slug',
            self.browser.find_element_by_id('id_slug').get_attribute(
                'placeholder'
            )
        )
        submit_button = self.browser.find_element_by_id('submit')
        self.assertEqual('Save', submit_button.get_attribute('value'))

    def test_submit_non_unique_slug_displays_error_message(self):
        self._access_change_slug_modal()

        ##
        # Get another experiment slug
        ##
        other_experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).last()

        # The trustee enter a slug that already exists
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_slug'
            ).send_keys(other_experiment.slug)
        )
        self.browser.find_element_by_id('id_slug').send_keys(Keys.ENTER)

        # The page refreshes telling her that the slug already exists
        self.wait_for(lambda: self.assertIn(
            'The slug entered is equal to other experiment slug. Please try '
            'again.',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_submit_empty_slug_displays_error_message(self):
        self._access_change_slug_modal()

        ##
        # Wait until element is visible, then remove element "required" from
        # input text element, to allow testing
        ##
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_slug').click()
        )
        self.browser.execute_script(
            'document.getElementById("id_slug").required = false;'
        )

        # She enters an empty slug and try to submit the change
        self.browser.find_element_by_id('id_slug').send_keys(Keys.ENTER)

        # As the change slug box is empty the page refreshes with an error
        # message
        self.wait_for(lambda: self.assertIn(
            'Empty slugs is not allowed. Please enter a valid slug',
            self.browser.find_element_by_tag_name('body').text
        ))

    @skip
    def test_submit_invalid_slug_displays_error_message(self):
        # TODO: skipping this test. We are testing this in views unittest. We
        # TODO: can't test this
        # TODO: because the javascript executed to prevent typing not allowed
        # TODO: chars works and the test fails. As we can't disable the
        # TODO: script code after DOM has render it. Tested mannualy without
        # TODO: javascript.
        self._access_change_slug_modal()

        # The trustee tryes to enter some invalid slug and submit it
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_slug'
            ).send_keys(random_utf8_string(random.randint(1, 50)))
        )
        self.browser.find_element_by_id('id_slug').send_keys(Keys.ENTER)

        # As the slug is invalid, the page refreshes telling her that the
        # slug is invalid
        self.wait_for(lambda: self.assertIn(
            'The slug entered is not allowed. Please enter a valid slug. '
            'Type only lowcase letters without accents, numbers, dash, '
            'and underscore signs',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_submit_slug_with_less_than_three_characters_displays_error_message(self):
        self._access_change_slug_modal()

        # The trustee tryes to enter a slug with less than three characters
        self.wait_for(
            lambda: self.browser.find_element_by_id('id_slug').send_keys('sl')
        )
        self.browser.execute_script(
            'document.getElementById("submit").disabled = false;'
        )
        self.browser.find_element_by_id('submit').click()

        # As the slug has only two characters, the page refreshes telling
        # her that the slug is invalid
        self.wait_for(lambda: self.assertIn(
            'The slug entered is two small. Please enter at least 3 '
            'characters',
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_submit_valid_slug_returns_redirect_with_success_message(self):
        self._access_change_slug_modal()

        # The trustee enters a valid slug and submit it
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_slug'
            ).send_keys('a-brand_new_slug')
        )
        self.browser.find_element_by_id('id_slug').send_keys(Keys.ENTER)

        # As the slug is valid, the page refreshes telling her that the slug
        # was changed successfully
        self.wait_for(lambda: self.assertIn(
            "The experiment's slug was modified",
            self.browser.find_element_by_tag_name('body').text
        ))

    def test_submit_same_slug_returns_redirect_with_no_message(self):
        experiment = self._access_change_slug_modal()

        # The trustee enters the same slug as current one
        self.wait_for(
            lambda: self.browser.find_element_by_id(
                'id_slug'
            ).send_keys(experiment.slug)
        )
        self.browser.find_element_by_id('id_slug').send_keys(Keys.ENTER)

        # As the slug entered is the same as current one the page refreshes
        # with no messages at all
        with self.assertRaises(NoSuchElementException):
            self.wait_for(lambda: self.browser.find_element_by_css_selector(
                '.warning-message'
            ))
