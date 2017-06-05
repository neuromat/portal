from datetime import datetime
from django.contrib.auth.models import User
from djipsum.faker import FakerModel

from experiments.models import Experiment, Study, Group, Researcher


def global_setup_ft():
    """
    This global setup creates basic object models that are used in 
    functional tests.
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    faker = FakerModel(app='experiments', model='Experiment')

    # Create 3 experiments for owner 1 and 2 for owner 2, and studies,
    # and groups associated
    for i in range(0, 3):
        experiment_owner1 = Experiment.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i+1,
            owner=owner1, version=1,
            sent_date=datetime.utcnow()
        )
        Study.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            start_date=datetime.utcnow(), experiment=experiment_owner1
        )
        Group.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment_owner1
        )

    for i in range(3, 5):
        experiment_owner2 = Experiment.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            nes_id=i + 1,
            owner=owner2, version=1,
            sent_date=datetime.utcnow()
        )
        Study.objects.create(
            title=faker.fake.text(max_nb_chars=15),
            description=faker.fake.text(max_nb_chars=200),
            start_date=datetime.utcnow(), experiment=experiment_owner2
        )
        Group.objects.create(
            title=faker.fake.text(max_nb_chars=50),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment_owner2
        )

    # Create researchers associated to studies created above
    for study in Study.objects.all():
        Researcher.objects.create(
            name=faker.fake.text(max_nb_chars=15),
            email=faker.fake.text(max_nb_chars=15),
            study=study
        )


def global_setup_ut():
    """
    This global setup creates basic object models that are used in 
    functional tests. 
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1,
        version=1, sent_date=datetime.utcnow()
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow()
    )

    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    Study.objects.create(start_date=datetime.utcnow(),
                         experiment=experiment2)

    Researcher.objects.create(name='Raimundo Nonato',
                              email='rnonato@example.com', study=study1)


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
