import tempfile

import shutil
from random import choice

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils.six import StringIO

from experiments.models import Gender, Study, Group, EEGSetting, \
    ExperimentalProtocol, EEGData, Experiment, EEG
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_group, create_participant, create_experimental_protocol, \
    create_eeg_setting, create_eeg_data, \
    create_eeg_step, create_genders, create_experiment_versions, create_owner


class CommandsTest(TestCase):

    def setUp(self):
        create_genders()

    def test_remove_experiment_last_version_removes_objects_associated(self):
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

    def test_remove_experiment_last_version_removes_only_last_version(self):

        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)
        experiment_versions = create_experiment_versions(5, experiment)
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

    def test_remove_experiment(self):

        owner = create_owner('labX')
        experiment = create_experiment(1, owner=owner)
        experiment_versions = create_experiment_versions(11, experiment)
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

    def test_send_confirmation_message(self):
        # TODO: implement it!
        pass
