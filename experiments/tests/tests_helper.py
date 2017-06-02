from datetime import datetime
from django.contrib.auth.models import User
from djipsum.faker import FakerModel

from experiments.models import Experiment, Study, Group


def global_setup():
    """
    This global setup creates basic object models that are used in 
    functional and unit tests.
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    # Create 3 experiments for owner 1 and 2 for owner 2, and studies,
    # and groups associated
    faker = FakerModel(app='experiments', model='Experiment')

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
            start_date=datetime.utcnow(),
            experiment=experiment_owner1
        )
        Group.objects.create(
            nes_id=i+1, title=faker.fake.text(max_nb_chars=15),
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
            nes_id=i+1, title=faker.fake.text(max_nb_chars=50),
            description=faker.fake.text(max_nb_chars=150),
            experiment=experiment_owner2
        )
