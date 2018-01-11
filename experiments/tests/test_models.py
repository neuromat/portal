import tempfile
from random import randint

import os

import shutil
from django.template.defaultfilters import slugify
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime
from faker import Factory

from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, RejectJustification, Publication, ExperimentalProtocol, Step, \
    StepAdditionalFile, Gender, File
from experiments.tests.tests_helper import global_setup_ut, apply_setup, \
    create_experiment, create_group, create_binary_file, create_eeg_setting, \
    create_eeg_electrode_localization_system, create_context_tree, create_step, \
    create_stimulus_step, create_experimental_protocol, create_tms_setting, \
    create_tms_data, create_participant, create_genders, create_eeg_data, \
    create_eeg_step, create_emg_step, create_emg_setting, create_emg_data, \
    create_goal_keeper_game_step, create_goal_keeper_game_data, \
    create_generic_data_collection_step, create_generic_data_collection_data, \
    create_additional_data, create_emg_electrode_placement


def add_temporary_file_to_file_instance(file_instance):
    """
    Create temporary file to add to file instance
    :param file_instance:  model related file instance to add a file
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        bin_file = create_binary_file(tmpdirname)
        with open(bin_file.name, 'rb') as f:
            file_instance.save('file.bin', f)


def create_model_instances_to_test_step_type_data():
    experiment = create_experiment(1)
    group = create_group(1, experiment)
    create_genders()
    participant = create_participant(
        1, group, Gender.objects.order_by('?').first()
    )
    return {
        'experiment': experiment, 'group': group, 'participant': participant
    }


def create_file_collected(qtty, step_type):
    """
    Return object if qtty = 1 or list of objects if qtty > 1
    :param qtty: number of files collected to be created
    :param step_type: DataCollection Step type to wich files are collected
    :return: object or list
    """
    files_collected = []
    for i in range(qtty):
        file_collected = File.objects.create()
        add_temporary_file_to_file_instance(file_collected.file)
        step_type.files.add(file_collected)
        files_collected.append(file_collected)
    if len(files_collected) == 1:
        return files_collected[0]
    return files_collected


@apply_setup(global_setup_ut)
class ResearcherModelTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        researcher = Researcher()
        self.assertEqual(researcher.name, '')
        self.assertEqual(researcher.email, '')

    def test_researcher_is_related_to_one_study(self):
        study = Study.objects.last()
        researcher = Researcher(study=study)
        researcher.save()
        self.assertEqual(researcher, study.researcher)

    def test_cannot_save_empty_attributes(self):
        researcher = Researcher(study=Study.objects.first())
        with self.assertRaises(ValidationError):
            researcher.full_clean()

    # TODO: test cannot save researcher without study


@apply_setup(global_setup_ut)
class StudyModelTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        study = Study()
        self.assertEqual(study.title, '')
        self.assertEqual(study.description, '')
        self.assertEqual(study.start_date, None)
        self.assertEqual(study.end_date, None)

    def test_cannot_save_empty_attributes(self):
        study = Study(title='', description='', start_date='')
        with self.assertRaises(ValidationError):
            study.save()
            study.full_clean()

    def test_study_has_only_one_experiment(self):
        # Valid because in tests_helper.py we are creating experiments tied
        # with studies
        experiment = Experiment.objects.last()
        study = Study(start_date=datetime.utcnow(),
                      experiment=experiment)
        with self.assertRaises(ValidationError):
            study.full_clean()


@apply_setup(global_setup_ut)
class ExperimentModelTest(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def setUp(self):
        global_setup_ut()

    def tearDown(self):
        # used only when testing deleting files
        if os.path.exists(self.TEMP_MEDIA_ROOT):
            shutil.rmtree(self.TEMP_MEDIA_ROOT)

    def test_default_attributes(self):
        experiment = Experiment()
        self.assertEqual(experiment.nes_id, None)
        self.assertEqual(experiment.title, '')
        self.assertEqual(experiment.description, '')
        self.assertEqual(experiment.data_acquisition_done, False)
        self.assertEqual(experiment.sent_date, None)
        self.assertEqual(experiment.version, None)
        self.assertEqual(experiment.status, experiment.RECEIVING)
        self.assertEqual(experiment.trustee, None)
        self.assertEqual(experiment.project_url, None)
        self.assertEqual(experiment.ethics_committee_url, None)
        self.assertEqual(experiment.ethics_committee_file, None)
        self.assertEqual(experiment.slug, '')
        self.assertEqual(experiment.downloads, 0)

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.first()
        # version=17: large number to avoid conflicts with global setup
        experiment = Experiment(
            nes_id=1, title='', description='', owner=owner,
            version=17, sent_date=datetime.utcnow()
        )
        with self.assertRaises(ValidationError):
            experiment.save()
            experiment.full_clean()

    def test_duplicate_experiments_are_invalid(self):
        owner = User.objects.first()
        Experiment.objects.create(nes_id=17, owner=owner,
                                  version=1, sent_date=datetime.utcnow())
        experiment = Experiment(nes_id=17, owner=owner,
                                version=1, sent_date=datetime.utcnow())
        with self.assertRaises(ValidationError):
            experiment.full_clean()

    def test_can_save_same_experiment_to_different_owners(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        Experiment.objects.create(
            title='A title', description='A description', nes_id=1,
            owner=owner1, version=17,
            sent_date=datetime.utcnow(),
            slug='slug6'  # last slug in tests_helper was 'slug'
        )
        experiment2 = Experiment(title='A title', description='A description',
                                 nes_id=1, owner=owner2,
                                 version=17,
                                 sent_date=datetime.utcnow(),
                                 slug='slug7')
        experiment2.full_clean()

    def test_experiment_is_related_to_owner(self):
        owner = User.objects.first()
        experiment = Experiment(nes_id=17, owner=owner,
                                version=1, sent_date=datetime.utcnow())
        experiment.save()
        self.assertIn(experiment, owner.experiment_set.all())

    def test_cannot_create_experiment_with_same_slug(self):
        fake = Factory.create()

        # slugs are automatically created in Experiment model when it's the
        # first saving; so we have to save two instances, and after modify
        # slug field to be the same, and only then try to save.
        e1 = Experiment.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            nes_id=randint(1, 10000),
            owner=User.objects.get(username='lab1'),
            version=1, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        e1.slug = 'same-slug'
        e1.save()
        e2 = Experiment.objects.create(
            title=fake.text(max_nb_chars=15),
            description=fake.text(max_nb_chars=200),
            nes_id=randint(1, 10000),
            owner=User.objects.get(username='lab1'),
            version=1,
            sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        e2.slug = 'same-slug'

        with self.assertRaises(ValidationError):
            e2.full_clean()

    def test_creating_experiment_creates_predefined_slug(self):
        fake = Factory.create()

        experiments_now = Experiment.objects.all().count()

        # create experiment: nes_id 1, owner lab1, first version
        e1 = Experiment.objects.create(
            title='This is a slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 1,
            owner=User.objects.get(username='lab1'),
            version=1, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e1.title), e1.slug)

        # create experiment: nes_id 1, owner lab1, second version,
        # title unaltered
        e2 = Experiment.objects.create(
            title='This is a slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 1,
            owner=User.objects.get(username='lab1'),
            version=2, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e1.title) + '-v2', e2.slug)

        # create experiment: nes_id 1, owner lab1, third version, title altered
        e3 = Experiment.objects.create(
            title='This is another slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 1,
            owner=User.objects.get(username='lab1'),
            version=3, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e1.title) + '-v3', e3.slug)

        # create experiment: nes_id 2, owner lab2, first version,
        # existing title from other experiment
        e4 = Experiment.objects.create(
            title='This is a slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 2,
            owner=User.objects.get(username='lab2'),
            version=1, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e4.title) + '-2', e4.slug)

        # create experiment: nes_id 2, owner lab2, second version,
        # title unaltered
        e5 = Experiment.objects.create(
            title='This is a slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 2,
            owner=User.objects.get(username='lab2'),
            version=2, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e4.title) + '-2-v2', e5.slug)

        # create experiment: nes_id 2, owner lab2, third version,
        # title unaltered
        e6 = Experiment.objects.create(
            title='This is a slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 2,
            owner=User.objects.get(username='lab2'),
            version=3, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e4.title) + '-2-v3', e6.slug)

        # create experiment: nes_id 3, owner lab2, first version,
        # non-existing title from other experiment
        e7 = Experiment.objects.create(
            title='This is one more slug',
            description=fake.text(max_nb_chars=200),
            nes_id=experiments_now + 3,
            owner=User.objects.get(username='lab2'),
            version=1, sent_date=datetime.utcnow(),
            status=Experiment.TO_BE_ANALYSED,
            data_acquisition_done=True,
        )
        self.assertEqual(slugify(e7.title), e7.slug)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_its_files(self):
        experiment = create_experiment(1)

        file_instance = experiment.ethics_committee_file
        add_temporary_file_to_file_instance(file_instance)

        experiment.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


@apply_setup(global_setup_ut)
class GroupModelTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        group = Group()
        self.assertEqual(group.title, '')
        self.assertEqual(group.description, '')

    def test_group_is_related_to_experiment(self):
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='Group A', description='A description',
            experiment=experiment
        )
        self.assertIn(group, experiment.groups.all())

    def test_cannot_save_empty_attributes(self):
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='', description='',
            experiment=experiment
        )
        with self.assertRaises(ValidationError):
            group.save()
            group.full_clean()


@apply_setup(global_setup_ut)
class CollaboratorModel(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        collaborator = Collaborator()
        self.assertEqual(collaborator.name, '')
        self.assertEqual(collaborator.team, '')
        self.assertEqual(collaborator.coordinator, False)

    def test_collaborator_is_related_to_study(self):
        study = Study.objects.first()
        collaborator = Collaborator.objects.create(
            name='Joãzinho trinta', team='Viradouro', study=study
        )
        self.assertIn(collaborator, study.collaborators.all())

    def test_cannot_save_empty_attributes(self):
        study = Study.objects.first()
        collaborator = Collaborator.objects.create(
            name='', team='', study=study
        )
        with self.assertRaises(ValidationError):
            collaborator.save()
            collaborator.full_clean()


@apply_setup(global_setup_ut)
class RejectJustificationModel(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        justification = RejectJustification()
        self.assertEqual(justification.message, '')

    def test_cannot_save_empty_attributes(self):
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS).first()
        justification = RejectJustification.objects.create(
            message='', experiment=experiment
        )
        with self.assertRaises(ValidationError):
            justification.save()
            justification.full_clean()

    def test_justification_message_is_related_to_one_experiment(self):
        experiment = Experiment.objects.filter(
            status=Experiment.UNDER_ANALYSIS).first()
        justification = RejectJustification(
            message='A justification', experiment=experiment
        )
        justification.save()
        self.assertEqual(justification, experiment.justification)


@apply_setup(global_setup_ut)
class PublicationModel(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        publication = Publication()
        self.assertEqual(publication.title, '')
        self.assertEqual(publication.citation, '')
        self.assertEqual(publication.url, None)

    def test_publication_is_related_to_experiment(self):
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).first()
        publication = Publication(
            title='Ein Titel', citation='Ein Zitat', experiment=experiment
        )
        publication.save()
        self.assertIn(publication, experiment.publications.all())

    def test_cannot_save_empty_attributes(self):
        experiment = Experiment.objects.filter(
            status=Experiment.TO_BE_ANALYSED
        ).first()
        publication = Publication(title='', citation='', experiment=experiment)
        with self.assertRaises(ValidationError):
            publication.save()
            publication.full_clean()


@apply_setup(global_setup_ut)
class ExperimentalProtocolModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def setUp(self):
        global_setup_ut()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.create_user(
            username='labor',
            password='nep-labor'
        )
        experiment = create_experiment(
            1, owner=owner, status=Experiment.TO_BE_ANALYSED
        )
        group = create_group(1, experiment)
        experimental_protocol = ExperimentalProtocol(group=group)
        with self.assertRaises(ValidationError):
            experimental_protocol.save()
            experimental_protocol.full_clean()

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        experiment = create_experiment(1)
        group = create_group(1, experiment)
        experimental_protocol = create_experimental_protocol(group)

        file_instance = experimental_protocol.image
        add_temporary_file_to_file_instance(file_instance)

        experimental_protocol.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


class EEGElectrodeLocalizationSystemModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        experiment = create_experiment(1)
        eeg_setting = create_eeg_setting(1, experiment)
        eeg_electrode_localization_system = \
            create_eeg_electrode_localization_system(eeg_setting)

        file_instance = eeg_electrode_localization_system.map_image_file
        add_temporary_file_to_file_instance(file_instance)

        eeg_electrode_localization_system.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


class EEGDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_instances_and_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        eeg_setting = create_eeg_setting(1, model_instances_dict['experiment'])
        eeg_step = create_eeg_step(model_instances_dict['group'], eeg_setting)
        eeg_data = create_eeg_data(
            eeg_setting, eeg_step, model_instances_dict['participant']
        )

        files_collected = create_file_collected(2, eeg_data)

        eeg_data.delete()
        self.assertFalse(File.objects.exists())
        for file_collected in files_collected:
            self.assertFalse(
                os.path.exists(os.path.join(
                    self.TEMP_MEDIA_ROOT, file_collected.file.name
                ))
            )


class EMGDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_instances_and_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        emg_setting = create_emg_setting(model_instances_dict['experiment'])
        emg_step = create_emg_step(model_instances_dict['group'], emg_setting)
        emg_data = create_emg_data(
            emg_setting, emg_step, model_instances_dict['participant']
        )

        files_collected = create_file_collected(2, emg_data)

        emg_data.delete()
        self.assertFalse(File.objects.exists())
        for file_collected in files_collected:
            self.assertFalse(
                os.path.exists(os.path.join(
                    self.TEMP_MEDIA_ROOT, file_collected.file.name
                ))
            )


class EMGElectrodePlacementModelTest(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.TEMP_MEDIA_ROOT):
            shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_its_files(self):
        emg_electrode_placement = create_emg_electrode_placement()

        file_instance = emg_electrode_placement.photo
        add_temporary_file_to_file_instance(file_instance)

        emg_electrode_placement.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


class GoalkeeperGameDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_instances_and_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        context_tree = create_context_tree(model_instances_dict['experiment'])
        goal_keeper_game_step = create_goal_keeper_game_step(
            model_instances_dict['group'], context_tree
        )
        goal_keeper_game_data = create_goal_keeper_game_data(
            goal_keeper_game_step, model_instances_dict['participant']
        )

        files_collected = create_file_collected(2, goal_keeper_game_data)

        goal_keeper_game_data.delete()
        self.assertFalse(File.objects.exists())
        for file_collected in files_collected:
            self.assertFalse(
                os.path.exists(os.path.join(
                    self.TEMP_MEDIA_ROOT, file_collected.file.name
                ))
            )


class GenericDataCollectionDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_instances_and_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        generic_data_collection_step = create_generic_data_collection_step(
            group=model_instances_dict['group']
        )
        generic_data_collection_data = create_generic_data_collection_data(
            generic_data_collection_step, model_instances_dict['participant']
        )

        files_collected = create_file_collected(2, generic_data_collection_data)

        generic_data_collection_data.delete()
        self.assertFalse(File.objects.exists())
        for file_collected in files_collected:
            self.assertFalse(
                os.path.exists(os.path.join(
                    self.TEMP_MEDIA_ROOT, file_collected.file.name
                ))
            )


class AdditionalDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_instances_and_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        additional_data = create_additional_data(
            model_instances_dict['participant']
        )

        files_collected = create_file_collected(2, additional_data)

        additional_data.delete()
        self.assertFalse(File.objects.exists())
        for file_collected in files_collected:
            self.assertFalse(
                os.path.exists(os.path.join(
                    self.TEMP_MEDIA_ROOT, file_collected.file.name
                ))
            )


class TMSDataModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        model_instances_dict = create_model_instances_to_test_step_type_data()
        tms_setting = create_tms_setting(1, model_instances_dict['experiment'])
        tms_data = create_tms_data(
            1, tms_setting, model_instances_dict['participant']
        )

        file_instance_1 = tms_data.hot_spot_map
        add_temporary_file_to_file_instance(file_instance_1)
        file_instance_2 = tms_data.localization_system_image
        add_temporary_file_to_file_instance(file_instance_2)

        tms_data.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance_1.name
            ))
        )
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance_2.name
            ))
        )


class ContextTreeModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        experiment = create_experiment(1)
        context_tree = create_context_tree(experiment)

        file_instance = context_tree.setting_file
        add_temporary_file_to_file_instance(file_instance)

        context_tree.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


class StepAdditionalFileModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        experiment = create_experiment(1)
        group = create_group(1, experiment)
        step = create_step(1, group, Step.EEG)
        step_additional_file = StepAdditionalFile.objects.create(
            step=step
        )

        file_instance = step_additional_file.file
        add_temporary_file_to_file_instance(file_instance)

        step_additional_file.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )


class StimulusModel(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_delete_instance_deletes_related_files(self):
        experiment = create_experiment(1)
        group = create_group(1, experiment)
        stimulus = create_stimulus_step(1, group)

        file_instance = stimulus.media_file
        add_temporary_file_to_file_instance(file_instance)

        stimulus.delete()
        self.assertFalse(
            os.path.exists(os.path.join(
                self.TEMP_MEDIA_ROOT, file_instance.name
            ))
        )
