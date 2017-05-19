from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime

from experiments.models import Experiment, Study, ProtocolComponent, \
    ExperimentStatus, Group


def global_setup(self):
    """
    This setup creates basic object models that are used in tests bellow.
    :param self: 
    """
    # Create two owners
    owner1 = User.objects.create_user(username='lab1')
    owner2 = User.objects.create_user(username='lab2')

    Study.objects.create(nes_id=1, start_date=datetime.utcnow(), owner=owner1)

    status = ExperimentStatus.objects.create(tag='to_be_approved')

    Experiment.objects.create(nes_id=1, owner=owner1, status=status,
                              version=1, sent_date=datetime.utcnow())
    Experiment.objects.create(nes_id=1, owner=owner2, status=status,
                              version=1, sent_date=datetime.utcnow())


def apply_setup(setup_func):
    """
    Defines a decorator that uses my_setup method.
    :param setup_func: my_setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap

# class ResearcherModelTest(TestCase):
#
#     def test_default_attributes(self):
#         researcher = Researcher()
#         self.assertEqual(researcher.first_name, '')
#         self.assertEqual(researcher.surname, '')
#         self.assertEqual(researcher.email, '')
#         self.assertEqual(researcher.nes_id, None)
#
#     def test_cannot_save_empty_attributes(self):
#         researcher = Researcher(nes_id=None)
#         with self.assertRaises(ValidationError):
#             researcher.full_clean()
#
#     def test_duplicate_researchers_are_invalid(self):
#         owner = User.objects.create_user(username='lab1')
#         create_researcher(nes_id=1, owner=owner)
#         researcher2 = Researcher(nes_id=1, owner=owner)
#         with self.assertRaises(ValidationError):
#             researcher2.full_clean()
#
#     def test_CAN_save_same_researcher_to_different_owners(self):
#         owner1 = User.objects.create_user(username='lab1')
#         owner2 = User.objects.create_user(username='lab2')
#         Researcher.objects.create(nes_id=1, owner=owner1)
#         researcher = Researcher(nes_id=1, owner=owner2)
#         researcher.full_clean()
#
#     def test_researcher_is_related_to_owner(self):
#         owner = User.objects.create_user(username='lab1')
#         researcher = Researcher(nes_id=1, owner=owner)
#         researcher.save()
#         self.assertIn(researcher, owner.researcher_set.all())


class ExperimentStatusModelTest(TestCase):
    def test_default_attributes(self):
        experiment_st = ExperimentStatus()
        self.assertEqual(experiment_st.tag, '')
        self.assertEqual(experiment_st.name, '')
        self.assertEqual(experiment_st.description, '')

    def test_cannot_save_empty_attributes(self):
        experiment_st = ExperimentStatus(tag='')
        with self.assertRaises(ValidationError):
            experiment_st.save()
            experiment_st.full_clean()


class StudyModelTest(TestCase):

    def test_default_attributes(self):
        study = Study()
        self.assertEqual(study.title, '')
        self.assertEqual(study.description, '')
        self.assertEqual(study.start_date, None)
        self.assertEqual(study.end_date, None)
        self.assertEqual(study.nes_id, None)

    def test_cannot_save_empty_attributes(self):
        study = Study(title='', description='', start_date='')
        with self.assertRaises(ValidationError):
            study.save()
            study.full_clean()

    def test_duplicate_studies_are_invalid(self):
        owner = User.objects.create_user(username='lab1')
        Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                             owner=owner)
        study = Study(nes_id=1, start_date=datetime.utcnow(), owner=owner)
        with self.assertRaises(ValidationError):
            study.full_clean()

    def test_CAN_save_same_study_to_different_owners(self):
        owner1 = User.objects.create(username='lab1')
        owner2 = User.objects.create(username='lab2')
        Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                             owner=owner1)
        study = Study(title='A title', description='A description', nes_id=1,
                      start_date=datetime.utcnow(), end_date=datetime.utcnow(),
                      owner=owner2)
        study.full_clean()

    def test_study_is_related_to_owner(self):
        owner = User.objects.create(username='lab1')
        study = Study(nes_id=1, start_date=datetime.utcnow(), owner=owner)
        study.save()
        self.assertIn(study, owner.study_set.all())


@apply_setup(global_setup)
class ExperimentModelTest(TestCase):

    def setUp(self):
        global_setup(self)

    def test_default_attributes(self):
        experiment = Experiment()
        self.assertEqual(experiment.nes_id, None)
        self.assertEqual(experiment.title, '')
        self.assertEqual(experiment.description, '')
        self.assertEqual(experiment.data_acquisition_done, False)
        self.assertEqual(experiment.ethics_committee_file, '')
        self.assertEqual(experiment.sent_date, None)
        self.assertEqual(experiment.version, None)

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.first()
        status = ExperimentStatus.objects.first()
        # version=17 to avoid conflicts with global setup
        experiment = Experiment(
            nes_id=1, title='', description='', owner=owner,
            status=status, version=17, sent_date=datetime.utcnow()
        )
        with self.assertRaises(ValidationError):
            experiment.save()
            experiment.full_clean()

    def test_duplicate_experiments_are_invalid(self):
        owner = User.objects.first()
        status = ExperimentStatus.objects.first()
        Experiment.objects.create(nes_id=17, owner=owner, status=status,
                                  version=1, sent_date=datetime.utcnow())
        experiment = Experiment(nes_id=17, owner=owner, status=status,
                                version=1, sent_date=datetime.utcnow())
        with self.assertRaises(ValidationError):
            experiment.full_clean()

    def test_CAN_save_same_experiment_to_different_owners(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        status = ExperimentStatus.objects.get(tag='to_be_approved')
        Experiment.objects.create(
            title='A title', description='A description', nes_id=1,
            owner=owner1, status=status, version=17,
            sent_date=datetime.utcnow()
        )
        experiment2 = Experiment(title='A title', description='A description',
                                 nes_id=1, owner=owner2,
                                 status=status, version=17,
                                 sent_date=datetime.utcnow())
        experiment2.full_clean()

    def test_experiment_is_related_owner_and_status(self):
        owner = User.objects.first()
        status = ExperimentStatus.objects.get(tag='to_be_approved')
        experiment = Experiment(nes_id=17, owner=owner, status=status,
                                version=1, sent_date=datetime.utcnow())
        experiment.save()
        self.assertIn(experiment, owner.experiment_set.all())
        self.assertIn(experiment, status.experiments.all())

    def test_experiment_has_one_study(self):
        pass  # TODO


@apply_setup(global_setup)
class ProtocolComponentModelTest(TestCase):

    def setUp(self):
        global_setup(self)

    def test_default_attributes(self):
        protocol_component = ProtocolComponent()
        self.assertEqual(protocol_component.identification, '')
        self.assertEqual(protocol_component.description, '')
        self.assertEqual(protocol_component.duration_value, None)
        self.assertEqual(protocol_component.component_type, '')
        self.assertEqual(protocol_component.nes_id, None)

    def test_protocol_component_is_related_to_experiment_and_owner(self):
        owner = User.objects.first()
        experiment = Experiment.objects.first()
        protocolcomponent = ProtocolComponent(
            identification='An identification',
            component_type='A component type',
            nes_id=1, experiment=experiment, owner=owner
        )
        protocolcomponent.save()
        self.assertIn(protocolcomponent, experiment.protocol_components.all())
        self.assertIn(protocolcomponent, owner.protocolcomponent_set.all())

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.last()
        experiment = Experiment.objects.first()
        protocol_component = ProtocolComponent(
            identification='', component_type='', nes_id=1,
            experiment=experiment, owner=owner
        )
        with self.assertRaises(ValidationError):
            protocol_component.save()
            protocol_component.full_clean()

    def test_duplicate_protocol_components_are_invalid(self):
        owner = User.objects.last()
        experiment = Experiment.objects.first()
        ProtocolComponent.objects.create(nes_id=1, experiment=experiment,
                                         owner=owner)
        protocol_component = ProtocolComponent(
            nes_id=1, identification='An identification',
            duration_value=10, component_type='A component type',
            experiment=experiment, owner=owner
        )
        with self.assertRaises(ValidationError):
            protocol_component.full_clean()

    def test_CAN_save_same_protocol_components_to_different_owners(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        experiment1 = Experiment.objects.get(owner=owner1)
        experiment2 = Experiment.objects.get(owner=owner2)
        ProtocolComponent.objects.create(
            nes_id=1, experiment=experiment1, owner=owner1
        )
        protocol_component = ProtocolComponent(
            nes_id=1, identification='An identification',
            duration_value=10, component_type='A component type',
            experiment=experiment2, owner=owner2,
        )
        protocol_component.full_clean()


@apply_setup(global_setup)
class GroupModelTest(TestCase):

    def setUp(self):
        global_setup(self)

    def test_default_attributes(self):
        group = Group()
        self.assertEqual(group.title, '')
        self.assertEqual(group.description, '')
        self.assertEqual(group.nes_id, None)

    def test_group_is_related_to_experiment_and_owner(self):
        owner = User.objects.first()
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment, owner=owner
        )
        self.assertIn(group, experiment.groups.all())
        self.assertIn(group, owner.group_set.all())

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.first()
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='', description='', nes_id=1,
            experiment=experiment, owner=owner
        )
        with self.assertRaises(ValidationError):
            group.save()
            group.full_clean()

    def test_duplicate_groups_are_invalid(self):
        owner = User.objects.first()
        experiment = Experiment.objects.first()
        Group.objects.create(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment, owner=owner
        )
        group = Group(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment, owner=owner
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_CAN_save_same_groups_to_different_owners(self):
        owner1 = User.objects.first()
        owner2 = User.objects.last()
        experiment1 = Experiment.objects.first()
        experiment2 = Experiment.objects.last()
        Group.objects.create(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment1, owner=owner1
        )
        group = Group(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment2, owner=owner2
        )
        group.full_clean()
