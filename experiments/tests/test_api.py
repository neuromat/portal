import io

from PIL import Image
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from experiments.models import Experiment, Study, \
    ProtocolComponent, ExperimentStatus, Group


def global_setup(self):
    """
    This setup creates basic object models that are used in tests bellow.
    :param self: 
    """
    owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
    owner2 = User.objects.create_user(username='lab2', password='nep-lab2')

    exp_status = ExperimentStatus.objects.create(tag='to_be_approved')

    experiment1 = Experiment.objects.create(
        title='Experiment 1', nes_id=1, owner=owner1, status=exp_status,
        version=1, sent_date=datetime.utcnow()
    )
    experiment2 = Experiment.objects.create(
        title='Experiment 2', nes_id=1, owner=owner2, status=exp_status,
        version=1, sent_date=datetime.utcnow()
    )

    Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                         experiment=experiment1, owner=owner1)
    Study.objects.create(nes_id=1, start_date=datetime.utcnow(),
                         experiment=experiment2, owner=owner2)


def apply_setup(setup_func):
    """
    Defines a decorator that uses my_setup method.
    :param setup_func: my_setup function
    :return: wrapper 
    """
    def wrap(cls):
        cls.setup = setup_func
        return cls
    return wrap

# class ResearcherAPITest(APITestCase):
#     list_url = reverse('api_researchers-list')
#
#     def test_get_returns_all_researchers(self):
#         owner = User.objects.create_user(username='lab1')
#         researcher1 = Researcher.objects.create(nes_id=1, owner=owner)
#         researcher2 = Researcher.objects.create(nes_id=2, owner=owner)
#         response = self.client.get(self.list_url)
#         self.assertEqual(
#             json.loads(response.content.decode('utf8')),
#             [
#                 {
#                     'id': researcher1.id,
#                     'first_name': researcher1.first_name,
#                     'surname': researcher1.surname,
#                     'email': researcher1.email,
#                     'studies': [],
#                     'nes_id': researcher1.nes_id,
#                     'owner': researcher1.owner.username
#                 },
#                 {
#                     'id': researcher2.id,
#                     'first_name': researcher2.first_name,
#                     'surname': researcher2.surname,
#                     'email': researcher2.email,
#                     'studies': [],
#                     'nes_id': researcher2.nes_id,
#                     'owner': researcher2.owner.username
#                 }
#             ]
#         )
#
#     def test_POSTing_a_new_researcher(self):
#         owner = User.objects.create_user(username='lab1', password='nep-lab1')
#         self.client.login(username=owner.username, password='nep-lab1')
#         response = self.client.post(
#             self.list_url,
#             {
#                 'first_name': 'João',
#                 'surname': 'das Rosas',
#                 'email': 'joao@rosas.com',
#                 'nes_id': 1,
#             }
#         )
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.client.logout()
#         new_researcher = Researcher.objects.first()
#         self.assertEqual(new_researcher.first_name, 'João')
#
#     def test_PUTing_an_existing_researcher(self):
#         # TODO: very large test
#         ###
#         # First we post a new researcher then we test PUTing
#         ###
#         # An owner post a researcher
#         owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
#         self.client.login(username=owner1.username, password='nep-lab1')
#         self.client.post(
#             self.list_url,
#             {
#                 'first_name': 'João',
#                 'surname': 'das Rosas',
#                 'email': 'joao@rosas.com',
#                 'nes_id': 2,
#             }
#         )
#         self.client.logout()
#
#         # Other owner post a researcher
#         owner2 = User.objects.create_user(username='lab2', password='nep-lab2')
#         self.client.login(username=owner2.username, password='nep-lab2')
#         self.client.post(
#             self.list_url,
#             {
#                 'first_name': 'Pedro',
#                 'surname': 'Santos',
#                 'email': 'pedro@santos.com',
#                 'nes_id': 2,
#             }
#         )
#         self.client.logout()
#
#         ###
#         # Now we test PUTing
#         ###
#         new_researcher = Researcher.objects.get(nes_id=2, owner=owner1)
#         detail_url1 = reverse(
#             'api_researchers-detail', kwargs={'nes_id': new_researcher.nes_id}
#         )
#         self.client.login(username=owner1.username, password='nep-lab1')
#         resp_put = self.client.patch(
#             detail_url1,
#             {
#                 'first_name': 'João Maria',
#                 'surname': 'das Rosas Vermelhas',
#                 'email': 'joao13@dasrosas.com',
#             }
#         )
#         self.assertEqual(resp_put.status_code, status.HTTP_200_OK)
#
#         ###
#         # Finally we test researcher updated
#         ###
#         updated_researcher = Researcher.objects.get(
#             nes_id=new_researcher.nes_id, owner=owner1
#         )
#         detail_url2 = reverse(
#             'api_researchers-detail',
#             kwargs={'nes_id': updated_researcher.nes_id}
#         )
#         resp_get = self.client.get(detail_url2)
#         self.assertEqual(
#             json.loads(resp_get.content.decode('utf8')),
#             {
#                 'id': updated_researcher.id,
#                 'first_name': 'João Maria',
#                 'surname': 'das Rosas Vermelhas',
#                 'email': 'joao13@dasrosas.com',
#                 'studies': [],
#                 'nes_id': updated_researcher.nes_id,
#                 'owner': updated_researcher.owner.username
#             }
#         )
#         self.client.logout()


@apply_setup(global_setup)
class ExperimentAPITest(APITestCase):
    list_url = reverse('api_experiments-list')

    def setUp(self):
        global_setup(self)

    def generate_image_file(self):
        """
        Generates an image file to test upload
        :return: image file
        """
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

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
                    'status': experiment1.status.tag,
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
                    'status': experiment2.status.tag,
                    'protocol_components': [],
                    'sent_date': experiment2.sent_date.strftime('%Y-%m-%d')
                }
            ]
        )

    def test_POSTing_a_new_experiment(self):
        owner = User.objects.get(username='lab1')
        image_file = self.generate_image_file()
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

    def test_PUTing_an_existing_experiment(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        detail_url = reverse(
            'api_experiments-detail', kwargs={'nes_id': experiment.nes_id}
        )
        self.client.login(username=owner.username, password='nep-lab1')
        resp_put = self.client.patch(
            detail_url,
            {
                'title': 'Changed experiment',
                'description': 'Changed description',
            }
        )
        self.assertEqual(resp_put.status_code, status.HTTP_200_OK)

        # Test experiment updated
        updated_experiment = Experiment.objects.get(
            nes_id=experiment.nes_id, owner=owner)
        detail_url2 = reverse(
            'api_experiments-detail',
            kwargs={'nes_id': updated_experiment.nes_id}
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
                'status': updated_experiment.status.tag,
                'protocol_components': [],
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


@apply_setup(global_setup)
class StudyAPITest(APITestCase):

    def setUp(self):
        global_setup(self)

    def test_get_returns_all_studies_of_an_experiment(self):
        study1 = Study.objects.first()
        study2 = Study.objects.last()
        experiment = Experiment.objects.first()
        list_url = reverse('api_studies-list',
                           kwargs={'nes_id': experiment.nes_id})
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
                    'nes_id': study1.nes_id,
                    'owner': study1.owner.username
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'experiment': 'Experiment 2',
                    'nes_id': study2.nes_id,
                    'owner': study2.owner.username
                },
            ]
        )

    def test_POSTing_a_new_study(self):
        owner = User.objects.get(username='lab1')
        exp_status = ExperimentStatus.objects.create(tag='to_be_approved')
        experiment = Experiment.objects.create(
            title='An experiment', nes_id=17, owner=owner, status=exp_status,
            version=1, sent_date=datetime.utcnow()
        )
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_studies-list',
                           kwargs={'nes_id': experiment.nes_id})
        response = self.client.post(
            list_url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'nes_id': 17,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_study = Study.objects.get(nes_id=17, owner=owner)
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


@apply_setup(global_setup)
class GroupAPITest(APITestCase):

    def setUp(self):
        global_setup(self)
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        experiment1 = Experiment.objects.get(nes_id=1, owner=owner1)
        experiment2 = Experiment.objects.get(nes_id=1, owner=owner2)
        Group.objects.create(
            title='A title', description='A description', nes_id=1,
            owner=owner1, experiment=experiment1
        )
        Group.objects.create(
            title='Other title', description='Other description', nes_id=2,
            owner=owner1, experiment=experiment1
        )
        Group.objects.create(
            title='A title', description='A description', nes_id=1,
            owner=owner2, experiment=experiment2
        )

    def test_get_returns_all_groups_short_url(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        group1 = Group.objects.get(nes_id=1, owner=owner1)
        group2 = Group.objects.get(nes_id=2, owner=owner1)
        group3 = Group.objects.get(nes_id=1, owner=owner2)
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
                    'nes_id': group1.nes_id,
                    'owner': group1.owner.username
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'nes_id': group2.nes_id,
                    'owner': group2.owner.username
                },
                {
                    'id': group3.id,
                    'title': group3.title,
                    'description': group3.description,
                    'experiment': group3.experiment.title,
                    'nes_id': group3.nes_id,
                    'owner': group3.owner.username
                }
            ]
        )

    def test_get_returns_all_groups_long_url(self):
        owner1 = User.objects.get(username='lab1')
        owner2 = User.objects.get(username='lab2')
        experiment = Experiment.objects.last()  # can be anyone
        group1 = Group.objects.get(nes_id=1, owner=owner1)
        group2 = Group.objects.get(nes_id=2, owner=owner1)
        group3 = Group.objects.get(nes_id=1, owner=owner2)
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'nes_id': experiment.nes_id})
        response = self.client.get(list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': group1.id,
                    'title': group1.title,
                    'description': group1.description,
                    'experiment': group1.experiment.title,
                    'nes_id': group1.nes_id,
                    'owner': group1.owner.username
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'nes_id': group2.nes_id,
                    'owner': group2.owner.username
                },
                {
                    'id': group3.id,
                    'title': group3.title,
                    'description': group3.description,
                    'experiment': group3.experiment.title,
                    'nes_id': group3.nes_id,
                    'owner': group3.owner.username
                }
            ]
        )

    def test_get_returns_groups_of_an_experiment(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        group1 = Group.objects.get(nes_id=1, owner=owner)
        group2 = Group.objects.get(nes_id=2, owner=owner)
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'nes_id': experiment.nes_id})
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
                    'nes_id': group1.nes_id,
                    'owner': group1.owner.username
                },
                {
                    'id': group2.id,
                    'title': group2.title,
                    'description': group2.description,
                    'experiment': group2.experiment.title,
                    'nes_id': group2.nes_id,
                    'owner': group2.owner.username
                }
            ]
        )
        self.client.logout()

    def test_POSTing_a_new_group(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'nes_id': experiment.nes_id})
        response = self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                'nes_id': 17,
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
        exp_status = ExperimentStatus.objects.get(tag='to_be_approved')
        experiment_v2 = Experiment.objects.create(
            nes_id=experiment_v1.nes_id, status=exp_status, version=2,
            sent_date=datetime.utcnow(), owner=owner
        )
        self.client.login(username=owner.username, password='nep-lab1')
        list_url = reverse('api_experiment_groups-list',
                           kwargs={'nes_id': experiment_v1.nes_id})
        self.client.post(
            list_url,
            {
                'title': 'A title',
                'description': 'A description',
                'nes_id': 1,
            }
        )
        self.client.logout()
        new_group = Group.objects.last()  # can retrieve last because we
        # just post new group
        self.assertEqual(new_group.experiment.id, experiment_v2.id)


@apply_setup(global_setup)
class ProtocolComponentAPITest(APITestCase):
    list_url = reverse('api_protocol_components-list')

    def setUp(self):
        global_setup(self)
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(owner=owner)
        ProtocolComponent.objects.create(
            identification='An identification',
            component_type='A component type',
            nes_id=1, experiment=experiment, owner=owner
        )
        ProtocolComponent.objects.create(
            identification='Other identification',
            component_type='Other component type',
            nes_id=2, experiment=experiment, owner=owner
        )

    def test_get_returns_all_protocolcomponents(self):
        protocol_component1 = ProtocolComponent.objects.get(nes_id=1)
        protocol_component2 = ProtocolComponent.objects.get(nes_id=2)
        response = self.client.get(self.list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': protocol_component1.id,
                    'identification': protocol_component1.identification,
                    'description': protocol_component1.description,
                    'duration_value': protocol_component1.duration_value,
                    'component_type': protocol_component1.component_type,
                    'nes_id': protocol_component1.nes_id,
                    'experiment': protocol_component1.experiment.title,
                    'owner': protocol_component1.owner.username
                },
                {
                    'id': protocol_component2.id,
                    'identification': protocol_component2.identification,
                    'description': protocol_component2.description,
                    'duration_value': protocol_component2.duration_value,
                    'component_type': protocol_component2.component_type,
                    'nes_id': protocol_component2.nes_id,
                    'experiment': protocol_component2.experiment.title,
                    'owner': protocol_component2.owner.username
                }
            ]
        )

    def test_POSTing_a_new_protocolcomponent(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(owner=owner)

        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            self.list_url,
            {
                'identification': 'An identification',
                'description': 'A description',
                'duration_value': 4,
                'component_type': 'A component type',
                'nes_id': 17,
                'experiment': experiment.nes_id
            }
        )
        self.client.logout()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_protocolcomponent = ProtocolComponent.objects.first()
        self.assertEqual(new_protocolcomponent.identification,
                         'An identification')

    def test_PUTing_an_existing_protocolcomponent(self):
        owner = User.objects.get(username='lab1')
        experiment = Experiment.objects.get(owner=owner)
        protocol_component = ProtocolComponent.objects.get(
            nes_id=1, owner=owner
        )
        detail_url1 = reverse(
            'api_protocol_components-detail',
            kwargs={'nes_id': protocol_component.nes_id}
        )
        self.client.login(username=owner.username, password='nep-lab1')
        resp_patch = self.client.patch(
            detail_url1,
            {
                'identification': 'Changed identification',
                'description': 'Changed description',
                'duration_value': 2,
                'component_type': 'Changed component type',
                'experiment': experiment.nes_id
            }
        )
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)

        # test protocol_component updated
        updated_protocol_component = ProtocolComponent.objects.get(
            nes_id=protocol_component.nes_id, owner=owner)
        detail_url2 = reverse(
            'api_protocol_components-detail',
            kwargs={'nes_id': updated_protocol_component.nes_id}
        )
        resp_get = self.client.get(detail_url2)
        self.assertEqual(
            json.loads(resp_get.content.decode('utf8')),
            {
                'id': updated_protocol_component.id,
                'identification': 'Changed identification',
                'description': 'Changed description',
                'duration_value': 2,
                'component_type': 'Changed component type',
                'nes_id': updated_protocol_component.nes_id,
                'experiment': updated_protocol_component.experiment.title,
                'owner': updated_protocol_component.owner.username
            }
        )
        self.client.logout()

