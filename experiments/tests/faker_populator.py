from datetime import datetime
from random import randint
from subprocess import call

from django.contrib.auth import models
from faker import Factory

# TODO: when executing from bash command line, final line identifier breaks
# imports. We are kepping in Collaborator in same line
from experiments.helpers import generate_image_file
from experiments.models import Collaborator, Gender, ExperimentalProtocol
from experiments.models import Experiment, Study, Group, Researcher
from experiments.models import Participant
from experiments.tests.tests_helper import create_experiment_groups
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

# Create genders
male = Gender.objects.create(name='Male')
female = Gender.objects.create(name='Female')

# Create groups' experimental protocols and participants
for group in Group.objects.all():
    ExperimentalProtocol.objects.create(
        group=group,
        textual_description=fake.text()
    )
    for i in range(2):
        Participant.objects.create(group=group, code=fake.ssn(),
                                   gender=female, age=randint(18, 80))
    Participant.objects.create(group=group, code=fake.ssn(), gender=male,
                               age=randint(18, 80))

for exp_pro in ExperimentalProtocol.objects.all():
    image_file = generate_image_file(
        randint(100, 500), randint(300, 700), fake.word() + '.jpg')
    exp_pro.image.save(image_file.name, image_file)
    exp_pro.save()
    # Update image of last experimental protocol with a null image to test
    # displaying default image: "No image"
exp_pro = ExperimentalProtocol.objects.last()
exp_pro.image = None
exp_pro.save()


# TODO: why is necessary to keep two blank lines for script run until the end?
