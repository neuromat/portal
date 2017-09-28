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


# TODO: we are testing only questionnaire view part. Complete with other
# TODO: tests: groups, studies, settings etc
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
        # Last experiment has questionnaires. See tests helper
        experiment = Experiment.objects.last()
        response = self.client.get('/experiments/' + experiment.slug + '/')

        # We've made last experiment approved contain questionnaire data in
        # tests helper
        q_steps = Step.objects.filter(type=Step.QUESTIONNAIRE)
        groups_with_qs = experiment.groups.filter(steps__in=q_steps)
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
                self.assertContains(
                    response,
                    'Questionnaire ' + questionnaire.survey_name
                )

        # Sample asserts for first questionnaire
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
        self.assertIn('Qual o lado da lesão?', response.content.decode())
        self.assertIn('Instituição do Estudo', response.content.decode())
        self.assertIn('The user enters a free text',
                      response.content.decode())
        self.assertIn('Tipo(s) de lesão(ões):', response.content.decode())
        self.assertIn('Trombose', response.content.decode())
        self.assertIn('Anexar exames.', response.content.decode())
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
            'q': '\"História de fratura\" \"trauma do seu plexo '
                 'braquial\" \"Lesão por arma de fogo\" \"Qual o lado '
                 'da lesão\" \"Extensão do Cotovelo\"'
        })
        self.assertEqual(response.status_code, 200)
        # TODO: we verify for 3 objects because test is catching invalid
        # TODO: questionnaires. See note 'Backlog' in notebook, 09/28/2017
        self.assertContains(response, '<tr', 3)  # because in search results
        # templates it's '<tr class ...>'
        # TODO: needs to know if it was brought correct results

    def test_search_questionnaire_returns_matchings_containing_search_strings(self):
        response = self.client.get('/search/', {
            'q': '\"História de fratura\" \"trauma do seu plexo '
                 'braquial\" \"Lesão por arma de fogo\" \"Qual o lado '
                 'da lesão\" \"Extensão do Cotovelo\"'
        })
        self.assertContains(response, 'História de fratura')
        self.assertContains(response, 'trauma do seu plexo braquial')
        self.assertContains(response, 'Lesão por arma de fogo')
        self.assertContains(response, 'Qual o lado da lesão')
        self.assertContains(response, 'Extensão do Cotovelo')
