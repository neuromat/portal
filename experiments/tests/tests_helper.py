import os
import random
import shutil
import tempfile
import zipfile
from datetime import datetime
from random import randint, choice

from django.conf import settings
# TODO: remove import above making the use of User model directly not
# TODO: model.User
from django.contrib.auth import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from faker import Factory

from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Participant, Gender, ExperimentalProtocol, \
    ClassificationOfDiseases, Keyword, Step, TMSSetting, TMSDevice, CoilModel, \
    TMSDeviceSetting, TMSData, EEGSetting, Questionnaire, \
    QuestionnaireLanguage, QuestionnaireDefaultLanguage, Publication, EEGData, \
    EEGElectrodeLocalizationSystem, ContextTree, Stimulus, EEG, EMG, \
    EMGSetting, EMGData, GoalkeeperGame, GoalkeeperGameData, \
    GenericDataCollection, GenericDataCollectionData, AdditionalData, \
    EMGElectrodePlacement, EEGElectrodeNet, EEGSolution, EEGFilterSetting, \
    EMGDigitalFilterSetting, ElectrodeModel, EMGElectrodeSetting, \
    EMGElectrodePlacementSetting, EMGSurfacePlacement, \
    EMGIntramuscularPlacement, EMGNeedlePlacement, EEGElectrodePosition, \
    SurfaceElectrode, IntramuscularElectrode, Instruction, \
    QuestionnaireResponse, ExperimentResearcher
# TODO: not protected any more. Fix this!
from experiments.views import _get_q_default_language_or_first

# the password used for trustees in tests
PASSWORD = 'labX'


def create_group(qtty, experiment):
    # TODO: refactor to accept more than one experiment (insert qtty parameter)
    """
    :param qtty: Number of groups
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    groups = []
    for i in range(qtty):
        group = Group.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=150),
            experiment=experiment
        )
        groups.append(group)

    if len(groups) == 1:
        return groups[0]
    return groups


def create_study(qtty, experiment):
    """
    :param qtty: number of studies to be created
    :param experiment: Experiment to be associated with Study
    """
    fake = Factory.create()

    studies = []
    for i in range(qtty):
        study = Study.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            start_date=datetime.utcnow(), experiment=experiment
        )
        studies.append(study)

    if len(studies) == 1:
        return studies[0]
    return studies


def create_owner(username=None):
    """
    :param username: String
    :return: auth.User model instance
    """
    fake = Factory.create()

    if not username:
        while True:
            username = fake.word()
            if not User.objects.filter(username=username):
                break

    return User.objects.create_user(username=username, password=PASSWORD)


def create_experiment(qtty, owner=None, status=Experiment.TO_BE_ANALYSED,
                      title=None):
    """
    :param qtty: number of experiments to be created
    :param owner: owner of experiment - User instance model
    :param status: experiment status
    """
    fake = Factory.create()

    if not owner:
        owner = create_owner()

    experiments = []
    for i in range(qtty):
        experiment = Experiment.objects.create(
            title=title if title else fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            # TODO: guarantee that this won't
            # TODO: genetates constraint violaton (nes_id, owner_id)!
            nes_id=randint(1, 10000),
            owner=owner, version=1,
            sent_date=datetime.utcnow(),
            status=status,
            data_acquisition_done=choice([True, False]),
        )
        experiments.append(experiment)

    if len(experiments) == 1:
        return experiments[0]
    return experiments


def create_next_version_experiment(experiment, release_notes=''):
    """
    :param experiment: Experiment model instance
    :param release_notes: string with version release notes
    :return: new experiment version
    """
    return Experiment.objects.create(
        owner=experiment.owner, nes_id=experiment.nes_id,
        version=experiment.version + 1, title=experiment.title,
        description=experiment.description, status=experiment.status,
        release_notes=release_notes
    )


def create_trustee_user(username=None):
    """
    Create a trustee user. First get or create the group 'trustees
    :return: User from group Trustee
    """
    group, created = models.Group.objects.get_or_create(name='trustees')

    faker = Factory.create()
    username = username if username else faker.word()

    trustee = models.User.objects.create_user(
        username=username, first_name=faker.first_name(),
        last_name=faker.last_name(), email=faker.email(),
        password=PASSWORD
    )
    group.user_set.add(trustee)

    return trustee


# deprecated: create researchers with create_researcher
def create_researchers():
    for study in Study.objects.all():
        create_researcher(study)


def create_researcher(study, first_name=None, last_name=None):
    """
    :param study: Study model instance
    :param first_name: researcher's first name
    :param last_name: researcher's last name
    :return: Researcher model instance
    """
    fake = Factory.create()
    return Researcher.objects.create(
        first_name=first_name or fake.first_name(),
        last_name=last_name or fake.last_name(),
        email=fake.email(), study=study,
    )


def create_genders():
    Gender.objects.create(name='male')
    Gender.objects.create(name='female')


def create_participant(qtty, group, gender):
    """
    :param qtty: number of objects to create
    :param gender: Gender model instance
    :param group: Group model instance
    """
    code = randint(1, 1000)

    participants = []
    for j in range(qtty):
        participant = Participant.objects.create(
            code=code, age=randint(18, 80),
            gender=gender,
            group=group
        )
        code += 1
        participants.append(participant)

    if len(participants) == 1:
        return participants[0]
    return participants


def create_experimental_protocol(group):
    """
    :type group: Group model instance
    """
    fake = Factory.create()

    exp_prot = ExperimentalProtocol.objects.create(
        group=group,
        textual_description=fake.text()
    )

    # create experimental protocol image
    image_file = generate_image_file(
        randint(100, 800), randint(300, 700), fake.word() + '.jpg'
    )
    exp_prot.image.save(image_file.name, image_file)
    exp_prot.save()

    return exp_prot


def create_classification_of_diseases():
    """
    :param qtty: number of objects to create 
    """
    fake = Factory.create()

    return ClassificationOfDiseases.objects.create(
        code=randint(1, 1000), description=fake.text(),
        abbreviated_description=fake.text(max_nb_chars=100),
        parent=None
    )


def create_experiment_researcher(experiment, first_name=None, last_name=None):
    fake = Factory.create()

    return ExperimentResearcher.objects.create(
        first_name=first_name or fake.first_name(),
        last_name=last_name or fake.last_name(),
        email=fake.email(), institution=fake.company(),
        experiment=experiment
    )


def create_keyword(keyword=None):
    """
    :param qtty: number of keywords to be created
    :param keyword: keyword to be craeted
    """
    fake = Factory.create()

    if keyword:
        return Keyword.objects.create(name=keyword)

    while True:
        keyword = fake.word()
        if not Keyword.objects.get(name=keyword):
            return Keyword.objects.create(name=keyword)


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
    :param qtty: number of Step model instances
    :param group: Group model instance
    :param type: Step type: eeg, emg, tms etc.
    """
    fake = Factory.create()

    steps = []
    for i in range(qtty):
        step = Step.objects.create(
            group=group,
            identification=fake.word(), numeration=fake.ssn(),
            type=type, order=randint(1, 20)
        )
        steps.append(step)

    if len(steps) == 1:
        return steps[0]
    return steps


def create_eeg_step(group, eeg_setting):
    """
    :param group: Group model instance
    :param eeg_setting: EEGSetting model instance
    """
    faker = Factory.create()

    return EEG.objects.create(
        group=group, eeg_setting=eeg_setting,
        identification=faker.word(), numeration=faker.ssn(),
        type=Step.EEG, order=randint(1, 20)
    )


def create_emg_setting(experiment):
    """
    :param experiment: Experiment model instance
    :return: EMGSetting model instance
    """
    faker = Factory.create()

    return EMGSetting.objects.create(
        experiment=experiment, name=faker.word(), description=faker.text(),
        acquisition_software_version=faker.ssn()
    )


def create_emg_step(group, emg_setting):
    """
    :param group: Group model instance
    :param emg_setting: EMGSetting model instance
    """
    faker = Factory.create()

    return EMG.objects.create(
        group=group, emg_setting=emg_setting,
        identification=faker.word(), numeration=faker.ssn(),
        type=Step.EMG, order=randint(1, 20)
    )


def create_goalkeepergame_step(group, context_tree):
    """
    :param group: Group model instance
    :param context_tree: Context Tree model instance
    :return: GoalkeeperGame model instance
    """
    faker = Factory.create()

    return GoalkeeperGame.objects.create(
        software_name=faker.word(), software_description=faker.text(),
        software_version=faker.word(), context_tree=context_tree,
        group=group, identification=faker.word(), numeration=faker.ssn(),
        type=Step.GOALKEEPER, order=randint(1, 20)
    )


def create_emg_data(emg_setting, emg_step, participant):
    """
    :param emg_setting: EMGSetting model instance
    :param emg_step: EMG(Step) model instance
    :param participant: Participant model instance
    """
    return EMGData.objects.create(
        emg_setting=emg_setting,
        step=emg_step,
        participant=participant,
        date=datetime.utcnow()
    )


def create_emg_electrode_placement():
    """
    :return: EMGElectrodePlacement model instance
    """
    faker = Factory.create()

    return EMGElectrodePlacement.objects.create(
        standardization_system_name=faker.word(),
        standardization_system_description=faker.text(),
        muscle_anatomy_origin=faker.text(),
        muscle_anatomy_insertion=faker.text(),
        muscle_anatomy_function=faker.text(),
        location=faker.text(),
        placement_type=faker.word()
    )


def create_emg_surface_placement():
    faker = Factory.create()

    return EMGSurfacePlacement.objects.create(
        standardization_system_name=faker.word(),
        start_posture=faker.text(),
        orientation=faker.text(),
        fixation_on_the_skin=faker.text(),
        reference_electrode=faker.text(),
        clinical_test=faker.text()
    )


def create_emg_intramuscular_placement():
    faker = Factory.create()

    return EMGIntramuscularPlacement.objects.create(
        standardization_system_name=faker.word(),
        method_of_insertion=faker.text(),
        depth_of_insertion=faker.text()
    )


def create_emg_needle_placement():
    faker = Factory.create()

    return EMGNeedlePlacement.objects.create(
        standardization_system_name=faker.word(),
        depth_of_insertion=faker.text()
    )


def create_emg_electrode_placement_setting(emg_electrode_setting,
                                           emg_electrode_placement):
    return EMGElectrodePlacementSetting.objects.create(
        emg_electrode_setting=emg_electrode_setting,
        emg_electrode_placement=emg_electrode_placement
    )


def create_eeg_electrode_position(eeg_electrode_localization_system,
                                  electrode_model):
    faker = Factory.create()

    return EEGElectrodePosition.objects.create(
        name=faker.word(),
        eeg_electrode_localization_system=eeg_electrode_localization_system,
        electrode_model=electrode_model,
        channel_index=13
    )


def create_stimulus_step(group):
    """
    :param group: Group model instance
    :return: Stimulus model instance
    """
    faker = Factory.create()

    return Stimulus.objects.create(
        group=group,
        identification=faker.word(), numeration=faker.ssn(),
        type=Step.STIMULUS, order=randint(1, 20),
        stimulus_type_name=faker.word()
    )


def create_instruction_step(group):
    faker = Factory.create()

    return Instruction.objects.create(
        group=group,
        identification=faker.word(), description=faker.text(),
        numeration=faker.ssn(), duration_value=randint(1, 20),
        duration_unit='min', order=randint(1, 20),
        number_of_repetitions=randint(1, 3),
        interval_between_repetitions_value=randint(3, 8),
        interval_between_repetitions_unit='min',
        random_position=choice([True, False]), type=Step.INSTRUCTION,
        text=faker.text()
    )


def create_tms_setting(qtty, experiment):
    """
    :param qtty: number of tmssetting settings
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    tms_settings = []
    for i in range(qtty):
        tms_setting = TMSSetting.objects.create(
            experiment=experiment,
            name=fake.word(),
            description=fake.text()
        )
        tms_settings.append(tms_setting)

    if len(tms_settings) == 1:
        return tms_settings[0]
    return tms_settings


def create_tms_device():
    """
    :param qtty: number of tms device objects to create
    """
    fake = Factory.create()

    return TMSDevice.objects.create(
            manufacturer_name=fake.word(),
            equipment_type=fake.word(),
            identification=fake.word(),
            description=fake.text(),
            serial_number=fake.ssn(),
            pulse_type=choice(['monophase', 'biphase'])
        )


def create_coil_model():
    """
    :param qtty: number of coil model objects to create
    """
    fake = Factory.create()
    return CoilModel.objects.create(
            name=fake.word(), coil_shape_name=fake.word(),
            coil_design=choice(['air_core_coil', 'biphase']),
            description=fake.text(), material_name=fake.word(),
            material_description=fake.text(),
        )


def create_tms_device_setting(tms_setting, tms_device, coil_model):
    """
    :param qtty: number of tms device setting objects to create
    :param tms_setting: TMSSetting model instance
    :param tms_device: TMSDevice model instance
    :param coil_model: CoilModel model instance
    """
    return TMSDeviceSetting.objects.create(
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

    tms_data_list = []
    for i in range(qtty):
        tms_data = TMSData.objects.create(
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
        tms_data_list.append(tms_data)

    if len(tms_data_list) == 1:
        return tms_data_list[0]
    return tms_data_list


def create_tmsdata_objects_to_test_search():
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


def create_eeg_setting(qtty, experiment):
    """
    :param qtty: number of eeg setting objects to create
    :param experiment: Experiment model instance
    """
    faker = Factory.create()

    eeg_settings = []
    for i in range(qtty):
        eeg_setting = EEGSetting.objects.create(
            experiment=experiment, name=faker.word(), description=faker.text()
        )
        eeg_settings.append(eeg_setting)

    if len(eeg_settings) == 1:
        return eeg_settings[0]
    return eeg_settings


def create_eeg_data(eeg_setting, eeg_step, participant):
    """
    :param eeg_setting: EEGSetting model instance
    :param eeg_step: EEG(Step) model instance
    :param participant: Participant model instance
    """
    return EEGData.objects.create(
        eeg_setting=eeg_setting,
        step=eeg_step,
        participant=participant,
        date=datetime.utcnow()
    )


def create_eeg_electrode_localization_system(eeg_setting):
    """
    :param eeg_setting: EEGSetting model instance
    """
    fake = Factory.create()
    return EEGElectrodeLocalizationSystem.objects.create(
        eeg_setting=eeg_setting,
        name=fake.word(),
    )


def create_eeg_electrodenet(eeg_setting):
    faker = Factory.create()

    return EEGElectrodeNet.objects.create(
        eeg_setting=eeg_setting, manufacturer_name=faker.word(),
        equipment_type='eeg_electrode_net', identification=faker.word(),
        description=faker.text(), serial_number=faker.ssn()
    )


def create_eeg_solution(eeg_setting):
    faker = Factory.create()

    return EEGSolution.objects.create(
        eeg_setting=eeg_setting, manufacturer_name=faker.word(),
        name=faker.word(), components=faker.text()
    )


def create_eeg_filter_setting(eeg_setting):
    faker = Factory.create()

    return EEGFilterSetting(
        eeg_setting=eeg_setting, eeg_filter_type_name=faker.word(),
        eeg_filter_type_description=faker.text(),
    )


def create_emg_digital_filter_setting(emg_setting):
    faker = Factory.create()

    return EMGDigitalFilterSetting(
        emg_setting=emg_setting, filter_type_name=faker.word(),
        filter_type_description=faker.text(),
    )


def create_goalkeeper_game_data(gkg_step, participant):
    """
    :param gkg_step: GoalkeeperGame(Step) model instance
    :param participant: Participant model instance
    :return: GoalkeeperGameData mode instance
    """
    return GoalkeeperGameData.objects.create(
        step=gkg_step, participant=participant, date=datetime.utcnow()
    )


def create_generic_data_collection_step(group):
    """
    :param group: Group model instance
    :return: GenericDataCollection model instance
    """
    faker = Factory.create()

    return GenericDataCollection.objects.create(
        group=group,
        identification=faker.word(), numeration=faker.ssn(),
        type=Step.GENERIC, order=randint(1, 20)
    )


def create_electrode_model():
    faker = Factory.create()

    return ElectrodeModel.objects.create(
        name=faker.word(), description=faker.text(), material=faker.word(),
        usability=choice(['disposable', 'reusable']), impedance=13,
        impedance_unit='ohm', inter_electrode_distance=13,
        inter_electrode_distance_unit='cm',
        electrode_configuration_name=faker.word(),
        electrode_type=choice(['surface', 'intramuscular', 'needle'])
    )


def create_surface_electrode():
    faker = Factory.create()

    return SurfaceElectrode.objects.create(
        name=faker.word(), description=faker.text(), material=faker.word(),
        usability=choice(ElectrodeModel.USABILITY_TYPES)[0], impedance=13,
        impedance_unit='ohm', inter_electrode_distance=13,
        inter_electrode_distance_unit='cm',
        electrode_configuration_name=faker.word(),
        electrode_type=choice(ElectrodeModel.ELECTRODE_TYPES)[0],
        conduction_type=choice(SurfaceElectrode.CONDUCTION_TYPES)[0],
        electrode_mode=choice(SurfaceElectrode.MODE_OPTIONS)[0],
        electrode_shape_name=faker.word(), electrode_shape_measure_value=13,
        electrode_shape_measure_unit='cm2'
    )


def create_intramuscular_electrode():
    faker = Factory.create()

    return IntramuscularElectrode.objects.create(
        name=faker.word(), description=faker.text(), material=faker.word(),
        usability=choice(ElectrodeModel.USABILITY_TYPES)[0], impedance=13,
        impedance_unit='ohm', inter_electrode_distance=13,
        inter_electrode_distance_unit='cm',
        electrode_configuration_name=faker.word(),
        electrode_type=choice(ElectrodeModel.ELECTRODE_TYPES)[0],
        strand=choice(IntramuscularElectrode.STRAND_TYPES)[0],
        insulation_material_name=faker.word(),
        insulation_material_description=faker.text(),
        length_of_exposed_tip=21
    )


def create_emg_electrode_setting(emg_setting, electrode_model):
    return EMGElectrodeSetting.objects.create(
        emg_setting=emg_setting, electrode_model=electrode_model
    )


def create_generic_data_collection_data(gdc_step, participant):
    return GenericDataCollectionData.objects.create(
        step=gdc_step, participant=participant, date=datetime.utcnow()
    )


def create_valid_questionnaires(groups):
    # TODO: create_valid_questionnaire (one for one group). Create csv's
    #  files on the fly
    q1 = create_questionnaire(1, 'q1', groups[0])
    q2 = create_questionnaire(1, 'q2', groups[0])
    q3 = create_questionnaire(1, 'q3', groups[1])

    # create questionnaire language data pt-br for questionnaire1
    create_questionnaire_language(
        q1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1_pt-br.csv',
        # our tests helper always consider 'en' as Default Language,
        # so we create this time as 'pt-br' to test creating questionnaire
        # default language in test_api (by the moment only test_api tests
        # creating questionnaire default language; can expand testing
        # questionnaire related models)
        'pt-br'
    )
    # create questionnaire language data fr for questionnaire1
    create_questionnaire_language(
        q1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1_fr.csv',
        # our tests helper always consider 'en' as Default Language,
        # so we create this time as 'pt-br' to test creating questionnaire
        # default language in test_api (by the moment only test_api tests
        # creating questionnaire default language; can expand testing
        # questionnaire related models)
        'fr'
    )

    # create questionnaire language data default for questionnaire2
    create_questionnaire_language(
        q2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2.csv', 'en'
    )
    # create questionnaire language data de for questionnaire2
    create_questionnaire_language(
        q2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2_de.csv', 'de'
    )

    # create questionnaire language data default for questionnaire3
    create_questionnaire_language(
        q3,
        settings.BASE_DIR + '/experiments/tests/questionnaire3.csv', 'en'
    )


def create_questionnaire_language(questionnaire, source, language):
    """
    Get the data from source file containing questionnaire csv data,
    and populates QuestionnaireLanguage object
    :param questionnaire: Questionnaire model instance
    :param source: file to read from
    :param language: language of the questionnaire
    :return: QuestionnaireLanguage model instance
    """
    file = open(source, 'r')
    # skip first line with column titles
    file.readline()
    # gets the questionnaire title in second line second column
    questionnaire_title = file.readline().split(',')[1]
    file.close()
    # open again to get all data
    with open(source, 'r') as fp:
        metadata = fp.read()

    q_language = QuestionnaireLanguage.objects.create(
        questionnaire=questionnaire,
        language_code=language,
        survey_name=questionnaire_title,
        survey_metadata=metadata
    )

    # we consider that English language is always the default language
    # for tests porposes
    if language == 'en':
        QuestionnaireDefaultLanguage.objects.create(
            questionnaire=questionnaire,
            questionnaire_language=QuestionnaireLanguage.objects.last()
        )

    return q_language


def create_questionnaire(qtty, code, group):
    """
    Create qtty questionnaire(s) for a group
    :param qtty: quantity of questionnaires to be created
    :param code: code of the questionnaire (defined to ease questionnaire
    testing)
    :param group: Group model instance
    """
    faker = Factory.create()

    q_list = []
    for i in range(qtty):
        q_list.append(Questionnaire.objects.create(
            code=code,
            group=group, order=randint(1, 10),
            identification='questionnaire',
            numeration=faker.ssn(),
            type=Step.QUESTIONNAIRE,
        ))

    if len(q_list) > 1:
        return q_list
    else:
        return q_list[0]


def create_questionnaire_responses(questionnaire, participant, source):
    """
    Create QuestionnaireResponse object for one participant for a given
    Questionnaire object
    :param questionnaire: Questionnaire model instance
    :param participant: Participant model instance
    :param source: File with json text
    """
    with open(source, 'r') as fp:
        responses = fp.read()

    return QuestionnaireResponse.objects.create(
        step=questionnaire, participant=participant, date=datetime.utcnow(),
        limesurvey_response=responses
    )


# Data Collection types constants
DC_EEG = 'eeg'


def create_binary_file(path):
    with open(os.path.join(path, 'file.bin'), 'wb') as f:
        f.write(b'carambola')
    return f


def create_additional_data(step, participant):
    return AdditionalData.objects.create(
        step=step, participant=participant, date=datetime.utcnow()
    )


def create_uploads_subdirs_and_files(uploads_subdir, empty=False):
    os.mkdir(uploads_subdir)
    for year in ['2017', '2018', '2019']:
        for month in ['03', '04']:
            for day in ['13', '14']:
                file_path = os.path.join(uploads_subdir, year, month, day)
                os.makedirs(file_path)
                if not empty:
                    if choice([0, 1]) == 0:
                        create_binary_file(file_path)


def create_download_subdirs(download_subdir):
    os.makedirs(download_subdir)
    create_binary_file(download_subdir)
    os.mkdir(os.path.join(download_subdir, 'Some_Group'))


def create_context_tree(experiment):
    """
    :param experiment: Experiment model instance
    """
    fake = Factory.create()

    return ContextTree.objects.create(
        setting_text=fake.text(),
        experiment=experiment,
        name=fake.word(),
        description=fake.text()
    )


def create_publication(experiment):
    """
    Create publications for experiment
    :param qtty: number of Publication's to be created
    :param experiment: Experiment model instance
    """
    faker = Factory.create()

    return Publication.objects.create(
            title=faker.sentence(nb_words=6), citation=faker.text(),
            url=faker.uri(),
            experiment=experiment
        )


def create_experiment_related_objects(experiment):
    """
    Create experiment related objects to test download experiment data
    pieces selected by the user.
    :param experiment: Experiment model instance
    """
    study = create_study(1, experiment)
    # necessary creating researcher for study. See comment in
    # search_indexes.StudyIndex class
    Researcher.objects.create(
        first_name='Negro', last_name='Belchior',
        email='belchior@example.com', study=study,
        citation_name='BELCHIOR, Negro'
    )
    for group in experiment.groups.all():
        create_participant(
            randint(2, 6), group,
            Gender.objects.get(name='female')
        )
        create_experimental_protocol(group)

    # create data collection
    # TODO: implement it!
    # Create data_collection(s) to test
    # test_views.test_POSTing_download_experiment_data_returns_correct_content
    # create_data_collection(experiment.groups.first(), 'eeg')


def create_q_language_dir(q, questionnaire_metadata_dir):
    q_default = _get_q_default_language_or_first(q)
    q_language_dir = os.path.join(
        questionnaire_metadata_dir,
        q.code + '_' + q_default.survey_name
    )
    return q_language_dir


def create_q_language_responses_dir_and_file(
        q, per_questionnaire_data_dir
):
    q_language_dir = create_q_language_dir(
        q, per_questionnaire_data_dir
    )
    os.mkdir(q_language_dir)
    file_path = os.path.join(
        q_language_dir, 'Responses_' + q.code + '.csv'
    )
    create_text_file(file_path, 'a, b, c\nd, e, f')


def create_q_language_metadata_dir_and_files(
        q, questionnaire_metadata_dir
):
    q_language_dir = create_q_language_dir(
        q, questionnaire_metadata_dir
    )
    os.mkdir(q_language_dir)
    for q_language in q.q_languages.all():
        file_path = os.path.join(
            q_language_dir,
            'Fields_' + q.code + '_' +
            q_language.language_code + '.csv'
        )
        create_text_file(file_path, 'a, b, c\nd, e, f')


def create_group_subdir(group_dir, name):
    subdir = os.path.join(group_dir, name)
    os.makedirs(subdir)
    return subdir


def create_text_file(file_path, text):
    file = open(file_path, 'w')
    file.write(text)
    file.close()


def create_download_dir_structure_and_files(experiment, temp_media_root):
    """
    Create a complete directory tree with possible experiment data
    directories/files that reproduces the directory/file structure
    created when Portal receives the experiment data through Rest API and
    triggers making download.zip file and directory/file structure.
    :param experiment: Experiment model instance
    :param temp_media_root: Temporary media root path
    """
    # define download experiment data root
    experiment_download_dir = os.path.join(
        temp_media_root, 'download', str(experiment.pk)
    )

    os.makedirs(experiment_download_dir)

    # create fake download.zip file
    with open(os.path.join(experiment_download_dir, 'download.zip'), 'wb') \
            as file:
        file.write(b'fake_experiment_data')
        file.close()

    # create License.txt file
    create_text_file(
        os.path.join(temp_media_root, 'download', 'LICENSE.txt'),
        'The GNU General Public License is a free, copyleft license for '
        'software and other kinds of works.'
    )

    # create CITATION.txt file
    create_text_file(
        os.path.join(
            temp_media_root, 'download', str(experiment.id), 'CITATION.txt'
        ),
        'How to cite'
    )

    # create Experiment.csv file
    create_text_file(
        os.path.join(experiment_download_dir, 'Experiment.csv'),
        'a, b, c\nd, e, f'
    )

    for group in experiment.groups.all():
        group_dir = os.path.join(
            experiment_download_dir, 'Group_' + slugify(group.title)
        )
        # TODO: sometimes on creating this subdir, test fails claiming that
        # TODO: 'Questionnaire_metadata' already exists. It seems that
        # TODO: some group title is repeating. Verify!
        questionnaire_metadata_dir = create_group_subdir(
            group_dir, 'Questionnaire_metadata'
        )
        per_questionnaire_data_dir = create_group_subdir(
            group_dir, 'Per_questionnaire_data'
        )
        per_participant_data_dir = create_group_subdir(
            group_dir, 'Per_participant_data'
        )
        experimental_protocol_dir = create_group_subdir(
            group_dir, 'Experimental_protocol'
        )

        # create questionnaire stuff
        for questionnaire_step in group.steps.filter(
                type=Step.QUESTIONNAIRE
        ):
            # TODO: see if using step_ptr is ok
            q = Questionnaire.objects.get(step_ptr=questionnaire_step)

            # create Questionnaire_metadata dir and files
            create_q_language_metadata_dir_and_files(
                q, questionnaire_metadata_dir
            )
            # create Per_questionnaire_data dir and file
            create_q_language_responses_dir_and_file(
                q, per_questionnaire_data_dir
            )
        # create Per_participant_data subdirs
        # TODO: inside that subdirs could be other dirs and files. By
        # TODO: now we are creating only the first subdirs levels
        for participant in group.participants.all():
            os.mkdir(os.path.join(
                per_participant_data_dir, 'Participant_' + participant.code
            ))

        # create Experimental_protocol subdirs
        # TODO: inside Experimental_protocol dir there are files,
        # TODO: as well as in that subdirs. By now we are creating only
        # TODO: the first subdirs levels
        for i in range(2):
            os.mkdir(os.path.join(
                experimental_protocol_dir, 'STEP_' + str(i)
            ))

        # create Participants.csv file
        create_text_file(
            os.path.join(group_dir, 'Participants.csv'),
            'a, b, c\nd, e, f'
        )


def remove_selected_subdir(selected, experiment, participant, group,
                           temp_media_root):
    experiment_download_dir = os.path.join(
        temp_media_root, 'download', str(experiment.pk)
    )

    ##
    # Remove subdirs from temp_file
    group_title_slugifyed = slugify(group.title)
    if 'experimental_protocol_g' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group_title_slugifyed,
            'Experimental_protocol'
        ))
    if 'questionnaires_g' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group_title_slugifyed,
            'Per_questionnaire_data'
        ))
    if 'participant_p' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group_title_slugifyed,
            'Per_participant_data', 'Participant_' + str(participant.code)
        ))
    # If group has questionnaires remove 'Questionnaire_metadata' subdir
    # randomly
    if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
        if randint(0, 1):
            shutil.rmtree(os.path.join(
                experiment_download_dir, 'Group_' + group_title_slugifyed,
                'Questionnaire_metadata'
            ))
    # remove Experiments.csv and Participants.csv randomly
    if randint(0, 1):
        os.remove(os.path.join(experiment_download_dir, 'Experiment.csv'))
    if randint(0, 1):
        os.remove(os.path.join(
            experiment_download_dir, 'Group_' + group_title_slugifyed,
            'Participants.csv'
        ))


def random_utf8_string(length):
    result = b''
    for i in range(length):
        a = b'\\u%04x' % random.randrange(0x10000)
        result = result + a
    result.decode('unicode-escape')
    return result.decode()
