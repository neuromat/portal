import os
import tempfile

import shutil
import zipfile

from django.contrib.auth.models import User
from django.test import override_settings, TestCase
from django.utils.text import slugify

from downloads.views import download_create
from experiments.models import Experiment
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_participant, create_group, create_questionnaire, \
    create_questionnaire_language, create_questionnaire_responses, \
    create_researcher, create_experiment_researcher
from nep import settings

TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DownloadCreateView(TestCase):

    def setUp(self):
        # license is in media/download/License.txt
        os.makedirs(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        license_file = os.path.join(TEMP_MEDIA_ROOT, 'download', 'License.txt')
        with open(license_file, 'w') as file:
            file.write('license')

    def tearDown(self):
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

    def create_download_subdirs(self):
        experiment = self.create_basic_experiment_data()
        group = self.create_questionnaire(experiment)
        download_create(experiment.id, '')

        return experiment, group

    def test_download_zip_file_has_license_file(self):
        experiment, group = self.create_download_subdirs()

        # get the zipped file to test against its content
        zip_file = os.path.join(
                TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
            )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())  # TODO: test this separately

        # compressed file must always contain License.txt file
        self.assertTrue(
            any('License.txt'
                in element for element in zipped_file.namelist()),
            'License.txt not in ' + str(zipped_file.namelist())
        )

    def test_download_dir_structure_has_citation_file(self):
        experiment, group = self.create_download_subdirs()

        self.assertIn(
            'CITATION.txt', os.listdir(os.path.join(
                TEMP_MEDIA_ROOT, 'download', str(experiment.id)
            ))
        )

    def test_download_zip_file_has_how_to_cite_content_in_citation_file_1(self):
        experiment = self.create_basic_experiment_data()
        create_researcher(experiment.study, 'Valdick', 'Soriano')
        download_create(experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')
        self.assertIn(
            'SORIANO, Valdick ' + experiment.title
            + '. Sent date: ' + str(experiment.sent_date),
            file.read().decode('utf-8')
        )

    def test_download_zip_file_has_how_to_cite_content_in_citation_file_2(self):
        experiment = self.create_basic_experiment_data()
        create_researcher(experiment.study, 'Valdick', 'Soriano')
        create_experiment_researcher(experiment, 'Diana', 'Ross')
        create_experiment_researcher(experiment, 'Guilherme', 'Boulos')
        create_experiment_researcher(experiment, 'Edimilson', 'Costa')
        download_create(experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')

        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')
        self.assertIn(
            'ROSS, Diana; BOULOS, Guilherme; COSTA, Edimilson '
            + experiment.title + '. Sent date: ' + str(experiment.sent_date),
            file.read().decode('utf-8')
        )

    def test_do_not_write_age_column_in_csv_file_if_participants_has_date_null_1(self):
        # example file:
        # /media/download/1/Group_odit/Per_participant_data/Participant_312
        # /STEP_861-20-7671_QUESTIONNAIRE/Q5489_narakas-and-waikakul.csv
        experiment, group = self.create_download_subdirs()

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
        experiment, group = self.create_download_subdirs()

        # check in Particpants.csv file
        participants_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id),
            'Group_' + slugify(group.title), 'Participants.csv'
        )
        f = open(participants_file, 'r')
        self.assertNotIn('age (years)', f.read())

    def test_do_not_write_age_column_in_csv_file_if_participants_has_date_null_3(self):
        # example file:
        # /media/download/1/Group_odit/Per_questionnaire_data
        # /Q6631_narakas_and_waikakul/Responses_Q6631.csv
        experiment, group = self.create_download_subdirs()

        # check in Per_questionnaire_data subdir
        per_questionnaire_data_dir = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id),
            'Group_' + slugify(group.title), 'Per_questionnaire_data'
        )
        for root, dirs, files in os.walk(per_questionnaire_data_dir):
            if not dirs:
                f = open(os.path.join(root, files[0]), 'r')
                self.assertNotIn('age (years)', f.read())
