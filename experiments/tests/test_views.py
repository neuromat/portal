from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from experiments.models import ExperimentStatus, Experiment, Study


def global_setup(self):
    """
    This setup creates basic object models that are used in tests bellow.
    :param self: 
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    exp_status = ExperimentStatus.objects.create(tag='to_be_approved')

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1, status=exp_status,
        version=1, sent_date=datetime.utcnow()
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2, status=exp_status,
        version=1, sent_date=datetime.utcnow()
    )

    Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                         experiment=experiment1, owner=owner1)
    Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                         experiment=experiment2, owner=owner2)


def apply_setup(setup_func):
    """
    Defines a decorator that uses my_setup method.
    :param setup_func: my_setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap


class HomePageTest(TestCase):

    def setUp(self):
        global_setup(self)

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'experiments/home.html')

    def test_access_experiment_detail_after_GET_experiment(self):
        experiment_id = str(Experiment.objects.first().id)
        response = self.client.get('/experiments/' + experiment_id + '/')
        self.assertEqual(response.status_code, 200)
