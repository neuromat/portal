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
from experiments.tests.tests_helper import global_setup_ut, apply_setup, \
    create_experiment, create_group, create_questionnaire, \
    create_experiment_researcher, create_next_version_experiment, PASSWORD, \
    create_owner, create_trustee_user, create_study

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
        self.assertEqual(self.to, emails)

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


@apply_setup(global_setup_ut)
class StudyAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_studies_short_url(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')

        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
        experiment3 = Experiment.objects.get(nes_id=2, owner=owner2)

        study1 = Study.objects.get(experiment=experiment1)
        study2 = Study.objects.get(experiment=experiment2)
        study3 = Study.objects.get(experiment=experiment3)
        list_url = reverse('api_studies-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': study1.id,
                    'title': study1.title,
                    'description': study1.description,
                    'start_date': study1.start_date.strftime('%Y-%m-%d'),
                    'end_date': study1.end_date,
                    'experiment': study1.experiment.title,
                    'keywords': list(study1.keywords.values('name'))
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
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')

        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
        experiment3 = Experiment.objects.get(nes_id=2, owner=owner2)

        study1 = Study.objects.get(experiment=experiment1)
        study2 = Study.objects.get(experiment=experiment2)
        study3 = Study.objects.get(experiment=experiment3)
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': experiment1.nes_id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': study1.id,
                    'title': study1.title,
                    'description': study1.description,
                    'start_date': study1.start_date.strftime('%Y-%m-%d'),
                    'end_date': study1.end_date,
                    'experiment': study1.experiment.title,
                    'keywords': list(study1.keywords.values('name'))
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
        owner = User.objects.get(username='lab2')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        study = Study.objects.get(experiment=experiment)
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        self.client.login(username=owner.username, password='nep-lab2')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': study.id,
                    'title': study.title,
                    'description': study.description,
                    'start_date': study.start_date.strftime('%Y-%m-%d'),
                    'end_date': study.end_date,
                    'experiment': 'Experiment 2',
                    'keywords': list(study.keywords.values('name'))
                },
            ]
        )

    def test_POSTing_a_new_study(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.create(
            title='An experiment', nes_id=17, owner=owner,
            version=1, sent_date=datetime.utcnow()
        )
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
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


@apply_setup(global_setup_ut)
class ResearcherAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_researchers_short_url(self):
        researcher1 = Researcher.objects.first()
        researcher2 = Researcher.objects.last()
        list_url = reverse('api_study_researchers-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': researcher1.id,
                    'first_name': researcher1.first_name,
                    'last_name': researcher1.last_name,
                    'email': researcher1.email,
                    'study': researcher1.study.title,
                    'citation_name': researcher1.citation_name
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
        study = Study.objects.last()
        researcher = Researcher.objects.create(study=study)
        list_url = reverse('api_study_researcher-list',
                           kwargs={'pk': study.id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': researcher.id,
                    'first_name': researcher.first_name,
                    'last_name': researcher.last_name,
                    'email': researcher.email,
                    'study': researcher.study.title,
                    'citation_name': researcher.citation_name
                }
            ]
        )

    def test_POSTing_a_new_researcher(self):
        study = Study.objects.last()
        owner = User.objects.get(username='lab1')
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_study_researcher-list',
                           kwargs={'pk': study.id})
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
                    'citation_name': self.experiment_researcher1.citation_name
                },
                {
                    'id': self.experiment_researcher2.id,
                    'first_name': self.experiment_researcher2.first_name,
                    'last_name': self.experiment_researcher2.last_name,
                    'email': self.experiment_researcher2.email,
                    'institution': self.experiment_researcher2.institution,
                    'experiment': self.experiment_researcher2.experiment.title,
                    'citation_name': self.experiment_researcher2.citation_name
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


@apply_setup(global_setup_ut)
class GroupAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_groups_short_url(self):
        # We've created 5 groups in global_setup_ut()
        groups = []
        for group in Group.objects.all():
            groups.append(group)
        list_url = reverse('api_groups-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': groups[0].id,
                    'title': groups[0].title,
                    'description': groups[0].description,
                    'experiment': groups[0].experiment.title,
                    'inclusion_criteria':
                        list(groups[0].inclusion_criteria.all())
                },
                {
                    'id': groups[1].id,
                    'title': groups[1].title,
                    'description': groups[1].description,
                    'experiment': groups[1].experiment.title,
                    'inclusion_criteria':
                        list(groups[1].inclusion_criteria.all())
                },
                {
                    'id': groups[2].id,
                    'title': groups[2].title,
                    'description': groups[2].description,
                    'experiment': groups[2].experiment.title,
                    'inclusion_criteria':
                        list(groups[2].inclusion_criteria.all())
                },
                {
                    'id': groups[3].id,
                    'title': groups[3].title,
                    'description': groups[3].description,
                    'experiment': groups[3].experiment.title,
                    'inclusion_criteria':
                        list(groups[3].inclusion_criteria.all())
                },
                {
                    'id': groups[4].id,
                    'title': groups[4].title,
                    'description': groups[4].description,
                    'experiment': groups[4].experiment.title,
                    'inclusion_criteria':
                        list(groups[4].inclusion_criteria.all())
                },
                {
                    'id': groups[5].id,
                    'title': groups[5].title,
                    'description': groups[5].description,
                    'experiment': groups[5].experiment.title,
                    'inclusion_criteria':
                        list(groups[5].inclusion_criteria.all())
                },
            ]
        )

    def test_get_returns_all_groups_long_url(self):
        owner1 = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner1)
        # We've created 5 groups in global_setup_ut()
        groups = []
        for group in Group.objects.all():
            groups.append(group)
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': groups[0].id,
                    'title': groups[0].title,
                    'description': groups[0].description,
                    'experiment': groups[0].experiment.title,
                    'inclusion_criteria':
                        list(groups[0].inclusion_criteria.all())
                },
                {
                    'id': groups[1].id,
                    'title': groups[1].title,
                    'description': groups[1].description,
                    'experiment': groups[1].experiment.title,
                    'inclusion_criteria':
                        list(groups[1].inclusion_criteria.all())
                },
                {
                    'id': groups[2].id,
                    'title': groups[2].title,
                    'description': groups[2].description,
                    'experiment': groups[2].experiment.title,
                    'inclusion_criteria':
                        list(groups[2].inclusion_criteria.all())
                },
                {
                    'id': groups[3].id,
                    'title': groups[3].title,
                    'description': groups[3].description,
                    'experiment': groups[3].experiment.title,
                    'inclusion_criteria':
                        list(groups[3].inclusion_criteria.all())
                },
                {
                    'id': groups[4].id,
                    'title': groups[4].title,
                    'description': groups[4].description,
                    'experiment': groups[4].experiment.title,
                    'inclusion_criteria':
                        list(groups[4].inclusion_criteria.all())
                },
                {
                    'id': groups[5].id,
                    'title': groups[5].title,
                    'description': groups[5].description,
                    'experiment': groups[5].experiment.title,
                    'inclusion_criteria':
                        list(groups[5].inclusion_criteria.all())
                },
            ]
        )

    def test_get_returns_groups_of_an_experiment(self):
        experiment = create_experiment(1)
        group1 = create_group(1, experiment)
        group2 = create_group(1, experiment)

        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        self.client.login(
            username=experiment.owner.username, password=PASSWORD
        )
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': group1.id,
                    'title': group1.title,
                    'description': group1.description,
                    'experiment': group1.experiment.title,
                    'inclusion_criteria': list(group1.inclusion_criteria.all())
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'inclusion_criteria': list(group2.inclusion_criteria.all())
                }
            ]
        )
        self.client.logout()

    def test_POSTing_a_new_group(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
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
        owner = User.objects.get(username='lab1')
        experiment_v1 = Experiment.objects.get(owner=owner, nes_id=1,
                                               version=1)
        experiment_v2 = Experiment.objects.create(
            nes_id=experiment_v1.nes_id, version=2,
            sent_date=datetime.utcnow(), owner=owner
        )
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment_v1.nes_id})
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
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                # we post inclusion_criteria's that exists in
                # ClassificationOfDiseases table. We create entries in tests
                # helper (this table is pre-populated in db in production
                # and homologation environments )
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
        # cod = classification of diseases
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                # we post inclusion_criteria's that exists in
                # ClassificationOfDiseases table. We create entries in tests
                # helper (this table is pre-populated in db in production
                # and homologation environments )
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


@apply_setup(global_setup_ut)
class PublicationsAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()
        Experiment.objects.create(
            title='Ein Experiment', nes_id=10,
            owner=User.objects.get(username='lab1'),
            version=1, sent_date=datetime.utcnow(),
            status=Experiment.RECEIVING,
            trustee=User.objects.get(username='claudia')
        )

    def test_GET_returns_all_publications_short_url(self):
        p_list = list()
        for publication in Publication.objects.all():
            p_list.append({
                'id': publication.id,
                'title': publication.title,
                'citation': publication.citation,
                'url': publication.url,
                'experiment': publication.experiment.title
            })

        list_url = reverse('api_publications-list')
        response = self.client.get(list_url)
        self.assertEqual(json.loads(response.content.decode('utf8')), p_list)

    def test_GET_returns_all_publications_long_url(self):
        p_list = list()
        for publication in Publication.objects.all():
            p_list.append({
                'id': publication.id,
                'title': publication.title,
                'citation': publication.citation,
                'url': publication.url,
                'experiment': publication.experiment.title
            })

        # last experiment approved has publications created in tests helper
        experiment = Experiment.objects.filter(
            status=Experiment.APPROVED
        ).last()

        list_url = reverse(
            'api_experiment_publications-list',
            kwargs={'experiment_nes_id': experiment.nes_id}
        )
        response = self.client.get(list_url)
        self.assertEqual(json.loads(response.content.decode('utf8')), p_list)

    def test_POSTing_a_new_publication(self):
        # we've created an experiment in setUp method
        experiment = Experiment.objects.last()
        self.client.login(username=experiment.owner, password='nep-lab1')
        list_url = reverse(
            'api_experiment_publications-list',
            kwargs={'experiment_nes_id': experiment.nes_id}
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

    def test_POSTing_new_publication_associates_with_last_experiment_version(
            self):
        # we've created an experiment in setUp method
        experiment_v1 = Experiment.objects.last()
        experiment_v2 = Experiment.objects.create(
            nes_id=experiment_v1.nes_id, version=2,
            sent_date=datetime.utcnow(), owner=experiment_v1.owner
        )
        self.client.login(
            username=experiment_v1.owner.username, password='nep-lab1'
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
        global_setup_ut()

    @skip
    def test_get_returns_all_questionnairesteps_short_url(self):
        # TODO: implement it!
        pass

    @skip
    def test_get_returns_all_questionnairesteps_long_url(self):
        # TODO: implement it!
        pass

    def test_POSTing_a_new_questionnairestep(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        group = Group.objects.filter(experiment=experiment).first()
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_questionnaire_step-list',
                           kwargs={'pk': group.id})
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
        global_setup_ut()
        owner = User.objects.create_user(
            username='labor1', password='nep-labor1'
        )
        create_experiment(1, owner, Experiment.APPROVED)

    @skip
    def test_get_returns_all_questionnairelanguages_short_url(self):
        # TODO: implement it!
        pass

    @skip
    def test_get_returns_all_questionnairelanguages_long_url(self):
        # TODO: implement it!
        pass

    def test_POSTing_a_new_questionnairelanguage_not_default(self):
        owner = User.objects.get(username='lab1')
        questionnaire = Questionnaire.objects.first()
        self.client.login(username=owner.username, password='nep-lab1')
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
        experiment = Experiment.objects.last()
        owner = User.objects.last()
        group = create_group(1, experiment)
        questionnaire = create_questionnaire(1, 'q1', group)

        self.client.login(username=owner.username, password='nep-labor1')
        list_url = reverse('api_questionnaire_language-list',
                           kwargs={'pk': questionnaire.id})
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
