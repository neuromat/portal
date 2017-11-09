import random
import sys

import haystack
from django.core.management import call_command

from experiments.models import Study, Experiment, Group, Step
from functional_tests.base import FunctionalTest

import time


class SearchTest(FunctionalTest):

    def setUp(self):
        super(SearchTest, self).setUp()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

    def tearDown(self):
        super(SearchTest, self).tearDown()
        self.haystack_index('clear_index')

    @staticmethod
    def haystack_index(action):
        # Redirect sys.stderr to avoid display
        # "GET http://127.0.0.1:9200/haystack/_mapping"
        # during tests.
        # TODO: see:
        # https://github.com/django-haystack/django-haystack/issues/1142
        stderr_backup, sys.stderr = sys.stderr, \
                                    open('/tmp/haystack_errors.txt', 'w+')
        call_command(action, verbosity=0, interactive=False)
        sys.stderr.close()
        sys.stderr = stderr_backup

    def verify_n_objects_in_table_rows(self, n, row_class):
        table = self.browser.find_element_by_id('search_table')
        count = len(table.find_elements_by_class_name(row_class))
        self.assertEqual(n, count)

    def search_for(self, string):
        search_box = self.browser.find_element_by_id('id_q')
        search_box.clear()
        search_box.send_keys(string)
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(1)

    def test_search_two_words_returns_correct_objects(self):

        # Joselina, a neuroscience researcher at Numec is delighted with the
        # NED Portal. She decides to search for experiments that contains
        # "Braquial Plexus" in whatever part of the portal. The search
        # engine is complex. Some of its facilities consists in ignoring
        # upper/lower case letters, search for terms individually and in
        # whatever order in the sentence, too.
        self.search_for('Brachial Plexus')
        # The search engine searches in all the site content.
        # As there are "Braquial Plexus", "braquial plexus" in experiments
        # data per se, and the two words are also found separated,
        # like 'brachial ... plexus' and 'plexus ... brachial', for intance, in
        # studies, groups, and study keywords, she sees in Search results
        # one list for each of them.
        # One experiment has 'Brachial Plexus' in title, other has 'Brachial
        # plexus' in description
        search_header_title = self.browser.find_element_by_tag_name('h2').text
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
        ##
        # The information of an experiment is organized this way: first line
        # is the object that was matched - in this case: Experiment. Second
        # line contains the field names and contents, starting with title.
        ##
        any(self.assertRegex(row.text, r'Experiment:.+\n\ntitle:')
            for row in experiment_rows)
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
                ' > Study: ' + study.title + '\n\ntitle:' in row.text
                for row in study_rows
            )
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
                'Experiment: ' + group.experiment.title +
                ' > Group: ' + group.title + '\n\ntitle:'
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
        self.search_for('Pero Vaz')
        # She sees that there is one Study whose one of the collaborators is
        # Pero Vaz.
        study_rows = \
            self.browser.find_elements_by_class_name('study-matches')
        self.assertTrue(any('Pero Vaz' in row.text for row in study_rows))

    def test_search_returns_only_last_version_experiments(self):

        # The researcher searches for 'Brachial Plexus'
        self.search_for('Brachial Plexus')

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
        self.search_for('Brachial Plexus')

        # As there are 4 experiments with 'Brachial Plexus' in title,
        # two approved, one under analysis, and one to be analysed (created
        # in tests helper), it's supposed to two matches occurs (the
        # experiments approved), the Experiment's tha has matches for
        # 'Brachial Plexus' haystack search results.
        self.verify_n_objects_in_table_rows(2, 'experiment-matches')

    def test_search_with_one_filter_returns_correct_objects(self):

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
        # The page refreshes displaying the results.
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(2, 'group-matches')

    def test_search_with_two_filters_returns_correct_objects(self):
        # Ok, Joselina now wants to search experiments that has EEG and EMG
        # in groups data collection. In multiple choices box she clicks in
        # EEG and EMG
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        self.browser.find_element_by_id('filter_box').click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(2)

        ##
        # There's an experiment group that has one EEG step and one EMG
        # step, besides "Plexus Brachial" in group description.
        # On the other hand, there's a group that has "Brachial Plexus" in
        # despcription, an EEG step but not an EMG step. So she will see only
        # one of the two groups.
        ##
        self.verify_n_objects_in_table_rows(1, 'group-matches')

    def test_search_with_AND_modifier_returns_correct_objects(self):
        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "brachial AND EEG" in that.
        self.search_for('brachial AND EEG')

        ##
        # As we created, in tests helper, an experiment with 'Brachial' in
        # experiment  title, 'EEG' in experiment description, and a study
        # with 'brachial ... EEG' in its description, the search results bring
        # an experiment and a study.
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        experiment = self.browser.find_element_by_class_name(
            'experiment-matches').text
        self.assertIn('Brachial', experiment)
        self.assertIn('EEG', experiment)
        self.verify_n_objects_in_table_rows(1, 'study-matches')
        study = self.browser.find_element_by_class_name(
            'study-matches').text
        self.assertIn('brachial', study)
        self.assertIn('EEG', study)

    def test_search_with_OR_modifier_returns_correct_objects(self):
        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "EMG OR EEG".
        ##
        # TODO: when change order - 'EEG OR EMG', test fails. Why?
        ##
        self.search_for('EMG OR EEG')

        ##
        # In tests helper, we have an experiment that has 'EMG' in title,
        # and 'EEG' in description. There's a study with 'EEG' in study
        # description. So, she's got two rows in Search Results.
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        experiment = self.browser.find_element_by_class_name(
            'experiment-matches').text
        self.assertIn('EMG', experiment)
        self.assertIn('EEG', experiment)
        self.verify_n_objects_in_table_rows(1, 'study-matches')
        study = self.browser.find_element_by_class_name(
            'study-matches').text
        self.assertIn('EEG', study)

    def test_search_with_NOT_modifier_returns_correct_objects(self):
        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "brachial NOT plexus".
        self.search_for('brachial NOT plexus')

        ##
        # In tests helper, we've created a group with only 'Brachial only'
        # in title. As other objects that has 'brachial' as a substring in
        # some field, has 'plexus' as a substring in some another field,
        # we obtain just one row in Search results: that group with
        # 'Brachial only' in title.
        ##
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        self.verify_n_objects_in_table_rows(1, 'group-matches')
        group_text = self.browser.find_element_by_class_name(
            'group-matches'
        ).text
        self.assertIn('Brachial', group_text)

    def test_search_with_quotes_returns_correct_objects(self):
        # Joselina sees in tooltip, when hovering mouse onto it, that she
        # can search by exact terms inside quotes.
        self.search_for('\"Plexus brachial\"')

        # As we have only one description in one group that has exactly
        # this string, Joselina will see only one row in Search Results list,
        # one that matches this group
        ##
        # Haystack SearchQuerySet filter method, content__exact attribute
        # does not differentiate by upper or lower case in that attribute.
        ##
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        self.verify_n_objects_in_table_rows(1, 'group-matches')
        group_text = self.browser.find_element_by_class_name(
            'group-matches'
        ).text
        self.assertIn('Plexus brachial', group_text)

    def test_hover_mouse_over_search_box_display_tooltip(self):
        # In exploring the search tools, Joselina sees that when she hover
        # the mouse in search box, a tooltip is shown, with tips on advanced
        # searches
        search_box = self.browser.find_element_by_id('id_q')
        tooltip_text = search_box.get_attribute('title')
        self.assertEqual(
            'You can search for terms in quotes to search for exact terms.\n'
            'You can use the modifiers AND, OR, '
            'NOT to combine terms to '
            'search. For instance:\nterm1 AND term2\nterm1 OR term2\nterm1 '
            'NOT term2\nAll kind of combinations with AND, OR, NOT are '
            'accepted in advanced searching.\nBy default, searching for '
            'terms separated with one or more spaces will apply the AND '
            'modifier.'
            , tooltip_text
        )
        tooltip_data_toggle = search_box.get_attribute('data-toggle')
        self.assertEqual('tooltip', tooltip_data_toggle)

    def test_search_only_with_two_filters_returns_correct_results(self):
        # Joselina wishes to search only experiments that has EMG and EEG
        # steps, regardless of search terms.
        self.browser.find_element_by_id('filter_box').click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(2)

        # As we have only one experiment with EMG and EEG steps, Joselina gets
        # only one row tha corresponds to that the experiment
        ##
        # If user searches only with filters selected (without a query in
        # search box, we display in search results, only experiment rows)
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        experiment_text = self.browser.find_element_by_class_name(
            'experiment-matches'
        ).text
        self.assertIn('Experiment changed to test filter only',
                      experiment_text)

    def test_search_only_with_one_filter_returns_correct_results_1(self):
        # Joselina wishes to search only experiments that has EEG
        # stpes, regardless of search terms.
        self.browser.find_element_by_id('filter_box').click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(2)

        # As we have only one experiment with EEG step, Joselina
        # gets only one row that corresponds to that the experiment
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        experiment_text = self.browser.find_element_by_class_name(
            'experiment-matches'
        ).text
        self.assertIn('Experiment changed to test filter only',
                      experiment_text)

    def test_search_only_with_one_filter_returns_correct_results_2(self):
        # Joselina wishes to search only experiments that has EMG
        # steps, regardless of search terms.
        self.browser.find_element_by_id('filter_box').click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()
        time.sleep(2)

        # As we have two experiments with EMG steps, Joselina
        # gets two rows that corresponds to that the experiments
        self.verify_n_objects_in_table_rows(2, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        table = self.browser.find_element_by_id('search_table')
        experiment_rows =  \
            table.find_elements_by_class_name('experiment-matches')
        count = 0
        for experiment in experiment_rows:
            if 'Brachial Plexus (with EMG Setting)' in experiment.text:
                count = count + 1
            if 'Experiment changed to test filter only' in experiment.text:
                count = count + 1
        self.assertEqual(2, count)

    def test_search_display_backhome_button(self):
        # When Joselina makes searches, a button to back homepage is
        # displayed on the right side, above the list of search results
        self.search_for('brachial plexus')
        link_home = self.browser.find_element_by_id('link_home')
        self.assertEqual('Back Home', link_home.text)
        link_home.click()
        time.sleep(1)

        # Joselina is back homepage
        table_title = self.browser.find_element_by_id(
            'id_table_title').find_element_by_tag_name('h2').text
        self.assertEqual('List of Experiments', table_title)

    def test_search_tmssetting_returns_correct_objects(self):
        # Joselina searches for a TMS Setting whose name is 'tmssettingname'
        self.search_for('tmssettingname')

        # As there is one TMSSetting object with that name, she sees just
        # one row in Search Results list
        self.verify_n_objects_in_table_rows(1, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmssetting_text = self.browser.find_element_by_class_name(
            'tmssetting-matches'
        ).text
        self.assertIn('tmssettingname', tmssetting_text)

    def test_search_tmsdevicesetting_returns_correct_objects(self):
        # Joselina searches for a TMS Device Setting whose name is
        # 'tmsdevicesettingname'
        # TODO: test for choice representation!
        self.search_for('single_pulse')

        # As there is three TMSDeviceSetting object with that name, she sees
        # just one row in Search Results list
        self.verify_n_objects_in_table_rows(3, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmsdevicesetting_text = self.browser.find_element_by_class_name(
            'tmsdevicesetting-matches'
        ).text
        self.assertIn('Single pulse', tmsdevicesetting_text)

    def test_search_tmsdevice_returns_correct_objects(self):
        # Joselina searches for an experiment in which was used a TMS Device
        # whose manufacturer name is 'Siemens'
        self.search_for('Siemens')

        # As there is one TMSDevice object that has Magstim as manufacturer,
        # but three TMSDeviceSetting objects that has that TMSDevice object as
        # a Foreign Key, she sees three rows in Search Results list
        self.verify_n_objects_in_table_rows(3, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmsdevicesetting_text = self.browser.find_element_by_class_name(
            'tmsdevice-matches'
        ).text
        self.assertIn('Siemens', tmsdevicesetting_text)

    def test_search_coilmodel_returns_correct_objects(self):
        # Joselina searches for an experiment in which was used a Coil Model
        # whose name is 'Magstim'
        self.search_for('Magstim')
        # As there is one CoilModel object that has Magstim as manufacturer,
        # but three TMSDeviceSetting objects that has that CoilModel object as
        # a Foreign Key, she sees three rows in Search Results list
        self.verify_n_objects_in_table_rows(3, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmsdevicesetting_text = self.browser.find_element_by_class_name(
            'coilmodel-matches'
        ).text
        self.assertIn('Magstim', tmsdevicesetting_text)

    def test_search_tmsdata_returns_correct_objects(self):
        # Obs.: the tests commented bellow "passed" manually in localhost,
        # by creating entries in faker_populator.

        # Joselina searches for an experiment whose TMSData of a participant
        # has collecting data from 'cerebral cortex'
        self.search_for('cerebral cortex')
        # As there is three TMSData object with 'cereberal cortex' as the
        # brain_area_name field, one of them associated with a TMSSetting
        # object, and other two associated with another TMSSetting object
        # she sees two rows in Search Results list
        self.verify_n_objects_in_table_rows(3, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmsdevicesetting_text = self.browser.find_element_by_class_name(
            'tmsdata-matches'
        ).text
        self.assertIn('cerebral cortex', tmsdevicesetting_text)

    def test_search_eegsetting_returns_correct_objects(self):
        # Joselina wants to search for experiments whose EEGSetting name is
        # 'eegsettingname'
        self.search_for('eegsettingname')

        # As there is three EEGSetting objects with that name,
        # one associated to an experiment, and the other two associated with
        # another experiment, she sees three rows in Search Results list
        self.verify_n_objects_in_table_rows(3, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        eegsetting_text = self.browser.find_element_by_class_name(
            'eegsetting-matches'
        ).text
        self.assertIn('eegsettingname', eegsetting_text)

    def test_search_questionnaire_data_returns_correct_objects_1(self):
        # Joselina wants to search for experiments that contains some
        # questionnaire data
        self.search_for('\"History of fracture?\"')

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.verify_n_objects_in_table_rows(1, 'questionnaire-matches')
        self.verify_n_objects_in_table_rows(0, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')

        questionnaire_text = self.browser.find_element_by_class_name(
            'questionnaire-matches'
        ).text
        self.assertIn('History of fracture', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_2(self):
        # Joselina wants to search for experiments that contains some
        # questionnaire data
        self.search_for('\"trauma of your brachial plexus\"')

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.verify_n_objects_in_table_rows(1, 'questionnaire-matches')
        self.verify_n_objects_in_table_rows(0, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')

        questionnaire_text = self.browser.find_element_by_class_name(
            'questionnaire-matches'
        ).text
        self.assertIn('trauma of your brachial plexus', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_3(self):
        # Joselina wants to search for experiments that contains a phrase
        self.search_for('\"Injury by firearm\"')

        # As there are one questionnaire with terms searched by Joselina,
        # it is displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.verify_n_objects_in_table_rows(1, 'questionnaire-matches')
        self.verify_n_objects_in_table_rows(0, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0,
                                            'experimentalprotocol-matches')

        questionnaire_text = self.browser.find_element_by_class_name(
            'questionnaire-matches'
        ).text
        self.assertIn('Injury by firearm', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_4(self):

        # Joselina wants to search for experiments that contains some
        # questionnaire data
        self.search_for('\"History of fracture\" \"What side of the injury\"')

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.verify_n_objects_in_table_rows(2, 'questionnaire-matches')
        self.verify_n_objects_in_table_rows(0, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')

        questionnaire_rows = self.browser.find_element_by_id(
            'search_table'
        ).text
        self.assertIn('History of fracture', questionnaire_rows)
        self.assertIn('What side of the injury', questionnaire_rows)

    def test_click_in_a_search_result_display_experiment_detail_page(self):
        # TODO: the test tests for some match types not all. Wold be better
        # TODO: to test for each and all match types.

        # The researcher searches for 'brachial' term
        self.search_for('brachial')

        # She obtains some results. She clicks in on result link randomly
        # and is redirected to experiment detail page
        results_table = self.browser.find_element_by_id('search_table')

        links = results_table.find_elements_by_tag_name('a')
        random_link = random.choice(links)
        random_link.click()
        time.sleep(1)

        detail_content_title = \
            self.browser.find_element_by_tag_name('h2').text
        self.assertEqual(detail_content_title,
                         'Open Database for Experiments in Neuroscience')
