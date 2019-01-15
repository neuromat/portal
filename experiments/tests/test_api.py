import json
import tempfile
from datetime import datetime
from unittest import skip

import os

import shutil
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import smart_str
from rest_framework import status
from rest_framework.test import APITestCase

from experiments import api
from experiments.api import ExperimentSerializer, \
    ExperimentResearcherSerializer
from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    ClassificationOfDiseases, Questionnaire, Step, \
    QuestionnaireLanguage, QuestionnaireDefaultLanguage, Publication, \
    ExperimentalProtocol, ExperimentResearcher
from experiments.tests.tests_helper import create_experiment, create_group, \
    create_questionnaire, \
    create_experiment_researcher, create_next_version_experiment, PASSWORD, \
    create_owner, create_trustee_user, create_study, create_researcher, \
    create_publication

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class ExperimentAPITest(APITestCase):
    list_url = reverse('api_experiments-list')

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment1 = create_experiment(1, owner=self.owner)
        # necessary to build export file in some tests
        create_study(1, self.experiment1)
        self.experiment2 = create_experiment(1, owner=self.owner)
        create_study(1, self.experiment2)

    def test_get_returns_all_experiments(self):
        # TODO:
        # this test uses a clever (and lean) way of testing API GET's.
        # Refactor other similar tests in this file.
        # See: https://realpython.com/test-driven-development-of-a-django-restful-api/
        # in contrast with
        # https://www.obeythetestinggoat.com/book/appendix_DjangoRestFramework.html
        experiments = Experiment.objects.all()
        serializer = ExperimentSerializer(experiments, many=True)

        response = self.client.get(self.list_url)
        self.assertEqual(response.data, serializer.data)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_POSTing_a_new_experiment(self):
        image_file = generate_image_file(100, 100, 'test.jpg')
        self.client.login(username=self.owner.username, password=PASSWORD)
        response = self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 17,
                'ethics_committee_file': image_file,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d')
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_experiment = Experiment.objects.get(nes_id=17, owner=self.owner)
        self.assertEqual(new_experiment.title, 'New experiment')

        shutil.rmtree(TEMP_MEDIA_ROOT)

    def test_POSTing_new_experiment_send_email_to_trustees(self):
        trustee1 = create_trustee_user('claudia')
        trustee2 = create_trustee_user('roque')
        emails = [trustee1.email, trustee2.email]

        self.send_mail_called = False

        # TODO: refactor using Python Mock Library
        def fake_send_mail(subject, body, from_email, to):
            self.send_mail_called = True
            self.subject = subject
            self.body = body
            self.from_email = from_email
            self.to = to

        api.send_mail = fake_send_mail

        self.client.login(username=self.owner.username, password=PASSWORD)
        response = self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 27,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d')
            }
        )

        self.assertTrue(self.send_mail_called)
        self.assertEqual(
            self.subject,
            'New experiment "' + response.data['title'] +
            '" has arrived in NEDP portal.'
        )
        self.assertEqual(self.from_email, 'noreplay@nep.prp.usp.br')
        self.assertListEqual(sorted(self.to), sorted(emails))

    def test_POSTing_experiment_generates_new_version(self):
        # post experiment already sended to portal
        self.client.login(username=self.owner.username, password=PASSWORD)
        response = self.client.post(
            self.list_url,
            {
                'title': 'New title',
                'description': 'New description',
                'nes_id': self.experiment1.nes_id,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'release_notes': 'This experiment has changed'
            }
        )
        self.client.logout()

        experiment_version_2 = Experiment.objects.last()
        self.assertEqual(experiment_version_2.version, 2)
        # included after including experiment release_notes field
        self.assertEqual(
            experiment_version_2.release_notes,
            'This experiment has changed'
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_PATCHing_an_existing_experiment(self):
        # Before generate download.zip file when changing experiment status
        # from RECEIVING to TO_BE_ANALYSED, we need to create the
        # license file in media/download/LICENSE.txt because that file needs
        # to be available before bulding download.zip file
        os.makedirs(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        license_file = os.path.join(TEMP_MEDIA_ROOT, 'download', 'LICENSE.txt')
        with open(license_file, 'w') as file:
            file.write('license')

        self.client.login(username=self.owner.username, password=PASSWORD)
        detail_url = reverse(
            'api_experiments-detail',
            kwargs={'experiment_nes_id': self.experiment1.nes_id}
        )
        resp_patch = self.client.patch(
            detail_url,
            {
                'title': 'Changed experiment',
                'description': 'Changed description',
            }
        )
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)

        resp_get = self.client.get(detail_url)
        self.assertEqual(
            json.loads(resp_get.content.decode('utf8')),
            {
                'id': self.experiment1.id,
                'title': 'Changed experiment',
                'description': 'Changed description',
                'data_acquisition_done':
                    self.experiment1.data_acquisition_done,
                'nes_id': self.experiment1.nes_id,
                'owner': self.experiment1.owner.username,
                'status': self.experiment1.status,
                'sent_date': self.experiment1.sent_date.strftime('%Y-%m-%d'),
                'project_url': self.experiment1.project_url,
                'ethics_committee_url':
                    self.experiment1.ethics_committee_url,
                'ethics_committee_file': None,
                'release_notes': self.experiment1.release_notes
            }
        )
        self.client.logout()

        shutil.rmtree(TEMP_MEDIA_ROOT)

    def test_POSTing_experiment_creates_version_one(self):
        self.client.login(username=self.owner.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d')
            }
        )
        self.client.logout()

        # Assert version of the experiment created is 1
        experiment = Experiment.objects.first()
        self.assertEqual(1, experiment.version)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_PATCHing_experiment_with_to_be_analysed_status_make_available_download_experiment(self):
        # first post a new experiment through API
        self.client.login(username=self.owner.username, password=PASSWORD)
        self.client.post(
            reverse('api_experiments-list'),
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 18,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'status': 'receiving'
            },
        )
        # We need also to post a study for the experiment posted, because
        # export requires that an experiment to have a study associated
        experiment = Experiment.objects.last()
        url = reverse(
            'api_experiment_studies-list',
            kwargs={'experiment_nes_id': experiment.nes_id}
        )
        self.client.post(
            url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
            }
        )

        # Before generate download.zip file we need to create the
        # license file in media/download/License.txt because that file needs
        # to be available before bulding download.zip file
        os.makedirs(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        license_file = os.path.join(TEMP_MEDIA_ROOT, 'download', 'LICENSE.txt')
        with open(license_file, 'w') as file:
            file.write('license')

        # After sending the experiment data we send a "message" notifying
        # that the experiment can be analysed
        detail_url = reverse(
            'api_experiments-detail',
            kwargs={'experiment_nes_id': experiment.nes_id}
        )
        self.client.patch(
            detail_url,
            {
                'status': experiment.TO_BE_ANALYSED,
            },
        )
        self.client.logout()

        # now we can test for downloading experiment
        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename=%s' % smart_str('download.zip')
        )

        shutil.rmtree(TEMP_MEDIA_ROOT)


class StudyAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner('lab1')
        self.experiment = create_experiment(1, self.owner)
        self.study = create_study(1, self.experiment)

    def test_get_returns_all_studies_short_url(self):
        owner2 = create_owner('lab2')

        experiment2 = create_experiment(1, owner2)
        experiment3 = create_experiment(1, owner2)

        study2 = create_study(1, experiment2)
        study3 = create_study(1, experiment3)
        list_url = reverse('api_studies-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.study.id,
                    'title': self.study.title,
                    'description': self.study.description,
                    'start_date': self.study.start_date.strftime('%Y-%m-%d'),
                    'end_date': self.study.end_date,
                    'experiment': self.study.experiment.title,
                    'keywords': list(self.study.keywords.values('name'))
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'experiment': study2.experiment.title,
                    'keywords': list(study2.keywords.values('name'))
                },
                {
                    'id': study3.id,
                    'title': study3.title,
                    'description': study3.description,
                    'start_date': study3.start_date.strftime('%Y-%m-%d'),
                    'end_date': study3.end_date,
                    'experiment': study3.experiment.title,
                    'keywords': list(study3.keywords.values('name'))
                }
            ]
        )

    def test_get_returns_all_studies_long_url_not_logged(self):
        owner2 = create_owner('lab2')

        experiment2 = create_experiment(1, owner2)
        experiment3 = create_experiment(1, owner2)

        study2 = create_study(1, experiment2)
        study3 = create_study(1, experiment3)
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': self.experiment.nes_id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.study.id,
                    'title': self.study.title,
                    'description': self.study.description,
                    'start_date': self.study.start_date.strftime('%Y-%m-%d'),
                    'end_date': self.study.end_date,
                    'experiment': self.study.experiment.title,
                    'keywords': list(self.study.keywords.values('name'))
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'experiment': study2.experiment.title,
                    'keywords': list(study2.keywords.values('name'))
                },
                {
                    'id': study3.id,
                    'title': study3.title,
                    'description': study3.description,
                    'start_date': study3.start_date.strftime('%Y-%m-%d'),
                    'end_date': study3.end_date,
                    'experiment': study3.experiment.title,
                    'keywords': list(study3.keywords.values('name'))
                }
            ]
        )

    def test_get_returns_all_studies_long_url_logged(self):
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': self.experiment.nes_id})
        self.client.login(username=self.owner.username, password=PASSWORD)
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.study.id,
                    'title': self.study.title,
                    'description': self.study.description,
                    'start_date': self.study.start_date.strftime('%Y-%m-%d'),
                    'end_date': self.study.end_date,
                    'experiment': self.experiment.title,
                    'keywords': list(self.study.keywords.values('name'))
                },
            ]
        )

    def test_POSTing_a_new_study(self):
        experiment = create_experiment(1, self.owner)
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_experiment_studies-list',
            kwargs={'experiment_nes_id': experiment.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_study = Study.objects.get(experiment=experiment)
        self.assertEqual(new_study.title, 'New study')

        # TODO:
        # IMPORTANT! Test client can't POST (PUT etc.) to Study model
        # without been its owner (indirectly by experiment's study). Ensure
        # that only same client can POST to that model.

        # def test_PUTing_an_existing_study(self):
        #     pass  # TODO: update test with new url
        #     owner = User.objects.get(username='lab2')
        #     study = Study.objects.get(owner=owner)
        #     detail_url = reverse(
        #         'api_studies-detail', kwargs={'nes_id': study.nes_id}
        #     )
        #     self.client.login(username=owner.username, password='nep-lab2')
        #     resp_patch = self.client.patch(
        #         detail_url,
        #         {
        #             'title': 'Changed title',
        #             'description': 'Changed description',
        #             'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
        #         }
        #     )
        #     self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        #
        #     # Test study updated
        #     resp_get = self.client.get(detail_url)
        #     self.assertEqual(
        #         json.loads(resp_get.content.decode('utf8')),
        #         {
        #             'id': study.id,
        #             'title': 'Changed title',
        #             'description': 'Changed description',
        #             'start_date': study.start_date.strftime('%Y-%m-%d'),
        #             'end_date': None,
        #             'nes_id': study.nes_id,
        #             'owner': study.owner.username
        #         }
        #     )
        #     self.client.logout()


class ResearcherAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment = create_experiment(1, self.owner)
        self.study = create_study(1, self.experiment)
        self.researcher = create_researcher(self.study)

    def test_get_returns_all_researchers_short_url(self):
        experiment2 = create_experiment(1, self.owner)
        study2 = create_study(1, experiment2)
        researcher2 = create_researcher(study2)
        list_url = reverse('api_study_researchers-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.researcher.id,
                    'first_name': self.researcher.first_name,
                    'last_name': self.researcher.last_name,
                    'email': self.researcher.email,
                    'study': self.researcher.study.title,
                    'citation_name': self.researcher.citation_name
                },
                {
                    'id': researcher2.id,
                    'first_name': researcher2.first_name,
                    'last_name': researcher2.last_name,
                    'email': researcher2.email,
                    'study': researcher2.study.title,
                    'citation_name': researcher2.citation_name
                }
            ]
        )

    def test_get_returns_researcher_long_url(self):
        list_url = reverse('api_study_researcher-list',
                           kwargs={'pk': self.study.id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.researcher.id,
                    'first_name': self.researcher.first_name,
                    'last_name': self.researcher.last_name,
                    'email': self.researcher.email,
                    'study': self.researcher.study.title,
                    'citation_name': self.researcher.citation_name
                }
            ]
        )

    def test_POSTing_a_new_researcher(self):
        experiment2 = create_experiment(1, self.owner)
        study2 = create_study(1, experiment2)
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse('api_study_researcher-list',
                           kwargs={'pk': study2.id})
        response = self.client.post(
            list_url,
            {
                'first_name': 'João',
                'last_name': 'das Rosas',
                'email': 'joao@rosas.com',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_researcher = Researcher.objects.last()
        self.assertEqual(new_researcher.first_name, 'João')
        self.assertEqual(new_researcher.last_name, 'das Rosas')


class ExperimentResearcherAPITest(APITestCase):

    def setUp(self):
        self.experiment1 = create_experiment(1)
        self.experiment2 = create_experiment(1)
        self.experiment_researcher1 = create_experiment_researcher(
            self.experiment1
        )
        self.experiment_researcher2 = create_experiment_researcher(
            self.experiment2
        )

    def test_get_returns_all_experiment_researchers_short_url(self):
        list_url = reverse('api_researchers-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.experiment_researcher1.id,
                    'first_name': self.experiment_researcher1.first_name,
                    'last_name': self.experiment_researcher1.last_name,
                    'email': self.experiment_researcher1.email,
                    'institution': self.experiment_researcher1.institution,
                    'experiment': self.experiment_researcher1.experiment.title,
                    'citation_name': self.experiment_researcher1.citation_name,
                    'citation_order': self.experiment_researcher1.citation_order
                },
                {
                    'id': self.experiment_researcher2.id,
                    'first_name': self.experiment_researcher2.first_name,
                    'last_name': self.experiment_researcher2.last_name,
                    'email': self.experiment_researcher2.email,
                    'institution': self.experiment_researcher2.institution,
                    'experiment': self.experiment_researcher2.experiment.title,
                    'citation_name': self.experiment_researcher2.citation_name,
                    'citation_order': self.experiment_researcher2.citation_order
                }
            ]
        )

    def test_get_returns_all_experiment_researchers_long_url(self):
        # TODO:
        # this test uses a clever (and lean) way of testing API GET's.
        # Refactor other similar tests in this file.
        # See: https://realpython.com/test-driven-development-of-a-django-restful-api/
        # in contrast with
        # https://www.obeythetestinggoat.com/book/appendix_DjangoRestFramework.html
        create_experiment_researcher(self.experiment2)
        experiment_researchers = ExperimentResearcher.objects.filter(
            experiment=self.experiment2
        )
        serializer = ExperimentResearcherSerializer(
            experiment_researchers, many=True
        )

        self.client.login(
            username=self.experiment2.owner.username,
            password=PASSWORD
        )

        list_url = reverse(
            'api_experiment_researchers-list',
            kwargs={'experiment_nes_id': self.experiment2.nes_id}
        )
        response = self.client.get(list_url)
        self.assertEqual(response.data, serializer.data)

    def test_POSTing_a_new_experiment_researcher(self):
        self.client.login(
            username=self.experiment1.owner.username,
            password=PASSWORD
        )
        list_url = reverse(
            'api_experiment_researchers-list',
            kwargs={'experiment_nes_id': self.experiment1.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'first_name': 'Astrojildo',
                'last_name': 'Pereira',
                'email': 'astrojildo@fsf.org',
                'institution': 'FSF',
                'citation_name': 'PEREIRA, Astrojildo'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_experiment_researcher = ExperimentResearcher.objects.last()
        self.assertEqual(new_experiment_researcher.first_name, 'Astrojildo')

    def test_POSTing_a_new_experiment_researcher_associates_with_last_experiment_version(self):
        # create experiment version 2
        create_next_version_experiment(self.experiment1)

        self.client.login(
            username=self.experiment1.owner.username,
            password=PASSWORD
        )
        list_url = reverse(
            'api_experiment_researchers-list',
            kwargs={'experiment_nes_id': self.experiment1.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'first_name': 'Astrojildo',
                'last_name': 'Pereira',
                'email': 'astrojildo@fsf.org',
                'institution': 'FSF',
                'citation_name': 'PEREIRA, Astrojildo'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_experiment_researcher = ExperimentResearcher.objects.last()
        self.assertEqual(new_experiment_researcher.first_name, 'Astrojildo')
        self.assertEqual(new_experiment_researcher.experiment.version, 2)


class GroupAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment = create_experiment(1, self.owner)
        self.group = create_group(1, self.experiment)

    def test_get_returns_all_groups_short_url(self):
        group2 = create_group(1, self.experiment)
        list_url = reverse('api_groups-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.group.id,
                    'title': self.group.title,
                    'description': self.group.description,
                    'experiment': self.group.experiment.title,
                    'inclusion_criteria':
                        list(self.group.inclusion_criteria.all())
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'inclusion_criteria':
                        list(group2.inclusion_criteria.all())
                }
            ]
        )

    def test_get_returns_all_groups_long_url(self):
        group2 = create_group(1, self.experiment)
        list_url = reverse(
            'api_experiment_groups-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.group.id,
                    'title': self.group.title,
                    'description': self.group.description,
                    'experiment': self.group.experiment.title,
                    'inclusion_criteria':
                        list(self.group.inclusion_criteria.all())
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'inclusion_criteria':
                        list(group2.inclusion_criteria.all())
                }
            ]
        )

    def test_get_returns_groups_of_an_experiment(self):
        experiment2 = create_experiment(1)
        group2 = create_group(1, experiment2)
        group3 = create_group(1, experiment2)

        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment2.nes_id})
        self.client.login(
            username=experiment2.owner.username, password=PASSWORD
        )
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'inclusion_criteria': list(group2.inclusion_criteria.all())
                },
                {
                    'id': group3.id,
                    'title': group3.title,
                    'description': group3.description,
                    'experiment': group3.experiment.title,
                    'inclusion_criteria': list(group3.inclusion_criteria.all())
                }
            ]
        )
        self.client.logout()

    def test_POSTing_a_new_group(self):
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_experiment_groups-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_group = Group.objects.last()
        self.assertEqual(new_group.title, 'A title')

    def test_POSTing_new_group_associates_with_last_experiment_version(self):
        experiment_v2 = create_next_version_experiment(self.experiment)
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_experiment_groups-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description'
            }
        )
        self.client.logout()
        # can retrieve last because we just post new group
        new_group = Group.objects.last()
        self.assertEqual(new_group.experiment.id, experiment_v2.id)

    def test_POSTing_new_group_adds_pre_existent_classification_of_diseases(self):
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_experiment_groups-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                'inclusion_criteria': [
                    {'code': 'A00'}, {'code': 'A1782'}, {'code': 'A3681'},
                    {'code': 'A74'}
                ]
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_group = Group.objects.last()
        self.assertEqual(new_group.inclusion_criteria.all().count(), 4)
        for inclusion_criteria in new_group.inclusion_criteria.all():
            self.assertEqual(inclusion_criteria,
                             ClassificationOfDiseases.objects.get(
                                 code=inclusion_criteria.code))
        self.client.logout()

    def test_POSTing_new_group_with_non_existing_code_saves_not_recognized_code(self):
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_experiment_groups-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                'inclusion_criteria': [
                    {'code': 'A009647'}, {'code': 'Z034754'}
                ]
            }, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_group = Group.objects.last()
        self.assertEqual(new_group.inclusion_criteria.all().count(), 2)
        for inclusion_criteria in new_group.inclusion_criteria.all():
            self.assertEqual(inclusion_criteria,
                             ClassificationOfDiseases.objects.get(
                                 code=inclusion_criteria.code))
            self.assertEqual(
                inclusion_criteria.description, 'Code not recognized'
            )
            self.assertEqual(
                inclusion_criteria.abbreviated_description,
                'Code not recognized'
            )
        self.client.logout()


class PublicationsAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment = create_experiment(1, self.owner)
        self.publication = create_publication(self.experiment)

    def test_GET_returns_all_publications_short_url(self):
        publication2 = create_publication(self.experiment)
        list_url = reverse('api_publications-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.publication.id,
                    'title': self.publication.title,
                    'citation': self.publication.citation,
                    'url': self.publication.url,
                    'experiment': self.publication.experiment.title
                },
                {
                    'id': publication2.id,
                    'title': publication2.title,
                    'citation': publication2.citation,
                    'url': publication2.url,
                    'experiment': publication2.experiment.title
                }
            ]
        )

    def test_GET_returns_all_publications_long_url(self):
        publication2 = create_publication(self.experiment)
        list_url = reverse(
            'api_experiment_publications-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': self.publication.id,
                    'title': self.publication.title,
                    'citation': self.publication.citation,
                    'url': self.publication.url,
                    'experiment': self.publication.experiment.title
                },
                {
                    'id': publication2.id,
                    'title': publication2.title,
                    'citation': publication2.citation,
                    'url': publication2.url,
                    'experiment': publication2.experiment.title
                }
            ]
        )

    def test_POSTing_a_new_publication(self):
        self.client.login(username=self.experiment.owner, password=PASSWORD)
        list_url = reverse(
            'api_experiment_publications-list',
            kwargs={'experiment_nes_id': self.experiment.nes_id}
        )
        response = self.client.post(
            list_url,
            {
                'title': 'Ein Titel',
                'citation': 'Ein Zitat',
                'url': 'http://brasil247.com'
            }
        )
        self.client.logout()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_publication = Publication.objects.last()
        self.assertEqual(new_publication.title, 'Ein Titel')

    def test_POSTing_new_publication_associates_with_last_experiment_version(self):
        experiment_v2 = create_next_version_experiment(self.experiment)
        self.client.login(
            username=self.owner.username, password=PASSWORD
        )
        list_url = reverse('api_experiment_publications-list', kwargs={
            'experiment_nes_id': experiment_v2.nes_id})
        self.client.post(
            list_url,
            {
                'title': 'Ein Titel Version zwei',
                'citation': 'Ein Zitat Version zwei',
                'url': 'http://diariodocentrodomundo.com.br'
            }
        )
        self.client.logout()
        new_publication = Publication.objects.last()
        self.assertEqual(new_publication.experiment.id, experiment_v2.id)


class QuestionnaireStepAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment = create_experiment(1, self.owner)
        self.group = create_group(1, self.experiment)

    @skip
    def test_get_returns_all_questionnairesteps_short_url(self):
        # TODO: implement it!
        pass

    @skip
    def test_get_returns_all_questionnairesteps_long_url(self):
        # TODO: implement it!
        pass

    def test_POSTing_a_new_questionnairestep(self):
        self.client.login(
            username=self.owner.username, password=PASSWORD
        )
        list_url = reverse(
            'api_questionnaire_step-list', kwargs={'pk': self.group.id}
        )
        response = self.client.post(
            list_url,
            {
                'code': 'U2',
                'identification': 'Banda Irlandesa',
                'numeration': '2',
                'type': Step.QUESTIONNAIRE,
                'order': '20'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_questionnairestep = Questionnaire.objects.last()
        self.assertEqual(new_questionnairestep.code, 'U2')


class QuestionnaireLanguageAPITest(APITestCase):

    def setUp(self):
        self.owner = create_owner(username='labX')
        self.experiment = create_experiment(1, self.owner)
        self.group = create_group(1, self.experiment)

    @skip
    def test_get_returns_all_questionnairelanguages_short_url(self):
        # TODO: implement it!
        pass

    @skip
    def test_get_returns_all_questionnairelanguages_long_url(self):
        # TODO: implement it!
        pass

    def test_POSTing_a_new_questionnairelanguage_not_default(self):
        questionnaire = create_questionnaire(1, 'code0', self.group)
        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse('api_questionnaire_language-list',
                           kwargs={'pk': questionnaire.id})
        response = self.client.post(
            list_url,
            {
                # we put a Russian questionnaire language tests helper
                # creates a pt-br questionnaire language
                'language_code': 'ru',
                'survey_name': 'Um lindo questionário',
                'survey_metadata': 'Uma _string_ gigante representando um '
                                   'questionário que vem do NES que está em '
                                   'csv'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_questionnaire_language = QuestionnaireLanguage.objects.last()
        self.assertEqual(
            new_questionnaire_language.survey_name, 'Um lindo questionário'
        )

    def test_POSTing_a_new_questionnairelanguage_default(self):
        questionnaire = create_questionnaire(1, 'q1', self.group)

        self.client.login(username=self.owner.username, password=PASSWORD)
        list_url = reverse(
            'api_questionnaire_language-list', kwargs={'pk': questionnaire.id}
        )
        response = self.client.post(
            list_url,
            {
                'language_code': 'en',
                'survey_name': 'Um lindo questionário que é o default',
                'survey_metadata': 'Uma "string" grande representando um '
                                   'questionário que vem do NES que está em '
                                   'csv e que é o default',
                'is_default': True
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_questionnaire_language = QuestionnaireLanguage.objects.last()
        self.assertEqual(
            new_questionnaire_language.survey_name,
            'Um lindo questionário que é o default'
        )
        questionnaire_default_language = \
            QuestionnaireDefaultLanguage.objects.last()
        self.assertEqual(
            questionnaire_default_language.questionnaire,
            questionnaire
        )
        self.assertEqual(
            questionnaire_default_language.questionnaire_language,
            new_questionnaire_language
        )

    def test_POSTing_new_questionnairelanguage_cant_create_more_default_languages(self):
        pass


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ExperimentalProtocolAPITest(APITestCase):

    def test_POSTing_new_experimental_protocol_with_image_creates_image_file(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        experiment = create_experiment(1, owner, Experiment.TO_BE_ANALYSED)
        group = create_group(1, experiment)
        image_file = generate_image_file(filename='datei.jpg')
        url = reverse(
            'api_group_experimental_protocol-list',
            kwargs={'pk': group.id}
        )
        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            url,
            {
                'image': image_file,
                'textual_description': 'Ein wunderbar Beschreibung'
            },
            format='multipart'
        )
        self.client.logout()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_exp_protocol = ExperimentalProtocol.objects.last()
        self.assertEqual(
            new_exp_protocol.textual_description, 'Ein wunderbar Beschreibung'
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(TEMP_MEDIA_ROOT, 'uploads',
                             datetime.utcnow().strftime('%Y/%m/%d'),
                             'datei.jpg'
                             )
            )
        )
