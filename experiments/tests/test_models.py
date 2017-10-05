from random import randint

from django.template.defaultfilters import slugify
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import datetime
from faker import Factory

from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, RejectJustification
from experiments.tests.tests_helper import global_setup_ut, apply_setup


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

    # TODO: cannot save researcher without study


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

    def setUp(self):
        global_setup_ut()

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
