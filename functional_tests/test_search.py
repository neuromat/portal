import random
import sys

import haystack
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

from experiments.models import Study, Experiment, Group, Step, EMGSetting, \
    GoalkeeperGame, ContextTree, EEGSetting, Stimulus, GenericDataCollection, \
    EMGElectrodePlacementSetting, EMGElectrodePlacement, EMGSurfacePlacement, \
    EMGIntramuscularPlacement, EMGNeedlePlacement, EEGElectrodePosition, \
    ElectrodeModel, SurfaceElectrode, IntramuscularElectrode, Instruction, \
    Gender
from experiments.tests.tests_helper import create_experiment, \
    create_emg_setting, create_group, create_goalkeepergame_step, \
    create_context_tree, create_eeg_setting, create_eeg_electrodenet, \
    create_eeg_solution, create_eeg_filter_setting, \
    create_eeg_electrode_localization_system, \
    create_emg_digital_filter_setting, create_stimulus_step, \
    create_generic_data_collection_step, create_electrode_model, \
    create_emg_electrode_setting, create_emg_electrode_placement, \
    create_emg_electrode_placement_setting, create_emg_surface_placement, \
    create_emg_intramuscular_placement, create_emg_needle_placement, \
    create_eeg_electrode_position, create_surface_electrode, \
    create_intramuscular_electrode, create_instruction_step, create_step, \
    create_publication, create_valid_questionnaires, \
    create_experiment_researcher, \
    create_trustee_user, create_study, create_researcher, create_keyword, \
    create_classification_of_diseases, create_next_version_experiment, \
    create_emg_step, create_participant, create_genders, \
    create_eeg_step, create_tms_setting, create_tms_device_setting, \
    create_tms_device, create_coil_model, create_tms_data
from functional_tests.base import FunctionalTest

import time


# To test haystack using a new index, instead of the settings.py index
TEST_HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE':
            'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': settings.HAYSTACK_TEST_URL,
        'INDEX_NAME': 'test_haystack',
        'TIMEOUT': 60 * 10,
    }
}


@override_settings(HAYSTACK_CONNECTIONS=TEST_HAYSTACK_CONNECTIONS)
class SearchTest(FunctionalTest):

    def setUp(self):
        create_genders()
        self.trustee1 = create_trustee_user('claudia')
        self.trustee2 = create_trustee_user('roque')
        super(SearchTest, self).setUp()
        # search works only with approved experiments
        self.experiment.status = Experiment.APPROVED
        self.experiment.save()

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

    @staticmethod
    def create_objects_to_test_search_emgsetting():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        create_emg_setting(experiment1)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        create_emg_setting(experiment2)
        create_emg_setting(experiment2)
        for emg_setting in EMGSetting.objects.all():
            emg_setting.name = 'emgsettingname'
            emg_setting.save()

    @staticmethod
    def create_objects_to_test_search_step():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        group1 = create_group(1, experiment1)
        group2 = create_group(1, experiment1)
        create_step(1, group1, random.choice(Step.STEP_TYPES)[0])
        create_step(1, group2, random.choice(Step.STEP_TYPES)[0])
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        group = create_group(1, experiment2)
        create_step(1, group, random.choice(Step.STEP_TYPES)[0])

    @staticmethod
    def create_objects_to_test_search_stimulus_step():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        group1 = create_group(1, experiment1)
        group2 = create_group(1, experiment1)
        create_stimulus_step(group1)
        create_stimulus_step(group2)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        group = create_group(1, experiment2)
        create_stimulus_step(group)
        for stimulus_step in Stimulus.objects.all():
            stimulus_step.stimulus_type_name = 'stimulusschritt'
            stimulus_step.save()

    @staticmethod
    def create_objects_to_test_search_instruction_step():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        group1 = create_group(1, experiment1)
        group2 = create_group(1, experiment1)
        create_instruction_step(group1)
        create_instruction_step(group2)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        group = create_group(1, experiment2)
        create_instruction_step(group)

    @staticmethod
    def create_objects_to_test_search_genericdatacollection_step():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        group1 = create_group(1, experiment1)
        group2 = create_group(1, experiment1)
        create_generic_data_collection_step(group1)
        create_generic_data_collection_step(group2)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        group = create_group(1, experiment2)
        create_generic_data_collection_step(group)
        for generic_data_collection in GenericDataCollection.objects.all():
            generic_data_collection.information_type_name = \
                'generischedatensammlung'
            generic_data_collection.save()

    @staticmethod
    def create_objects_to_test_search_goalkeepergame_step():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        group1 = create_group(1, experiment1)
        group2 = create_group(1, experiment1)
        context_tree1 = create_context_tree(experiment1)
        create_goalkeepergame_step(group1, context_tree1)
        create_goalkeepergame_step(group2, context_tree1)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        group = create_group(1, experiment2)
        context_tree2 = create_context_tree(experiment2)
        create_goalkeepergame_step(group, context_tree2)
        for goalkeepergame in GoalkeeperGame.objects.all():
            goalkeepergame.software_name = 'goalkeepergame'
            goalkeepergame.software_description = 'Ein Beschreibung'
            goalkeepergame.save()

    @staticmethod
    def create_objects_to_test_search_eeg_setting():
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        create_eeg_setting(1, experiment1)
        create_eeg_setting(1, experiment1)
        create_eeg_setting(1, experiment2)
        for eeg_setting in EEGSetting.objects.all():
            eeg_setting.name = 'eegsettingname'
            eeg_setting.save()

    @staticmethod
    def create_objects_to_test_search_emgelectrodeplacementsetting(type):
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        emg_setting = create_emg_setting(experiment1)
        electrode_model = create_electrode_model()
        emg_electrode_setting = create_emg_electrode_setting(
            emg_setting, electrode_model
        )
        if type == 'emg_electrode_placement':
            emg_type_placement = create_emg_electrode_placement()
        elif type == 'emg_surface_placement':
            emg_type_placement = create_emg_surface_placement()
        elif type == 'emg_intramuscular_placement':
            emg_type_placement = create_emg_intramuscular_placement()
        elif type == 'emg_needle_placement':
            emg_type_placement = create_emg_needle_placement()

        create_emg_electrode_placement_setting(
            emg_electrode_setting, emg_type_placement
        )
        for emg_electrode_placement_setting in \
                EMGElectrodePlacementSetting.objects.all():
            # TODO: make search_term = 'quadrizeps' and put in method argument
            emg_electrode_placement_setting.muscle_name = 'quadrizeps'
            emg_electrode_placement_setting.save()

    @staticmethod
    def create_objects_to_test_search_eegelectrodeposition(
            type='electrode_model'):
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        eeg_setting = create_eeg_setting(1, experiment1)
        eeg_electrode_localization_system = \
            create_eeg_electrode_localization_system(eeg_setting)
        if type == 'electrode_model':
            electrode_model = create_electrode_model()
        elif type == 'surface_electrode':
            electrode_model = create_surface_electrode()
        elif type == 'intramuscular_electrode':
            electrode_model = create_intramuscular_electrode()

        create_eeg_electrode_position(
            eeg_electrode_localization_system, electrode_model
        )

    def create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_electrode_placement(
            self, search_text):
        self.create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_electrode_placement')
        # TODO: should test for all attributes
        for emg_electrode_placement in EMGElectrodePlacement.objects.all():
            emg_electrode_placement.standardization_system_name = search_text
            emg_electrode_placement.save()

    def create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_surface_placement(
            self, search_text):
        self.create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_surface_placement'
        )
        # TODO: should test for all attributes
        for emg_surface_placement in EMGSurfacePlacement.objects.all():
            emg_surface_placement.start_posture = search_text
            emg_surface_placement.save()

    def create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_intramuscular_placement(
            self, search_text):
        self.create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_intramuscular_placement'
        )
        # TODO: should test for all attributes
        for emg_intramuscular_placement in EMGIntramuscularPlacement.objects.all():
            emg_intramuscular_placement.method_of_insertion = search_text
            emg_intramuscular_placement.save()

    def create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_needle_placement(
            self, search_text):
        self.create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_needle_placement'
        )
        # TODO: should test for all attributes
        for emg_needle_placement in EMGNeedlePlacement.objects.all():
            emg_needle_placement.depth_of_insertion = search_text
            emg_needle_placement.save()

    def create_objects_to_test_search_eeg_electrode_position_with_electrode_model(
            self, search_text):
        self.create_objects_to_test_search_eegelectrodeposition(
            'electrode_model'
        )
        # TODO: should test for all attributes
        for electrode_model in ElectrodeModel.objects.all():
            electrode_model.name = search_text
            electrode_model.save()

    def check_matches(self, matches, css_selector, text):
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            matches, css_selector
        ))
        element_text = self.browser.find_element_by_class_name(
            css_selector
        ).text
        self.assertIn(text, element_text)

    def test_click_in_a_search_result_display_experiment_detail_page(self):
        # TODO: the test tests for some match types, not all. Wold be better
        # TODO: to test for each and all match types.
        self.experiment.status = Experiment.APPROVED
        self.experiment.title = 'brachial'
        self.experiment.save()
        study = create_study(1, self.experiment)
        study.title = 'brachial'
        study.save()
        create_researcher(study)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # The researcher searches for 'brachial' term
        self.search_for('brachial')

        # She obtains some results. She clicks in on A result link randomly
        # and is redirected to experiment detail page
        self.wait_for(
            lambda:
            self.browser.find_element_by_id('search_table')
        )

        links = self.browser.find_element_by_id(
            'search_table'
        ).find_elements_by_tag_name('a')
        random_link = random.choice(links)
        random_link.click()

        self.wait_for(
            lambda:
            self.assertEqual(
                self.browser.find_element_by_tag_name('h2').text,
                'Open Database for Experiments in Neuroscience'
            )
        )

    def test_search_two_words_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'Brachial Plexus'
        self.experiment.save()
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Brachial Plexus'
        e2.save()
        e3 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e3.title = 'Brachial Plexus'
        e3.save()
        e4 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e4.title = 'Brachial Plexus (with EMG Setting)'
        e4.description = 'Ein Beschreibung. Brachial plexus repair by ' \
                         'peripheral nerve ' \
                         'grafts directly into the spinal cord in rats ' \
                         'Behavioral and anatomical evidence of ' \
                         'functional recovery. The EEG text.'
        e4.save()
        create_keyword('brachial plexus')
        study = create_study(1, self.experiment)
        study.description = 'The brachial artery is the major blood vessel ' \
                            'of the (upper) arm. It\'s correlated with ' \
                            'plexus. This study should have an experiment ' \
                            'with EEG.'
        study.keywords.add('brachial plexus')
        create_researcher(study)
        study.save()
        group = create_group(1, self.experiment)
        group.description = 'Plexus brachial is written in wrong order. ' \
                            'Correct is Brachial plexus.'
        ic = create_classification_of_diseases()
        ic.code = 'BP'
        ic.description = 'brachial Plexus'
        ic.abbreviated_description = 'brachial Plexus'
        ic.save()
        group.inclusion_criteria.add(ic)
        group.save()
        group2 = create_group(1, e4)
        group2.title = 'Brachial only'
        group2.description = 'Brachial plexus is a set of nerves.'
        group2.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

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
        self.wait_for(lambda: self.assertEqual(
            self.browser.find_element_by_tag_name('h2').text, 'Search Results'
        ))

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

    def test_search_returns_only_last_version_experiments(self):
        next_version = create_next_version_experiment(self.experiment)
        next_version.description = 'Ein Beschreibung'
        next_version.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # The researcher searches for 'Brachial Plexus'
        self.search_for(next_version.description)

        # She want's to see only last experiments versions -
        # as tests helper creates version 2 of an experiment, only version 2
        # is supposed to appear in search results. Obs.: this test only
        # tests for duplicate result, not for the correct version.
        self.wait_for(lambda: self.browser.find_element_by_id('search_table'))
        table = self.browser.find_element_by_id('search_table')
        experiment_rows = \
            table.find_elements_by_class_name('experiment-matches')
        count = 0
        for experiment in experiment_rows:
            if next_version.description in experiment.text:
                count = count + 1
        self.assertEqual(1, count)

    def test_search_returns_only_approved_experiments(self):
        ##
        # Create objects to search below
        ##
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Brachial Plexus'
        e2.save()
        e3 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e3.description = 'Brachial Plexus'
        e3.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # The researcher searches for 'Brachial Plexus'
        self.search_for('Brachial Plexus')

        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            2, 'experiment-matches'
        ))

    def test_search_with_one_filter_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'Brachial Plexus'
        self.experiment.save()
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Brachial Plexus'
        e2.save()
        group = create_group(1, e2)
        group.title = 'Brachial Plexus'
        group.save()
        emg_setting = create_emg_setting(e2)
        create_emg_step(group, emg_setting)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina is happy. When she searched for Brachial Plexus, she found
        # the experiment she recently sent to portal through NES. She wants to
        # explore more in depth the portal search functionality.
        # In select box bellow search box she can choose filters like EEG,
        # TMS, EMS, among others. She types "brachial plexus" in search box,
        # and selects EMG in select box. Then she clicks in search button.
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        # IMPORTANT: need to remove bootstrap select javascript/css plugins
        # to select filter(s)
        self.browser.execute_script(
            'document.getElementById("id_bs_select_css").remove();'
            'document.getElementById("id_bs_select_js").remove();'
        )
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.wait_for(
            lambda: self.browser.find_element_by_id('submit_terms').click()
        )

        ##
        # As there are 2 experiments with 'Brachial Plexus' in title,
        # it's expected that Joselina sees only one Experiment search
        # result, given that she chosen to filter experiments that has EMG
        # Setting.
        # The page refreshes displaying the results.
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(1, 'group-matches')

    def test_search_with_two_filters_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'Brachial Plexus'
        self.experiment.save()
        group1 = create_group(1, self.experiment)
        group1.title = 'Brachial Plexus'
        group1.save()
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Brachial Plexus'
        e2.save()
        group2 = create_group(1, e2)
        group2.title = 'Brachial Plexus'
        group2.save()
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Ok, Joselina now wants to search experiments that has EEG and EMG
        # in groups data collection. In multiple choices box she clicks in
        # EEG and EMG
        search_box = self.browser.find_element_by_id('id_q')
        search_box.send_keys('Brachial Plexus')
        # IMPORTANT: need to remove bootstrap select javascript/css plugins
        # to select filter(s)
        self.browser.execute_script(
            'document.getElementById("id_bs_select_css").remove();'
            'document.getElementById("id_bs_select_js").remove();'
        )
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()

        ##
        # There's an experiment group that has one EEG step and one EMG
        # step, besides "Plexus Brachial" in group description.
        # On the other hand, there's a group that has "Brachial Plexus" in
        # despcription, an EEG step but not an EMG step. So she will see only
        # one of the two groups.
        ##
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(1, 'group-matches')

    def test_search_with_AND_modifier_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'Brachial Plexus'
        self.experiment.description = 'EEG'
        self.experiment.save()
        study = create_study(1, self.experiment)
        study.description = 'brachial something EEG'
        study.save()
        create_researcher(study)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Brachial Plexus'
        e2.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "brachial AND EEG" in that.
        self.search_for('brachial AND EEG')

        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'experiment-matches'
        ))
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
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'EMG Experiment'
        self.experiment.description = 'Ops, it\'s EEG in fact'
        self.experiment.save()
        study = create_study(1, self.experiment)
        study.description = 'brachial something EEG'
        study.save()
        create_researcher(study)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Goal Keeper Game experiment'
        e2.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "EMG OR EEG".
        ##
        # TODO: when change order - 'EEG OR EMG', test fails. Fix it?
        ##
        self.search_for('EMG OR EEG')

        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'experiment-matches'
        ))
        experiment = self.browser.find_element_by_class_name(
            'experiment-matches'
        ).text
        self.assertIn('EMG', experiment)
        self.assertIn('EEG', experiment)
        self.verify_n_objects_in_table_rows(1, 'study-matches')
        study = self.browser.find_element_by_class_name(
            'study-matches').text
        self.assertIn('EEG', study)

    def test_search_with_NOT_modifier_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'brachial'
        self.experiment.description = 'plexus'
        self.experiment.save()
        study = create_study(1, self.experiment)
        study.description = 'brachial plexus'
        study.save()
        create_researcher(study)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'brachial plexus'
        e2.save()
        group = create_group(1, e2)
        group.title = 'Brachial only'
        group.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # In a tooltip that pops up when hovering the mouse upon
        # search box input text, Joselina sees that she can apply modifiers
        # to do advanced search.
        # So, she types "brachial NOT plexus".
        self.search_for('brachial NOT plexus')

        ##
        # We've created a group with only 'Brachial only'
        # in title. As other objects that has 'brachial' as a substring in
        # some field, has 'plexus' as a substring in some another field,
        # we obtain just one row in Search results: that group with
        # 'Brachial only' in title.
        ##
        self.wait_for(
            lambda: self.verify_n_objects_in_table_rows(
                0, 'experiment-matches'
            )
        )
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        self.verify_n_objects_in_table_rows(1, 'group-matches')
        group_text = self.browser.find_element_by_class_name(
            'group-matches'
        ).text
        self.assertIn('Brachial', group_text)

    def test_search_with_quotes_returns_correct_objects(self):
        ##
        # Create objects to search below
        # TODO:
        # search for "Plexus brachial" returns an entry for
        # experiment with self.experiment.title = 'Plexus' and
        # self.experiment.description = 'brachial'. Fix it!
        ##
        self.experiment.title = 'Plexus'
        # self.experiment.description = 'brachial' (see TODO)
        self.experiment.save()
        study = create_study(1, self.experiment)
        study.description = 'Plexus'
        study.save()
        create_researcher(study)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'brachial Plexus'
        e2.save()
        group = create_group(1, e2)
        group.description = 'Plexus brachial'
        group.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

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
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            0, 'experiment-matches'
        ))
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
            'terms separated with one or more spaces will apply the OR '
            'modifier.'
            , tooltip_text
        )
        tooltip_data_toggle = search_box.get_attribute('data-toggle')
        self.assertEqual('tooltip', tooltip_data_toggle)

    def test_search_only_with_two_filters_returns_correct_results(self):
        ##
        # Create objects to search below
        ##
        group1 = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Experiment changed to test filter only'
        e2.save()
        group2 = create_group(1, e2)
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        ##
        # IMPORTANT: need to remove bootstrap select javascript/css plugins
        # to select filter(s)
        ##
        self.browser.execute_script(
            'document.getElementById("id_bs_select_css").remove();'
            'document.getElementById("id_bs_select_js").remove();'
        )
        # Joselina wishes to search only experiments that has EMG and EEG
        # steps, regardless of search terms
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()

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
        ##
        # Create objects to search below
        ##
        group1 = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Experiment changed to test filter only'
        e2.save()
        group2 = create_group(1, e2)
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        ##
        # IMPORTANT: need to remove bootstrap select javascript/css plugins
        # to select filter(s)
        ##
        self.browser.execute_script(
            'document.getElementById("id_bs_select_css").remove();'
            'document.getElementById("id_bs_select_js").remove();'
        )

        # Joselina wishes to search only experiments that has EEG
        # steps, regardless of search terms
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EEG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()

        # As we have only one experiment with EEG step, Joselina
        # gets only one row that corresponds to that the experiment
        self.verify_n_objects_in_table_rows(1, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        experiment_text = self.browser.find_element_by_class_name(
            'experiment-matches'
        ).text
        self.assertIn(
            'Experiment changed to test filter only', experiment_text
        )

    def test_search_only_with_one_filter_returns_correct_results_2(self):
        ##
        # Create objects to search below
        ##
        self.experiment.title = 'Brachial Plexus (with EMG Setting)'
        self.experiment.save()
        group1 = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Experiment changed to test filter only'
        e2.save()
        group2 = create_group(1, e2)
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)
        create_experiment(1, self.trustee1, Experiment.APPROVED)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        ##
        # IMPORTANT: need to remove bootstrap select javascript/css plugins
        # to select filter(s)
        ##
        self.browser.execute_script(
            'document.getElementById("id_bs_select_css").remove();'
            'document.getElementById("id_bs_select_js").remove();'
        )

        # Joselina wishes to search only experiments that has EMG
        # steps, regardless of search terms.
        self.browser.find_element_by_xpath(
            "//select/option[@value='" + Step.EMG + "']"
        ).click()
        self.browser.find_element_by_id('submit_terms').click()

        # As we have two experiments with EMG steps, Joselina
        # gets two rows that corresponds to that experiments
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
        self.wait_for(lambda: self.assertEqual(
            'Back Home', self.browser.find_element_by_id('link_home').text
        ))
        # She clicks in back home page button
        self.browser.find_element_by_id('link_home').click()

        # She's back homepage
        self.wait_for(
            lambda:
            self.assertEqual(self.browser.find_element_by_id(
                'id_table_title'
            ).find_element_by_tag_name('h2').text, 'List of Experiments')
        )

    def test_search_nothing_redirects_to_homepage(self):
        # Joselina is at Portal homepage and accidentally clicks on search
        # button without specify search terms or a filter.
        self.search_for('')

        # She's back homepage
        self.wait_for(
            lambda:
            self.assertEqual(self.browser.find_element_by_id(
                'id_table_title'
            ).find_element_by_tag_name('h2').text, 'List of Experiments')
        )

    def test_search_tmssetting_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        group1 = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Experiment changed to test filter only'
        e2.save()
        group2 = create_group(1, e2)
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)
        tms_setting = create_tms_setting(1, e2)
        tms_setting.name = 'tmssettingname'
        tms_setting.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina searches for a TMS Setting whose name is 'tmssettingname'
        self.search_for('tmssettingname')

        # As there is one TMSSetting object with that name, she sees just
        # one row in Search Results list
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'tmssetting-matches'
        ))
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmssetting_text = self.browser.find_element_by_class_name(
            'tmssetting-matches'
        ).text
        self.assertIn('tmssettingname', tmssetting_text)

    def test_search_tmsdevicesetting_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        group1 = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group1, emg_setting)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        e2.title = 'Experiment changed to test filter only'
        e2.save()
        group2 = create_group(1, e2)
        emg_setting = create_emg_setting(e2)
        create_emg_step(group2, emg_setting)
        eeg_setting = create_eeg_setting(1, e2)
        create_eeg_step(group2, eeg_setting)
        tms_setting = create_tms_setting(1, e2)
        tms_device = create_tms_device()
        coil_model = create_coil_model()
        tms_ds = create_tms_device_setting(tms_setting, tms_device, coil_model)
        ##
        # TODO:
        # change model to work with constant not literal. See Experiment
        # model.
        ##
        tms_ds.pulse_stimulus_type = 'single_pulse'
        tms_ds.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina searches for a TMS Device Setting whose name is
        # 'tmsdevicesettingname'
        # TODO: test for choice representation!
        self.search_for('single_pulse')

        # As there is one TMSDeviceSetting object with that name, she sees
        # just one row in Search Results list
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'tmsdevicesetting-matches'
        ))
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
        ##
        # Create objects to search below
        ##
        tms_setting1 = create_tms_setting(1, self.experiment)
        tms_device1 = create_tms_device()
        tms_device1.manufacturer_name = 'Magstim'
        tms_device1.save()
        coil_model = create_coil_model()
        create_tms_device_setting(tms_setting1, tms_device1, coil_model)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        tms_setting2 = create_tms_setting(1, e2)
        tms_device2 = create_tms_device()
        tms_device2.manufacturer_name = 'Siemens'
        tms_device2.save()
        coil_model = create_coil_model()
        create_tms_device_setting(tms_setting2, tms_device2, coil_model)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina searches for an experiment in which was used a TMS Device
        # whose manufacturer name is 'Siemens'
        self.search_for('Siemens')

        # As there is one TMSDevice object that has Magstim as manufacturer,
        # and one TMSDeviceSetting objects that has that TMSDevice object as
        # a Foreign Key, she sees 1 row in Search Results list
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'tmsdevice-matches'
        ))
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')
        tmsdevice_text = self.browser.find_element_by_class_name(
            'tmsdevice-matches'
        ).text
        self.assertIn('Siemens', tmsdevice_text)

    def test_search_coilmodel_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        tms_setting1 = create_tms_setting(1, self.experiment)
        tms_device1 = create_tms_device()
        coil_model1 = create_coil_model()
        coil_model1.name = 'Super Coil Model'
        coil_model1.save()
        create_tms_device_setting(tms_setting1, tms_device1, coil_model1)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        tms_setting2 = create_tms_setting(1, e2)
        tms_device2 = create_tms_device()
        coil_model2 = create_coil_model()
        coil_model2.name = 'Other name'
        coil_model2.save()
        create_tms_device_setting(tms_setting2, tms_device2, coil_model2)

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina searches for an experiment in which was used a Coil Model
        # whose name is 'Magstim'
        self.search_for('Super Coil Model')
        # As there is one CoilModel whose name is 'Super Coil Model',
        # and other whose name is 'Other name', she sees one row in Search
        # Results list
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'coilmodel-matches'
        ))
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
        self.assertIn('Super Coil Model', tmsdevicesetting_text)

    def test_search_tmsdata_returns_correct_objects(self):
        ##
        # Create objects to search below
        ##
        group1 = create_group(1, self.experiment)
        tms_setting1 = create_tms_setting(1, self.experiment)
        p2 = create_participant(1, group1, Gender.objects.first())
        create_tms_data(1, tms_setting1, p2)
        e2 = create_experiment(1, self.trustee1, Experiment.APPROVED)
        group2 = create_group(1, e2)
        tms_setting2 = create_tms_setting(1, e2)
        p2 = create_participant(1, group2, Gender.objects.first())
        tms_data = create_tms_data(1, tms_setting2, p2)
        tms_data.brain_area_name = 'cerebral cortex'
        tms_data.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina searches for an experiment whose TMSData of a participant
        # has collecting data from 'cerebral cortex'
        self.search_for('cerebral cortex')
        # As there is one TMSData object with 'cereberal cortex' as the
        # brain_area_name field, she sees one rows in Search Results list
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'tmsdata-matches'
        ))
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
        self.create_objects_to_test_search_eeg_setting()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments whose EEGSetting name is
        # 'eegsettingname'
        self.search_for('eegsettingname')

        # As there are three EEGSetting objects with that name,
        # one associated to an experiment, and the other two associated with
        # another experiment, she sees three rows in Search Results list
        self.check_matches(3, 'eegsetting-matches', 'eegsettingname')

    def test_search_eegelectrodenet_equipment_returns_correct_objects(self):
        haystack.connections.reload('default')
        self.create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_electrode_net = create_eeg_electrodenet(eeg_setting)
            eeg_electrode_net.manufacturer_name = 'Hersteller'
            eeg_electrode_net.save()

        self.haystack_index('rebuild_index')

        # Severino wants to search for experiments that has certain
        # equipment associated to an experiment setting
        self.search_for('Hersteller')

        # There are three maches craeted above
        self.check_matches(3, 'eeg_electrode_net-matches', 'Hersteller')

    def test_search_emgsetting_returns_correct_objects(self):
        self.create_objects_to_test_search_emgsetting()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments whose EMGSetting name is
        # 'emgsettingname'
        self.search_for('emgsettingname')

        # As there is three EMGSetting objects with that name,
        # one associated to an experiment, and the other two associated with
        # another experiment, she sees three rows in Search Results list
        self.check_matches(3, 'emgsetting-matches', 'emgsettingname')

    def test_search_eegsolution_returns_correct_objects(self):
        self.create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_solution = create_eeg_solution(eeg_setting)
            eeg_solution.manufacturer_name = 'Hersteller'
            eeg_solution.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Severino wants to search for experiments that has certain
        # equipment associated to an EEG solution
        self.search_for('Hersteller')

        # There are three maches craeted above
        self.check_matches(3, 'eeg_solution-matches', 'Hersteller')

    def test_search_eegfiltersetting_returns_correct_objects(self):
        self.create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_filter_setting = create_eeg_filter_setting(eeg_setting)
            eeg_filter_setting.eeg_filter_type_name = 'FilterTyp'
            eeg_filter_setting.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Severino wants to search for experiments that has certain
        # equipment associated to an EEG filter setting
        self.search_for('FilterTyp')

        # There are three maches craeted above
        self.check_matches(3, 'eeg_filter_setting-matches', 'FilterTyp')

    def test_search_emgdigitalfiltersetting_returns_correct_objects(self):
        self.create_objects_to_test_search_emgsetting()

        for emg_setting in EMGSetting.objects.all():
            emg_ditital_filter_setting = create_emg_digital_filter_setting(
                emg_setting
            )
            emg_ditital_filter_setting.filter_type_name = 'FilterTyp'
            emg_ditital_filter_setting.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Severino wants to search for experiments that has certain
        # equipment associated to an EMG digital filter setting
        self.search_for('FilterTyp')

        # There are three maches craeted above
        self.check_matches(3, 'emg_dgital_filter_setting-matches', 'FilterTyp')

    def test_search_eegelectrodelocalizationsystem_returns_correct_objects(
            self):
        self.create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_electrode_localization_system = \
                create_eeg_electrode_localization_system(eeg_setting)
            eeg_electrode_localization_system.name = 'Elektrodenlokalisierung'
            eeg_electrode_localization_system.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Severino wants to search for experiments that has certain
        # equipment associated to an EEG solution
        self.search_for('Elektrodenlokalisierung')

        # There are three maches craeted above
        self.check_matches(
            3, 'eeg_electrode_localiation_system-matches',
            'Elektrodenlokalisierung'
        )

    def test_search_questionnaire_data_returns_correct_objects_1(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments that contains some
        # questionnaire data
        self.search_for('\"Histoire de la fracture?\"')

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'questionnaire-matches'
        ))
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
        self.assertIn('Histoire de la fracture', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_2(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments that contains some
        # questionnaire data.
        self.search_for('\"História de fratura?\"')

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results.
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'questionnaire-matches'
        ))
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
        self.assertIn('História de fratura', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_3(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments that contains a phrase
        self.search_for('\"Welche Seite der Verletzung?\"')

        # As there are one questionnaire with terms searched by Joselina,
        # it is displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'questionnaire-matches'
        ))
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
        self.assertIn('Welche Seite der Verletzung', questionnaire_text)

    def test_search_questionnaire_data_returns_correct_objects_4(self):
        experiment = Experiment.objects.last()
        create_valid_questionnaires(experiment)
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments that contains some
        # questionnaire data
        self.search_for(
            '\"Qual região apresenta alteração do trofismo\" '
            '\"History of the current disease\"'
        )

        # As there are two questionnaires with terms searched by Joselina,
        # they are displayed in search results
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            2, 'questionnaire-matches'
        ))
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
        self.assertIn(
            'Qual região apresenta alteração do trofismo', questionnaire_rows
        )
        self.assertIn('History of the current disease', questionnaire_rows)

    def test_search_publications_returns_correct_objects(self):
        experiment = Experiment.objects.last()
        create_publication(experiment)
        ##
        # As publications created have fields filled with lorem ipsum stuff,
        # we change some of that fields to further search form them.
        ##
        publication = experiment.publications.first()
        publication.title = 'Vargas, Claudia Verletzung des Plexus Brachialis'
        publication.save()

        ##
        # Rebuid index to incorporate experiment publication change
        ##
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for experiments that are associated with
        # scientific publications
        self.search_for('\"Verletzung des Plexus Brachialis\"')

        # As there is one publication with that string in it's title,
        # Joselina sees one search result displaying the experiment that
        # publication belongs to, and any other search result of other
        # possible objects
        self.wait_for(lambda: self.verify_n_objects_in_table_rows(
            1, 'publication-matches'
        ))
        self.verify_n_objects_in_table_rows(0, 'questionnaire-matches')
        self.verify_n_objects_in_table_rows(0, 'eegsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'emgsetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdata-matches')
        self.verify_n_objects_in_table_rows(0, 'coilmodel-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevice-matches')
        self.verify_n_objects_in_table_rows(0, 'tmsdevicesetting-matches')
        self.verify_n_objects_in_table_rows(0, 'tmssetting-matches')
        self.verify_n_objects_in_table_rows(0, 'experiment-matches')
        self.verify_n_objects_in_table_rows(0, 'study-matches')
        self.verify_n_objects_in_table_rows(0, 'group-matches')
        self.verify_n_objects_in_table_rows(0, 'experimentalprotocol-matches')

        publication_text = self.browser.find_element_by_class_name(
            'publication-matches'
        ).text
        self.assertIn('Verletzung des Plexus Brachialis', publication_text)

    def test_search_step_returns_correct_objects(self):
        search_text = 'schritt'
        self.create_objects_to_test_search_step()
        for step in Step.objects.all():
            step.identification = search_text
            step.save()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # TODO: it was craeted a total of 8 steps in global_setup_ft(). So,
        # TODO: we add those to our checking. Eliminate global_setup_ft() and
        # TODO: make model instances created by demand in each test.
        self.check_matches(3, 'step-matches', search_text)

    def test_search_stimulus_step_returns_correct_objects(self):
        self.create_objects_to_test_search_stimulus_step()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for('stimulusschritt')

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(3, 'stimulus_step-matches', 'stimulusschritt')

    def test_search_instruction_step_returns_correct_objects(self):
        search_text = 'anweisungsschritt'
        self.create_objects_to_test_search_instruction_step()
        for instruction_step in Instruction.objects.all():
            instruction_step.text = search_text
            instruction_step.save()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # As there are three instruction steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(3, 'instruction_step-matches', search_text)

    def test_search_genericdatacollection_step_returns_correct_objects(self):
        self.create_objects_to_test_search_genericdatacollection_step()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for('generischedatensammlung')

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            3, 'generic_data_colletiong_step-matches',
            'generischedatensammlung'
        )

    def test_search_goalkeepergame_step_returns_correct_objects(self):
        self.create_objects_to_test_search_goalkeepergame_step()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given context tree of a Goal Keeper
        # Game Phase
        self.search_for('goalkeepergame')

        # As there are three context trees with that string, two from two
        # goalkeeper game phase steps bounded to two groups of one experiment,
        # and one from other goalkeeper step bounded to another group,
        # she sees three results
        self.check_matches(3, 'goalkeepergame-matches', 'goalkeepergame')

        # Now Joselina searchs for 'Ein Beschreibung' that is exactly what
        # is in software description field of GoalkeeperGame model
        self.search_for('Ein Beschreibung')

        # Again that is three matches
        self.check_matches(3, 'goalkeepergame-matches', 'Ein Beschreibung')

    def test_search_context_tree_returns_correct_objects(self):
        ##
        # Create objects needed
        ##
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        create_context_tree(experiment1)
        create_context_tree(experiment1)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        create_context_tree(experiment2)
        for context_tree in ContextTree.objects.all():
            context_tree.setting_text = 'wunderbarcontexttree'
            context_tree.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Edson searchs for a given context tree experiment setting
        self.search_for('wunderbarcontexttree')

        # there are three matches (as we created them above)
        self.check_matches(3, 'context_tree-matches', 'wunderbarcontexttree')

    def test_search_emgelectrodeplacementsetting_returns_correct_objects(
            self):
        self.create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_electrode_placement'
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for('quadrizeps')

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            1, 'emg_electrode_placement_setting-matches', 'quadrizeps'
        )

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_1(self):
        search_text = 'standardisierung'
        self.create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_electrode_placement(
            search_text
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            1, 'emg_electrode_placement_setting-matches', search_text
        )

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_2(self):
        search_text = 'starthaltung'
        self.create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_surface_placement(
            search_text
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            1, 'emg_electrode_placement_setting-matches', search_text
        )

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_3(self):
        search_text = 'einfügung'
        self.create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_intramuscular_placement(
            search_text
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            1, 'emg_electrode_placement_setting-matches', search_text
        )

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_4(self):
        search_text = 'nadelplatzierung'
        self.create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_needle_placement(
            search_text
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given stimulus step
        self.search_for(search_text)

        # As there are three stimulus steps with that string, two from
        # groups of one experiment, and one from other group of another
        # experiment, she sees three results
        self.check_matches(
            1, 'emg_electrode_placement_setting-matches', search_text
        )

    def test_search_eeg_electrode_position(self):
        search_text = 'elektrodenposition'
        self.create_objects_to_test_search_eegelectrodeposition()
        for eeg_electrode_position in EEGElectrodePosition.objects.all():
            eeg_electrode_position.name = search_text
            eeg_electrode_position.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a give electrode position name
        self.search_for(search_text)

        # As there are one electrode position name with that string she sees
        # one result
        self.check_matches(
            1, 'eeg_electrode_position-matches', search_text
        )

    def test_search_eeg_electrode_position_returns_correct_related_objects_1(
            self):
        search_text = 'elektrodenmodell'
        self.create_objects_to_test_search_eegelectrodeposition(
            'electrode_model'
        )
        # TODO: should test for all attributes
        for electrode_model in ElectrodeModel.objects.all():
            electrode_model.name = search_text
            electrode_model.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given electrode model
        self.search_for(search_text)

        # As there are one electrode model with that string, she sees one
        # result
        # TODO: the assertion inside this method is passing when it
        # TODO: wouldn't. Apparenttly the result come with empty string.
        # TODO: Verify!
        self.check_matches(1, 'eeg_electrode_position-matches', search_text)

    def test_search_eeg_electrode_position_returns_correct_related_objects_2(
            self):
        search_text = 'oberflächenelektrode'
        self.create_objects_to_test_search_eegelectrodeposition(
            'surface_electrode'
        )
        # TODO: should test for all attributes
        for surface_electrode in SurfaceElectrode.objects.all():
            surface_electrode.electrode_shape_name = search_text
            surface_electrode.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given surface electrode
        self.search_for(search_text)

        # As there are one surface electrode with that string, she sees one
        # result
        self.check_matches(1, 'eeg_electrode_position-matches', search_text)

    def test_search_eeg_electrode_position_returns_correct_related_objects_3(self):
        search_text = 'intramuskuläre'
        self.create_objects_to_test_search_eegelectrodeposition(
            'intramuscular_electrode'
        )
        # TODO: should test for all attributes
        for intramuscular_electrode in IntramuscularElectrode.objects.all():
            intramuscular_electrode.strand = search_text
            intramuscular_electrode.save()

        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for a given intramuscular electrode
        self.search_for(search_text)

        # As there is one intramuscular electrode with that string, she sees
        # one result
        self.check_matches(1, 'eeg_electrode_position-matches', search_text)

    def test_search_experiment_researcher(self):
        experiment = create_experiment(1, status=Experiment.APPROVED)
        create_experiment_researcher(
            experiment, first_name='Guilherme', last_name='Boulos'
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

        # Joselina wants to search for an experiment that has Boulos as one
        # of the researchers last name
        search_text = 'Boulos'
        self.search_for(search_text)

        # As there's one experiment with given researcher, she sees one result
        self.check_matches(1, 'experiment_researcher-matches', search_text)

        # Now she wants to search by first name, that is 'Guilherme'
        search_text = 'Guilherme'
        self.search_for(search_text)
        time.sleep(0.5)  # TODO: remove explicit delay

        # As there's one experiment with given researcher, she sees one result
        self.check_matches(1, 'experiment_researcher-matches', search_text)
