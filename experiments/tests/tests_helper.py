from datetime import datetime
from random import randint, choice

from django.contrib.auth import models
from faker import Factory

from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, Participant, Gender, ExperimentalProtocol, \
    ClassificationOfDiseases, Keyword, Step, TMSSetting, TMSDevice, CoilModel, \
    TMSDeviceSetting, TMSData

import random


def create_experiment_groups(qtty, experiment):
    """
    :param qtty: Number of groups
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    for i in range(qtty):
        Group.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=150),
            experiment=experiment
        )


def create_study(experiment):
    """
    :param experiment: Experiment to be associated with Study
    """
    fake = Factory.create()

    Study.objects.create(
        title=fake.text(max_nb_chars=15),
        description=fake.text(max_nb_chars=200),
        start_date=datetime.utcnow(), experiment=experiment
    )


def create_experiment(qtty, owner, status):
    """
    :param qtty: Number of experiments
    :param owner: Owner of experiment - User instance model
    :param status: Expeeriment status
    """
    fake = Factory.create()

    for i in range(qtty):
        experiment = Experiment.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            nes_id=randint(1, 10000),  # TODO: guarantee that this won't
            # genetates constraint violaton (nes_id, owner_id)
            owner=owner, version=1,
            sent_date=datetime.utcnow(),
            status=status,
            data_acquisition_done=choice([True, False])
        )
        create_study(experiment)
        create_experiment_groups(randint(2, 3), experiment)


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
    fake = Factory.create()

    for study in Study.objects.all():
        Researcher.objects.create(
            name=fake.name(),
            email=fake.email(),
            study=study
        )
        Collaborator.objects.create(name=fake.text(max_nb_chars=15),
                                    team=fake.text(max_nb_chars=15),
                                    coordinator=False, study=study)


def create_participant(qtty, group, gender):
    """
    :param gender:
    :param qtty:
    :param group: Group model instance
    """
    code = randint(1, 1000)
    for j in range(qtty):
        Participant.objects.create(
            code=code, age=randint(18, 80),
            gender=gender,
            group=group
        )
        code += 1


def create_experiment_protocol(group):
    """
    :type group: Group model instance
    """
    fake = Factory.create()

    ExperimentalProtocol.objects.create(
        group=group,
        textual_description=fake.text()
    )
    for exp_pro in ExperimentalProtocol.objects.all():
        image_file = generate_image_file(
            randint(100, 800), randint(300, 700), fake.word() + '.jpg'
        )
        exp_pro.image.save(image_file.name, image_file)
        exp_pro.save()
        # Update image of last experimental protocol with a null image to test
        # displaying default image: "No image"
    exp_pro = ExperimentalProtocol.objects.last()
    exp_pro.image = None
    exp_pro.save()


def create_classification_of_deseases(qtty):
    """
    :param qtty: number of objects to create 
    """
    fake = Factory.create()

    for i in range(qtty):
        ClassificationOfDiseases.objects.create(
            code=randint(1, 1000), description=fake.text(),
            abbreviated_description=fake.text(max_nb_chars=100),
            parent=None
        )


def create_study_collaborator(qtty, study):
    """
    :param qtty: number of collaborators 
    :param study: Study model instance
    """
    fake = Factory.create()

    for i in range(qtty):
        Collaborator.objects.create(
            name=fake.name(), team=fake.word(),
            coordinator=randint(0, 1),
            study=study
        )


def create_keyword(qtty):
    """
    :param qtty: number of keywords to be created 
    """
    fake = Factory.create()

    Keyword.objects.create(name=fake.word())
    for i in range(qtty):
        while True:
            keyword = fake.word()
            if not Keyword.objects.filter(name=keyword):
                break
        Keyword.objects.create(name=keyword)
    # To test search
    Keyword.objects.create(name='brachial plexus')


def associate_experiments_to_trustees():
    trustee1 = models.User.objects.get(username='claudia')  # requires
    # creates trustee Claudia
    trustee2 = models.User.objects.get(username='roque')  # requires
    # creates trustee Roque
    for experiment in Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS):
        experiment.trustee = choice([trustee1, trustee2])
    # Guarantee that at least one experiment has trustee as Claudia and one
    # experiment has trustee as Roque (requires creates at least two
    # experiments that are under analysis).
    exp1 = Experiment.objects.filter(status=Experiment.UNDER_ANALYSIS).first()
    exp2 = Experiment.objects.filter(status=Experiment.UNDER_ANALYSIS).last()
    exp1.trustee = trustee1
    exp1.save()
    exp2.trustee = trustee2
    exp2.save()


def create_ethics_committee_info(experiment):
    fake = Factory.create()

    experiment.project_url = fake.uri()
    experiment.ethics_committee_url = fake.uri()
    # TODO: generate PDF
    file = generate_image_file(500, 800, fake.word() + '.jpg')
    experiment.ethics_committee_file.save(file.name, file)
    experiment.save()


def create_step(qtty, group, type):
    """
    :param qtty: number of emg settings
    :param group: Experiment model instance
    :param type: step type: eeg, emg, tms etc.
    """
    fake = Factory.create()

    for i in range(qtty):
        Step.objects.create(
            group=group,
            identification=fake.word(), numeration=fake.ssn(),
            type=type, order=randint(1, 20)
        )


def create_tms_setting(qtty, experiment):
    """
    :param qtty: number of tmssetting settings
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    for i in range(qtty):
        TMSSetting.objects.create(
            experiment=experiment,
            name=fake.word(),
            description=fake.text()
        )


def create_tms_device(qtty):
    """
    :param qtty: number of tms device objects to create
    """
    fake = Factory.create()

    for i in range(qtty):
        TMSDevice.objects.create(
            manufacturer_name=fake.word(),
            equipment_type=fake.word(),
            identification=fake.word(),
            description=fake.text(),
            serial_number=fake.ssn(),
            pulse_type=choice(['monophase', 'biphase'])
        )


def create_coil_model(qtty):
    """
    :param qtty: number of coil model objects to create
    """
    fake = Factory.create()
    for i in range(qtty):
        CoilModel.objects.create(
            name=fake.word(), coil_shape_name=fake.word(),
            coil_design=choice(['air_core_coil', 'biphase']),
            description=fake.text(), material_name=fake.word(),
            material_description=fake.text(),
        )


def create_tms_device_setting(qtty, tms_setting, tms_device, coil_model):
    """
    :param qtty: number of tms device setting objects to create
    :param tms_setting: TMSSetting model instance
    :param tms_device: TMSDevice model instance
    :param coil_model: CoilModel model instance
    """
    for i in range(qtty):
        TMSDeviceSetting.objects.create(
            tms_setting=tms_setting, tms_device=tms_device, coil_model=coil_model,
            pulse_stimulus_type=choice(['single_pulse', 'paired_pulse',
                                        'repetitive_pulse'])
        )


def create_tms_data(qtty, tmssetting, participant):
    """
    :param qtty: number of tms data objects to create
    :param tmssetting: TMSSetting model instance
    :param participant: Participant model instance
    """
    faker = Factory.create()

    for i in range(qtty):
        TMSData.objects.create(
            participant=participant,
            date=datetime.utcnow(),
            tms_setting=tmssetting,
            resting_motor_threshold=round(random.uniform(0, 10), 2),
            test_pulse_intensity_of_simulation=round(random.uniform(0, 10), 2),
            second_test_pulse_intensity=round(random.uniform(0, 10), 2),
            interval_between_pulses=randint(0, 10),
            interval_between_pulses_unit='s',
            time_between_mep_trials=randint(0, 10),
            description=faker.text(), hotspot_name=faker.word(),
            localization_system_name=faker.word(),
            localization_system_description=faker.text(),
            brain_area_name=faker.word(),
            brain_area_description=faker.text(),
            brain_area_system_name=faker.word(),
            brain_area_system_description=faker.text()
        )


def objects_to_test_search():
    """
    Requires having created at least one Participant and two TMSSetting objects
    """
    participant = Participant.objects.last()
    create_tms_data(1, TMSSetting.objects.first(), participant)
    tms_data = TMSData.objects.last()
    tms_data.brain_area_name = 'cerebral cortex'
    tms_data.save()
    create_tms_data(1, TMSSetting.objects.last(), participant)
    tms_data = TMSData.objects.last()
    tms_data.brain_area_name = 'cerebral cortex'
    tms_data.save()
    create_tms_data(1, TMSSetting.objects.last(), participant)
    tms_data = TMSData.objects.last()
    tms_data.brain_area_name = 'cerebral cortex'
    tms_data.save()


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

    # Create 5 experiments for 2 owners, randomly, and studies (groups are
    # created inside create_experiment_and_study)
    create_experiment(2, choice([owner1, owner2]),
                      Experiment.TO_BE_ANALYSED)
    # To test search
    experiment = Experiment.objects.last()
    experiment.title = 'Brachial Plexus'
    experiment.save()

    create_experiment(2, choice([owner1, owner2]),
                      Experiment.UNDER_ANALYSIS)
    # To test search
    experiment = Experiment.objects.last()
    experiment.title = 'Brachial Plexus'
    experiment.save()

    create_experiment(4, choice([owner1, owner2]),
                      Experiment.APPROVED)
    # Put some non-random strings in one approved experiment to test search
    experiment = Experiment.objects.last()
    experiment.title = 'Brachial Plexus'
    experiment.description = 'Ein Beschreibung.'
    experiment.save()
    # Create version 2 of the experiment to test search - necessary to change
    # some field other than title, to include a non-random text, because we
    # are highlitghing the terms searched, and this put span's elements in
    # html with search results, causing dificulty to search 'Brachial
    # Plexus' in experiment title in test_search.py.
    # Related to: test_search_returns_only_last_version_experiment test.
    experiment.pk = None
    experiment.version = 2
    experiment.save()

    # To test search: we've created one experiment approved with 'Brachial
    # Plexus' in its title. We now create another experiment approved also
    # with 'Brachial Plexus' in title, and with EMG settings, to test
    # searching with filter.
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment = Experiment.objects.last()
    experiment.title = 'Brachial Plexus (with EMG Setting)'
    experiment.description = 'Ein Beschreibung. Brachial plexus repair by ' \
                             'peripheral nerve ' \
                             'grafts directly into the spinal cord in rats ' \
                             'Behavioral and anatomical evidence of ' \
                             'functional recovery. The EEG text.'
    experiment.save()
    create_step(1, experiment.groups.first(), Step.EMG)

    # We change first experiment study approved to contain 'brachial' in
    # study description, so it have to be found by search test
    study = Study.objects.filter(
        experiment__status=Experiment.APPROVED
    ).first()
    study.description = 'The brachial artery is the major blood vessel of ' \
                        'the (upper) arm. It\'s correlated with plexus. ' \
                        'This study should have an experiment with EEG.'
    # We put a keyword with the string 'brachial plexus' in the study to
    # also be found by search test
    study.keywords.add('brachial plexus')
    study.save()

    # To test search
    group = Group.objects.filter(
        experiment__status=Experiment.APPROVED
    ).first()
    group.description = 'Plexus brachial is written in wrong order. Correct ' \
                        'is Brachial plexus.'
    group.save()
    create_step(1, group, Step.EEG)
    create_step(1, group, Step.EMG)
    # To test search
    group.experiment.title = 'Experiment changed to test filter only'
    group.experiment.save()

    # TODO: test for matches Classification of Diseases
    ic = ClassificationOfDiseases.objects.create(
        code='BP', description='brachial Plexus',
        abbreviated_description='brachial Plexus',
        parent=None
    )
    group.inclusion_criteria.add(ic)
    group.save()

    # To test search
    group = Group.objects.filter(
        experiment__status=Experiment.APPROVED
    ).last()
    group.description = 'Brachial plexus is a set of nerves.'
    group.save()
    create_step(1, group, Step.EMG)

    # To test search
    create_experiment_groups(
        1, Experiment.objects.filter(status=Experiment.APPROVED).first()
    )
    group = Group.objects.last()
    group.title = 'Brachial only'
    group.save()

    # We create one experiment approved with ethics committee information
    create_ethics_committee_info(Experiment.objects.last())
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.NOT_APPROVED)

    # Associate trustee to experiments under analysis (requires create
    # experiments before)
    associate_experiments_to_trustees()

    # To test search
    experiment = Experiment.objects.get(
        trustee=models.User.objects.get(username='claudia')
    )
    experiment.title = 'Experiment analysed by Claudia'
    experiment.save()

    # Create study collaborators (requires creating studies before)
    for study in Study.objects.all():
        create_study_collaborator(randint(2, 3), study)
    # To test search
    study = Study.objects.filter(
        experiment__status=Experiment.APPROVED
    ).last()
    collaborator = Collaborator.objects.filter(study=study).first()
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

    # Create genders
    gender1 = Gender.objects.create(name='male')
    gender2 = Gender.objects.create(name='female')

    # Create some entries for ClassificationOfDiseases
    create_classification_of_deseases(10)

    # Create randint(3, 7) participants for each group (requires create
    # groups before)
    for group in Group.objects.all():
        create_experiment_protocol(group)
        create_participant(
            randint(3, 7), group,
            gender1 if randint(1, 2) == 1 else gender2
        )
        ic1 = choice(ClassificationOfDiseases.objects.all())
        ic2 = choice(ClassificationOfDiseases.objects.all())
        group.inclusion_criteria.add(ic1, ic2)

    # Create researchers associated to studies created in
    # create_experiment_and_study method
    # Requires running create_experiment_study_group before
    create_researchers()

    ##
    # To test searching TMS things
    ##
    # Create TMSSetting from an experiment Approved, to test search
    experiment = Experiment.objects.filter(status=Experiment.APPROVED).first()
    create_tms_setting(1, experiment)  # 1º TMSSetting
    tms_setting = TMSSetting.objects.last()
    tms_setting.name = 'tmssettingname'
    tms_setting.save()
    # Create TMSDeviceSetting from a TMSSetting to test search
    # Required creating TMSSetting from experimenta Approved, first
    create_tms_device(1)  # 1º TMSDevice
    tms_device = TMSDevice.objects.last()
    tms_device.manufacturer_name = 'Siemens'
    tms_device.save()
    create_coil_model(1)  # 1º CoilModel
    coil_model = CoilModel.objects.last()
    coil_model.name = 'Magstim'
    coil_model.save()
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)  #
    # 1º TMSDeviceSetting
    tms_device_setting = TMSDeviceSetting.objects.last()
    tms_device_setting.pulse_stimulus_type = 'single_pulse'
    tms_device_setting.save()
    # Create another TMSSetting and associate with same TMSDeviceSetting
    # created above to test searching TMSDevice and CoilModel
    create_tms_setting(1, experiment)  # 2º TMSSetting
    tms_setting = TMSSetting.objects.last()
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)  # 2º
    # TMSDeviceSetting
    # Create others TMSDevice and CoilModel associated with TMSDeviceSetting >
    # TMSSetting > Experiment
    create_tms_setting(1, experiment)  # 3º TMSSetting
    tms_setting = TMSSetting.objects.last()
    # TODO: IMPORTANT! when creating a new TMSDevice and a new CoilModel to
    # TODO: associate with new TMSDeviceSetting, the tests with filters in
    # TODO: test_search fails. See
    # create_tms_device(1)  # 2º TMSDevice
    # tms_device = TMSDevice.objects.last()
    # tms_device.manufacturer_name = 'Siemens'
    # tms_device.save()
    # create_coil_model(1)  # 2º CoilModel
    # coil_model = CoilModel.objects.last()
    # coil_model.name = 'Magstim'
    # coil_model.save()
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)  # 3º
    # TMSDeviceSetting

    # Create TMSData objects to test search
    # TODO: the tests returns non-deterministic search results.
    # objects_to_test_search()

    ##
    # DEBUG
    ##
    # for group in Group.objects.all():
    #     print(group.steps.all())
    # print('\n')


def global_setup_ut():
    """
    This global setup creates basic object models that are used in 
    unittests.
    """
    owner1 = models.User.objects.create_user(username='lab1',
                                             password='nep-lab1')
    owner2 = models.User.objects.create_user(username='lab2',
                                             password='nep-lab2')

    # Create group Trustees
    create_trustee_users()

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.UNDER_ANALYSIS,
        trustee=models.User.objects.get(username='claudia')
    )
    experiment3 = Experiment.objects.create(
        title='Experiment 3', nes_id=2, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED
    )
    create_ethics_committee_info(experiment3)

    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    study2 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment2)
    # Create a study and doesn't associate it with researcher bellow.
    # This is to testing creating research associate it with a study in
    # test_models.py
    Study.objects.create(start_date=datetime.utcnow(),
                         experiment=experiment3)

    Researcher.objects.create(name='Raimundo Nonato',
                              email='rnonato@example.com', study=study1)
    Researcher.objects.create(name='Raimunda da Silva',
                              email='rsilva@example.com', study=study2)

    # Create some keywords to associate with studies
    create_keyword(10)
    # Associate keywords with studies
    for study in Study.objects.all():
        kw1 = choice(Keyword.objects.all())
        kw2 = choice(Keyword.objects.all())
        kw3 = choice(Keyword.objects.all())
        study.keywords.add(kw1, kw2, kw3)

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
