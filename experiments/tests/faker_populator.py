from datetime import datetime
from random import randint, choice
from subprocess import call

from django.contrib.auth import models
from faker import Factory

# TODO: when executing from bash command line, final line identifier breaks
# imports. We are kepping in Collaborator in same line
from experiments.models import Collaborator, Gender, ClassificationOfDiseases
from experiments.models import Experiment, Study, Group, Researcher
from experiments.tests.tests_helper import create_experiment_groups, create_classification_of_deseases, create_experiment_protocol, create_participants
from nep.local_settings import BASE_DIR


# Clear database and run migrate
call(['rm', BASE_DIR + '/db.sqlite3'])
call([BASE_DIR + '/manage.py', 'migrate'])

fake = Factory.create()

# Create api clients users (experiment owners)
owner1 = models.User.objects.create_user(username='lab1', password='nep-lab1')
owner2 = models.User.objects.create_user(username='lab2', password='nep-lab2')

# Create group trustees
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

for i in range(1, 4):
    experiment_owner1 = Experiment.objects.create(
        title=fake.name(),
        description=fake.text(),
        nes_id=i,
        owner=owner1, version=1,
        sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    Study.objects.create(
        title=fake.name(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner1
    )
    create_experiment_groups(randint(1, 3), experiment_owner1)

for i in range(4, 6):
    experiment_owner2 = Experiment.objects.create(
        title=fake.name(),
        description=fake.text(),
        nes_id=i,
        owner=owner2, version=1,
        sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    Study.objects.create(
        title=fake.name(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner2
    )
    create_experiment_groups(randint(1, 3), experiment_owner2)

# Create researchers associated to studies created above
for study in Study.objects.all():
    Researcher.objects.create(name=fake.name(), email=fake.email(),
                              study=study)

# Create study's collaborators
study = Study.objects.get(experiment=Experiment.objects.first())
for i in range(2):
    Collaborator.objects.create(name=fake.name(),
                                team=fake.company(),
                                coordinator=False, study=study)

Collaborator.objects.create(name=fake.name(),
                            team=fake.company(),
                            coordinator=True, study=study)

# Create some entries for ClassificationOfDiseases
create_classification_of_deseases(10)

# Create genders
gender1 = Gender.objects.create(name='Male')
gender2 = Gender.objects.create(name='Female')

# Create groups' experimental protocols and participants
for group in Group.objects.all():
    create_experiment_protocol(group)
    create_participants(
        randint(3, 7), group,
        gender1 if randint(1, 2) == 1 else gender2
    )
    ic1 = choice(ClassificationOfDiseases.objects.all())
    ic2 = choice(ClassificationOfDiseases.objects.all())
    group.inclusion_criteria.add(ic1, ic2)


# TODO: why is necessary to keep two blank lines for script run until the end?
