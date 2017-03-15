from django.test import TestCase
from django.core.exceptions import ValidationError
from experiments.models import Experiment


class HomePageTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')


class ExperimentModelTest(TestCase):

    def test_default_title(self):
        experiment = Experiment()
        self.assertEqual(experiment.title, '')

    def test_cannot_save_empty_title(self):
        experiment = Experiment(title='')
        with self.assertRaises(ValidationError):
            experiment.save()
            experiment.full_clean()
