from datetime import datetime
from random import randint, choice

from django.contrib.auth import models
from djipsum.faker import FakerModel

from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator


def create_experiment_study_group(qtty, owner, status):
    faker = FakerModel(app='experiments', model='Experiment')

    for i in range(0, qtty):
        experiment = Experiment.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=randint(0, 10000),  # TODO: guarantee that this won't genetates constraint violaton (nes_id, owner_id)
            owner=owner, version=1,
            sent_date=datetime.utcnow(),
            status=status
        )
        Study.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            start_date=datetime.utcnow(), experiment=experiment
        )
        Group.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment
        )


def create_trustee_users():
    group = models.Group.objects.create(name='trustees')

    # Create 2 trustee users and add them to trustees group
    trustee1 = models.User.objects.create_user(
        username='claudia', first_name='Claudia', last_name='Vargas',
        password='passwd'
    )
    trustee2 = models.User.objects.create_user(
        username='roque', first_name='Antonio', last_name='Roque',
        password='passwd'
    )
    group.user_set.add(trustee1)
    group.user_set.add(trustee2)


def create_researchers():
    faker = FakerModel(app='experiments', model='Experiment')

    for study in Study.objects.all():
        Researcher.objects.create(
            name=faker.fake.text(max_nb_chars=15),
            email=faker.fake.text(max_nb_chars=15),
            study=study
        )
        Collaborator.objects.create(name=faker.fake.text(max_nb_chars=15),
                                    team=faker.fake.text(max_nb_chars=15),
                                    coordinator=False, study=study)


def global_setup_ft():
    """
    This global setup creates basic object models that are used in 
    functional tests.
    """
    # Create 2 API clients
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    # Create group Trustees
    create_trustee_users()

    # Create 3 experiments for owner 1 and 2 for owner 2, and studies,
    # and groups associated
    create_experiment_study_group(2, choice([owner1, owner2]), Experiment.TO_BE_ANALYSED)
    create_experiment_study_group(1, choice([owner1, owner2]), Experiment.UNDER_ANALYSIS)
    create_experiment_study_group(1, choice([owner1, owner2]), Experiment.APPROVED)
    create_experiment_study_group(1, choice([owner1, owner2]), Experiment.NOT_APPROVED)

    # Create researchers associated to studies created in create_experiment_study_group method
    # Requires running create_experiment_study_group before
    create_researchers()


def global_setup_ut():
    """
    This global setup creates basic object models that are used in 
    unittests.
    """
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.UNDER_ANALYSIS
    )

    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    Study.objects.create(start_date=datetime.utcnow(),
                         experiment=experiment2)

    Researcher.objects.create(name='Raimundo Nonato',
                              email='rnonato@example.com', study=study1)
    Collaborator.objects.create(
        name='Colaborador 1', team='Numec', coordinator=True,
        study=study1
    )
    Collaborator.objects.create(
        name='Colaborador 2', team='Numec', coordinator=False,
        study=study1
    )


def apply_setup(setup_func):
    """
    Defines a decorator that uses global setup method.
    :param setup_func: global setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap
