from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from experiments.models import Experiment
from experiments.tests.tests_helper import apply_setup, global_setup_ut


@apply_setup(global_setup_ut)
class HomePageTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')

    def test_access_experiment_detail_after_GET_experiment(self):
        experiment_id = str(Experiment.objects.first().id)
        response = self.client.get('/experiments/' + experiment_id + '/')
        self.assertEqual(response.status_code, 200)

    def test_uses_detail_template(self):
        experiment_id = str(Experiment.objects.first().id)
        response = self.client.get('/experiments/' + experiment_id + '/')
        self.assertTemplateUsed(response, 'experiments/detail.html')

