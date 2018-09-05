import tempfile

import shutil
from random import choice

import os
from unittest.mock import patch

from django.core.management import call_command, BaseCommand
from django.test import TestCase, override_settings
from django.utils.six import StringIO

from experiments.models import Gender, Study, Group, EEGSetting, \
    ExperimentalProtocol, EEGData, Experiment, EEG
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_group, create_participant, create_experimental_protocol, \
    create_eeg_setting, create_eeg_data, \
    create_eeg_step, create_genders, create_next_version_experiment, create_owner, \
    create_uploads_subdirs_and_files, \
    create_download_subdirs
from nep import settings


class CommandsTest(TestCase):
    TEMP_MEDIA_ROOT = ''

    def setUp(self):
        create_genders()
        self.TEMP_MEDIA_ROOT = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.TEMP_MEDIA_ROOT

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_last_version_removes_objects_associated(
            self, mock_user_input
    ):
        """
        Do not test for files deleted. This tests are made in models tests.
        """
        # create experiment and some objects associated with it
        experiment = create_experiment(1)
        create_study(1, experiment)
        groups = create_group(3, experiment)
        eeg_setting = create_eeg_setting(1, experiment)
        exp_prot = None  # just to protect assert below
        for group in groups:
            exp_prot = create_experimental_protocol(group)
            eeg_step = create_eeg_step(group, eeg_setting)
            participants = create_participant(
                3, group, gender=Gender.objects.order_by('?').first()
            )
            for participant in participants:
                create_eeg_data(eeg_setting, eeg_step, participant)

        # remove experiment last version and its related objects
        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            '--last', stdout=out
        )

        # asserts
        self.assertFalse(Experiment.objects.exists())
        self.assertFalse(Study.objects.exists())
        self.assertFalse(EEGSetting.objects.exists())
        # TODO: fix this after fix tests helper (does not create model
        # TODO: instances for all in it, create under demand in tests). Test
        # TODO: for all objects at once.
        for group in groups:
            self.assertFalse(Group.objects.filter(pk=group.id).exists())
            self.assertFalse(ExperimentalProtocol.objects.filter(
                pk=exp_prot.id
            ).exists())
            self.assertFalse(EEG.objects.filter(group=group).exists())
            self.assertFalse(group.participants.exists())
        self.assertFalse(EEGData.objects.exists())

        self.assertIn(
            'Last version of experiment "%s" successfully removed'
            % experiment.title, out.getvalue()
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_last_version_removes_only_last_version(
            self, mock_user_input
    ):

        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)
        experiment_versions = create_next_version_experiment(5, experiment)
        experiment_version = choice(experiment_versions)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiment_version.nes_id, experiment_version.owner,
            '--last', stdout=out
        )

        self.assertEqual(5, Experiment.objects.count())
        self.assertEqual(5, Experiment.lastversion_objects.last().version)

        self.assertIn(
            'Last version of experiment "%s" successfully removed'
            % experiment.title, out.getvalue()
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_removes_all_versions(self, mock_user_input):

        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)
        experiment_versions = create_next_version_experiment(11, experiment)
        experiment_version = choice(experiment_versions)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiment_version.nes_id, experiment_version.owner,
            stdout=out
        )

        self.assertFalse(Experiment.objects.exists())
        self.assertIn(
            'All versions of experiment "%s" successfully removed'
            % experiment.title, out.getvalue()
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_removes_media_download_experiment_subdir(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiments = create_experiment(2, owner=owner)

        download_subdirs = []
        for experiment in experiments:
            download_subdir = os.path.join(
                self.TEMP_MEDIA_ROOT, 'download', str(experiment.id)
            )
            create_download_subdirs(download_subdir)
            download_subdirs.append(download_subdir)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiments[0].nes_id, experiments[0].owner,
            stdout=out
        )

        self.assertFalse(os.path.exists(download_subdirs[0]))
        self.assertTrue(os.path.exists(
            os.path.join(self.TEMP_MEDIA_ROOT, 'download')
        ))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_the_only_experiment_that_exists_removes_media_download_subdir(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        download_subdir = os.path.join(
            self.TEMP_MEDIA_ROOT, 'download', str(experiment.id)
        )

        create_download_subdirs(download_subdir)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiment.nes_id, experiment.owner,
            stdout=out
        )

        self.assertFalse(os.path.exists(download_subdir))
        self.assertFalse(os.path.exists(
            os.path.join(self.TEMP_MEDIA_ROOT, 'download')
        ))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_removes_uploads_subdirs_if_they_are_empty(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        uploads_subdir = os.path.join(self.TEMP_MEDIA_ROOT, 'uploads')
        create_uploads_subdirs_and_files(uploads_subdir)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiment.nes_id, experiment.owner,
            stdout=out
        )

        for root, dirs, files in os.walk(uploads_subdir):
            # it's in a path tree leaf wo files (e.g. 'uploads/2018/01/15')
            if not dirs:
                self.assertTrue(os.path.exists(root))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_removes_uploads_subdir_if_there_are_not_files(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        uploads_subdir = os.path.join(self.TEMP_MEDIA_ROOT, 'uploads')
        create_uploads_subdirs_and_files(uploads_subdir, empty=True)

        out = StringIO()
        call_command(
            'remove_experiment',
            experiment.nes_id, experiment.owner,
            stdout=out
        )

        self.assertFalse(os.path.exists(uploads_subdir))
        self.assertTrue(os.path.exists(self.TEMP_MEDIA_ROOT))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_last_version_display_message_wait(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            '--last', stdout=out
        )

        self.assertIn(
            'Removing last version of experiment "%s" data and files...'
            % experiment.title, out.getvalue()
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_display_message_removing(self, mock_user_input):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            stdout=out
        )

        self.assertIn(
            'Removing all versions of experiment "%s" data and files...'
            % experiment.title, out.getvalue()
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_displays_prompt_and_user_confirm_removing(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            stdout=out
        )

        self.assertEqual(mock_user_input.called, True)
        (text,), kwargs = mock_user_input.call_args
        self.assertEqual(text, BaseCommand().style.WARNING(
            'All versions of experiment "%s" will be destroyed and cannot be '
            'recovered. Are you sure? (Yes/n) ' % experiment.title))
        self.assertFalse(Experiment.objects.exists())

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='n')
    def test_remove_experiment_displays_prompt_and_user_do_not_confirm_removing(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            stdout=out
        )

        self.assertEqual(mock_user_input.called, True)
        (text,), kwargs = mock_user_input.call_args
        self.assertEqual(text, BaseCommand().style.WARNING(
            'All versions of experiment "%s" will be destroyed and cannot be '
            'recovered. Are you sure? (Yes/n) ' % experiment.title))
        self.assertTrue(Experiment.objects.exists())
        self.assertIn('Aborted', out.getvalue())

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='Yes')
    def test_remove_experiment_last_version_displays_prompt_and_user_confirm_removing(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            '--last', stdout=out
        )

        self.assertEqual(mock_user_input.called, True)
        (text,), kwargs = mock_user_input.call_args
        self.assertEqual(text, BaseCommand().style.WARNING(
            'Last version of experiment "%s" will be destroyed and cannot be '
            'recovered. Are you sure? (Yes/n) ' % experiment.title))
        self.assertFalse(Experiment.objects.exists())

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @patch('experiments.management.commands.remove_experiment.get_input',
           return_value='n')
    def test_remove_experiment_last_version_displays_prompt_and_user_do_not_confirm_removing(
            self, mock_user_input
    ):
        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)

        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            '--last', stdout=out
        )

        self.assertEqual(mock_user_input.called, True)
        (text,), kwargs = mock_user_input.call_args
        self.assertEqual(text, BaseCommand().style.WARNING(
            'Last version of experiment "%s" will be destroyed and cannot be '
            'recovered. Are you sure? (Yes/n) ' % experiment.title))
        self.assertTrue(Experiment.objects.exists())
        self.assertIn('Aborted', out.getvalue())
