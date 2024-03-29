import io
import os
import random
import re
import sys
import tempfile
from unittest import skip

import haystack
import shutil
from django.contrib import auth
from django.contrib.auth.models import User, Permission
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse, resolve
from django.utils.text import slugify
from haystack.query import SearchQuerySet

from experiments import views
from experiments.forms import ChangeSlugForm
from experiments.models import Experiment, Step, \
    QuestionnaireDefaultLanguage, QuestionnaireLanguage, Group, ContextTree, \
    EEGSetting, EMGSetting, EEGElectrodePosition, ElectrodeModel, \
    SurfaceElectrode, IntramuscularElectrode, Instruction, Gender
from experiments.tests.tests_helper import create_experiment_related_objects, \
    create_download_dir_structure_and_files, \
    create_experiment, create_trustee_user, \
    create_next_version_experiment, random_utf8_string, create_context_tree, \
    create_eeg_electrodenet, create_eeg_solution, create_eeg_filter_setting, \
    create_eeg_electrode_localization_system, \
    create_emg_digital_filter_setting, create_group, create_questionnaire, \
    create_questionnaire_language, create_valid_questionnaires, \
    create_publication, create_experiment_researcher, create_study, \
    create_researcher, PASSWORD, create_genders, create_emg_setting, \
    create_emg_step
from experiments.views import change_slug
from functional_tests import test_search
from nep import settings


class HomePageTest(TestCase):

    def setUp(self):
        self.experiment = create_experiment(1)

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')

    def test_there_is_not_experiments_approved_display_nothing(self):
        create_experiment(1, self.experiment.owner, Experiment.UNDER_ANALYSIS)
        create_experiment(1, self.experiment.owner, Experiment.NOT_APPROVED)
        create_experiment(1, self.experiment.owner, Experiment.RECEIVING)

        response = self.client.get('/')

        self.assertFalse(response.context['experiments'].exists())

    def test_when_new_version_of_experiment_was_not_approved_display_last_approved_version(self):
        self.experiment.status = Experiment.APPROVED
        self.experiment.save()

        exp_new_version = create_experiment(1, self.experiment.owner)
        exp_new_version.nes_id = self.experiment.nes_id
        exp_new_version.version = self.experiment.version + 1
        exp_new_version.save()

        response = self.client.get('/')

        self.assertIn(self.experiment, response.context['experiments'])

    def test_trustee_can_change_experiment_status_with_a_POST_request(self):
        study = create_study(1, self.experiment)
        create_researcher(study)
        trustee_user = create_trustee_user()
        self.client.login(username=trustee_user.username, password=PASSWORD)
        response = self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.UNDER_ANALYSIS}
        )
        # Is it redirecting?
        self.assertEqual(response.status_code, 302)
        # TODO:
        # Is it using correct template after redirecting
        # experiment has changed status to UNDER_ANALYSIS?
        experiment = Experiment.objects.get(pk=self.experiment.id)
        self.assertEqual(experiment.status, Experiment.UNDER_ANALYSIS)

    def test_send_email_to_researcher_when_trustee_changes_status(self):
        """
        We test for changing status from UNDER_ANALYSIS to APPROVED.
        Other are similar.
        """
        # TODO: See if is valid to implement all of them.
        study = create_study(1, self.experiment)
        create_researcher(study)

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
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.APPROVED, 'warning_email_to':
                self.experiment.study.researcher.email},
            )

        self.assertTrue(self.send_mail_called)
        self.assertEqual(self.subject,
                         'Your experiment was approved')
        self.assertEqual(self.from_email, 'noreplay@nep.prp.usp.br')
        self.assertEqual(self.to, [self.experiment.study.researcher.email])

    def test_adds_success_message(self):
        # TODO: see if it is worth to test other messages
        self.experiment.status = Experiment.UNDER_ANALYSIS
        self.experiment.save()
        study = create_study(1, self.experiment)
        create_researcher(study)

        response = self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.APPROVED, 'warning_email_to':
                self.experiment.study.researcher.email},
            follow=True
        )

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'An email was sent to ' +
            self.experiment.study.researcher.first_name +
            ' ' + self.experiment.study.researcher.last_name +
            ' warning that the experiment changed status to Approved.'
        )
        self.assertEqual(message.tags, "success")

    def test_cant_change_status_to_not_approved_without_justification(self):
        self.experiment.status = Experiment.UNDER_ANALYSIS
        self.experiment.save()
        self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.NOT_APPROVED},
        )
        # experiment has mantained status UNDER_ANALYSIS?
        experiment = Experiment.objects.get(pk=self.experiment.id)
        self.assertEqual(experiment.status, Experiment.UNDER_ANALYSIS)

    # TODO!
    def test_doesnt_send_email_when_status_remains_the_same(self):
        pass

    def test_when_change_status_to_not_approved_save_justification_message(self):
        study = create_study(1, self.experiment)
        create_researcher(study)
        self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.NOT_APPROVED,
             'justification': '404 Bad experiment!'},
            )
        self.assertNotEqual('', self.experiment.justification)

    def test_change_status_to_under_analysis_associate_experiment_with_trustee(self):
        study = create_study(1, self.experiment)
        create_researcher(study)
        trustee_user = create_trustee_user()
        self.client.login(username=trustee_user.username, password=PASSWORD)
        self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.UNDER_ANALYSIS},
        )
        experiment = Experiment.objects.get(pk=self.experiment.id)
        self.assertEqual(trustee_user, experiment.trustee)

    def test_change_status_from_under_analysis_to_to_be_analysed_disassociate_trustee(self):
        trustee_user = create_trustee_user()
        self.client.login(username=trustee_user.username, password=PASSWORD)
        self.client.post(
            '/experiments/' + str(self.experiment.id) + '/change_status/',
            {'status': Experiment.TO_BE_ANALYSED},
            )
        experiment = Experiment.objects.get(pk=self.experiment.id)
        self.assertEqual(None, experiment.trustee)


# test haystack using a new index, instead of the settings.py index
TEST_HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE':
            'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': settings.HAYSTACK_TEST_URL,
        'INDEX_NAME': 'test_haystack',
        'TIMEOUT': 60 * 10,
    }
}


# TODO: complete with other tests: groups, studies, settings etc
class ExperimentDetailTest(TestCase):

    def setUp(self):
        # TODO: it's created in other tests suites, so was breaking here
        if not Gender.objects.all():
            create_genders()

        owner = User.objects.create_user(
            username='labor3', password='nep-labor3'
        )
        self.experiment = create_experiment(1, owner, Experiment.APPROVED)

    def _asserts_for_first_questionnaire(self, response):
        # assert for questions in right order for first group (groups can be
        # displayed in different orders)
        self.assertRegex(
            response.content.decode(),
            'Primeiro Grupo[\s\S]+'
            'História de fratura[\s\S]+'
            'Já fez alguma cirurgia ortopédica?[\s\S]+'
            'Fez alguma cirurgia de nervo?[\s\S]+'
            'História prévia de dor[\s\S]+'
            'Identifique o evento que levou ao trauma do seu plexo '
            'braquial[\s\S]+'
        )
        # assert for questions in right order for second group (groups can be
        # displayed in different orders)
        self.assertRegex(
            response.content.decode(),
            'Segundo Grupo[\s\S]+'
            'Teve alguma fratura associada à lesão?[\s\S]+'
            'Realiza Fisioterapia regularmente?[\s\S]+'
            'Faz uso de dispositivo auxiliar?[\s\S]+'
            'Qual(is)?[\s\S]+'
            'Texto mostrado ao participante'
        )

    def _asserts_for_second_questionnaire(self, response):
        ##
        # Make exaustive assertions for all question types
        self.assertIn('First Group', response.content.decode())
        self.assertIn('Third Group', response.content.decode())
        # Y - Yes/No
        self.assertIn('<em>Participant answers</em> yes <em>or</em> not',
                      response.content.decode())
        # D - Date
        self.assertIn('Participant enters a date in a date field',
                      response.content.decode())
        # X - Text display (Boiler plate question in old versions of
        # LimeSurvey)
        self.assertIn('A text is displayed to the participant (user does not '
                      'answer this question)',
                      response.content.decode())
        # 1 - Array Dual Scale
        self.assertIn('Questão Array dual scale', response.content.decode())
        self.assertIn(
            'Subquestion Array Dual Scale', response.content.decode()
        )
        self.assertIn('Answer Array dual scale', response.content.decode())
        # | - File Upload
        self.assertIn('Attach exams.', response.content.decode())
        self.assertIn(
            'Participant uploads file(s)', response.content.decode()
        )
        # M - Multiple choice
        self.assertIn('Institution of the Study', response.content.decode())
        self.assertIn('Injury type (s):', response.content.decode())
        self.assertIn('Thrombosis', response.content.decode())
        # L - List (Radio)
        self.assertIn('What side of the injury?', response.content.decode())
        # N - Numerical Input
        self.assertIn('Questão Numerical Input', response.content.decode())
        self.assertIn(
            'Participant answers with a numerical value',
            response.content.decode()
        )
        # H - Array (Flexible Labels) by Column
        self.assertIn('Questão Array by column', response.content.decode())
        self.assertIn(
            'Subquestion array by column 1', response.content.decode()
        )
        self.assertIn('Answer array by column 2', response.content.decode())

        # ; - Array (Flexible Labels) multiple texts
        # ; - Array (Flexible Labels) multiple texts
        self.assertIn('Questão Array (Texts)', response.content.decode())
        self.assertIn(
            '(This question is a matrix based on the following fields)',
            response.content.decode()
        )
        # 5 - 5 point choice
        self.assertIn('Five Point Choice', response.content.decode())
        self.assertIn(
            'Participant chooses a level from 1 to 5 or no level',
            response.content.decode()
        )
        # A - Array (5 Point Choice)
        self.assertIn(
            'Questão Array (5 point choice)', response.content.decode()
        )
        self.assertIn('subquestionSQ001', response.content.decode())
        self.assertIn(
            '(For each subquestion the participant chooses a level from 1 to '
            '5 or no level)',
            response.content.decode()
        )
        # C - Array (Yes/No/Uncertain)
        self.assertIn(
            'Participant chooses a level from 1 to 5 or no level',
            response.content.decode()
        )
        self.assertIn('subquestionSQ002', response.content.decode())
        self.assertIn(
            '<em>(For each subquestion the participant chooses between</em> '
            'Yes, No, Uncertain, No answer<em>)</em>',
            response.content.decode()
        )
        # E - Array (Increase/Same/Decrease)
        self.assertIn(
            'Questão Array (Increase/Same/Decrease)', response.content.decode()
        )
        self.assertIn('Subquestion (I/S/D)', response.content.decode())
        self.assertIn(
            '(For each subquestion the participant chooses between</em> '
            'Increase, Same, Decrease<em>)</em>',
            response.content.decode()
        )
        # G - Gender
        self.assertIn('Questão Gender', response.content.decode())
        self.assertIn(
            'Participant chooses between Female, Male, No answer',
            response.content.decode()
        )
        # I - Language Switch
        self.assertIn('Questão Language Switch', response.content.decode())
        self.assertIn(
            'Participant chooses between predefined languages',
            response.content.decode()
        )
        # K - Multiple Numerical Input
        self.assertIn(
            'Questão Multiple numerical input', response.content.decode()
        )
        self.assertIn(
            'Subquestion multiple numerical input', response.content.decode()
        )
        self.assertIn(
            '(For each subquestion the participant enters a numerical value)',
            response.content.decode()
        )
        # O - List With Comment
        self.assertIn('Questão List with comment', response.content.decode())
        self.assertIn('answer list with comments', response.content.decode())
        self.assertIn(
            '(Participant chooses one out of the options and can fill '
            'a text box with a comment)',
            response.content.decode()
        )
        # Q - Multiple Short Text
        self.assertIn('Questão Multiple short text', response.content.decode())
        self.assertIn(
            'Subquestion multiple short question', response.content.decode()
        )
        self.assertIn(
            '(For each subquestion the participant enters a free text)',
            response.content.decode()
        )
        # R - Ranking
        self.assertIn('Questão Ranking', response.content.decode())
        self.assertIn('Answer Ranking', response.content.decode())
        self.assertIn(
            '(Participant ranks the options)',
            response.content.decode()
        )
        # S - Short Free Text
        self.assertIn('Questão Short free text', response.content.decode())
        self.assertIn(
            'Participant enters a short free text',
            response.content.decode()
        )
        # U - Huge Free Text
        self.assertIn('Questão Huge Free Text', response.content.decode())
        # T - Long Free Text
        # U - Huge Free Text
        self.assertIn(
            'Participant enters a free text', response.content.decode()
        )
        # ! - List (Dropdown)
        self.assertIn('Questão List (dropdown)', response.content.decode())
        self.assertIn('código A3', response.content.decode())
        self.assertIn(
            '(Participant chooses one option out of a dropdown list)',
            response.content.decode()
        )
        # : - Array (Flexible Labels) multiple drop down
        self.assertIn(
            'Questão Array (Flexible Labels) multiple drop down',
            response.content.decode()
        )
        self.assertIn(
            '(This question is a matrix based on the following '
            'fields. For each matrix cell the participant chooses '
            'one option out of a dropdown list)',
            response.content.decode()
        )

    def _asserts_for_third_questionnaire(self, response):
        self.assertIn('Segundo Grupo', response.content.decode())
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

    @staticmethod
    def _get_q_default_language_or_first(questionnaire):
        # TODO: correct this to adapt to unique QuestionnaireDefaultLanguage
        #  model with OneToOne with Questionnaire
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

    def test_access_experiment_detail_with_wrong_url_returns_404_http_status_code(self):
        slug = str(Experiment.objects.first().slug)[:-3]
        response = self.client.get('/experiments/' + slug + '/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('404 - Not Found', response.content.decode())
        self.assertIn(
            'Ops... It seems you tried to access an inexistent page.',
            response.content.decode()
        )
        self.assertIn(
            'Neuroscience Experiments Database', response.content.decode(),
        )
        self.assertIn('Related Projects', response.content.decode())

    def test_uses_detail_template(self):
        slug = str(Experiment.objects.first().slug)
        response = self.client.get('/experiments/' + slug + '/')
        self.assertTemplateUsed(response, 'experiments/detail.html')

    def test_access_experiment_detail_returns_questionnaire_data_for_default_or_first_language(self):
        experiment = Experiment.objects.last()
        g1 = create_group(1, experiment)
        g2 = create_group(1, experiment)
        create_experiment_related_objects(experiment)
        create_valid_questionnaires([g1, g2])

        response = self.client.get('/experiments/' + experiment.slug + '/')

        for group in experiment.groups.all():
            self.assertContains(
                response,
                'Questionnaires for group ' + group.title
            )
            for questionnaire in group.steps.filter(type=Step.QUESTIONNAIRE):
                # The rule is display default questionnaire language data or
                # first questionnaire language data if not set default
                # questionnaire language. So we mimic the function
                # _get_q_default_language_or_first from views that do that.
                # TODO: In tests helper we always create default
                # TODO: questionnaire language as English. So we would test
                # TODO: only if we had first language.
                q_language = self._get_q_default_language_or_first(
                    questionnaire
                )
                self.assertContains(
                    response, 'Questionnaire ' + q_language.survey_name
                )

        # Sample asserts for first questionnaire
        # (in Portuguese, as first questionnaire, first language, created in
        # tests helper is in Portuguese).
        self._asserts_for_first_questionnaire(response)

        # sample asserts for second questionnaire
        self._asserts_for_second_questionnaire(response)

        # sample asserts for third questionnaire
        self._asserts_for_third_questionnaire(response)

    def test_access_experiment_detail_returns_questionnaire_data_for_other_language(self):
        # TODO!
        pass

    def test_access_experiment_without_questionnaires_returns_null_questionnaires(self):
        # First experiment has not questionnaires. See tests helper
        experiment = Experiment.objects.first()
        response = self.client.get('/experiments/' + experiment.slug + '/')

        self.assertFalse(response.context['questionnaires'])

    def test_access_experiment_with_invalid_questionnaire_returns_invalid_questionnaire(self):
        group = create_group(1, self.experiment)
        q = create_questionnaire(1, 'q4', group)
        create_questionnaire_language(
            q, settings.BASE_DIR + '/experiments/tests/questionnaire4.csv',
            'en'
        )

        response = self.client.get(
            '/experiments/' + self.experiment.slug + '/'
        )

        self.assertEqual(
            response.context['questionnaires'][group.title][q.id]['survey_metadata'],
            'invalid_questionnaire'
        )

    def test_access_experiment_with_one_valid_questionnaire_and_other_invalid(self):
        experiment = Experiment.objects.last()
        g1 = create_group(1, experiment)
        g2 = create_group(1, experiment)
        q1 = create_questionnaire(1, 'q1', g1)
        # invalid questionnaire
        create_questionnaire_language(
            q1,
            settings.BASE_DIR + '/experiments/tests/questionnaire4.csv',
            'pt-BR'
        )
        # valid questionnaire
        q2 = create_questionnaire(1, 'q2', g2)
        create_questionnaire_language(
            q2,
            settings.BASE_DIR + '/experiments/tests/questionnaire1_pt-br.csv',
            'en'
        )

        response = self.client.get('/experiments/' + experiment.slug + '/')

        self.assertEqual(
            response.context['questionnaires'][g1.title][q1.id][
                'survey_metadata'], 'invalid_questionnaire'
        )
        self.assertNotEqual(
            response.context['questionnaires'][g2.title][q2.id][
                'survey_metadata'], 'invalid_questionnaire'
        )

    def test_experiment_detail_page_has_change_slug_form(self):
        experiment = create_experiment(1)

        response = self.client.get('/experiments/' + experiment.slug + '/')
        self.assertIsInstance(response.context['form'], ChangeSlugForm)

    def test_access_experiment_wo_other_experiment_versions_returns_no_other(self):
        response = self.client.get('/experiments/' + self.experiment.slug + '/')

        # other_versions are the other experiments versions
        self.assertFalse(response.context['other_versions'])

    def test_access_experiment_with_other_experiment_versions_returns_other_versions(self):
        experiment_v2 = create_next_version_experiment(self.experiment)
        experiment_v3 = create_next_version_experiment(experiment_v2)

        response = self.client.get('/experiments/' + experiment_v3.slug + '/')

        # other_versions are the other experiments versions
        self.assertEqual(len(response.context['other_versions']), 2)


class ChangeExperimentSlugTest(TestCase):

    def setUp(self):
        trustee = create_trustee_user('claudia')
        group = auth.models.Group.objects.get(name='trustees')
        permission = Permission.objects.get(codename='change_slug')
        group.permissions.add(permission)

        trustee_user = User.objects.get(username=trustee.username)
        self.client.login(username=trustee_user.username, password=PASSWORD)

        create_experiment(1)

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

    def test_cannot_POST_slug_if_not_in_staff(self):
        # logout from the system, as we alread is logged in in setUp method
        self.client.logout()

        experiment_before = Experiment.objects.first()
        new_slug = 'a-brand_new-slug'
        response = self.client.post(
            '/experiments/' + str(experiment_before.id) + '/change_slug/',
            {'slug': new_slug}
        )
        self.assertEqual(response.status_code, 403)

        # get the experiment after posting new slug without permission
        experiment_after = Experiment.objects.first()

        self.assertNotEqual(experiment_after.slug, new_slug)

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
        experiment_v2 = create_next_version_experiment(experiment)
        experiment_v3 = create_next_version_experiment(experiment_v2)
        experiment_v4 = create_next_version_experiment(experiment_v3)

        self.client.post(
            '/experiments/' + str(experiment_v4.id) +
            '/change_slug/',
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
        # TODO: we want to display message as errors in form not as normal
        # TODO: messages
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

    def test_submit_non_unique_slug_displays_error_message(self):
        # TODO: we want to display message as errors in form not as normal
        # TODO: messages; make test in test_forms too
        experiment_before = Experiment.objects.first()
        other_experiment = create_experiment(1)
        response = self.client.post(
            '/experiments/' + str(experiment_before.id) + '/change_slug/',
            {'slug': other_experiment.slug}, follow=True
        )
        experiment_after = Experiment.objects.first()
        self.assertEqual(experiment_before.slug, experiment_after.slug)

        message = list(response.context['messages'])[0]
        self.assertEqual(
            message.message,
            'The slug entered is equal to other experiment slug. Please try '
            'again.'
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
            'Type only lowcase letters without accents, numbers, dash, '
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

    def test_POSTing_same_slug_returns_no_message(self):
        experiment = Experiment.objects.first()
        response = self.client.post(
            '/experiments/' + str(experiment.id) + '/change_slug/',
            {'slug': experiment.slug}, follow=True
        )
        self.assertFalse(response.context['messages'])


@override_settings(HAYSTACK_CONNECTIONS=TEST_HAYSTACK_CONNECTIONS)
class SearchTest(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='labor2', password='nep-labor2'
        )
        self.experiment = create_experiment(1, self.owner, Experiment.APPROVED)
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

    def tearDown(self):
        self.haystack_index('clear_index')

    @staticmethod
    def haystack_index(action):
        # Redirect sys.stderr to avoid display
        # "GET http://127.0.0.1:9200/haystack/_mapping" during tests
        # TODO: see:
        # TODO: https://github.com/django-haystack/django-haystack/issues/1142
        # TODO: path.join
        stderr_backup, sys.stderr = sys.stderr, open('/dev/null', 'w+')
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

    def test_search_nothing_redirects_to_homepage(self):
        response = self.client.get('/search/', {'q': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/')

    @skip
    def test_search_returns_only_approved_experiments(self):
        # response without filter
        response = self.client.get('/search/', {'q': 'Braquial+Plexus'})
        # TODO: complete this test!

    def test_change_status_from_UNDER_ANALYSIS_to_APPROVED_reindex_haystack(
            self):
        # TODO: testing calling celery task directly. Didn't work posting
        # TODO: approved experiment. Test with POST!
        experiment = create_experiment(
            1, self.owner, Experiment.UNDER_ANALYSIS
        )
        experiment.status = Experiment.APPROVED
        experiment.save()

        self.haystack_index('rebuild_index')

        results = SearchQuerySet().filter(content=experiment.title)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].model_name, 'experiment')
        self.assertEqual(results[0].object.title, experiment.title)

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

    def test_search_step_returns_correct_objects(self):
        search_text = 'schritt'
        test_search.SearchTest().create_objects_to_test_search_step()
        for step in Step.objects.all():
            step.identification = search_text
            step.save()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, search_text)

    def test_search_stimulus_step_returns_correct_objects(self):
        test_search.SearchTest().create_objects_to_test_search_stimulus_step()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'stimulusschritt')

    def test_search_instruction_step_returns_correct_objects(self):
        search_text = 'anweisungsschritt'
        test_search.SearchTest().\
            create_objects_to_test_search_instruction_step()
        for instruction_step in Instruction.objects.all():
            instruction_step.text = search_text
            instruction_step.save()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, search_text)

    def test_search_genericdatacollection_step_returns_correct_objects(self):
        test_search.SearchTest().\
            create_objects_to_test_search_genericdatacollection_step()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'generischedatensammlung')

    def test_search_emgelectrodeplacementsetting_returns_correct_objects(self):
        test_search.SearchTest(). \
            create_objects_to_test_search_emgelectrodeplacementsetting(
            'emg_electrode_placement')
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, 'quadrizeps')

    def test_search_eeg_electrode_position(self):
        search_text = 'elektrodenposition'
        test_search.SearchTest(). \
            create_objects_to_test_search_eegelectrodeposition()
        for eeg_electrode_position in EEGElectrodePosition.objects.all():
            eeg_electrode_position.name = search_text
            eeg_electrode_position.save()

        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    # TODO: This test pass when it wouldn't
    def test_search_eeg_electrode_position_returns_correct_related_objects_1(self):
        search_text = 'elektrodenmodell'
        test_search.SearchTest(
        ).create_objects_to_test_search_eegelectrodeposition()

        # TODO: should test for all attributes
        for electrode_model in ElectrodeModel.objects.all():
            electrode_model.name = search_text
            electrode_model.save()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_eeg_electrode_position_returns_correct_related_objects_2(self):
        search_text = 'oberflächenelektrode'
        test_search.SearchTest(
        ).create_objects_to_test_search_eegelectrodeposition(
            'surface_electrode'
        )

        # TODO: should test for all attributes
        for surface_electrode in SurfaceElectrode.objects.all():
            surface_electrode.name = search_text
            surface_electrode.save()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_eeg_electrode_position_returns_correct_related_objects_3(self):
        search_text = 'intramuskuläre'
        test_search.SearchTest(
        ).create_objects_to_test_search_eegelectrodeposition(
            'intramuscular_electrode'
        )

        # TODO: should test for all attributes
        for intramuscular_electrode in IntramuscularElectrode.objects.all():
            intramuscular_electrode.strand = search_text
            intramuscular_electrode.save()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_1(self):
        search_text = 'standardisierung'
        test_search.SearchTest(). \
            create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_electrode_placement(
            search_text
        )
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_2(self):
        search_text = 'starthaltung'
        test_search.SearchTest(). \
            create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_surface_placement(
            search_text
        )
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_3(self):
        search_text = 'einfügung'
        test_search.SearchTest(). \
            create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_intramuscular_placement(
            search_text
        )
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_emgelectrodeplacementsetting_returns_correct_related_objects_4(self):
        search_text = 'nadelplatzierung'
        test_search.SearchTest(). \
            create_objects_to_test_search_emgelectrodeplacementsetting_with_emg_needle_placement(
            search_text
        )
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(1, search_text)

    def test_search_goalkeepergame_step_returns_correct_objects(self):
        test_search.SearchTest()\
            .create_objects_to_test_search_goalkeepergame_step()
        self.haystack_index('rebuild_index')
        self.check_matches_on_response(3, 'goalkeepergame')

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

    def test_search_with_filter_returns_correct_objects(self):
        group = create_group(1, self.experiment)
        emg_setting = create_emg_setting(self.experiment)
        create_emg_step(group, emg_setting)
        create_experiment(1, self.owner, Experiment.APPROVED)

        self.haystack_index('rebuild_index')
        response = self.client.get('/search/', {'q': '', 'filter': 'emg'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<tr', 1)

    def test_search_with_term_and_filter_returns_correct_objects(self):
        search_text = 'plexus'
        self.experiment.description = 'plexus'
        self.experiment.save()
        group = create_group(1, self.experiment)
        group.title = search_text
        group.save()
        emg_setting = create_emg_setting(self.experiment)
        emg_step = create_emg_step(group, emg_setting)
        emg_step.identification = search_text
        emg_step.save()
        # create new experiment without steps (and groups)
        create_experiment(1, self.owner, Experiment.TO_BE_ANALYSED)

        self.haystack_index('rebuild_index')
        response = self.client.get(
            '/search/', {'q': search_text, 'filter': 'emg'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<tr', 1)  # 2: group and step

    def test_search_emgdigitalfiltersetting_returns_correct_objects(self):
        test_search.SearchTest().create_objects_to_test_search_emgsetting()

        for emg_setting in EMGSetting.objects.all():
            emg_ditital_filter_setting = create_emg_digital_filter_setting(
                emg_setting
            )
            emg_ditital_filter_setting.filter_type_name = 'FilterTyp'
            emg_ditital_filter_setting.save()

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
        experiment = Experiment.objects.last()
        group = create_group(1, experiment)
        q = create_questionnaire(1, 'q', group)
        # TODO: use path.join
        create_questionnaire_language(
            q,
            settings.BASE_DIR + '/experiments/tests/questionnaire1.csv',
            'en'
        )
        haystack.connections.reload('default')
        self.haystack_index('rebuild_index')

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

    def test_search_publications_returns_correct_number_of_objects(self):
        experiment = Experiment.objects.last()
        publication = create_publication(experiment)
        publication.title = 'Vargas, Claudia Verletzung des Plexus Brachialis'
        publication.save()

        # rebuid index to incorporate experiment publication change
        self.haystack_index('rebuild_index')

        response = self.client.get('/search/', {
            'q': '\"Verletzung des Plexus Brachialis\"'
        })
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 1)

    def test_search_experiment_research_returns_correct_number_of_objects(self):
        experiment = Experiment.objects.last()
        create_experiment_researcher(experiment, 'Boulos')

        # rebuid index to incorporate experiment publication change
        self.haystack_index('rebuild_index')

        response = self.client.get('/search/', {'q': 'Boulos'})
        self.assertEqual(response.status_code, 200)
        # because in search results templates it's '<tr class ...>'
        self.assertContains(response, '<tr', 1)


class DownloadExperimentTest(TestCase):

    TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp())

    def setUp(self):
        # TODO: it's created in other tests suites, so was breaking here
        if not Gender.objects.all():
            create_genders()
        owner = User.objects.create_user(
            username='labor1', password='nep-labor1'
        )
        experiment = create_experiment(1, owner, Experiment.APPROVED)
        g1 = create_group(1, experiment)
        g2 = create_group(1, experiment)
        create_experiment_related_objects(experiment)
        create_valid_questionnaires([g1, g2])
        create_download_dir_structure_and_files(
            experiment, self.TEMP_MEDIA_ROOT
        )

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    def asserts_experimental_protocol(self, ep_value, group1, group2,
                                      zipped_file):
        ep_group_str = re.search(
            "experimental_protocol_g([0-9]+)", ep_value
        )
        ep_group_id = int(ep_group_str.group(1))
        if group1.id == ep_group_id:
            group_title_slugifyed = slugify(group1.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed in element for element in
                    zipped_file.namelist())
            )
            # TODO: maybe it's necessary to construct the string representing
            # TODO: the path with file system specific separator ('/' or '\')
            self.assertTrue(
                any('Group_' + group_title_slugifyed + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                group_title_slugifyed = slugify(group2.title)
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            group_title_slugifyed = slugify(group2.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed in element for element in
                    zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                self.assertFalse(
                    any('Group_' + slugify(group1.title) +
                        '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )

    def asserts_questionnaires(self, q_value, group1, group2,
                               zipped_file):
        q_group_str = re.search("questionnaires_g([0-9]+)", q_value)
        q_group_id = int(q_group_str.group(1))
        if group1.id == q_group_id:
            group_title_slugifyed = slugify(group1.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                group_title_slugifyed = slugify(group2.title)
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group_title_slugifyed +
                            '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            group_title_slugifyed = slugify(group2.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                group_title_slugifyed = slugify(group1.title)
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group_title_slugifyed +
                            '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )

        # when user select "Per Questionnaire Data" option the file
        # Participants.csv has to be in compressed file
        questionnaire_group = Group.objects.get(pk=q_group_id)
        group_title_slugifyed = slugify(questionnaire_group.title)
        self.assertTrue(
            any('Group_' + group_title_slugifyed + '/Participants.csv'
                in element for element in zipped_file.namelist()
                ), 'Group_' + group_title_slugifyed +
                   '/Participants.csv not in ' + str(zipped_file.namelist())
        )

    def assert_participants(self, group1, group2, participant1, participant2,
                            zipped_file, both):
        group_title_slugifyed = slugify(group1.title)
        self.assertTrue(
            any('Group_' + group_title_slugifyed + '/Per_participant_data'
                in element for element in zipped_file.namelist())
        )
        self.assertTrue(
            any('Group_' + group_title_slugifyed +
                '/Per_participant_data/Participant_' +
                participant1.code
                in element for element in zipped_file.namelist())
        )
        if not both and (group1 != group2):
            group_title_slugifyed = slugify(group2.title)
            self.assertFalse(
                any('Group_' + group_title_slugifyed +
                    '/Per_participant_data/Participant_' + participant2.code
                    in element for element in zipped_file.namelist()),
                'Group_' + group_title_slugifyed +
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

        # Request the url to download compacted file again
        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        self.client.get(url)

        # Get the experiment again
        experiment = Experiment.objects.first()

        self.assertEqual(experiment.downloads, 2)

        # Remove fake download.zip file
        os.remove(settings.BASE_DIR + experiment.download_url.url)

    def test_POSTing_download_experiment_data_without_choices_redirects_to_experiment_detail_view(self):
        experiment = Experiment.objects.last()

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
        # TODO: possible implementation masking javascript
        pass

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_GETing_download_experiment_view_without_compressed_file_redirects_to_experiment_detail_view(self):
        experiment = Experiment.objects.last()

        os.remove(os.path.join(
            self.TEMP_MEDIA_ROOT, 'download', str(experiment.id),
            'download.zip'
        ))

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.get(url)

        # As we don't have in 'media/download/<experiment.id>/download.zip'
        # file the system should redirects to experiment detail page
        self.assertRedirects(
            response,
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )


class AuthenticationSystemTest(TestCase):

    def test_forget_password_uses_correct_template(self):
        response = self.client.get('/password_reset/')
        # TODO:
        # This assert is ok even if the template used is the original one in
        # django/contrib/admin/templates/registration/password_reset_form.html
        # The true test is below, where we test strings in the page.
        # Because we're remodeling the page.
        self.assertTemplateUsed(
            response, 'registration/password_reset_form.html'
        )

    # As we are reusing the Django authentication system (with same
    # templates names) we test for an element that is in original
    # template but not in ours.
    def test_forget_password_returns_correct_content(self):
        response = self.client.get('/password_reset/')
        self.assertNotContains(
            response,
            'Django administration'
        )

    def test_forget_password_sent_email_done_uses_correct_template(self):
        response = self.client.get('/password_reset/done/')
        # TODO:
        # This assert is ok even if the template used is the original one in
        # django/contrib/admin/templates/registration/password_reset_done.html
        # The true test is below, where we test strings in the page.
        # Because we're remodeling the page.
        self.assertTemplateUsed(
            response, 'registration/password_reset_done.html'
        )

    # As we are reusing the Django authentication system (with same
    # templates names) we test for an element that is in original
    # template but not in ours.
    def test_forget_password_sent_email_done_returns_correct_content(self):
        response = self.client.get('/password_reset/done/')
        self.assertNotContains(response, 'Django administration')

    @skip
    def test_POST_forget_password_send_email_to_request_user(self):
        # Do not test: it's Django feature; instead
        # testing mail.outbox in functional tests
        pass

    def test_reset_password_from_reset_password_email_sent_uses_correct_template(self):
        user = User.objects.create_user(
            username='elaine', email='elaine@example.com', password='elaine'
        )
        self.client.post('/password_reset/', data={'email': user.email})

        # get the email sent in post above
        email = mail.outbox[0]
        url_search = re.search(r'http://testserver/.+', email.body)
        if not url_search:
            self.fail('Could not find url in email body:\n' + email.body)
        url = url_search.group(0)

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # TODO:
        # This assert is ok even if the template used is the original one in
        # django/contrib/admin/templates/registration/password_reset_confirm
        # .html
        # The true test is below, where we test strings in the page.
        # Because we're remodeling the page.
        self.assertTemplateUsed(
            response, 'registration/password_reset_confirm.html'
        )
        self.assertContains(response, 'Type key terms/words to be searched')
        # As we are reusing the Django authentication system (with same
        # templates names) we test for an element that is in original
        # template but not in ours.
        self.assertNotContains(response, 'Django administration')
