import random
import re
import tempfile
import zipfile
from unittest import skip

import haystack
import sys
import io
import os

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse, resolve
from django.utils.encoding import smart_str
from haystack.query import SearchQuerySet

from experiments import views
from experiments.forms import ChangeSlugForm
from experiments.models import Experiment, Step, Questionnaire, \
    QuestionnaireDefaultLanguage, QuestionnaireLanguage, Group, ContextTree, \
    EEGSetting
from experiments.tests.tests_helper import apply_setup, global_setup_ut, \
    create_experiment_related_objects, \
    create_download_dir_structure_and_files, \
    remove_selected_subdir, create_experiment, create_trustee_users, \
    create_experiment_versions, random_utf8_string, create_context_tree, \
    create_eeg_electrodenet, create_eeg_solution, create_eeg_filter_setting, \
    create_eeg_electrode_localization_system
from experiments.views import change_slug
from functional_tests import test_search
from nep import settings


@apply_setup(global_setup_ut)
class HomePageTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')

    def test_trustee_can_change_experiment_status_with_a_POST_request(self):
        trustee_user = User.objects.get(username='claudia')
        # password='passwd' from test helper
        self.client.login(username=trustee_user.username, password='passwd')
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).first()
        response = self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.UNDER_ANALYSIS}
        )
        # Is it redirecting?
        self.assertEqual(response.status_code, 302)
        # TODO: is it using correct template after redirecting
        # TODO: experiment has changed status to UNDER_ANALYSIS?
        experiment = Experiment.objects.get(pk=experiment.id)
        self.assertEqual(experiment.status, Experiment.UNDER_ANALYSIS)

    def test_send_email_to_researcher_when_trustee_changes_status(self):
        """
        We test for changing status from UNDER_ANALYSIS to APPROVED.
        Other are similar.
        """
        # TODO: See if is valid to implement all of them.
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()

        self.send_mail_called = False

        # TODO: refactor using Python Mock Library
        def fake_send_mail(subject, body, from_email, to):
            self.send_mail_called = True
            self.subject = subject
            self.body = body
            self.from_email = from_email
            self.to = to

        views.send_mail = fake_send_mail

        self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.APPROVED, 'warning_email_to':
                experiment.study.researcher.email},
            )

        self.assertTrue(self.send_mail_called)
        self.assertEqual(self.subject,
                         'Your experiment was approved')
        self.assertEqual(self.from_email, 'noreplay@nep.prp.usp.br')
        self.assertEqual(self.to, [experiment.study.researcher.email])

    def test_adds_success_message(self):
        # TODO: see if it is worth to test other messages
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()

        response = self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.APPROVED, 'warning_email_to':
                experiment.study.researcher.email},
            follow=True
        )

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'An email was sent to ' + experiment.study.researcher.name +
            ' warning that the experiment changed status to Approved.'
        )
        self.assertEqual(message.tags, "success")

    def test_cant_change_status_to_not_approved_without_justification(self):
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()
        self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.NOT_APPROVED},
            )
        # experiment has mantained status UNDER_ANALYSIS?
        experiment = Experiment.objects.get(pk=experiment.id)
        self.assertEqual(experiment.status, Experiment.UNDER_ANALYSIS)

    # TODO!
    def test_doesnt_send_email_when_status_remains_the_same(self):
        pass

    def test_when_change_status_to_not_approved_save_justification_message(self):
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()
        self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.NOT_APPROVED,
             'justification': '404 Bad experiment!'},
            )
        experiment = Experiment.objects.get(pk=experiment.id)
        self.assertNotEqual('', experiment.justification)

    def test_change_status_to_under_analysis_associate_experiment_with_trustee(self):
        trustee_user = User.objects.get(username='claudia')
        # password='passwd' from test helper
        self.client.login(username=trustee_user.username, password='passwd')
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).first()
        self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.UNDER_ANALYSIS},
            )
        experiment = Experiment.objects.get(pk=experiment.id)
        self.assertEqual(trustee_user, experiment.trustee)

    def test_change_status_from_under_analysis_to_to_be_analysed_disassociate_trustee(self):
        trustee_user = User.objects.get(username='claudia')
        # password='passwd' from test helper
        self.client.login(username=trustee_user.username, password='passwd')
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()
        self.client.post(
            '/experiments/' + str(experiment.id) + '/change_status/',
            {'status': Experiment.TO_BE_ANALYSED},
            )
        experiment = Experiment.objects.get(pk=experiment.id)
        self.assertEqual(None, experiment.trustee)


# To test haystack using a new index, instead of the settings.py index
TEST_HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE':
            'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'test_haystack',
        'TIMEOUT': 60 * 10,
    }
}


# TODO: we are testing only questionnaire view part. Complete with other
# TODO: tests: groups, studies, settings etc
@apply_setup(global_setup_ut)
class ExperimentDetailTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def get_q_default_language_or_first(self, questionnaire):
        # TODO: correct this to adapt to unique QuestionnaireDefaultLanguage
        # TODO: model with OneToOne with Questionnaire
        qdl = QuestionnaireDefaultLanguage.objects.filter(
            questionnaire=questionnaire
        ).first()
        if qdl:
            return qdl.questionnaire_language
        else:
            return QuestionnaireLanguage.objects.filter(
                questionnaire=questionnaire
            ).first()

    def test_access_experiment_detail_after_GET_experiment(self):
        slug = str(Experiment.objects.first().slug)
        response = self.client.get('/experiments/' + slug + '/')
        self.assertEqual(response.status_code, 200)

    def test_uses_detail_template(self):
        slug = str(Experiment.objects.first().slug)
        response = self.client.get('/experiments/' + slug + '/')
        self.assertTemplateUsed(response, 'experiments/detail.html')

    def test_access_experiment_detail_returns_questionnaire_data_for_default_or_first_language(self):
        # Last experiment has questionnaires. See tests helper
        experiment = Experiment.objects.last()
        # we've made last experiment contain questionnaire data in tests helper
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = experiment.groups.filter(steps__in=q_steps)

        response = self.client.get('/experiments/' + experiment.slug + '/')
        if groups_with_qs.count() == 0:
            self.fail('There are no groups with questionnaires. Have you '
                      'been created the questionnaires in tests helper?')
        for group in groups_with_qs:
            self.assertContains(
                response,
                'Questionnaires for group ' + group.title
            )
            for step in group.steps.filter(type=Step.QUESTIONNAIRE):
                questionnaire = Questionnaire.objects.get(step_ptr=step)
                # The rule is display default questionnaire language data or
                # first questionnaire language data if not set default
                # questionnaire language. So we mimic the function
                # _get_q_default_language_or_first from views that do that.
                # TODO: In tests helper we always create default
                # TODO: questionnaire language as English. So we would to test
                # TODO: only if we had first language.
                q_language = self.get_q_default_language_or_first(
                    questionnaire
                )
                self.assertContains(
                    response, 'Questionnaire ' + q_language.survey_name
                )

        # Sample asserts for first questionnaire (in Portuguese, as first
        # questionnaire, first language, created in tests helper is in
        # Portuguese).
        self.assertIn('História de fratura', response.content.decode())
        self.assertIn('Já fez alguma cirurgia ortopédica?',
                      response.content.decode())
        self.assertIn('Fez alguma cirurgia de nervo?',
                      response.content.decode())
        self.assertIn('Identifique o evento que levou ao trauma do seu plexo '
                      'braquial. É possível marcar mais do que um evento.',
                      response.content.decode())
        self.assertIn('Teve alguma fratura associada à lesão?',
                      response.content.decode())
        self.assertIn('The user enters a date in a date field',
                      response.content.decode())

        # Sample asserts for second questionnaire
        self.assertIn('What side of the injury?', response.content.decode())
        self.assertIn('Institution of the Study', response.content.decode())
        self.assertIn('The user enters a free text',
                      response.content.decode())
        self.assertIn('Injury type (s):', response.content.decode())
        self.assertIn('Thrombosis', response.content.decode())
        self.assertIn('Attach exams.', response.content.decode())
        self.assertIn('The user uploads file(s)',
                      response.content.decode())
        self.assertIn('<em>The user answers</em> yes <em>or</em> not',
                      response.content.decode())

        # Sample asserts for third questionnaire
        self.assertIn('Refere dor após a lesão?', response.content.decode())
        self.assertIn('EVA da dor principal:', response.content.decode())
        self.assertIn('Qual região apresenta alteração do trofismo?',
                      response.content.decode())
        self.assertIn('Atrofia', response.content.decode())
        self.assertIn('Qual(is) artéria(s) e/ou vaso(s) foram acometidos?',
                      response.content.decode())
        self.assertIn('Artéria axilar', response.content.decode())
        self.assertIn('Quando foi submetido(a) à cirurgia(s) de plexo '
                      'braquial (mm/aaaa)?', response.content.decode())

    def test_access_experiment_detail_returns_questionnaire_data_for_other_language(self):
        # TODO!
        pass

    def test_access_experiment_without_questionnaires_returns_null_questionnaires(self):
        # First experiment has not questionnaires. See tests helper
        experiment = Experiment.objects.first()
        response = self.client.get('/experiments/' + experiment.slug + '/')

        self.assertFalse(response.context['questionnaires'])

    def test_access_experiment_with_invalid_questionnaire_returns_invalid_questionnaire(self):
        # First approved experiment has an invalid questionnaire in first
        # group. See tests helper
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED).first()
        group = experiment.groups.first()
        step = group.steps.get(type=Step.QUESTIONNAIRE)
        questionnaire = Questionnaire.objects.get(step_ptr=step)

        response = self.client.get('/experiments/' + experiment.slug + '/')

        self.assertEqual(
            response.context['questionnaires']
            [group.title][questionnaire.id]['survey_metadata'],
            'invalid_questionnaire'
        )

    def test_access_experiment_with_one_valid_questionnaire_and_other_invalid(self):
        # Last 'to be analysed' experiment has an invalid questionnaire in
        # first group and a valid questionnaire in last group. See tests
        # helper.
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED).last()
        group1 = experiment.groups.first()
        group2 = experiment.groups.last()
        step1 = group1.steps.get(type=Step.QUESTIONNAIRE)
        step2 = group2.steps.get(type=Step.QUESTIONNAIRE)
        q1 = Questionnaire.objects.get(step_ptr=step1)
        q2 = Questionnaire.objects.get(step_ptr=step2)

        response = self.client.get('/experiments/' + experiment.slug + '/')

        self.assertEqual(
            response.context['questionnaires'][group1.title][q1.id][
                'survey_metadata'], 'invalid_questionnaire'
        )
        self.assertNotEqual(
            response.context['questionnaires'][group2.title][q2.id][
                'survey_metadata'], 'invalid_questionnaire'
        )

    def test_experiment_detail_page_has_change_slug_form(self):
        experiment = create_experiment(1)

        response = self.client.get('/experiments/' + experiment.slug + '/')
        self.assertIsInstance(response.context['form'], ChangeSlugForm)


class ChangeExperimentSlugTest(TestCase):

    def setUp(self):
        create_experiment(1)
        trustee_users = create_trustee_users()
        trustee = trustee_users[0]
        self.client.login(username=trustee.username, password='passwd')

    def test_change_slug_url_resolves_to_change_slug_view(self):
        experiment = Experiment.objects.first()

        found = resolve(
            '/experiments/' + str(experiment.id) + '/change_slug/'
        )
        self.assertEqual(found.func, change_slug)

    def test_POSTing_new_slug_returns_redirect_to_experiment_detail_page(self):
        experiment = Experiment.objects.first()

        response = self.client.post(
            '/experiments/' + str(experiment.id) + '/change_slug/',
            {'slug': 'a-brand_new-slug'}
        )
        self.assertEqual(response.status_code, 302)

    def test_POSTing_a_valid_first_version_slug_saves_new_slug_correctly(self):
        experiment = Experiment.objects.first()

        response = self.client.post(
            '/experiments/' + str(experiment.id) + '/change_slug/',
            {'slug': 'a-brand_new-slug-for-version-1'},
            follow=True
        )

        experiment = Experiment.objects.first()
        self.assertEqual('a-brand_new-slug-for-version-1', experiment.slug)

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            "The experiment's slug was modified"
        )
        self.assertEqual(message.tags, "success")

    def test_POSTing_a_valid_n_experiment_version_changes_all_slugs_correctly(
            self):
        experiment = Experiment.objects.first()
        experiment_versions = create_experiment_versions(3, experiment)
        last_version = experiment_versions[len(experiment_versions) - 1]

        self.client.post(
            '/experiments/' + str(last_version.id) + '/change_slug/',
            {'slug': 'new-slug-for-version-4'}
        )

        for experiment in Experiment.objects.all():
            version = experiment.version
            version_suffix = '-v' + str(version) if version > 1 else ''
            self.assertEqual(
                'new-slug-for-version-4' + version_suffix,
                experiment.slug
            )

    def test_POSTing_empty_slug_returns_error_message(self):
        experiment_before = Experiment.objects.first()

        response = self.client.post(
            '/experiments/' + str(experiment_before.id) + '/change_slug/',
            {'slug': ''}, follow=True
        )

        experiment_after = Experiment.objects.first()
        self.assertEqual(experiment_before.slug, experiment_after.slug)

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'Empty slugs is not allowed. Please enter a valid slug'
        )
        self.assertEqual(message.tags, "error")

    def test_POSTing_invalid_slug_returns_error_message(self):
        # generates random string to post random utf-8 slug
        # TODO: verify if function is returning correct string
        slug = random_utf8_string(random.randint(1, 50))

        experiment_before = Experiment.objects.first()
        response = self.client.post(
            '/experiments/' + str(experiment_before.id) + '/change_slug/',
            {'slug': slug}, follow=True
        )
        experiment_after = Experiment.objects.first()
        self.assertEqual(experiment_before.slug, experiment_after.slug)

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'The slug entered is not allowed. Please enter a valid slug. '
            'Type only letters without accents, numbers, dash, '
            'and underscore signs'
        )
        self.assertEqual(message.tags, "error")
    
    def test_POSTing_slug_with_less_than_three_characters_returns_error_message(self):
        experiment_before = Experiment.objects.first()
        response = self.client.post(
            '/experiments/' + str(experiment_before.id) + '/change_slug/',
            {'slug': 'ab'}, follow=True
        )
        experiment_after = Experiment.objects.first()
        self.assertEqual(experiment_before.slug, experiment_after.slug)

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'The slug entered is two small. Please enter at least 3 '
            'characters'
        )
        self.assertEqual(message.tags, "error")


@override_settings(HAYSTACK_CONNECTIONS=TEST_HAYSTACK_CONNECTIONS)
@apply_setup(global_setup_ut)
class SearchTest(TestCase):

    def setUp(self):
        global_setup_ut()
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

    def tearDown(self):
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

    def check_matches_on_response(self, matches, text):
        response = self.client.get('/search/', {'q': text})
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', matches)

    def test_search_redirects_to_homepage_with_search_results(self):
        response = self.client.get('/search/', {'q': 'plexus'})
        self.assertEqual(response.status_code, 200)
        # TODO: is it needed to test for redirected page?

    def test_search_returns_only_approved_experiments(self):
        # response without filter
        response = self.client.get('/search/', {'q': 'Braquial+Plexus'})
        # TODO: complete this test!

    def test_change_status_from_UNDER_ANALYSIS_to_APPROVED_reindex_haystack(
            self):
        # TODO: testing calling celery task directly. Didn't work posting
        # TODO: approved experiment. Test with POST!
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS
        ).first()
        experiment.status = Experiment.APPROVED
        experiment.save()

        # We are calling method directly without delay method. Test is not
        # recognizing the result, although celery log reports success.
        # rebuild_haystack_index()
        # When calling 'rebuild_haystack_index()' in tests that boring
        # warning message from haystack pop in tests results, so we redirect
        # sys.stderr to a temp file and call_command manually, like we did in
        # functional tests
        self.haystack_index('rebuild_index')

        # Tests helper creates an experiment UNDER_ANALYSIS with 'Experiment
        # 2' as experiment title
        results = SearchQuerySet().filter(content='Experiment 2')
        # TODO: by now we have 4 models being indexed
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].model_name, 'experiment')
        self.assertEqual(results[0].object.title, 'Experiment 2')

    # TODO: test other searched objects
    def test_search_eegsetting_returns_correct_number_of_objects(self):
        test_search.SearchTest().create_objects_to_test_search_eeg_setting()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'eegsettingname')

    def test_search_eegsetting_returns_matchings_containing_search_strings(self):
        pass
        # TODO!

    def test_search_emgsetting_returns_correct_number_of_objects(self):
        test_search.SearchTest().create_objects_to_test_search_emgsetting()

        self.haystack_index('rebuild_index')

        response = self.client.get('/search/', {'q': 'emgsettingname'})
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 3)

    def test_search_goalkeepergame_step_returns_correct_objects(self):
        test_search.SearchTest()\
            .create_objects_to_test_search_goalkeepergame_step()

        self.haystack_index('rebuild_index')

        response = self.client.get('/search/', {'q': 'goalkeepergame'})
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 3)

    def test_search_context_tree_returns_correct_objects(self):
        # create objects needed
        experiment1 = create_experiment(1, status=Experiment.APPROVED)
        create_context_tree(experiment1)
        create_context_tree(experiment1)
        experiment2 = create_experiment(1, status=Experiment.APPROVED)
        create_context_tree(experiment2)
        for context_tree in ContextTree.objects.all():
            context_tree.setting_text = 'wunderbarcontexttree'
            context_tree.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'wunderbarcontexttree')

    def test_search_eegelectrodenet_equipment_returns_correct_objects(self):
        test_search.SearchTest().create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_electrode_net = create_eeg_electrodenet(eeg_setting)
            eeg_electrode_net.manufacturer_name = 'Hersteller'
            eeg_electrode_net.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'Hersteller')

    def test_search_eegsolution_returns_correct_objects(self):
        test_search.SearchTest().create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_solution = create_eeg_solution(eeg_setting)
            eeg_solution.manufacturer_name = 'Hersteller'
            eeg_solution.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'Hersteller')

    def test_search_eegfiltersetting_returns_correct_objects(self):
        test_search.SearchTest().create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_filter_setting = create_eeg_filter_setting(eeg_setting)
            eeg_filter_setting.eeg_filter_type_name = 'FilterTyp'
            eeg_filter_setting.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'FilterTyp')

    def test_search_eegelectrodelocalizationsystem_returns_correct_objects(
            self):
        test_search.SearchTest().create_objects_to_test_search_eeg_setting()

        for eeg_setting in EEGSetting.objects.all():
            eeg_electrode_localization_system = \
                create_eeg_electrode_localization_system(eeg_setting)
            eeg_electrode_localization_system.name = 'Elektrodenlokalisierung'
            eeg_electrode_localization_system.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'Elektrodenlokalisierung')

    def test_search_questionnaire_returns_correct_number_of_objects(self):
        response = self.client.get('/search/', {
            'q': '\"History of fracture\" \"trauma of your '
                 'brachial plexus\" \"Injury by firearm\" \"What side of the '
                 'injury\" \"Elbow Extension\"'
        })
        self.assertEqual(response.status_code, 200)
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 1)
        # TODO: needs to know if it was brought correct results

    def test_search_questionnaire_returns_matchings_containing_search_strings(self):
        response = self.client.get('/search/', {
            'q': '\"History of fracture?\" \"trauma of your '
                 'brachial plexus\" \"Injury by firearm\" \"What side of the '
                 'injury\" \"Elbow Extension\"'
        })
        self.assertContains(response, 'History of fracture')
        self.assertContains(response, 'trauma of your brachial plexus')
        self.assertContains(response, 'Injury by firearm')
        self.assertContains(response, 'What side of the injury')
        self.assertContains(response, 'Elbow Extension')

    def test_search_publications_resturns_correct_number_of_objects(self):
        ##
        # It was created two publications for last experiment created in
        # tests helper
        ##
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()
        ##
        # As publications created have fields filled with lorem ipsum stuff,
        # we change some of that fields to further search form them
        ##
        publication = experiment.publications.first()
        publication.title = 'Vargas, Claudia Verletzung des Plexus Brachialis'
        publication.save()

        ##
        # Rebuid index to incorporate experiment publication change
        ##
        self.haystack_index('rebuild_index')

        response = self.client.get('/search/', {
            'q': '\"Verletzung des Plexus Brachialis\"'
        })
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 1)


@apply_setup(global_setup_ut)
class DownloadExperimentTest(TestCase):

    TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp(), 'media')

    def setUp(self):
        global_setup_ut()

    def asserts_experimental_protocol(self, ep_value, group1, group2,
                                      zipped_file):
        ep_group_str = re.search(
            "experimental_protocol_g([0-9]+)", ep_value
        )
        ep_group_id = int(ep_group_str.group(1))
        if group1.id == ep_group_id:
            self.assertTrue(
                any('Group_' + group1.title in element for element in
                    zipped_file.namelist())
            )
            # TODO: maybe it's necessary to construct the string representing
            # TODO: the path with file system specific separator ('/' or '\')
            self.assertTrue(
                any('Group_' + group1.title + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                self.assertFalse(
                    any('Group_' + group2.title + '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            self.assertTrue(
                any('Group_' + group2.title in element for element in
                    zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group2.title + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                self.assertFalse(
                    any('Group_' + group1.title + '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )

    def asserts_questionnaires(self, q_value, group1, group2,
                               zipped_file):
        q_group_str = re.search("questionnaires_g([0-9]+)", q_value)
        q_group_id = int(q_group_str.group(1))
        if group1.id == q_group_id:
            self.assertTrue(
                any('Group_' + group1.title + '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group1.title + '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group2.title + '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group2.title + '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            self.assertTrue(
                any('Group_' + group2.title + '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group2.title + '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group1.title + '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group1.title + '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )

        # when user select "Per Questionnaire Data" option the file
        # Participants.csv has to be in compressed file
        questionnaire_group = Group.objects.get(pk=q_group_id)
        self.assertTrue(
            any('Group_' + questionnaire_group.title + '/Participants.csv'
                in element for element in zipped_file.namelist()
                ), 'Group_' + questionnaire_group.title + '/Participants.csv '
                                                          'not in ' +
                   str(zipped_file.namelist())
        )

    def assert_participants(self, group1, group2, participant1, participant2,
                            zipped_file, both):
        self.assertTrue(
            any('Group_' + group1.title + '/Per_participant_data'
                in element for element in zipped_file.namelist())
        )
        self.assertTrue(
            any('Group_' + group1.title + '/Per_participant_data/Participant_' +
                participant1.code
                in element for element in zipped_file.namelist())
        )
        if not both and (group1 != group2):
            self.assertFalse(
                any('Group_' + group2.title +
                    '/Per_participant_data/Participant_' + participant2.code
                    in element for element in zipped_file.namelist()),
                'Group_' + group2.title +
                '/Per_participant_data/Participant_' +
                participant2.code + ' is in ' + str(zipped_file.namelist())
            )

    def user_choices_based_asserts(self, selected_items, group1, group2,
                                   participant1, participant2, zipped_file):
        """
        There are a combination without repetition of three in four selection
        possibilities that are:
            - experimental protocol, questionnaires, participant of group1,
            participant of group2
        This results in four possibilites: C(4, 3) = 4.
        But for questionnaires and experimental protocol we can have two
        other possibilities, and it's precisely the case when group1 !=
        group2. So at the end, we are left with a combination of 3 elements
        in 6 possibilites: C(6, 3) = 20
        :param selected_items: dictionnary
        :param group1: Group model instance
        :param group2: Group model instance
        :param participant1: Participant model instance (always perteining
        to a different group of participant2. Obs.: it could be equal to
        participant2 because group is a foreign key for participant, but in
        the function calling the participant1 != participant2)
        :param participant2: participant model instance
        :param zipped_file:
        """
        if {'ep', 'q', 'p_g1'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, False)

        if {'ep', 'q', 'p_g2'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group2, group1, participant2,
                                     participant1,
                                     zipped_file, False)

        if {'ep', 'p_g1', 'p_g2'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, True)

        if {'q', 'p_g1', 'p_g2'}.issubset(selected_items.keys()):
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, True)

    def test_downloading_experiment_data_increases_download_counter(self):
        # Create fake download.zip file
        file = io.BytesIO()
        file.write(b'fake_experiment_data')
        file.name = 'download.zip'

        experiment = Experiment.objects.first()
        experiment.download_url.save(file.name, file)
        experiment.save()

        # Request the url to download compacted file
        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # As the experiment Experiment instance was updated we've got it again
        experiment = Experiment.objects.first()

        self.assertEqual(experiment.downloads, 1)

        # Request the url do download compacted file again
        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        self.client.get(url)

        # Get the experiment again
        experiment = Experiment.objects.first()

        self.assertEqual(experiment.downloads, 2)

        # Remove fake download.zip file
        os.remove(settings.BASE_DIR + experiment.download_url.url)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_POSTing_download_experiment_data_returns_correct_content(self):
        # Last approved experiment has 2 groups and questionnaire steps (with
        # questionnaires data) created in tests helper
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()
        # Create study and participants and experimental protocol for
        # this experiment. That's what it's missing.
        create_experiment_related_objects(experiment)

        # Create a complete directory tree with possible experiment data
        # directories/files that reproduces the directory/file structure
        # created when Portal receives the experiment data through Rest API.
        create_download_dir_structure_and_files(
            experiment, self.TEMP_MEDIA_ROOT
        )

        # get groups and participants for tests below
        g1 = experiment.groups.order_by('?').first()
        g2 = experiment.groups.order_by('?').first()  # can be equal to g1
        if g1 == g2:
            participants = list(g1.participants.order_by('?'))
            p1 = participants[0]
            p2 = participants[len(participants) - 1]
        else:
            p1 = g1.participants.order_by('?').first()
            p2 = g2.participants.order_by('?').first()

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})

        # random select items, simulating user posting items to download
        all_items = {
            'ep': 'experimental_protocol_g' + str(g1.id),
            'q': 'questionnaires_g' + str(g2.id),
            'p_g1': 'participant_p' + str(p1.id) + '_g' + str(g1.id),
            'p_g2': 'participant_p' + str(p2.id) + '_g' + str(g2.id)
        }
        selected_items = {}
        for i in range(3):
            random_choice = random.choice(list(all_items.keys()))
            selected_items[random_choice] = all_items[random_choice]
            all_items.pop(random_choice, 0)
        response = self.client.post(
            url, {
                'download_selected': selected_items.values()
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename=%s' % smart_str('download.zip')
        )

        # get the zipped file to test against its content
        file = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(file, 'r')
        self.assertIsNone(zipped_file.testzip())

        # compressed file must always contain Experiments.csv
        self.assertTrue(
            any('Experiment.csv'
                in element for element in zipped_file.namelist()),
            'Experiment.csv not in ' + str(zipped_file.namelist())
        )

        # test for compressed folders based on items selected by user
        self.user_choices_based_asserts(
            selected_items, g1, g2, p1, p2, zipped_file
        )

        # For each group, if it has questionnaire(s) in its experimental
        # protocol, it must contain questionnaire(s) metadata in group
        # subdir of the compressed file.
        for group in [g1, g2]:
            if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
                self.assertTrue(
                    any('Group_' + group.title + '/Questionnaire_metadata'
                        in element for element in zipped_file.namelist()),
                    '"Group_' + group.title +
                    '/Questionnaire_metadata" subdir not in: ' +
                    str(zipped_file.namelist())
                )

    def test_POSTing_download_experiment_data_without_choices_redirects_to_experiment_detail_view(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        # POST without data, as when nothing is selected, the request do not
        # even send the variable in "name" attribute of the select tag
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )

    @skip
    def test_POSTing_all_options_redirects_to_view_with_GET_request(self):
        # we are prevent submit data in detail.html with JQuery by now
        # TODO: possible implementation without javascript
        pass

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_POSTing_option_data_has_not_correspondent_subdir_redirects_to_experiment_detail_view(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # Create other objects required for this experiment to test POSTing
        # data and download dir structure
        create_experiment_related_objects(experiment)
        create_download_dir_structure_and_files(
            experiment, self.TEMP_MEDIA_ROOT
        )

        group = experiment.groups.order_by('?').first()
        participant = group.participants.order_by('?').first()

        options = [
            'experimental_protocol_g' + str(group.id),
            'questionnaires_g' + str(group.id),
            'participant_p' + str(participant.id) + '_g' + str(group.id)
        ]

        selected = random.choice(options)
        # Remove the selected option corresponded subdir simulated that the
        # subdir does not exist.
        remove_selected_subdir(
            selected, experiment, participant, group, self.TEMP_MEDIA_ROOT
        )

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.post(
            url, {
                'download_selected': selected
            }
        )

        self.assertRedirects(
            response,
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_GETing_download_experiment_view_without_compressed_file_redirects_to_experiment_detail_view(self):
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        # create temp 'media/download/<experiment.id>' subdir
        os.makedirs(
            os.path.join(self.TEMP_MEDIA_ROOT, 'download', str(experiment.id))
        )

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.get(url)

        # As we have nothing in 'media/download/<experiment.id>' the system
        # should redirects to experiment detail page
        self.assertRedirects(
            response,
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )
