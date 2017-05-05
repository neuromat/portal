from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime

from experiments.models import Experiment, Study, Researcher, \
    ProtocolComponent, ExperimentVersion


def create_researcher(nes_id, owner):
    """
    Creates researcher model object that are used
    in test classes that depends on it. 
    """
    return Researcher.objects.create(nes_id=nes_id, owner=owner)


def create_study(nes_id, owner):
    """
    Creates study model object that are used
    in test classes that depends on it. 
    """
    researcher = create_researcher(nes_id=nes_id, owner=owner)
    return Study.objects.create(nes_id=nes_id, start_date=datetime.utcnow(),
                                researcher=researcher, owner=researcher.owner)


def create_experiment(nes_id, owner):
    """
    Creates experiment model object that are used
    in test classes that depends on it. 
    """
    study = create_study(nes_id=nes_id, owner=owner)
    return Experiment.objects.create(nes_id=nes_id, study=study,
                                     owner=study.owner)


class ResearcherModelTest(TestCase):

    def test_default_attributes(self):
        researcher = Researcher()
        self.assertEqual(researcher.first_name, '')
        self.assertEqual(researcher.surname, '')
        self.assertEqual(researcher.email, '')
        self.assertEqual(researcher.nes_id, None)

    def test_cannot_save_empty_attributes(self):
        researcher = Researcher(nes_id=None)
        with self.assertRaises(ValidationError):
            researcher.full_clean()

    def test_duplicate_researchers_are_invalid(self):
        owner = User.objects.create_user(username='lab1')
        create_researcher(nes_id=1, owner=owner)
        researcher2 = Researcher(nes_id=1, owner=owner)
        with self.assertRaises(ValidationError):
            researcher2.full_clean()

    def test_CAN_save_same_researcher_to_different_owners(self):
        owner1 = User.objects.create_user(username='lab1')
        owner2 = User.objects.create_user(username='lab2')
        Researcher.objects.create(nes_id=1, owner=owner1)
        researcher = Researcher(nes_id=1, owner=owner2)
        researcher.full_clean()

    def test_researcher_is_related_to_owner(self):
        owner = User.objects.create_user(username='lab1')
        researcher = Researcher(nes_id=1, owner=owner)
        researcher.save()
        self.assertIn(researcher, owner.researcher_set.all())


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
        researcher1 = Researcher.objects.create(nes_id=1, owner=owner)
        researcher2 = Researcher.objects.create(nes_id=2, owner=owner)
        Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                             researcher=researcher1, owner=owner)
        study = Study(nes_id=1, start_date=datetime.utcnow(),
                      researcher=researcher2, owner=owner)
        with self.assertRaises(ValidationError):
            study.full_clean()

    def test_CAN_save_same_study_to_different_owners(self):
        owner1 = User.objects.create(username='lab1')
        owner2 = User.objects.create(username='lab2')
        researcher1 = create_researcher(nes_id=1, owner=owner1)
        researcher2 = create_researcher(nes_id=1, owner=owner2)
        Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                             researcher=researcher1, owner=researcher1.owner)
        study = Study(title='A title', description='A description', nes_id=1,
                      start_date=datetime.utcnow(),
                      end_date=datetime.utcnow(),
                      researcher=researcher2, owner=researcher2.owner)
        study.full_clean()

    def test_study_is_related_to_researcher_and_owner(self):
        owner = User.objects.create(username='lab1')
        researcher = create_researcher(nes_id=1, owner=owner)
        study = Study(nes_id=1, start_date=datetime.utcnow(),
                      researcher=researcher, owner=owner)
        study.save()
        self.assertIn(study, researcher.studies.all())
        self.assertIn(study, owner.study_set.all())


class ExperimentModelTest(TestCase):

    def test_default_attributes(self):
        experiment = Experiment()
        self.assertEqual(experiment.title, '')
        self.assertEqual(experiment.description, '')
        self.assertEqual(experiment.data_acquisition_done, False)
        self.assertEqual(experiment.nes_id, None)

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.create(username='lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        study = Study.objects.create(
            nes_id=1, start_date=datetime.utcnow(), researcher=researcher,
            owner=owner)
        # TODO: why we need to pass nes_id, study and owner and in
        # StudyModelTest's test_cannot_save_empty_attributes not?
        experiment = Experiment(
            nes_id=1, title='', description='', study=study, owner=owner
        )
        with self.assertRaises(ValidationError):
            experiment.save()
            experiment.full_clean()

    def test_duplicate_experiments_are_invalid(self):
        owner = User.objects.create_user(username='lab2')
        study = create_study(nes_id=1, owner=owner)
        Experiment.objects.create(nes_id=1, study=study, owner=owner)
        experiment = Experiment(nes_id=1, study=study, owner=owner)
        with self.assertRaises(ValidationError):
            experiment.full_clean()

    def test_CAN_save_same_experiment_to_different_owners(self):
        owner1 = User.objects.create_user(username='lab1')
        owner2 = User.objects.create_user(username='lab2')
        study2 = create_study(nes_id=1, owner=owner2)
        create_experiment(nes_id=1, owner=owner1)
        experiment = Experiment(title='A title', description='A description',
                                nes_id=1, study=study2, owner=owner2)
        experiment.full_clean()

    def test_experiment_is_related_to_study_and_owner(self):
        owner = User.objects.create(username='lab2')
        study = create_study(nes_id=1, owner=owner)
        experiment = Experiment(nes_id=1, study=study, owner=owner)
        experiment.save()
        self.assertIn(experiment, study.experiments.all())
        self.assertIn(experiment, owner.experiment_set.all())


class ProtocolComponentModelTest(TestCase):

    def test_default_attributes(self):
        protocol_component = ProtocolComponent()
        self.assertEqual(protocol_component.identification, '')
        self.assertEqual(protocol_component.description, '')
        self.assertEqual(protocol_component.duration_value, None)
        self.assertEqual(protocol_component.component_type, '')
        self.assertEqual(protocol_component.nes_id, None)

    def test_protocol_component_is_related_to_experiment_and_owner(self):
        owner = User.objects.create(username='lab2')
        experiment = create_experiment(nes_id=1, owner=owner)
        protocolcomponent = ProtocolComponent(
            identification='An identification',
            component_type='A component type',
            nes_id=1, experiment=experiment, owner=owner
        )
        protocolcomponent.save()
        self.assertIn(protocolcomponent, experiment.protocol_components.all())
        self.assertIn(protocolcomponent, owner.protocolcomponent_set.all())

    def test_cannot_save_empty_attributes(self):
        owner = User.objects.create(username='lab2')
        experiment = create_experiment(nes_id=1, owner=owner)
        protocol_component = ProtocolComponent(
            identification='', component_type='', nes_id=1,
            experiment=experiment, owner=owner
        )
        with self.assertRaises(ValidationError):
            protocol_component.save()
            protocol_component.full_clean()

    def test_duplicate_protocol_components_are_invalid(self):
        owner = User.objects.create(username='lab2')
        experiment = create_experiment(nes_id=1, owner=owner)
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
        owner1 = User.objects.create(username='lab2')
        owner2 = User.objects.create(username='lab3')
        experiment1 = create_experiment(nes_id=1, owner=owner1)
        experiment2 = create_experiment(nes_id=1, owner=owner2)

        ProtocolComponent.objects.create(nes_id=1, experiment=experiment1,
                                         owner=owner1)
        ProtocolComponent.objects.create(nes_id=1, experiment=experiment2,
                                         owner=owner2)


class ExperimentVersionTest(TestCase):

    def test_default_attributes(self):
        experiment_version = ExperimentVersion()
        self.assertEqual(experiment_version.version, None)

    def test_cannot_save_empty_attributes(self):
        experiment_version = ExperimentVersion(version=None)
        with self.assertRaises(ValidationError):
            experiment_version.full_clean()

    def test_version_is_related_to_experiment(self):
        owner = User.objects.create(username='lab1')
        experiment = create_experiment(nes_id=1, owner=owner)
        version = ExperimentVersion(experiment=experiment, version=2)
        version.save()
        self.assertIn(version, experiment.versions.all())
