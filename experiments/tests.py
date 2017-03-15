from django.test import TestCase
from django.core.exceptions import ValidationError
from experiments.models import Experiment


class HomePageTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')


class ExperimentModelTest(TestCase):

    def test_default_attributes(self):
        experiment = Experiment()
        self.assertEqual(experiment.title, '')
        self.assertEqual(experiment.description, '')
        self.assertEqual(experiment.is_public, False)
        self.assertEqual(experiment.data_acquisition_done, False)

    def test_cannot_save_empty_attributes(self):
        # TODO: is it necessary to test for one attribute at time too?
        experiment = Experiment(title='', description='')
        with self.assertRaises(ValidationError):
            experiment.save()
            experiment.full_clean()
