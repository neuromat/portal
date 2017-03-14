from django.test import TestCase
from experiments.models import Experiment


class HomePageTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')


class ExperimentModelTest(TestCase):

    def test_default_title(self):
        experiment = Experiment()
        self.assertEqual(experiment.title, '')
