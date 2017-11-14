import zipfile
import haystack
import sys
import io
import os
import shutil

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from haystack.query import SearchQuerySet

from experiments import views
from experiments.models import Experiment, Step, Questionnaire, \
    QuestionnaireDefaultLanguage, QuestionnaireLanguage
from experiments.tests.tests_helper import apply_setup, global_setup_ut, \
    create_experiment_related_objects
from experiments.views import _get_q_default_language_or_first
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
            {'status': Experiment.UNDER_ANALYSIS},
            )
        # Is it redirecting?
        self.assertEqual(response.status_code, 302)
        # TODO: is it using correct template after redirecting
        # experiment has changed status to UNDER_ANALYSIS?
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
        # TODO: see if is worth to test other messages
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
        # results = SearchQuerySet().all()  # DEBUG
        # TODO: by now we have 4 models been indexed
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].model_name, 'experiment')
        self.assertEqual(results[0].object.title, 'Experiment 2')

    # TODO: test other searched objects
    def test_search_eegsetting_returns_correct_number_of_objects(self):
        response = self.client.get('/search/', {'q': 'eegsettingname'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<tr', 3)  # because in search results
        # templates it's '<tr class ...>'

    def test_search_eegsetting_returns_matchings_containing_search_strings(self):
        pass
        # TODO!

    def test_search_questionnaire_returns_correct_number_of_objects(self):
        response = self.client.get('/search/', {
            'q': '\"History of fracture\" \"trauma of your '
                 'brachial plexus\" \"Injury by firearm\" \"What side of the '
                 'injury\" \"Elbow Extension\"'
        })
        self.assertEqual(response.status_code, 200)
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.assertContains(response, '<tr', 1)  # because in search results
        # templates it's '<tr class ...>'
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


@apply_setup(global_setup_ut)
class DownloadExperimentTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def create_q_language_dir(self, q, questionnaire_metadata_dir):
        q_default = _get_q_default_language_or_first(q)
        q_language_dir = os.path.join(
            questionnaire_metadata_dir,
            q.code + '_' + q_default.survey_name
        )
        return q_language_dir

    def create_q_language_responses_dir_and_file(
            self, q, per_questionnaire_data_dir
    ):
        q_language_dir = self.create_q_language_dir(
            q, per_questionnaire_data_dir
        )
        os.mkdir(q_language_dir)
        file_path = os.path.join(
            q_language_dir, 'Responses_' + q.code + '.csv'
        )
        self.create_text_file(file_path, 'a, b, c\nd, e, f')

    def create_q_language_metadata_dir_and_files(
            self, q, questionnaire_metadata_dir
    ):
        q_language_dir = self.create_q_language_dir(
            q, questionnaire_metadata_dir
        )
        os.mkdir(q_language_dir)
        for q_language in q.q_languages.all():
            file_path = os.path.join(
                q_language_dir,
                'Fields_' + q.code + '_' +
                q_language.language_code + '.csv'
            )
            self.create_text_file(file_path, 'a, b, c\nd, e, f')

    def create_group_subdir(self, group_dir, name):
        subdir = os.path.join(
            group_dir, name
        )
        os.makedirs(subdir)
        return subdir

    def create_text_file(self, file_path, text):
        file = open(file_path, 'w')
        file.write(text)
        file.close()

    def create_download_dir_structure_and_files(self, experiment):
        # create download experiment data root
        experiment_download_dir = os.path.join(
            settings.MEDIA_ROOT, 'download', str(experiment.pk)
        )

        # remove subdir if exists before creating that
        shutil.rmtree(experiment_download_dir)
        os.mkdir(experiment_download_dir)

        # create Experiment.csv file
        self.create_text_file(
            os.path.join(experiment_download_dir, 'Experiment.csv'),
            'a, b, c\nd, e, f'
        )

        for group in experiment.groups.all():
            group_dir = os.path.join(
                experiment_download_dir, 'Group_' + group.title
            )
            questionnaire_metadata_dir = self.create_group_subdir(
                group_dir, 'Questionnaire_metadata'
            )
            per_questionnaire_data_dir = self.create_group_subdir(
                group_dir, 'Per_questionnaire_data'
            )
            per_participant_data_dir = self.create_group_subdir(
                group_dir, 'Per_participant_data'
            )
            experimental_protocol_dir = self.create_group_subdir(
                group_dir, 'Experimental_protocol'
            )

            # create questionnaire stuff
            for questionnaire_step in group.steps.filter(
                    type=Step.QUESTIONNAIRE
            ):
                # TODO: see if using step_ptr is ok
                q = Questionnaire.objects.get(step_ptr=questionnaire_step)

                # create Questionnaire_metadata dir and files
                self.create_q_language_metadata_dir_and_files(
                    q, questionnaire_metadata_dir
                )
                # create Per_questionnaire_data dir and file
                self.create_q_language_responses_dir_and_file(
                    q, per_questionnaire_data_dir
                )
            # create Per_participant_data subdirs
            # TODO: inside that subdirs could be other dirs and files. By
            # TODO: now we are creating only the first subdirs levels
            for participant in group.participants.all():
                os.mkdir(os.path.join(
                    per_participant_data_dir, 'Participant_' + participant.code
                ))

            # create Experimental_protocol subdirs
            # TODO: inside Experimental_protocol dir there are files,
            # TODO: as well as in that subdirs. By now we are creating only
            # TODO: the first subdirs levels
            for i in range(2):
                os.mkdir(os.path.join(
                    experimental_protocol_dir, 'STEP_' + str(i)
                ))

            # create Participants.csv file
            self.create_text_file(
                os.path.join(group_dir, 'Participants.csv'),
                'a, b, c\nd, e, f'
            )

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

    def test_POSTing_download_experiment_data_returns_correct_content(self):
        # Last approved experiment has 2 groups and questionnaire steps (
        # with questionnaires data) created in tests helper
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()
        # Create study and participants and experimental protocol for
        # experiment
        create_experiment_related_objects(experiment)

        # Create a complete directory tree with all possible experiment data
        # directories/files that reproduces the directory/file structure
        # created when Portal receives the experiment data through Rest API.
        self.create_download_dir_structure_and_files(experiment)
        # get groups and participants for tests below
        g1 = experiment.groups.order_by('?').first()
        g2 = experiment.groups.order_by('?').first()  # yes, can be equal to g1
        p1 = experiment.groups.first().participants.order_by('?').first()
        p2 = experiment.groups.last().participants.order_by('?').first()

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.post(
            url, {
                'download_selected': [
                    'experimental_protocol_g' + str(g1.id),
                    'questionnaires_g' + str(g2.id),
                    'participant_p' + str(p1.id) + '_g' + str(
                        experiment.groups.first().id),
                    'participant_p' + str(p2.id) + '_g' + str(
                        experiment.groups.last().id),
                ]
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename="download.zip"'
        )

        # Get the zipped file to test against its content
        file = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(file, 'r')
        self.assertIsNone(zipped_file.testzip())

        # Test for ziped folders
        self.assertTrue('Group_' + g1.title, any(zipped_file.namelist()))
        self.assertTrue('Group_' + g2.title, any(zipped_file.namelist()))
        self.assertTrue('Experimental_protocol', any(zipped_file.namelist()))
        self.assertTrue('Per_participant_data', any(zipped_file.namelist()))
        self.assertTrue('Questionnaire_metadata', any(zipped_file.namelist()))

        self.fail('Finish this test!')

    def test_POSTing_download_experiment_data_without_choices_redirects_to_experiment_detail_view(self):
        # Last approved experiment created in tests helper has all
        # possible experiment data to download
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
