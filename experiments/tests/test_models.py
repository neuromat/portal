from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime

from experiments.models import Experiment, Study, ProtocolComponent, Group
from experiments.tests.tests_helper import global_setup_ut, apply_setup

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


# class ExperimentStatusModelTest(TestCase):
#     def test_default_attributes(self):
#         experiment_st = ExperimentStatus()
#         self.assertEqual(experiment_st.tag, '')
#         self.assertEqual(experiment_st.name, '')
#         self.assertEqual(experiment_st.description, '')
#
#     def test_cannot_save_empty_attributes(self):
#         experiment_st = ExperimentStatus(tag='')
#         with self.assertRaises(ValidationError):
#             experiment_st.save()
#             experiment_st.full_clean()


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

    def test_duplicate_studies_are_invalid(self):
        experiment = Experiment.objects.last()
        study = Study(start_date=datetime.utcnow(),
                      experiment=experiment)
        with self.assertRaises(ValidationError):
            study.full_clean()

    # def test_CAN_save_same_study_to_different_owners(self):
    #     # TODO: maybe not necessary anymore
    #     owner2 = User.objects.last()
    #     experiment = Experiment.objects.last()
    #     study = Study(title='A title', description='A description', nes_id=1,
    #                   start_date=datetime.utcnow(), end_date=datetime.utcnow(),
    #                   experiment=experiment, owner=owner2)
    #     study.full_clean()

    # TODO: adapt test so we see if study is related to experiment owner
    # def test_study_is_related_to_owner(self):
    #     owner = User.objects.first()
    #     experiment = Experiment.objects.last()
    #     study = Study(start_date=datetime.utcnow(), experiment=experiment)
    #     study.save()
    #     self.assertIn(study, owner.study_set.all())

    def test_study_has_one_experiment(self):
        # TODO: this test is incomplete. Finish it!
        owner = User.objects.first()
        experiment = Experiment.objects.first()
        study1 = Study.objects.first()
        study2 = Study(start_date=datetime.utcnow(),
                       experiment=experiment)


@apply_setup(global_setup_ut)
class ExperimentModelTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        experiment = Experiment()
        self.assertEqual(experiment.nes_id, None)
        self.assertEqual(experiment.title, '')
        self.assertEqual(experiment.description, '')
        self.assertEqual(experiment.data_acquisition_done, False)
        self.assertEqual(experiment.ethics_committee_file, '')
        self.assertEqual(experiment.sent_date, None)
        self.assertEqual(experiment.version, None)
        self.assertEqual(experiment.status, experiment.RECEIVING)

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

    def test_CAN_save_same_experiment_to_different_owners(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        Experiment.objects.create(
            title='A title', description='A description', nes_id=1,
            owner=owner1, version=17,
            sent_date=datetime.utcnow()
        )
        experiment2 = Experiment(title='A title', description='A description',
                                 nes_id=1, owner=owner2,
                                 version=17,
                                 sent_date=datetime.utcnow())
        experiment2.full_clean()

    def test_experiment_is_related_to_owner(self):
        owner = User.objects.first()
        experiment = Experiment(nes_id=17, owner=owner,
                                version=1, sent_date=datetime.utcnow())
        experiment.save()
        self.assertIn(experiment, owner.experiment_set.all())


# @apply_setup(global_setup_ut)
# class ProtocolComponentModelTest(TestCase):
#
#     def setUp(self):
#         global_setup_ut()
#
#     def test_default_attributes(self):
#         protocol_component = ProtocolComponent()
#         self.assertEqual(protocol_component.identification, '')
#         self.assertEqual(protocol_component.description, '')
#         self.assertEqual(protocol_component.duration_value, None)
#         self.assertEqual(protocol_component.component_type, '')
#         self.assertEqual(protocol_component.nes_id, None)
#
#     def test_protocol_component_is_related_to_experiment_and_owner(self):
#         owner = User.objects.first()
#         experiment = Experiment.objects.first()
#         protocolcomponent = ProtocolComponent(
#             identification='An identification',
#             component_type='A component type',
#             nes_id=1, experiment=experiment, owner=owner
#         )
#         protocolcomponent.save()
#         self.assertIn(protocolcomponent, experiment.protocol_components.all())
#         self.assertIn(protocolcomponent, owner.protocolcomponent_set.all())
#
#     def test_cannot_save_empty_attributes(self):
#         owner = User.objects.last()
#         experiment = Experiment.objects.first()
#         protocol_component = ProtocolComponent(
#             identification='', component_type='', nes_id=1,
#             experiment=experiment, owner=owner
#         )
#         with self.assertRaises(ValidationError):
#             protocol_component.save()
#             protocol_component.full_clean()
#
#     def test_duplicate_protocol_components_are_invalid(self):
#         owner = User.objects.last()
#         experiment = Experiment.objects.first()
#         ProtocolComponent.objects.create(nes_id=1, experiment=experiment,
#                                          owner=owner)
#         protocol_component = ProtocolComponent(
#             nes_id=1, identification='An identification',
#             duration_value=10, component_type='A component type',
#             experiment=experiment, owner=owner
#         )
#         with self.assertRaises(ValidationError):
#             protocol_component.full_clean()
#
#     def test_CAN_save_same_protocol_components_to_different_owners(self):
#         owner1 = User.objects.get(username='lab1')
#         owner2 = User.objects.get(username='lab2')
#         experiment1 = Experiment.objects.get(owner=owner1)
#         experiment2 = Experiment.objects.get(owner=owner2)
#         ProtocolComponent.objects.create(
#             nes_id=1, experiment=experiment1, owner=owner1
#         )
#         protocol_component = ProtocolComponent(
#             nes_id=1, identification='An identification',
#             duration_value=10, component_type='A component type',
#             experiment=experiment2, owner=owner2,
#         )
#         protocol_component.full_clean()


@apply_setup(global_setup_ut)
class GroupModelTest(TestCase):

    def setUp(self):
        global_setup_ut()

    def test_default_attributes(self):
        group = Group()
        self.assertEqual(group.title, '')
        self.assertEqual(group.description, '')
        self.assertEqual(group.nes_id, None)

    def test_group_is_related_to_experiment(self):
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment
        )
        self.assertIn(group, experiment.groups.all())

    def test_cannot_save_empty_attributes(self):
        experiment = Experiment.objects.first()
        group = Group.objects.create(
            title='', description='', nes_id=1,
            experiment=experiment
        )
        with self.assertRaises(ValidationError):
            group.save()
            group.full_clean()

    def test_duplicate_groups_are_invalid(self):
        experiment = Experiment.objects.first()
        Group.objects.create(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment
        )
        group = Group(
            title='Group A', description='A description', nes_id=1,
            experiment=experiment
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    # def test_CAN_save_same_groups_to_different_owners(self):
    #     # TODO: maybe not necessary anymore
    #     owner1 = User.objects.first()
    #     owner2 = User.objects.last()
    #     experiment1 = Experiment.objects.first()
    #     experiment2 = Experiment.objects.last()
    #     Group.objects.create(
    #         title='Group A', description='A description', nes_id=1,
    #         experiment=experiment1, owner=owner1
    #     )
    #     group = Group(
    #         title='Group A', description='A description', nes_id=1,
    #         experiment=experiment2, owner=owner2
    #     )
    #     group.full_clean()
