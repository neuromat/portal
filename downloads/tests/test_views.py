import io
import os
import random
import re
import tempfile

import shutil
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.text import slugify

from downloads.views import download_create
from experiments.models import Experiment, Gender, Questionnaire, \
    QuestionnaireLanguage, Step, Group
from experiments.tests.tests_helper import create_experiment, create_study, \
    create_participant, create_group, create_questionnaire, \
    create_questionnaire_language, create_questionnaire_responses, \
    create_researcher, create_experiment_researcher, create_genders, \
    create_experimental_protocol, create_step, remove_selected_subdir

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DownloadCreateViewTest(TestCase):

    def setUp(self):
        # TODO: it's created in other tests suites, so was breaking here
        if not Gender.objects.all():
            create_genders()

        # license is in media/download/License.txt
        os.makedirs(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        license_file = os.path.join(TEMP_MEDIA_ROOT, 'download', 'LICENSE.txt')
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
    def create_questionnaire_stuff(group, participant):
        """
        Necessary the following files to exist:
            - settings.BASE_DIR/experiments/tests/questionnaire7.csv
            - settings.BASE_DIR/experiments/tests/response_questionnaire7.json
        """
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

        return questionnaire

    def create_download_subdirs(self):
        experiment = self.create_basic_experiment_data()
        group = create_group(1, experiment)
        participant = create_participant(
            1, group, Gender.objects.get(name='female')
        )
        participant.age = None
        participant.save()
        self.create_questionnaire_stuff(group, participant)
        download_create(experiment.id, '')

        return experiment, group

    def asserts_experimental_protocol(self, ep_value, group1, group2,
                                      zipped_file):
        ep_group_str = re.search(
            "experimental_protocol_g([0-9]+)", ep_value
        )
        ep_group_id = int(ep_group_str.group(1))
        if group1.id == ep_group_id:
            group_title_slugifyed = slugify(group1.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed in element for element in
                    zipped_file.namelist())
            )
            # TODO: maybe it's necessary to construct the string representing
            # TODO: the path with file system specific separator ('/' or '\')
            self.assertTrue(
                any('Group_' + group_title_slugifyed + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                group_title_slugifyed = slugify(group2.title)
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            group_title_slugifyed = slugify(group2.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed in element for element in
                    zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed + '/Experimental_protocol'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                self.assertFalse(
                    any('Group_' + slugify(group1.title) +
                        '/Experimental_protocol'
                        in element for element in zipped_file.namelist())
                )

    def asserts_questionnaires(self, q_value, group1, group2,
                               zipped_file):
        q_group_str = re.search("questionnaires_g([0-9]+)", q_value)
        q_group_id = int(q_group_str.group(1))
        if group1.id == q_group_id:
            group_title_slugifyed = slugify(group1.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                group_title_slugifyed = slugify(group2.title)
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group_title_slugifyed +
                            '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )
        else:  # group2.id == ep_group_id
            group_title_slugifyed = slugify(group2.title)
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Questionnaire_metadata'
                    in element for element in zipped_file.namelist())
            )
            self.assertTrue(
                any('Group_' + group_title_slugifyed +
                    '/Per_questionnaire_data'
                    in element for element in zipped_file.namelist())
            )
            if group1 != group2:
                # Questionnaire_metadata subdir exists if group2 has
                # questionnaire(s).
                group_title_slugifyed = slugify(group1.title)
                if group2.steps.filter(type=Step.QUESTIONNAIRE).count() == 0:
                    self.assertFalse(
                        any('Group_' + group_title_slugifyed +
                            '/Questionnaire_metadata'
                            in element for element in zipped_file.namelist())
                    )
                self.assertFalse(
                    any('Group_' + group_title_slugifyed +
                        '/Per_questionnaire_data'
                        in element for element in zipped_file.namelist())
                )

        # when user select "Per Questionnaire Data" option the file
        # Participants.csv has to be in compressed file
        questionnaire_group = Group.objects.get(pk=q_group_id)
        group_title_slugifyed = slugify(questionnaire_group.title)
        self.assertTrue(
            any('Group_' + group_title_slugifyed + '/Participants.csv'
                in element for element in zipped_file.namelist()
                ), 'Group_' + group_title_slugifyed +
                   '/Participants.csv not in ' + str(zipped_file.namelist())
        )

    def assert_participants(self, group1, group2, participant1, participant2,
                            zipped_file, both):
        group_title_slugifyed = slugify(group1.title)
        self.assertTrue(
            any('Group_' + group_title_slugifyed + '/Per_participant_data'
                in element for element in zipped_file.namelist())
        )
        self.assertTrue(
            any('Group_' + group_title_slugifyed +
                '/Per_participant_data/Participant_' +
                participant1.code
                in element for element in zipped_file.namelist())
        )
        if not both and (group1 != group2):
            group_title_slugifyed = slugify(group2.title)
            self.assertFalse(
                any('Group_' + group_title_slugifyed +
                    '/Per_participant_data/Participant_' + participant2.code
                    in element for element in zipped_file.namelist()),
                'Group_' + group_title_slugifyed +
                '/Per_participant_data/Participant_' +
                participant2.code + ' is in ' + str(zipped_file.namelist())
            )

    def user_choices_based_asserts(self, selected_items, group1, group2,
                                   participant1, participant2, zipped_file):
        """
        There are a combination without repetition of three in four selection
        possibilities that are:
            - experimental protocol, questionnaires, participant of group1,
            participant of group2
        This results in four possibilites: C(4, 3) = 4.
        But for questionnaires and experimental protocol we can have two
        other possibilities, and it's precisely the case when group1 !=
        group2. So at the end, we are left with a combination of 3 elements
        in 6 possibilites: C(6, 3) = 20
        :param selected_items: dictionnary
        :param group1: Group model instance
        :param group2: Group model instance
        :param participant1: Participant model instance (always perteining
        to a different group of participant2. Obs.: it could be equal to
        participant2 because group is a foreign key for participant, but in
        the function calling the participant1 != participant2)
        :param participant2: participant model instance
        :param zipped_file:
        """
        if {'ep', 'q', 'p_g1'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, False)

        if {'ep', 'q', 'p_g2'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group2, group1, participant2,
                                     participant1,
                                     zipped_file, False)

        if {'ep', 'p_g1', 'p_g2'}.issubset(selected_items.keys()):
            # experimental protocol
            self.asserts_experimental_protocol(selected_items['ep'], group1,
                                               group2, zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, True)

        if {'q', 'p_g1', 'p_g2'}.issubset(selected_items.keys()):
            # questionnaires
            self.asserts_questionnaires(selected_items['q'], group1, group2,
                                        zipped_file)
            # participants
            self.assert_participants(group1, group2, participant1,
                                     participant2,
                                     zipped_file, True)

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
            any('LICENSE.txt'
                in element for element in zipped_file.namelist()),
            'LICENSE.txt not in ' + str(zipped_file.namelist())
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
        researcher = create_researcher(experiment.study, 'Valdick', 'Soriano')
        researcher.citation_name = 'SORIANO, Valdick'
        researcher.save()

        download_create(experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')
        self.assertIn(
            'SORIANO, Valdick. ' + experiment.title
            + '. Sent date: ' + str(experiment.sent_date),
            file.read().decode('utf-8')
        )

    def test_download_zip_file_has_how_to_cite_content_in_citation_file_2(self):
        experiment = self.create_basic_experiment_data()
        create_researcher(experiment.study, 'Valdick', 'Soriano')
        create_experiment_researcher(experiment, 'Diana', 'Ross')
        researcher = create_experiment_researcher(
            experiment, 'Guilherme', 'Boulos'
        )
        researcher.citation_name = 'BOULOS, Guilherme C.'
        researcher.save()
        create_experiment_researcher(experiment, 'Edimilson', 'Costa')
        download_create(experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        # TODO: use path.join
        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')
        self.assertIn(
            'ROSS, Diana; BOULOS, Guilherme C.; COSTA, Edimilson. '
            + experiment.title + '. Sent date: ' + str(experiment.sent_date),
            file.read().decode('utf-8')
        )

    def test_download_zip_file_has_questionnaire_metadata_in_question_order(self):
        experiment, group = self.create_download_subdirs()
        questionnaire = Questionnaire.objects.get(group=group)
        q_language = QuestionnaireLanguage.objects.get(
            questionnaire=questionnaire
        )
        download_create(experiment.id, '')

        # get the zipped file to test against questions order
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        # TODO: use path.join
        file = zipped_file.open(
            'EXPERIMENT_DOWNLOAD/Group_' + slugify(group.title) +
            '/Questionnaire_metadata/' + questionnaire.code + '_' +
            slugify(q_language.survey_name) + '/Fields_' + questionnaire.code +
            '_en.csv'  # TODO: path.join
        )
        # The right order of the questions (in csv file it's not in right
        # order)
        self.assertRegex(
            file.read().decode('utf-8'),
            'opcTabela2cotovel[\s\S]+'
            'acquisitiondate[\s\S]+'
            'opcTabela1ombro[\s\S]+'
        )

    def test_download_zip_file_has_researchers_citation_in_right_order(self):
        experiment = self.create_basic_experiment_data()
        researcher1 = create_experiment_researcher(experiment, 'Diana', 'Ross')
        researcher1.citation_order = 21
        researcher1.save()

        researcher2 = create_experiment_researcher(
            experiment, 'Guilherme', 'Boulos'
        )
        researcher2.citation_order = 3
        researcher2.save()

        create_experiment_researcher(experiment, 'Edimilson', 'Costa')
        download_create(experiment.id, '')

        # get the zipped file to test against its content
        zip_file = os.path.join(
            TEMP_MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        zipped_file = zipfile.ZipFile(zip_file, 'r')

        file = zipped_file.open('EXPERIMENT_DOWNLOAD/CITATION.txt', 'r')
        self.assertIn(
            'BOULOS, Guilherme; ROSS, Diana; COSTA, Edimilson. '
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

    def test_POSTing_download_experiment_data_returns_correct_content(self):
        experiment = self.create_basic_experiment_data()

        g1 = create_group(1, experiment)
        root_step1 = create_step(1, g1, Step.BLOCK)
        exp_prot1 = create_experimental_protocol(g1)
        exp_prot1.root_step = root_step1
        exp_prot1.save()
        p1 = create_participant(1, g1, Gender.objects.get(name='male'))
        p2 = create_participant(1, g1, Gender.objects.get(name='female'))
        q1 = self.create_questionnaire_stuff(g1, p1)
        q1.parent = root_step1
        q1.save()
        q2 = self.create_questionnaire_stuff(g1, p2)
        q2.parent = root_step1
        q2.save()

        g2 = create_group(1, experiment)
        root_step2 = create_step(1, g2, Step.BLOCK)
        exp_prot2 = create_experimental_protocol(g2)
        exp_prot2.root_step = root_step2
        exp_prot2.save()
        p3 = create_participant(1, g2, Gender.objects.get(name='male'))
        p4 = create_participant(1, g2, Gender.objects.get(name='female'))
        q3 = self.create_questionnaire_stuff(g2, p3)
        q3.parent = root_step2
        q3.save()
        q4 = self.create_questionnaire_stuff(g2, p4)
        q4.parent = root_step2
        q4.save()

        download_create(experiment.id, '')

        # get groups and participants for tests below
        g1 = experiment.groups.order_by('?').first()
        g2 = experiment.groups.order_by('?').first()  # can be equal to g1
        if g1 == g2:
            participants = list(g1.participants.order_by('?'))
            p1 = participants[0]
            p2 = participants[len(participants) - 1]
        else:
            p1 = g1.participants.order_by('?').first()
            p2 = g2.participants.order_by('?').first()

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})

        # random select items, simulating user posting items to download
        all_items = {
            'ep': 'experimental_protocol_g' + str(g1.id),
            'q': 'questionnaires_g' + str(g2.id),
            'p_g1': 'participant_p' + str(p1.id) + '_g' + str(g1.id),
            'p_g2': 'participant_p' + str(p2.id) + '_g' + str(g2.id)
        }
        selected_items = {}
        for i in range(3):
            random_choice = random.choice(list(all_items.keys()))
            selected_items[random_choice] = all_items[random_choice]
            all_items.pop(random_choice, 0)
        response = self.client.post(
            url, {'download_selected': selected_items.values()}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename=%s' % smart_str('download.zip')
        )

        # get the zipped file to test against its content
        file = io.BytesIO(response.content)
        zipped_file = zipfile.ZipFile(file, 'r')
        self.assertIsNone(zipped_file.testzip())

        # compressed file must always contain License.txt file
        self.assertTrue(
            any('LICENSE.txt'
                in element for element in zipped_file.namelist()),
            'LICENSE.txt not in ' + str(zipped_file.namelist())
        )

        # compressed file must always contain CITATION.txt file
        self.assertTrue(
            any('CITATION.txt'
                in element for element in zipped_file.namelist()),
            'CITATION.txt not in ' + str(zipped_file.namelist())
        )

        # compressed file must always contain Experiments.csv
        self.assertTrue(
            any('Experiment.csv'
                in element for element in zipped_file.namelist()),
            'Experiment.csv not in ' + str(zipped_file.namelist())
        )

        # test for compressed folders based on items selected by user
        self.user_choices_based_asserts(
            selected_items, g1, g2, p1, p2, zipped_file
        )

        # For each group, if it has questionnaire(s) in its experimental
        # protocol, it must contain questionnaire(s) metadata in group
        # subdir of the compressed file.
        for group in [g1, g2]:
            if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
                group_title_slugifyed = slugify(group.title)
                self.assertTrue(
                    any('Group_' + group_title_slugifyed +
                        '/Questionnaire_metadata'
                        in element for element in zipped_file.namelist()),
                    '"Group_' + group_title_slugifyed +
                    '/Questionnaire_metadata" subdir not in: ' +
                    str(zipped_file.namelist())
                )

    def test_POSTing_option_data_has_not_correspondent_subdir_redirects_to_experiment_detail_view(self):
        experiment = self.create_basic_experiment_data()

        g1 = create_group(1, experiment)
        root_step1 = create_step(1, g1, Step.BLOCK)
        exp_prot1 = create_experimental_protocol(g1)
        exp_prot1.root_step = root_step1
        exp_prot1.save()
        p1 = create_participant(1, g1, Gender.objects.get(name='male'))
        p2 = create_participant(1, g1, Gender.objects.get(name='female'))
        q1 = self.create_questionnaire_stuff(g1, p1)
        q1.parent = root_step1
        q1.save()
        q2 = self.create_questionnaire_stuff(g1, p2)
        q2.parent = root_step1
        q2.save()

        g2 = create_group(1, experiment)
        root_step2 = create_step(1, g2, Step.BLOCK)
        exp_prot2 = create_experimental_protocol(g2)
        exp_prot2.root_step = root_step2
        exp_prot2.save()
        p3 = create_participant(1, g2, Gender.objects.get(name='male'))
        p4 = create_participant(1, g2, Gender.objects.get(name='female'))
        q3 = self.create_questionnaire_stuff(g2, p3)
        q3.parent = root_step2
        q3.save()
        q4 = self.create_questionnaire_stuff(g2, p4)
        q4.parent = root_step2
        q4.save()

        download_create(experiment.id, '')

        group = experiment.groups.order_by('?').first()
        participant = group.participants.order_by('?').first()

        options = [
            'experimental_protocol_g' + str(group.id),
            'questionnaires_g' + str(group.id),
            'participant_p' + str(participant.id) + '_g' + str(group.id)
        ]

        selected = random.choice(options)
        # Remove the selected option corresponded subdir simulated that the
        # subdir does not exist.
        remove_selected_subdir(
            selected, experiment, participant, group, TEMP_MEDIA_ROOT
        )

        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.post(url, {'download_selected': selected})

        self.assertRedirects(
            response,
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )
