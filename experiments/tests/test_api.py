import io

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from experiments.models import Experiment, Study, Group, Researcher, \
    Collaborator
from experiments.tests.helpers import generate_image_file
from experiments.tests.tests_helper import global_setup_ut, apply_setup


@apply_setup(global_setup_ut)
class ExperimentAPITest(APITestCase):
    list_url = reverse('api_experiments-list')

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_experiments(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')

        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
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
                    'ethics_committee_file': None,
                    'owner': experiment1.owner.username,
                    'status': experiment1.status,
                    'protocol_components': [],
                    'sent_date': experiment1.sent_date.strftime('%Y-%m-%d')
                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'nes_id': experiment2.nes_id,
                    'ethics_committee_file': None,
                    'owner': experiment2.owner.username,
                    'status': experiment2.status,
                    'protocol_components': [],
                    'sent_date': experiment2.sent_date.strftime('%Y-%m-%d')
                }
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

        self.client.logout()

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
                'ethics_committee_file': None,
                'owner': updated_experiment.owner.username,
                'protocol_components': [],
                'status': updated_experiment.status,
                'sent_date': updated_experiment.sent_date.strftime('%Y-%m-%d')
            }
        )
        self.client.logout()

    def test_POSTing_experiments_creates_versions_one(self):
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


@apply_setup(global_setup_ut)
class StudyAPITest(APITestCase):

    def setUp(self):
        global_setup_ut()

    def test_get_returns_all_studies_short_url(self):
        study1 = Study.objects.first()
        study2 = Study.objects.last()
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
                    'experiment': 'Experiment 1',
                    'keywords': list(study1.keywords.all())
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'experiment': 'Experiment 2',
                    'keywords': list(study1.keywords.all())
                },
            ]
        )

    def test_get_returns_all_studies_long_url(self):
        owner = User.objects.get(username='lab2')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        study1 = Study.objects.first()
        study2 = Study.objects.last()
        list_url = reverse('api_experiment_studies-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
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
                    'experiment': 'Experiment 1',
                    'keywords': list(study1.keywords.all())
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'experiment': 'Experiment 2',
                    'keywords': list(study2.keywords.all())
                },
            ]
        )

    def test_get_returns_all_studies_of_an_experiment(self):
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
                    'keywords': list(study.keywords.all())
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

        # TODO: IMPORTANT! Test client can't POST (PUT etc.) to a model without
        # been its owner. This requires adds, at first, an owner to all
        # models, and ensure that only same client can POST to that model.

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
        study = Study.objects.last()
        researcher2 = Researcher.objects.create(
            name='Torquato Neto',
            email='tn@example.com', study=study
        )
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
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
        # TODO: refactor! Include in global setup
        Group.objects.create(
            title='A title', description='A description',
            experiment=experiment1
        )
        Group.objects.create(
            title='Other title', description='Other description',
            experiment=experiment1
        )
        Group.objects.create(
            title='A title', description='A description',
            experiment=experiment2
        )

    def test_get_returns_all_groups_short_url(self):
        group1 = Group.objects.get(id=1)
        group2 = Group.objects.get(id=2)
        group3 = Group.objects.get(id=3)
        list_url = reverse('api_groups-list')
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

    def test_get_returns_all_groups_long_url(self):
        owner1 = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner1)
        group1 = Group.objects.first()
        group2 = Group.objects.get(id=2)
        group3 = Group.objects.get(id=3)
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'experiment_nes_id': experiment.nes_id})
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
        new_group = Group.objects.first()
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
        new_group = Group.objects.last()  # can retrieve last because we
        # just post new group
        self.assertEqual(new_group.experiment.id, experiment_v2.id)


# @apply_setup(global_setup_ut)
# class ProtocolComponentAPITest(APITestCase):
#     list_url = reverse('api_protocol_components-list')
#
#     def setUp(self):
#         global_setup_ut()
#         owner = User.objects.get(username='lab1')
#         experiment = Experiment.objects.get(owner=owner)
#         ProtocolComponent.objects.create(
#             identification='An identification',
#             component_type='A component type',
#             nes_id=1, experiment=experiment, owner=owner
#         )
#         ProtocolComponent.objects.create(
#             identification='Other identification',
#             component_type='Other component type',
#             nes_id=2, experiment=experiment, owner=owner
#         )
#
#     def test_get_returns_all_protocolcomponents(self):
#         protocol_component1 = ProtocolComponent.objects.get(nes_id=1)
#         protocol_component2 = ProtocolComponent.objects.get(nes_id=2)
#         response = self.client.get(self.list_url)
#         self.assertEqual(
#             json.loads(response.content.decode('utf8')),
#             [
#                 {
#                     'id': protocol_component1.id,
#                     'identification': protocol_component1.identification,
#                     'description': protocol_component1.description,
#                     'duration_value': protocol_component1.duration_value,
#                     'component_type': protocol_component1.component_type,
#                     'nes_id': protocol_component1.nes_id,
#                     'experiment': protocol_component1.experiment.title,
#                     'owner': protocol_component1.owner.username
#                 },
#                 {
#                     'id': protocol_component2.id,
#                     'identification': protocol_component2.identification,
#                     'description': protocol_component2.description,
#                     'duration_value': protocol_component2.duration_value,
#                     'component_type': protocol_component2.component_type,
#                     'nes_id': protocol_component2.nes_id,
#                     'experiment': protocol_component2.experiment.title,
#                     'owner': protocol_component2.owner.username
#                 }
#             ]
#         )
#
#     def test_POSTing_a_new_protocolcomponent(self):
#         owner = User.objects.get(username='lab1')
#         experiment = Experiment.objects.get(owner=owner)
#
#         self.client.login(username=owner.username, password='nep-lab1')
#         response = self.client.post(
#             self.list_url,
#             {
#                 'identification': 'An identification',
#                 'description': 'A description',
#                 'duration_value': 4,
#                 'component_type': 'A component type',
#                 'nes_id': 17,
#                 'experiment': experiment.nes_id
#             }
#         )
#         self.client.logout()
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         new_protocolcomponent = ProtocolComponent.objects.first()
#         self.assertEqual(new_protocolcomponent.identification,
#                          'An identification')
#
#     def test_PUTing_an_existing_protocolcomponent(self):
#         owner = User.objects.get(username='lab1')
#         experiment = Experiment.objects.get(owner=owner)
#         protocol_component = ProtocolComponent.objects.get(
#             nes_id=1, owner=owner
#         )
#         detail_url1 = reverse(
#             'api_protocol_components-detail',
#             kwargs={'nes_id': protocol_component.nes_id}
#         )
#         self.client.login(username=owner.username, password='nep-lab1')
#         resp_patch = self.client.patch(
#             detail_url1,
#             {
#                 'identification': 'Changed identification',
#                 'description': 'Changed description',
#                 'duration_value': 2,
#                 'component_type': 'Changed component type',
#                 'experiment': experiment.nes_id
#             }
#         )
#         self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
#
#         # test protocol_component updated
#         updated_protocol_component = ProtocolComponent.objects.get(
#             nes_id=protocol_component.nes_id, owner=owner)
#         detail_url2 = reverse(
#             'api_protocol_components-detail',
#             kwargs={'nes_id': updated_protocol_component.nes_id}
#         )
#         resp_get = self.client.get(detail_url2)
#         self.assertEqual(
#             json.loads(resp_get.content.decode('utf8')),
#             {
#                 'id': updated_protocol_component.id,
#                 'identification': 'Changed identification',
#                 'description': 'Changed description',
#                 'duration_value': 2,
#                 'component_type': 'Changed component type',
#                 'nes_id': updated_protocol_component.nes_id,
#                 'experiment': updated_protocol_component.experiment.title,
#                 'owner': updated_protocol_component.owner.username
#             }
#         )
#         self.client.logout()
