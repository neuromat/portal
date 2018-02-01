import os
import random
import shutil
import tempfile
from datetime import datetime
from random import randint, choice
from faker import Factory

from django.contrib.auth.models import User
# TODO: remove import above making the use of User model directly not
# TODO: model.User
from django.contrib.auth import models

from nep import settings
from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, Participant, Gender, ExperimentalProtocol, \
    ClassificationOfDiseases, Keyword, Step, TMSSetting, TMSDevice, CoilModel, \
    TMSDeviceSetting, TMSData, EEGSetting, Questionnaire, \
    QuestionnaireLanguage, QuestionnaireDefaultLanguage, Publication, EEGData, \
    EEGElectrodeLocalizationSystem, ContextTree, Stimulus, EEG, EMG, \
    EMGSetting, EMGData, GoalkeeperGame, GoalkeeperGameData, \
    GenericDataCollection, GenericDataCollectionData, AdditionalData, \
    EMGElectrodePlacement, EEGElectrodeNet, EEGSolution, EEGFilterSetting, \
    EMGDigitalFilterSetting, ElectrodeModel, EMGElectrodeSetting, \
    EMGElectrodePlacementSetting, EMGSurfacePlacement
from experiments.views import _get_q_default_language_or_first


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
    if not username:
        fake = Factory.create()
        username = fake.word()

    return User.objects.create_user(username=username, password='labX')


def create_experiment(qtty, owner=None, status=Experiment.TO_BE_ANALYSED):
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
            title=fake.text(max_nb_chars=15),
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


def create_experiment_versions(qtty, experiment):
    """
    :param qtty: number of versions to create
    :param experiment: Experiment model instance
    :return: list of all versions including the first
    """
    current_version = experiment.version
    for version in range(qtty):
        experiment_version = experiment
        experiment_version.pk = None
        experiment_version.version = current_version + 1
        experiment_version.save()
        current_version += 1

    experiment_versions = []
    for ev in Experiment.objects.all():
        experiment_versions.append(ev)
    return experiment_versions


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

    trustees = list()
    trustees.append(trustee1)
    trustees.append(trustee2)
    return trustees


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


def create_genders():
    Gender.objects.create(name='male')
    Gender.objects.create(name='female')


def create_participant(qtty, group, gender):
    """
    :param gender:
    :param qtty:
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


def create_emg_electrode_placement_setting(emg_electrode_setting,
                                           emg_electrode_placement):
    return EMGElectrodePlacementSetting.objects.create(
        emg_electrode_setting=emg_electrode_setting,
        emg_electrode_placement=emg_electrode_placement
    )


def create_stimulus_step(group):
    """
    :param group: Group model instance
    :return: Stimulus model instance
    """
    fake = Factory.create()

    return Stimulus.objects.create(
        group=group,
        identification=fake.word(), numeration=fake.ssn(),
        type=Step.STIMULUS, order=randint(1, 20),
        stimulus_type_name=fake.word()
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
        equipment_type='eeg_electrode_net', identification=faker.text(),
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
        usability=choice(['disposable', 'reusable']),
        electrode_configuration_name=faker.word(),
        electrode_type=choice(['surface', 'intramuscular', 'needle'])
    )


def create_emg_electrode_setting(emg_setting, electrode_model):
    return EMGElectrodeSetting.objects.create(
        emg_setting=emg_setting, electrode_model=electrode_model
    )


def create_generic_data_collection_data(gdc_step, participant):
    return GenericDataCollectionData.objects.create(
        step=gdc_step, participant=participant, date=datetime.utcnow()
    )


def create_questionnaire_language(questionnaire, source, language):
    """
    Get the data from source file containing questionnaire csv data,
    and populates QuestionnaireLanguage object
    :param questionnaire: Questionnaire model instance
    :param source: file to read from
    :param language: language of the questionnaire
    """
    # catch file to read the data
    file = open(source, 'r')
    # skip first line with column titles
    file.readline()
    # gets the questionnaire title in second line second column
    questionnaire_title = file.readline().split(',')[1]
    file.close()
    # open again to get all data
    with open(source, 'r') as fp:
        metadata = fp.read()

    QuestionnaireLanguage.objects.create(
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


def create_questionnaire(qtty, code, group):
    """
    Create qtty questionnaire(s) for a group
    :param qtty: quantity of questionnaires to be created
    :param code: code of the questionnaire (defined to ease questionnaire
    testing)
    :param group: Group model instance
    """

    for i in range(qtty):
        Questionnaire.objects.create(
            code=code,
            group=group, order=randint(1, 10),
            identification='questionnaire',
            type=Step.QUESTIONNAIRE,
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


def create_publication(qtty, experiment):
    """
    Create publications for experiment
    :param qtty: number of Publication's to be created
    :param experiment: Experiment model instance
    """
    faker = Factory.create()

    for i in range(qtty):
        Publication.objects.create(
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
    create_study(1, experiment)
    study = Study.objects.last()
    # necessary creating researcher for study. See comment in
    # search_indexes.StudyIndex class
    Researcher.objects.create(
        name='Negro Belchior', email='belchior@example.com', study=study
    )
    gender1 = Gender.objects.create(name='male')
    gender2 = Gender.objects.create(name='female')
    for group in experiment.groups.all():
        create_participant(
            randint(2, 6), group,
            gender1 if randint(1, 2) == 1 else gender2
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
    subdir = os.path.join(
        group_dir, name
    )
    os.makedirs(subdir)
    return subdir


def create_text_file(file_path, text):
    file = open(file_path, 'w')
    file.write(text)
    file.close()


def create_download_dir_structure_and_files(experiment, temp_media_root):
    # define download experiment data root
    experiment_download_dir = os.path.join(
        temp_media_root, 'download', str(experiment.pk)
    )

    # remove subdir if exists before creating that
    if os.path.exists(experiment_download_dir):
        shutil.rmtree(experiment_download_dir)
    os.makedirs(experiment_download_dir)

    # create Experiment.csv file
    create_text_file(
        os.path.join(experiment_download_dir, 'Experiment.csv'),
        'a, b, c\nd, e, f'
    )

    for group in experiment.groups.all():
        group_dir = os.path.join(
            experiment_download_dir, 'Group_' + group.title
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
    # Define download experiment data root. This and subdirs created
    # below has to be the same as defined in
    # create_download_dir_structure_and_files.
    experiment_download_dir = os.path.join(
        temp_media_root, 'download', str(experiment.pk)
    )
    if 'experimental_protocol_g' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group.title,
            'Experimental_protocol'
        ))
    if 'questionnaires_g' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group.title,
            'Per_questionnaire_data'
        ))
    if 'participant_p' in selected:
        shutil.rmtree(os.path.join(
            experiment_download_dir, 'Group_' + group.title,
            'Per_participant_data', 'Participant_' + participant.code
        ))
    # If group has questionnaires remove 'Questionnaire_metadata' subdir
    # randomly.
    if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
        if randint(0, 1) == 1:
            shutil.rmtree(os.path.join(
                experiment_download_dir, 'Group_' + group.title,
                'Questionnaire_metadata'
            ))

    # Remove Experiments.csv and Participants.csv randomly
    if randint(0, 1) == 1:
        os.remove(os.path.join(
            experiment_download_dir, 'Experiment.csv'
        ))
    if randint(0, 1) == 1:
        os.remove(os.path.join(
            experiment_download_dir, 'Group_' + group.title,
            'Participants.csv'
        ))


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

    # Create experiments for 2 owners, randomly
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.TO_BE_ANALYSED)
    experiment1 = Experiment.objects.last()
    create_study(1, experiment1)
    create_group(randint(2, 3), experiment1)

    create_experiment(1, choice([owner1, owner2]),
                      Experiment.TO_BE_ANALYSED)
    experiment2 = Experiment.objects.last()
    create_study(1, experiment2)
    create_group(randint(2, 3), experiment2)
    # To test search
    experiment2.title = 'Brachial Plexus'
    experiment2.save()

    create_experiment(1, choice([owner1, owner2]),
                      Experiment.UNDER_ANALYSIS)
    experiment3 = Experiment.objects.last()
    create_study(1, experiment3)
    create_group(randint(2, 3), experiment3)
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.UNDER_ANALYSIS)
    experiment4 = Experiment.objects.last()
    create_study(1, experiment4)
    create_group(randint(2, 3), experiment4)
    # To test search
    experiment4.title = 'Brachial Plexus'
    experiment4.save()

    # TODO: refactor to create the 4 experiments at once (how it was
    # TODO: before)
    # TODO: see TODO's in create_study and create_group methods
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment5 = Experiment.objects.last()
    create_study(1, experiment5)
    create_group(randint(2, 3), experiment5)
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment6 = Experiment.objects.last()
    create_study(1, experiment6)
    create_group(randint(2, 3), experiment6)
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment7 = Experiment.objects.last()
    create_study(1, experiment7)
    create_group(randint(2, 3), experiment7)
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment8 = Experiment.objects.last()
    create_study(1, experiment8)
    create_group(randint(2, 3), experiment8)
    # Put some non-random strings in one approved experiment to test search
    experiment8.title = 'Brachial Plexus'
    experiment8.description = 'Ein Beschreibung.'
    experiment8.save()
    # Create version 2 of the experiment to test search - necessary to change
    # some field other than title, to include a non-random text, because we
    # are highlitghing the terms searched, and this put span's elements in
    # html with search results, causing dificulty to search 'Brachial
    # Plexus' in experiment title in test_search.py.
    # Related to: test_search_returns_only_last_version_experiment test.
    # experiment.pk = None # ???
    experiment8.version = 2
    experiment8.save()

    # To test search: we've created one experiment approved with 'Brachial
    # Plexus' in its title. We now create another experiment approved also
    # with 'Brachial Plexus' in title, and with EMG settings, to test
    # searching with filter.
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.APPROVED)
    experiment9 = Experiment.objects.last()
    create_study(1, experiment9)
    create_group(randint(2, 3), experiment9)
    experiment9.title = 'Brachial Plexus (with EMG Setting)'
    experiment9.description = 'Ein Beschreibung. Brachial plexus repair by ' \
                             'peripheral nerve ' \
                             'grafts directly into the spinal cord in rats ' \
                             'Behavioral and anatomical evidence of ' \
                             'functional recovery. The EEG text.'
    experiment9.save()
    create_step(1, experiment9.groups.first(), Step.EMG)
    # Associate publications with experiment to test publications
    create_publication(2, experiment9)

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
    create_group(
        1, Experiment.objects.filter(status=Experiment.APPROVED).first()
    )
    group = Group.objects.last()
    group.title = 'Brachial only'
    group.save()

    # We create one experiment approved with ethics committee information
    create_ethics_committee_info(Experiment.objects.last())
    create_experiment(1, choice([owner1, owner2]),
                      Experiment.NOT_APPROVED)
    experiment10 = Experiment.objects.last()
    create_study(1, experiment10)
    create_group(randint(2, 3), experiment10)

    # Associate trustee to experiments under analysis (requires create
    # experiments before)
    associate_experiments_to_trustees()

    # To test search
    experiment11 = Experiment.objects.get(
        trustee=models.User.objects.get(username='claudia')
    )
    experiment11.title = 'Experiment analysed by Claudia'
    experiment11.save()

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

    # Create some invalid entries for ClassificationOfDiseases model.
    # They are invalid because in create_classification_of_diseases method
    # the code are generated with a faker.
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.description = 'Code not recognized'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.description = 'Code not recognized'
    cd.save()

    # Create valid entries for ClassificationOfDiseases model.
    # We give valid codes to the objects created.
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A00'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A1782'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A3681'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A74'
    cd.save()

    # Create randint(3, 7) participants for all groups (requires create
    # groups before), and experimental protocols
    for group in Group.objects.all():
        create_experimental_protocol(group)
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
    experiment12 = Experiment.objects.filter(
        status=Experiment.APPROVED).first()
    create_tms_setting(1, experiment12)  # 1º TMSSetting
    tms_setting = TMSSetting.objects.last()
    tms_setting.name = 'tmssettingname'
    tms_setting.save()
    # Create TMSDeviceSetting from a TMSSetting to test search
    # Required creating TMSSetting from experiment Approved, first
    create_tms_device(1)  # 1º TMSDevice
    tms_device = TMSDevice.objects.last()
    tms_device.manufacturer_name = 'Siemens'
    tms_device.save()
    create_coil_model(1)  # 1º CoilModel
    coil_model = CoilModel.objects.last()
    coil_model.name = 'Magstim'
    coil_model.save()
    # 1º TMSDeviceSetting
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)  #
    tms_device_setting = TMSDeviceSetting.objects.last()
    tms_device_setting.pulse_stimulus_type = 'single_pulse'
    tms_device_setting.save()
    # Create another TMSSetting and associate with same TMSDeviceSetting
    # created above to test searching TMSDevice and CoilModel
    create_tms_setting(1, experiment12)  # 2º TMSSetting
    tms_setting = TMSSetting.objects.last()
    # 2º TMSDeviceSetting
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)
    tms_device_setting = TMSDeviceSetting.objects.last()
    tms_device_setting.pulse_stimulus_type = 'single_pulse'
    tms_device_setting.save()
    # Create others TMSDevice and CoilModel associated with TMSDeviceSetting >
    # TMSSetting > Experiment
    create_tms_setting(1, experiment12)  # 3º TMSSetting
    tms_setting = TMSSetting.objects.last()
    # TODO: IMPORTANT! when creating a new TMSDevice and a new CoilModel to
    # TODO: associate with new TMSDeviceSetting, the tests with filters in
    # TODO: test_search fails. See
    create_tms_device(1)  # 2º TMSDevice
    tms_device = TMSDevice.objects.last()
    tms_device.manufacturer_name = 'Siemens'
    tms_device.save()
    create_coil_model(1)  # 2º CoilModel
    coil_model = CoilModel.objects.last()
    coil_model.name = 'Magstim'
    coil_model.save()
    # 3º TMSDeviceSetting
    create_tms_device_setting(1, tms_setting, tms_device, coil_model)
    tms_device_setting = TMSDeviceSetting.objects.last()
    tms_device_setting.pulse_stimulus_type = 'single_pulse'
    tms_device_setting.save()
    # Create TMSData objects to test search
    create_tmsdata_objects_to_test_search()

    # Create Questionnaire objects
    # (requires valid files 'questionnaire1.csv', 'questionnaire2.csv',
    # 'questionnaire3.csv', and their language variations in
    # 'experiments/tests' subdirectory)
    experiment13 = Experiment.objects.filter(
        status=Experiment.APPROVED
    ).last()
    # TODO: not necessary while creating groups
    # TODO: inside create_experiment function. This has to be refactor.
    create_group(2, experiment13)
    group_first = experiment13.groups.first()
    create_questionnaire(1, 'q1', group_first)
    questionnaire1 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire1
    create_questionnaire_language(
        questionnaire1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1.csv',
        'en'
    )
    # create questionnaire language data in French for questionnaire1
    create_questionnaire_language(
        questionnaire1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1_fr.csv',
        'fr'
    )
    # create questionnaire language data in Brazilian Portuguese for
    # questionnaire1
    create_questionnaire_language(
        questionnaire1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1_pt-br.csv',
        'pt-br'
    )

    create_questionnaire(1, 'q2', group_first)
    questionnaire2 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire2
    create_questionnaire_language(
        questionnaire2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2.csv',
        'en'
    )
    # create questionnaire language data in German for questionnaire2
    create_questionnaire_language(
        questionnaire2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2_de.csv',
        'de'
    )

    group_last = experiment13.groups.last()
    create_questionnaire(1, 'q3', group_last)
    questionnaire3 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire3
    create_questionnaire_language(
        questionnaire3,
        settings.BASE_DIR + '/experiments/tests/questionnaire3.csv',
        'en'
    )

    # Create invalid Questionnaire object
    # (requires invalid files 'questionnaire4.csv' in 'experiments/tests'
    # subdirectory)
    experiment = Experiment.objects.filter(
        status=Experiment.APPROVED
    ).first()
    group = experiment.groups.first()
    create_questionnaire(1, 'q4', group)
    questionnaire4 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire4
    create_questionnaire_language(
        questionnaire4,
        settings.BASE_DIR + '/experiments/tests/questionnaire4.csv',
        'en'
    )


def random_utf8_string(length):
    result = b''
    for i in range(length):
        a = b'\\u%04x' % random.randrange(0x10000)
        result = result + a
    result.decode('unicode-escape')
    return result.decode()


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
        status=Experiment.TO_BE_ANALYSED,
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.UNDER_ANALYSIS,
        trustee=models.User.objects.get(username='claudia'),
    )
    experiment3 = Experiment.objects.create(
        title='Experiment 3', nes_id=2, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.TO_BE_ANALYSED,
    )
    experiment4 = Experiment.objects.create(
        title='Experiment 4', nes_id=3, owner=owner1,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.APPROVED,
    )
    experiment5 = Experiment.objects.create(
        title='Experiment 5', nes_id=4, owner=owner2,
        version=1, sent_date=datetime.utcnow(),
        status=Experiment.APPROVED,
    )
    create_ethics_committee_info(experiment3)

    create_group(2, experiment1)
    create_group(1, experiment2)

    # TODO: create with the method already existing. Same for below
    study1 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment1)
    study2 = Study.objects.create(start_date=datetime.utcnow(),
                                  experiment=experiment2)
    # Create a study and doesn't associate it with researcher bellow.
    # This is to testing creating researcher associate it with a study in
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

    # Create valid Questionnaire objects
    # (requires the files 'questionnaire1.csv', 'questionnaire2.csv' and
    # 'questionnaire3.csv' being generated in 'experiments/tests' subdirectory)
    create_group(2, experiment5)
    group_first = experiment5.groups.first()
    create_questionnaire(1, 'q1', group_first)
    questionnaire1 = Questionnaire.objects.last()
    # create questionnaire language data pt-br for questionnaire1
    create_questionnaire_language(
        questionnaire1,
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
        questionnaire1,
        settings.BASE_DIR + '/experiments/tests/questionnaire1_fr.csv',
        # our tests helper always consider 'en' as Default Language,
        # so we create this time as 'pt-br' to test creating questionnaire
        # default language in test_api (by the moment only test_api tests
        # creating questionnaire default language; can expand testing
        # questionnaire related models)
        'fr'
    )

    # create questionnaire language data default for questionnaire2
    create_questionnaire(1, 'q2', group_first)
    questionnaire2 = Questionnaire.objects.last()
    create_questionnaire_language(
        questionnaire2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2.csv', 'en'
    )
    # create questionnaire language data de for questionnaire2
    questionnaire2 = Questionnaire.objects.last()
    create_questionnaire_language(
        questionnaire2,
        settings.BASE_DIR + '/experiments/tests/questionnaire2_de.csv',
        'de'
    )

    group_last = experiment5.groups.last()
    create_questionnaire(1, 'q3', group_last)
    questionnaire3 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire3
    create_questionnaire_language(
        questionnaire3,
        settings.BASE_DIR + '/experiments/tests/questionnaire3.csv',
        'en'
    )

    # create two publications for experiment4
    create_publication(2, experiment4)
    # create one publication for experiment5
    create_publication(1, experiment5)

    # Create invalid Questionnaire object
    # (requires file 'questionnaire4.csv', being generated in
    # 'experiments/tests' subdirectory)
    create_group(1, experiment4)
    group = experiment4.groups.last()
    create_questionnaire(1, 'q4', group)
    # create questionnaire language data default for questionnaire4
    questionnaire4 = Questionnaire.objects.last()
    create_questionnaire_language(
        questionnaire4,
        settings.BASE_DIR + '/experiments/tests/questionnaire4.csv',
        'en'
    )

    # Create an invalid and a valid Questionnaire objects
    # (requires the files 'questionnaire5.csv' and 'questionnaire6.csv,
    # being generated in 'experiments/tests' subdirectory)
    create_group(2, experiment3)
    group = experiment3.groups.first()
    create_questionnaire(1, 'q5', group)
    questionnaire5 = Questionnaire.objects.last()
    # create questionnaire language data default for questionnaire5
    create_questionnaire_language(
        questionnaire5,
        settings.BASE_DIR + '/experiments/tests/questionnaire5.csv',
        'en'
    )
    group = experiment3.groups.last()
    create_questionnaire(1, 'q6', group)
    questionnaire6 = Questionnaire.objects.last()
    create_questionnaire_language(
        questionnaire6,
        settings.BASE_DIR + '/experiments/tests/questionnaire6.csv',
        'en'
    )

    # Create some entries in ClassificationOfDiseases to test adding real codes
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A00'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A1782'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A3681'
    cd.save()
    create_classification_of_deseases(1)
    cd = ClassificationOfDiseases.objects.last()
    cd.code = 'A74'
    cd.save()


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
