import tempfile

import shutil

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils.six import StringIO

from experiments.models import Gender, Study, Group, EEGSetting, \
    ExperimentalProtocol, Participant, EEGData
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_group, create_participant, create_experimental_protocol, \
    create_data_collection, create_eeg_setting

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommandsTest(TestCase):

    def setUp(self):
        Gender.objects.create(name='male')
        Gender.objects.create(name='female')

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT)
        # pass

    def test_remove_experiment_last_version(self):
        # create experiment and other object associated with it
        experiment = create_experiment(1)
        study = create_study(1, experiment)
        groups = create_group(3, experiment)
        eeg_setting = create_eeg_setting(1, experiment)
        exp_prot = None  # just to protect assert below
        for group in groups:
            exp_prot = create_experimental_protocol(group)
            participants = create_participant(
                3, group, gender=Gender.objects.order_by('?').first()
            )
            for participant in participants:
                create_data_collection(
                    participant, 'eeg', eeg_setting
                )

        # remove experiment last version and its related objects
        out = StringIO()
        call_command(
            'remove_experiment', experiment.nes_id, experiment.owner,
            '--last', stdout=out
        )

        # asserts
        self.assertFalse(Study.objects.filter(pk=study.id).exists())
        self.assertFalse(EEGSetting.objects.filter(pk=eeg_setting.id).exists())
        # TODO: fix this after fix tests helper (does not create model
        # TODO: instances for all in it, create under demand in tests). Test
        # TODO: for all objects at once.
        for group in groups:
            self.assertFalse(Group.objects.filter(pk=group.id).exists())
            self.assertFalse(ExperimentalProtocol.objects.filter(
                pk=exp_prot.id
            ).exists())
            self.assertFalse(group.participants.exists())
        self.assertFalse(EEGData.objects.exists())

        self.assertIn(
            'Last version of experiment "%s" successfully removed'
            % experiment.title, out.getvalue()
        )
