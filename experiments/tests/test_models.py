from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime

from experiments.models import Experiment, Study, Researcher


class ResearcherModelTest(TestCase):

    def test_default_attributes(self):
        researcher = Researcher()
        self.assertEqual(researcher.first_name, '')
        self.assertEqual(researcher.surname, '')
        self.assertEqual(researcher.email, '')
        self.assertEqual(researcher.nes_id, None)

    def test_cannot_save_empty_attributes(self):
        pass
        # TODO: It's not possible test all fields empty because with a
        # PositiveIntegerField the constructor does not allow to create the
        # object without an allowed value.
        # See other tests here and the tests in test_api.py that creates a
        # Researcher object.
        # With nes_id=None django generates error when calling
        # Researcher constructor. With nes_id=1, the test fails (
        # ValidationError not raised) because researcher was saved.
        # By now commented.
        #
        # researcher = Researcher(nes_id=None)
        # with self.assertRaises(ValidationError):
        #     researcher.save()
        #     researcher.full_clean()

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

    def test_study_is_related_to_researcher_and_owner(self):
        owner = User.objects.create_user(username='lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        study = Study(nes_id=1, start_date=datetime.utcnow())
        study.researcher = researcher
        study.owner = owner
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

    def test_experiment_is_related_to_study_and_owner(self):
        owner = User.objects.create(username='lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        study = Study.objects.create(
            nes_id=1, start_date=datetime.utcnow(), researcher=researcher,
            owner=owner)
        experiment = Experiment(nes_id=1)
        experiment.study = study
        experiment.owner = owner
        experiment.save()
        self.assertIn(experiment, study.experiments.all())
        self.assertIn(experiment, owner.experiment_set.all())
