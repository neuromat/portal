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
from experiments.helpers import generate_image_file
from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator, ClassificationOfDiseases, Questionnaire, Step, \
    QuestionnaireLanguage, QuestionnaireDefaultLanguage, Publication, \
    ExperimentalProtocol
from experiments.tests.tests_helper import global_setup_ut, apply_setup, \
    create_experiment, create_group, create_questionnaire


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@apply_setup(global_setup_ut)
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ExperimentAPITest(APITestCase):
    list_url = reverse('api_experiments-list')

    def setUp(self):
        global_setup_ut()

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT)

    def test_get_returns_all_experiments(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')

        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
        experiment3 = Experiment.objects.get(nes_id=2, owner=owner2)
        experiment4 = Experiment.objects.get(nes_id=3, owner=owner1)
        response = self.client.get(self.list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': experiment1.id,
                    'title': experiment1.title,
                    'description': experiment1.description,
                    'data_acquisition_done':
                        experiment1.data_acquisition_done,
                    'nes_id': experiment1.nes_id,
                    'owner': experiment1.owner.username,
                    'status': experiment1.status,
                    'sent_date': experiment1.sent_date.strftime('%Y-%m-%d'),
                    'project_url': experiment1.project_url,
                    'ethics_committee_url': experiment1.ethics_committee_url,
                    'ethics_committee_file': None

                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'nes_id': experiment2.nes_id,
                    'owner': experiment2.owner.username,
                    'status': experiment2.status,
                    'sent_date': experiment2.sent_date.strftime('%Y-%m-%d'),
                    'project_url': experiment1.project_url,
                    'ethics_committee_url': experiment1.ethics_committee_url,
                    'ethics_committee_file': None
                },
                {
                    'id': experiment3.id,
                    'title': experiment3.title,
                    'description': experiment3.description,
                    'data_acquisition_done':
                        experiment3.data_acquisition_done,
                    'nes_id': experiment3.nes_id,
                    'owner': experiment3.owner.username,
                    'status': experiment3.status,
                    'sent_date': experiment3.sent_date.strftime('%Y-%m-%d'),
                    'project_url': experiment3.project_url,
                    'ethics_committee_url': experiment3.ethics_committee_url,
                    'ethics_committee_file': 'http://testserver' +
                                             experiment3.ethics_committee_file.url
                },
                {
                    'id': experiment4.id,
                    'title': experiment4.title,
                    'description': experiment4.description,
                    'data_acquisition_done':
                        experiment4.data_acquisition_done,
                    'nes_id': experiment4.nes_id,
                    'owner': experiment4.owner.username,
                    'status': experiment4.status,
                    'sent_date': experiment4.sent_date.strftime('%Y-%m-%d'),
                    'project_url': experiment4.project_url,
                    'ethics_committee_url': experiment4.ethics_committee_url,
                    'ethics_committee_file': None
                },
            ]
        )

    def test_POSTing_a_new_experiment(self):
        owner = User.objects.get(username='lab1')
        image_file = generate_image_file(100, 100, 'test.jpg')
        self.client.login(username=owner.username, password='nep-lab1')
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
        new_experiment = Experiment.objects.get(nes_id=17, owner=owner)
        self.assertEqual(new_experiment.title, 'New experiment')

    def test_POSTing_new_experiment_send_email_to_trustees(self):
        trustees = User.objects.filter(groups__name='trustees')
        emails = []
        for trustee in trustees:
            emails += trustee.email

        self.send_mail_called = False

        # TODO: refactor using Python Mock Library
        def fake_send_mail(subject, body, from_email, to):
            self.send_mail_called = True
            self.subject = subject
            self.body = body
            self.from_email = from_email
            self.to = to

        api.send_mail = fake_send_mail

        owner = User.objects.get(username='lab1')
        self.client.login(username=owner.username, password='nep-lab1')
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
        owner = User.objects.get(username='lab1')
        # get experiment created in setUp: it has version=1
        experiment = Experiment.objects.get(nes_id=1, owner=owner)

        # Post experiment already sended to portal
        self.client.login(username=owner.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New title',
                'description': 'New description',
                'nes_id': experiment.nes_id,
                'sent_date': datetime.utcnow().strftime('%Y-%m-%d')
            }
        )
        self.client.logout()

        # We have just posted the experiment so we can get the last one
        experiment_version_2 = Experiment.objects.last()
        self.assertEqual(experiment_version_2.version, 2)

    def test_PATCHing_an_existing_experiment(self):
        # TODO: get last version
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        detail_url = reverse(
            'api_experiments-detail',
            kwargs={'experiment_nes_id': experiment.nes_id}
        )
        self.client.login(username=owner.username, password='nep-lab1')
        resp_patch = self.client.patch(
            detail_url,
            {
                'title': 'Changed experiment',
                'description': 'Changed description',
                'status': experiment.TO_BE_ANALYSED,
            }
        )
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)

        # Test experiment updated
        updated_experiment = Experiment.objects.get(
            nes_id=experiment.nes_id, owner=owner)
        detail_url2 = reverse(
            'api_experiments-detail',
            kwargs={'experiment_nes_id': updated_experiment.nes_id}
        )
        resp_get = self.client.get(detail_url2)
        self.assertEqual(
            json.loads(resp_get.content.decode('utf8')),
            {
                'id': updated_experiment.id,
                'title': 'Changed experiment',
                'description': 'Changed description',
                'data_acquisition_done':
                    updated_experiment.data_acquisition_done,
                'nes_id': updated_experiment.nes_id,
                'owner': updated_experiment.owner.username,
                'status': updated_experiment.status,
                'sent_date': updated_experiment.sent_date.strftime('%Y-%m-%d'),
                'project_url': updated_experiment.project_url,
                'ethics_committee_url':
                    updated_experiment.ethics_committee_url,
                'ethics_committee_file': None
            }
        )
        self.client.logout()

    def test_POSTing_experiments_creates_version_one(self):
        owner = User.objects.get(username='lab1')
        self.client.login(username=owner.username, password='nep-lab1')
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

    def test_PATCHing_experiment_with_to_be_analysed_status_make_available_download_experiment(self):
        # First we post a new experiment through API
        owner = User.objects.get(username='lab1')
        self.client.login(username=owner.username, password='nep-lab1')
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

        # Now we can test for downloading experiment
        url = reverse('download-view', kwargs={'experiment_id': experiment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename=%s' % smart_str('download.zip')
        )


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

        # TODO: IMPORTANT! Test client can't POST (PUT etc.) to Study model
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
        list_url = reverse('api_researchers-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': researcher1.id,
                    'name': researcher1.name,
                    'email': researcher1.email,
                    'study': researcher1.study.title
                },
                {
                    'id': researcher2.id,
                    'name': researcher2.name,
                    'email': researcher2.email,
                    'study': researcher2.study.title
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
                    'name': researcher.name,
                    'email': researcher.email,
                    'study': researcher.study.title
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
                'name': 'João das Rosas',
                'email': 'joao@rosas.com',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_researcher = Researcher.objects.last()
        self.assertEqual(new_researcher.name, 'João das Rosas')


@apply_setup(global_setup_ut)
class CollaboratorAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_collaborators_short_url(self):
        collaborator1 = Collaborator.objects.first()
        collaborator2 = Collaborator.objects.last()
        list_url = reverse('api_collaborators-list')
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': collaborator1.id,
                    'name': collaborator1.name,
                    'team': collaborator1.team,
                    'coordinator': collaborator1.coordinator,
                    'study': collaborator1.study.title,
                },
                {
                    'id': collaborator2.id,
                    'name': collaborator2.name,
                    'team': collaborator2.team,
                    'coordinator': collaborator2.coordinator,
                    'study': collaborator2.study.title,
                }
            ]
        )

    def test_get_returns_all_collaborators_long_url(self):
        study = Study.objects.last()
        collaborator = Collaborator.objects.create(
            name='Cristiano', team='Real', coordinator=True, study=study
        )
        list_url = reverse('api_study_collaborators-list',
                           kwargs={'pk': study.id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': collaborator.id,
                    'name': collaborator.name,
                    'team': collaborator.team,
                    'coordinator': True,
                    'study': collaborator.study.title
                }
            ]
        )

    def test_POSTing_a_new_collaborator(self):
        study = Study.objects.last()
        owner = User.objects.get(username='lab2')
        self.client.login(username=owner.username, password='nep-lab2')
        list_url = reverse('api_study_collaborators-list',
                           kwargs={'pk': study.id})
        response = self.client.post(
            list_url,
            {
                'name': 'Rolando Lero',
                'email': 'rolando@example.com',
                'team': 'Escolinha do Prof. Raimundo',
                'coordinator': True
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_collaborator = Collaborator.objects.last()
        self.assertEqual(new_collaborator.name, 'Rolando Lero')


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
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        group1 = Group.objects.get(id=1, experiment=experiment)
        group2 = Group.objects.get(id=2, experiment=experiment)
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
        self.client.login(username=owner.username, password='nep-lab1')
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
