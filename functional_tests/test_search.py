from django.core.management import call_command
from selenium.webdriver.common.keys import Keys

from experiments.models import Study, Experiment, Group, Step
from functional_tests.base import FunctionalTest

import time


class SearchTest(FunctionalTest):

    def setUp(self):
        super(SearchTest, self).setUp()
        call_command('rebuild_index', verbosity=0, interactive=False)

    @staticmethod
    def rebuild_index():
        call_command('rebuild_index', verbosity=0, interactive=False)

    def verify_n_experiments_in_table_rows(self, n):
        table = self.browser.find_element_by_id('search_table')
        experiment_rows = \
            table.find_elements_by_class_name('experiment-matches')
        count = 0
        for experiment in experiment_rows:
            if 'Brachial Plexus' in experiment.text:
                count = count + 1
        self.assertEqual(n, count)

    def test_two_words_searched_return_correct_objects(self):

        # Joselina, a neuroscience researcher at Numec is delighted with the
        # NED Portal. She decides to search for experiments that contains
        # "Braquial Plexus" in whatever part of the portal. The search
        # engine is complex. Some of its facilities consists in ignoring
        # upper/lower case letters, search for terms individually and in
        # whatever order in the sentence, too.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(1)
        # The search engine searches in all the site content.
        # As there are "Braquial Plexus", "braquial plexus" in experiments
        # data per se, and the two words are also found separated,
        # like 'brachial ... plexus' and 'plexus ... brachial', for intance, in
        # studies, groups, and study keywords, she sees in Search results
        # one list for each of them.
        # One experiment has 'Brachial Plexus' in title, other has 'Brachial
        # plexus' in description
        search_header_title = self.browser.find_element_by_tag_name('h3').text
        self.assertEqual(search_header_title, 'Search Results')

        table = self.browser.find_element_by_id('search_table')
        experiment_rows = \
            table.find_elements_by_class_name('experiment-matches')
        self.assertTrue(
            any('Brachial Plexus' in row.text for row in experiment_rows)
        )
        self.assertTrue(
            any('Brachial plexus' in row.text for row in experiment_rows)
        )
        # The information of an experiment is organized this way: first line
        # is the object that was matched - in this case: Experiment. Second
        # line contains the field names and contents, starting with title.
        self.assertTrue(
            any(
                'Experiment\n\ntitle:' in row.text for row in experiment_rows
            ), [row.text for row in experiment_rows]
        )
        # There's an experiment whose study has the word 'brachial' in study
        # description, and 'brachial plexus' in one of the study keywords -
        # when there are matches in other models data besides
        # experiment, a new line in the results displays other models'
        # matches, below the experiment that model pertains.
        study = Study.objects.filter(
            experiment__status=Experiment.APPROVED
        ).first()
        study_rows = \
            self.browser.find_elements_by_class_name('study-matches')
        self.assertTrue(
            any(
                'Experiment: ' + study.experiment.title +
                ' > Study\n\ntitle:' in row.text for row in study_rows
            ), [row.text for row in study_rows]
        )
        self.assertTrue(any('brachial' in row.text for row in study_rows))
        self.assertTrue(
            any('brachial plexus' in row.text for row in study_rows)
        )

        # There's one group with the string 'Plexus brachial' in
        # group description, and 'brachial Plexus' in group inclusion criteria
        group = Group.objects.filter(
            experiment__status=Experiment.APPROVED
        ).first()
        group_rows = self.browser.find_elements_by_class_name('group-matches')
        self.assertTrue(
            any(
                'Experiment: ' + group.experiment.title + ' > Groups\n\ntitle:'
                in row.text for row in group_rows
            ), [row.text for row in group_rows]
        )
        self.assertTrue(
            any('Plexus brachial' in row.text for row in group_rows)
        )
        self.assertTrue(
            any('brachial Plexus' in row.text for row in group_rows)
        )

        # The researcher now wishes to search for a study that has as
        # collaborator a coleague of her, called Pero Vaz.
        # She types 'Pero Vaz' in search box and hits Enter.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.clear()
        search_box.send_keys('Pero Vaz')
        # self.browser.find_element_by_id('submit_terms').click()
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)
        # She sees that there is one Study whose one of the collaborators is
        # Pero Vaz.
        study_rows = \
            self.browser.find_elements_by_class_name('study-matches')
        self.assertTrue(any('Pero Vaz' in row.text for row in study_rows))

    def test_search_returns_only_last_version_experiments(self):

        # The researcher searches for 'Brachial Plexus'
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(1)

        # She want's to see only last experiments versions -
        # as tests helper creates version 2 of an experiment, only version 2
        # is supposed to appear in search results. Obs.: this test only
        # tests for duplicate result, not for the correct version.
        table = self.browser.find_element_by_id('search_table')
        # we make experiment.description = Ein Beschreibung in tests helper
        experiment_rows = \
            table.find_elements_by_class_name('experiment-matches')
        count = 0
        for experiment in experiment_rows:
            if 'Ein Beschreibung' in experiment.text:
                count = count + 1
        self.assertEqual(1, count)

    def test_search_returns_only_approved_experiments(self):

        # The researcher searches for 'Brachial Plexus'
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(1)

        # As there are 3 experiments with 'Brachial Plexus' in title,
        # one approved, one under analysis, and one to be analysed (created
        # in tests helper), it's supposed to only one match occurs (the
        # experiment approved), one that is Experiment and has title equals
        # to 'Brachial Plexus'
        self.verify_n_experiments_in_table_rows(2)

    def test_search_with_filters_returns_correct_objects(self):

        # Joselina is happy. When she searched for Brachial Plexus, she found
        # the experiment she recently sent to portal through NES. She wants to
        # explore more in depth the portal search functionality.
        # In select box bellow search box she can choose filters like EEG,
        # TMS, EMS, among others. She types "brachial plexus" in search box,
        # and selects EMG in select box. Then she clicks in search button.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(1)

        ##
        # As there are 2 experiments with 'Brachial Title' in title,
        # it's expected that Joselina sees only one Experiment search
        # result, given that she chosen to filter experiments that has EMG
        # Setting.
        # The page refreshes displaying the results
        self.verify_n_experiments_in_table_rows(1)
        
        self.fail('Finish this test!')
