import os
import tempfile

import shutil
from django.contrib.auth.models import User
from django.test import override_settings, TestCase
from django.utils.text import slugify

from downloads.views import download_create
from experiments.models import Experiment
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_participant, create_group, create_questionnaire, \
    create_questionnaire_language, create_questionnaire_responses
from nep import settings

TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DownloadCreateView(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT)

    @staticmethod
    def create_basic_experiment_data():
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        experiment = create_experiment(1, owner, Experiment.TO_BE_ANALYSED)
        create_study(1, experiment)
        return experiment

    @staticmethod
    def create_questionnaire(experiment):
        """
        Necessary the following files to exist:
            - settings.BASE_DIR/experiments/tests/questionnaire7.csv
            - settings.BASE_DIR/experiments/tests/response_questionnaire7.json
        """
        group = create_group(1, experiment)
        participant = create_participant(1, group)
        participant.age = None
        participant.save()
        questionnaire = create_questionnaire(1, 'Q5489', group)
        create_questionnaire_language(
            questionnaire,
            settings.BASE_DIR + '/experiments/tests/questionnaire7.csv',
            'en'
        )
        create_questionnaire_responses(
            questionnaire, participant,
            settings.BASE_DIR +
            '/experiments/tests/response_questionnaire7.json'
        )
        return group

    def test_create_download_subdir_if_not_exist(self):
        experiment = self.create_basic_experiment_data()
        download_create(experiment.id, '')

        self.assertTrue(
            os.path.exists(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        )

    def test_do_not_write_age_column_in_csv_file_if_participants_has_date_null_1(self):
        # example file:
        # /media/download/1/Group_odit/Per_participant_data/Participant_312
        # /STEP_861-20-7671_QUESTIONNAIRE/Q5489_narakas-and-waikakul.csv
        experiment = self.create_basic_experiment_data()
        group = self.create_questionnaire(experiment)

        download_create(experiment.id, '')

        # check in Per_participant_data subdir
        per_participant_data_dir = os.path.join(
                TEMP_MEDIA_ROOT, 'download', str(experiment.id),
                'Group_' + slugify(group.title), 'Per_participant_data'
            )
        for root, dirs, files in os.walk(per_participant_data_dir):
            if not dirs:
                f = open(os.path.join(root, files[0]), 'r')
                self.assertNotIn('age (years)', f.read())

    def test_do_not_write_age_column_in_csv_file_if_participants_has_date_null_2(self):
        # example file:
        # /media/download/1/Group_odit/Participants.csv
        experiment = self.create_basic_experiment_data()
        group = self.create_questionnaire(experiment)

        download_create(experiment.id, '')

        # check in Particpants.csv file
        participants_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id),
            'Group_' + slugify(group.title), 'Participants.csv'
        )
        f = open(participants_file, 'r')
        self.assertNotIn('age (years)', f.read())
