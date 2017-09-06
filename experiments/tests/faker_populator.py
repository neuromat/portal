from datetime import datetime
from random import randint, choice
from subprocess import call

from django.contrib.auth import models
from faker import Factory

# python manage.py shell < experiments/tests/faker_populator.py
# TODO: when executing from bash command line, final line identifier breaks
# imports. We are kepping in Collaborator in same line
from experiments.models import Gender, ClassificationOfDiseases, Keyword, \
    Collaborator, Step, TMSSetting, TMSDevice, CoilModel, TMSDeviceSetting
from experiments.models import Experiment, Study, Group, Researcher
from experiments.tests.tests_helper import create_experiment_groups, \
    create_ethics_committee_info, create_step, create_tms_setting, \
    create_tms_device, create_coil_model, create_tms_device_setting, \
    create_tmsdata_objects_to_test_search
from experiments.tests.tests_helper import create_classification_of_deseases
from experiments.tests.tests_helper import create_experiment_protocol
from experiments.tests.tests_helper import create_participant
from experiments.tests.tests_helper import create_study_collaborator
from experiments.tests.tests_helper import create_keyword
from nep.local_settings import BASE_DIR


# Clear sqlite database and run migrate
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
        status=Experiment.TO_BE_ANALYSED,
        data_acquisition_done=choice([True, False])
    )
    Study.objects.create(
        title=fake.word().title(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner1
    )
    # to test search (necessary to approve experiment(s) in front-end or
    # directly in database)
    if i == 1:
        study = Study.objects.last()
        study.description = 'The brachial artery is the major blood vessel ' \
                            'of  the (upper) arm. It\'s correlated with ' \
                            'plexus.'
        # We put a keyword with the string 'brachial plexus' in the study to
        # also be found by search test
        study.keywords.add('brachial plexus')
        study.save()

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
    # to test search (necessary to approve experiment(s) in front-end or
    # directly in database)
    if i == 4:
        experiment_owner2.title = 'Brachial Plexus'
        experiment_owner2.save()
    if i == 5:
        experiment_owner2.description = \
            'Brachial plexus repair by peripheral nerve ' \
            'grafts directly into the spinal cord in rats ' \
            'Behavioral and anatomical evidence of ' \
            'functional recovery'
        experiment_owner2.save()

    Study.objects.create(
        title=fake.word().title(),
        description=fake.text(),
        start_date=datetime.utcnow(), experiment=experiment_owner2
    )
    create_experiment_groups(randint(1, 3), experiment_owner2)

# to test search (necessary to approve experiment(s) in front-end or
# directly in database)
group = Group.objects.first()
group.description = 'Plexus brachial (com EMG) is writed in wrong order. ' \
                    'Correct is Brachial plexus.'
ic = ClassificationOfDiseases.objects.create(
    code='BP', description='brachial Plexus',
    abbreviated_description='brachial Plexus',
    parent=None
)
group.inclusion_criteria.add(ic)
group.save()
# to test search with filter (necessary to approve experiment(s) in
# front-end or directly in database)
create_step(1, group, Step.EMG)

# to test search with filter (necessary to approve experiment(s) in
# front-end or directly in database)
group = Group.objects.last()
group.title = 'Brachial Plexus com EEG'
group.save()
create_step(1, group, Step.EEG)

# to test search with filter (necessary to approve experiment(s) in
# front-end or directly in database)
group = Group.objects.get(
    id=(Group.objects.last().id + Group.objects.first().id) // 2
)
group.title = 'Brachial Plexus com EEG e EMG'
group.save()
create_step(1, group, Step.EEG)
create_step(1, group, Step.EMG)

# Create researchers associated to studies created above
for study in Study.objects.all():
    Researcher.objects.create(name=fake.name(),
                              email='claudia.portal.neuromat@gmail.com',
                              study=study)
# to test search (necessary to approve experiment(s) in front-end or
# directly in database)
researcher = Researcher.objects.last()
researcher.name = 'Yolanda Fuentes'
researcher.save()

# Create study collaborators (requires creating studies before)
for study in Study.objects.all():
    create_study_collaborator(randint(2, 3), study)
# To test search (necessary to approve experiment(s) in front-end or
# directly in database)
collaborator = Collaborator.objects.last()
collaborator.name = 'Pero Vaz'
collaborator.save()

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
    create_participant(
        randint(3, 7), group,
        gender1 if randint(1, 2) == 1 else gender2
    )
    ic1 = choice(ClassificationOfDiseases.objects.all())
    ic2 = choice(ClassificationOfDiseases.objects.all())
    group.inclusion_criteria.add(ic1, ic2)

# Create TMSSetting from an experiment Approved, to test search.
# Obs.: TO VERIFY SEARCH TMS things, change Experiment status to APPROVED
# after run this faker populator
experiment = Experiment.objects.first()
create_tms_setting(1, experiment)
tms_setting = TMSSetting.objects.last()
tms_setting.name = 'tmssettingname'
tms_setting.save()

# Create TMSDeviceSetting from a TMSSetting to test search
# Required creating TMSSetting from experiment Approved, first
create_tms_device(1)
tms_device = TMSDevice.objects.last()
create_coil_model(1)
coil_model = CoilModel.objects.last()
create_tms_device_setting(1, tms_setting, tms_device, coil_model)
tms_device_setting = TMSDeviceSetting.objects.last()
tms_device_setting.pulse_stimulus_type = 'single_pulse'
tms_device_setting.save()

# Create TMSDevice to test search
tms_device.manufacturer_name = 'Siemens'
tms_device.save()
# Create another TMSSetting and associate with same TMSDeviceSetting
# created above to test searching
create_tms_setting(1, experiment)
tms_setting = TMSSetting.objects.last()
tmsds = create_tms_device_setting(1, tms_setting, tms_device, coil_model)

# Create TMSData to test search
create_tmsdata_objects_to_test_search()

# TODO: After populating models we call 'manage.py rebuild_index --noinput' to
# TODO: rebuild haystack search index - to manually test searching.


# TODO: why is necessary to keep two blank lines for script run until the end?
