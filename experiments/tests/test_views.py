import haystack
import sys
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from haystack.query import SearchQuerySet

from experiments import views
from experiments.models import Experiment, Step, Questionnaire
from experiments.tasks import rebuild_haystack_index
from experiments.tests.tests_helper import apply_setup, global_setup_ut


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


# TODO: test other stuf
class ExperimentDetailTest(TestCase):

    def setUp(self):
        global_setup_ut()
        
    def test_access_experiment_detail_after_GET_experiment(self):
        slug = str(Experiment.objects.first().slug)
        response = self.client.get('/experiments/' + slug + '/')
        self.assertEqual(response.status_code, 200)

    def test_uses_detail_template(self):
        slug = str(Experiment.objects.first().slug)
        response = self.client.get('/experiments/' + slug + '/')
        self.assertTemplateUsed(response, 'experiments/detail.html')

    def test_access_experiment_detail_returns_questionnaire_data(self):
        experiment = Experiment.objects.last()
        slug = str(experiment.slug)
        response = self.client.get('/experiments/' + slug + '/')

        # We've made last experiment approved contain questionnaire data in
        # tests helper
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = experiment.groups.filter(steps__in=q_steps)
        if groups_with_qs.count() == 0:
            self.fail('There are no groups with questionnaires. Have you '
                      'been created the questionnaires in tests helper?')
        for group in groups_with_qs:
            self.assertContains(
                'Questionnaires for group ' + group.name,
                response
            )
            for step in group.steps:
                questionnaire = Questionnaire.objects.get(step_ptr=step)
                self.assertIn(
                    'Questionnaire ' + questionnaire.survey_name,
                    response
                )

        # Sample asserts for first questionnaire
        self.assertIn('História da fratura', response)
        self.assertIn('Fratura da costela', response)
        self.assertIn('História prévia de dor?', response)
        self.assertIn('T1', response)
        self.assertIn('data da lesão:', response)
        self.assertIn('User fill in a date.', response)
        self.assertIn('<em>User answers</em> yes <em>or</em> not.',
                      response)
        # Sample asserts for second questionnaire
        self.assertIn('Já fez alguma cirurgia ortopédica?',
                      response)
        self.assertIn('Fez alguma cirurgia de nervo?', response)
        self.assertIn('Identifique o evento que levou ao trauma do seu plexo '
                      'braquial. É possível marcar mais do que um evento.',
                      response)
        self.assertIn('Lesão por queimadura', response)
        self.assertIn('Faz uso de dispositivo auxiliar?',
                      response)
        self.assertIn('História da doença atual:', response)
        self.assertIn('User fills in a text field.', response)
        # Sample asserts for third questionnaire
        self.assertIn('C5-T1', response)
        self.assertIn('Qual a localização da lesão ao exame clínico?',
                      response)
        self.assertIn('Anestesia', response)
        self.assertIn('T3', response)
        self.assertIn('Sensibilidade Superficial Tátil:',
                      response)
        self.assertIn('Número do participante:', response)
        self.assertIn('User fills in with a number.', response)


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
        rebuild_haystack_index()

        # Tests helper creates an experiment UNDER_ANALYSIS with 'Experiment
        # 2' as experiment title
        results = SearchQuerySet().filter(content='Experiment 2')
        # results = SearchQuerySet().all()  # DEBUG
        # TODO: by now we have 4 models been indexed
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].model_name, 'experiment')
        self.assertEqual(results[0].object.title, 'Experiment 2')

    # TODO: test other objects following this structure
    def test_search_eegsetting_returns_correct_objects(self):
        response = self.client.get('/search/', {'q': 'eegsettingname'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<tr', 3)  # because in search results
        # templates it's '<tr class ...>'
