from datetime import datetime
from random import randint, choice
from subprocess import call

from django.contrib.auth import models
from faker import Factory

# python manage.py shell < experiments/tests/faker_populator.py
# TODO: when executing from bash command line, final line identifier breaks
# imports. We are kepping in Collaborator in same line
from experiments.models import Gender, ClassificationOfDiseases, Keyword
from experiments.models import Experiment, Study, Group, Researcher
from experiments.tests.tests_helper import create_experiment_groups, \
    create_ethics_committee_info
from experiments.tests.tests_helper import create_classification_of_deseases
from experiments.tests.tests_helper import create_experiment_protocol
from experiments.tests.tests_helper import create_participants
from experiments.tests.tests_helper import create_study_collaborator
from experiments.tests.tests_helper import create_keyword
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
        title=fake.word().title(),
        description=fake.text(),
        nes_id=i,
        owner=owner1, version=1,
        sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    Study.objects.create(
        title=fake.word().title(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner1
    )
    create_ethics_committee_info(experiment_owner1)
    create_experiment_groups(randint(1, 3), experiment_owner1)

for i in range(4, 6):
    experiment_owner2 = Experiment.objects.create(
        title=fake.word().title(),
        description=fake.text(),
        nes_id=i,
        owner=owner2, version=1,
        sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    Study.objects.create(
        title=fake.word().title(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner2
    )
    create_experiment_groups(randint(1, 3), experiment_owner2)

# Create researchers associated to studies created above
for study in Study.objects.all():
    Researcher.objects.create(name=fake.name(),
                              email='claudia.portal.neuromat@gmail.com',
                              study=study)

# Create study collaborators (requires creating studies before)
for study in Study.objects.all():
    create_study_collaborator(randint(2, 3), study)

# Create some keywords to associate with studies
create_keyword(10)
# Associate keywords with studies
for study in Study.objects.all():
    kw1 = choice(Keyword.objects.all())
    kw2 = choice(Keyword.objects.all())
    kw3 = choice(Keyword.objects.all())
    study.keywords.add(kw1, kw2, kw3)

# Create some entries for ClassificationOfDiseases
create_classification_of_deseases(10)

# Create genders
gender1 = Gender.objects.create(name='male')
gender2 = Gender.objects.create(name='female')

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
