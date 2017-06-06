from datetime import datetime
from django.contrib.auth.models import User
from faker import Factory

# TODO: when executing from bash command line, final line identifier breaks
# imports. We are kepping in Collaborator in same line
from experiments.models import Experiment, Study, Group, Researcher, Collaborator

fake = Factory.create()

owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

for i in range(1, 4):
    experiment_owner1 = Experiment.objects.create(
        title=fake.name(),
        description=fake.text(),
        nes_id=i,
        owner=owner1, version=1,
        sent_date=datetime.utcnow()
    )
    Study.objects.create(
        title=fake.name(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner1
    )
    Group.objects.create(
        title=fake.name(),
        description=fake.text(),
        experiment=experiment_owner1
    )

for i in range(4, 6):
    experiment_owner2 = Experiment.objects.create(
        title=fake.name(),
        description=fake.text(),
        nes_id=i,
        owner=owner2, version=1,
        sent_date=datetime.utcnow()
    )
    Study.objects.create(
        title=fake.name(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner2
    )
    Group.objects.create(
        title=fake.name(),
        description=fake.text(),
        experiment=experiment_owner2
    )

    # Create researchers associated to studies created above
for study in Study.objects.all():
    Researcher.objects.create(
        name=fake.name(),
        email=fake.email(),
        study=study
    )

    # Create study's collaborators
study = Study.objects.get(experiment=Experiment.objects.first())
for i in range(1, 3):
    Collaborator.objects.create(name=fake.name(),
                                team=fake.company(),
                                coordinator=False, study=study)

Collaborator.objects.create(name=fake.name(),
                            team=fake.company(),
                            coordinator=True, study=study)
