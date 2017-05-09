from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from reversion.models import Version

from experiments.models import Experiment, Researcher, Study, \
    ProtocolComponent, ExperimentVersion, ExperimentVersionMeta


def create_study(nes_id, owner):
    """
    Create Study model object to be used to test classes below.
    :param nes_id: client nes id
    :param owner: client owner
    :return: 
    """
    researcher = Researcher.objects.create(nes_id=nes_id, owner=owner)
    # TODO: What a strange behavior. Maybe post question in Stackoverflow.
    # When trying to create our_user User instance without username, test
    # doesn't pass. But in the first User instance created (other_user
    # above), without username, test pass.
    return Study.objects.create(
        nes_id=nes_id, start_date=datetime.utcnow(), researcher=researcher,
        owner=owner
    )


def create_experiment(nes_id, owner):
    """
    Create Experiment model object to be used to test classes below.
    :param nes_id: client nes id
    :param owner: client owner 
    :return: Experiment object model
    """
    study = create_study(nes_id=nes_id, owner=owner)
    return Experiment.objects.create(
            nes_id=nes_id, title='Our title', description='Our description',
            study=study, owner=owner
    )


class ResearcherAPITest(APITestCase):
    list_url = reverse('api_researchers-list')

    def test_get_returns_all_researchers(self):
        owner = User.objects.create_user(username='lab1')
        researcher1 = Researcher.objects.create(nes_id=1, owner=owner)
        researcher2 = Researcher.objects.create(nes_id=2, owner=owner)
        response = self.client.get(self.list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': researcher1.id,
                    'first_name': researcher1.first_name,
                    'surname': researcher1.surname,
                    'email': researcher1.email,
                    'studies': [],
                    'nes_id': researcher1.nes_id,
                    'owner': researcher1.owner.username
                },
                {
                    'id': researcher2.id,
                    'first_name': researcher2.first_name,
                    'surname': researcher2.surname,
                    'email': researcher2.email,
                    'studies': [],
                    'nes_id': researcher2.nes_id,
                    'owner': researcher2.owner.username
                }
            ]
        )

    def test_POSTing_a_new_researcher(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            self.list_url,
            {
                'first_name': 'João',
                'surname': 'das Rosas',
                'email': 'joao@rosas.com',
                'nes_id': 1,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_researcher = Researcher.objects.first()
        self.assertEqual(new_researcher.first_name, 'João')

    def test_PUTing_an_existing_researcher(self):
        # TODO: very large test
        ###
        # First we post a new researcher then we test PUTing
        ###
        # An owner post a researcher
        owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
        self.client.login(username=owner1.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'first_name': 'João',
                'surname': 'das Rosas',
                'email': 'joao@rosas.com',
                'nes_id': 2,
            }
        )
        self.client.logout()

        # Other owner post a researcher
        owner2 = User.objects.create_user(username='lab2', password='nep-lab2')
        self.client.login(username=owner2.username, password='nep-lab2')
        self.client.post(
            self.list_url,
            {
                'first_name': 'Pedro',
                'surname': 'Santos',
                'email': 'pedro@santos.com',
                'nes_id': 2,
            }
        )
        self.client.logout()

        ###
        # Now we test PUTing
        ###
        new_researcher = Researcher.objects.get(nes_id=2, owner=owner1)
        detail_url1 = reverse(
            'api_researchers-detail', kwargs={'nes_id': new_researcher.nes_id}
        )
        self.client.login(username=owner1.username, password='nep-lab1')
        resp_put = self.client.patch(
            detail_url1,
            {
                'first_name': 'João Maria',
                'surname': 'das Rosas Vermelhas',
                'email': 'joao13@dasrosas.com',
            }
        )
        self.assertEqual(resp_put.status_code, status.HTTP_200_OK)

        ###
        # Finally we test researcher updated
        ###
        updated_researcher = Researcher.objects.get(
            nes_id=new_researcher.nes_id, owner=owner1
        )
        detail_url2 = reverse(
            'api_researchers-detail',
            kwargs={'nes_id': updated_researcher.nes_id}
        )
        resp_get = self.client.get(detail_url2)
        self.assertEqual(
            json.loads(resp_get.content.decode('utf8')),
            {
                'id': updated_researcher.id,
                'first_name': 'João Maria',
                'surname': 'das Rosas Vermelhas',
                'email': 'joao13@dasrosas.com',
                'studies': [],
                'nes_id': updated_researcher.nes_id,
                'owner': updated_researcher.owner.username
            }
        )
        self.client.logout()


class StudyAPITest(APITestCase):
    list_url = reverse('api_studies-list')

    def test_get_returns_all_studies(self):
        owner = User.objects.create_user(username='lab1')
        study1 = create_study(nes_id=1, owner=owner)
        study2 = create_study(nes_id=2, owner=owner)
        response = self.client.get(self.list_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': study1.id,
                    'title': study1.title,
                    'description': study1.description,
                    'start_date': study1.start_date.strftime('%Y-%m-%d'),
                    'end_date': study1.end_date,
                    'nes_id': study1.nes_id,
                    'researcher': study1.researcher.first_name,
                    'experiments': [],
                    'owner': study1.owner.username
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'nes_id': study2.nes_id,
                    'experiments': [],
                    'researcher': study2.researcher.first_name,
                    'owner': study1.owner.username
                },
            ]
        )

    def test_POSTing_a_new_study(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            self.list_url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'nes_id': 1,
                'researcher': researcher.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_study = Study.objects.first()
        self.assertEqual(new_study.title, 'New study')

        # TODO: IMPORTANT! Test client can't POST (PUT etc.) to a model without
        # been its owner. This requires adds, at first, an owner to all
        # models, and ensure that only same client can POST to that model.

    def test_PUTing_an_existing_study(self):
        # TODO: very large test
        ###
        # First we post a new study then we test PUTing
        ###
        # An owner post a study
        owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner1)
        self.client.login(username=owner1.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'nes_id': 2,
                'researcher': researcher.id
            }
        )
        self.client.logout()

        # Other owner post a study
        owner2 = User.objects.create_user(username='lab2', password='nep-lab2')
        researcher = Researcher.objects.create(nes_id=1, owner=owner2)
        self.client.login(username=owner2.username, password='nep-lab2')
        self.client.post(
            self.list_url,
            {
                'title': 'Other study',
                'description': 'Other description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'nes_id': 2,
                'researcher': researcher.id
            }
        )
        self.client.logout()

        ###
        # Now we test PUTing
        ###
        new_study = Study.objects.get(nes_id=2, owner=owner2)
        detail_url1 = reverse(
            'api_studies-detail', kwargs={'nes_id': new_study.nes_id}
        )
        self.client.login(username=owner2.username, password='nep-lab2')
        resp_put = self.client.patch(
            detail_url1,
            {
                'title': 'Changed title',
                'description': 'Changed description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
            }
        )
        self.assertEqual(resp_put.status_code, status.HTTP_200_OK)

        # Finally we test study updated
        updated_study = Study.objects.get(
            nes_id=new_study.nes_id, owner=owner2
        )
        detail_url2 = reverse(
            'api_studies-detail', kwargs={'nes_id': updated_study.nes_id}
        )
        resp_get = self.client.get(detail_url2)
        self.assertEqual(
            json.loads(resp_get.content.decode('utf8')),
            {
                'id': updated_study.id,
                'title': 'Changed title',
                'description': 'Changed description',
                'start_date': updated_study.start_date.strftime('%Y-%m-%d'),
                'end_date': None,
                'nes_id': updated_study.nes_id,
                'experiments': [],
                'researcher': updated_study.researcher.first_name,
                'owner': updated_study.owner.username
            }
        )
        self.client.logout()


class ExperimentAPITest(APITestCase):
    list_url = reverse('api_experiments-list')

    def test_get_returns_all_experiments(self):
        owner = User.objects.create_user(username='lab1')
        experiment1 = create_experiment(nes_id=1, owner=owner)
        experiment2 = create_experiment(nes_id=2, owner=owner)
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
                    'study': experiment1.study.title,
                    'owner': experiment1.owner.username,
                    'protocol_components': []
                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'nes_id': experiment2.nes_id,
                    'study': experiment2.study.title,
                    'owner': experiment2.owner.username,
                    'protocol_components': []
                }
            ]
        )

    def test_POSTing_a_new_experiment(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        study = create_study(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'study': study.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_experiment = Experiment.objects.first()
        self.assertEqual(new_experiment.title, 'New experiment')

    def test_PUTing_an_existing_experiment(self):
        # TODO: very large test
        ###
        # First we post a new experiment then we test PUTing
        ###
        # An owner post an experiment
        owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
        study = create_study(nes_id=2, owner=owner1)
        self.client.login(username=owner1.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'study': study.id
            }
        )
        self.client.logout()

        # Other owner post a study
        owner2 = User.objects.create_user(username='lab2', password='nep-lab2')
        study = create_study(nes_id=2, owner=owner2)
        self.client.login(username=owner2.username, password='nep-lab2')
        self.client.post(
            self.list_url,
            {
                'title': 'Other experiment',
                'description': 'Other description',
                'nes_id': 1,
                'study': study.id
            }
        )
        self.client.logout()

        # Now we test PUTing
        new_experiment = Experiment.objects.get(nes_id=1, owner=owner2)
        detail_url1 = reverse(
            'api_experiments-detail', kwargs={'nes_id': new_experiment.nes_id}
        )
        self.client.login(username=owner2.username, password='nep-lab2')
        resp_put = self.client.patch(
            detail_url1,
            {
                'title': 'Changed experiment',
                'description': 'Changed description',
            }
        )
        self.assertEqual(resp_put.status_code, status.HTTP_200_OK)

        # Finally we test experiment updated
        updated_experiment = Experiment.objects.get(
            nes_id=new_experiment.nes_id, owner=owner2)
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
                'study': updated_experiment.study.title,
                'owner': updated_experiment.owner.username,
                'protocol_components': []
            }
        )
        self.client.logout()

    def test_POSTing_experiments_creates_versions(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        study = create_study(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'study': study.id
            }
        )
        self.client.logout()

        # Assert version of the experiment created is 1
        experiment = Experiment.objects.first()
        last_version = ExperimentVersion.objects.filter(
            experiment=experiment).last()
        self.assertEqual(1, last_version.version)

    def test_PUTing_experiments_creates_version(self):
        # First we put a new experiment: this will create first version
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        study = create_study(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'study': study.id
            }
        )
        self.client.logout()

        # Now we obtain the experiment created and patch it
        new_experiment = Experiment.objects.first()
        detail_url = reverse(
            'api_experiments-detail', kwargs={'nes_id': new_experiment.nes_id})
        self.client.login(username=owner.username, password='nep-lab1')
        self.client.patch(
            detail_url,
            {
                'title': 'Changed experiment',
                'description': 'Changed description',
            }
        )
        self.client.logout()

        # Assert version of the experiment updated is 2
        last_version = ExperimentVersion.objects.filter(
            experiment=new_experiment).last()
        self.assertEqual(2, last_version.version)


class ProtocolComponentAPITest(APITestCase):
    list_url = reverse('api_protocol_components-list')

    def test_get_returns_all_protocolcomponents(self):
        owner = User.objects.create_user(username='lab1')
        experiment = create_experiment(nes_id=1, owner=owner)
        protocol_component1 = ProtocolComponent.objects.create(
            identification='An identification',
            component_type='A component type',
            nes_id=1, experiment=experiment, owner=owner
        )
        protocol_component2 = ProtocolComponent.objects.create(
            identification='Other identification',
            component_type='Other component type',
            nes_id=2, experiment=experiment, owner=owner
        )
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
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        experiment = create_experiment(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        response = self.client.post(
            self.list_url,
            {
                'identification': 'An identification',
                'description': 'A description',
                'duration_value': 4,
                'component_type': 'A component type',
                'nes_id': 1,
                'experiment': experiment.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_protocolcomponent = ProtocolComponent.objects.first()
        self.assertEqual(new_protocolcomponent.identification,
                         'An identification')

    def test_PUTing_an_existing_protocolcomponent(self):
        # TODO: very large test
        ###
        # First we post a new protocol_component, then we test PUTing
        ###
        # A owner post a protocol component
        owner1 = User.objects.create_user(username='lab1', password='nep-lab1')
        experiment1 = create_experiment(nes_id=2, owner=owner1)
        self.client.login(username=owner1.username, password='nep-lab1')
        self.client.post(
            self.list_url,
            {
                'identification': 'An identification',
                'description': 'A description',
                'duration_value': 4,
                'component_type': 'A component type',
                'nes_id': 1,
                'experiment': experiment1.nes_id
            }
        )
        self.client.logout()

        # Other owner post a protocol component
        owner2 = User.objects.create_user(username='lab2', password='nep-lab2')
        experiment2 = create_experiment(nes_id=2, owner=owner2)
        self.client.login(username=owner2.username, password='nep-lab2')
        self.client.post(
            self.list_url,
            {
                'identification': 'Other identification',
                'description': 'Other description',
                'duration_value': 1,
                'component_type': 'Other component type',
                'nes_id': 1,
                'experiment': experiment2.nes_id
            }
        )
        self.client.logout()

        # Now we test PUTing
        new_protocol_component = ProtocolComponent.objects.get(
            nes_id=1, owner=owner2
        )
        detail_url1 = reverse(
            'api_protocol_components-detail',
            kwargs={'nes_id': new_protocol_component.nes_id}
        )
        self.client.login(username=owner2.username, password='nep-lab2')
        resp_put = self.client.patch(
            detail_url1,
            {
                'identification': 'Changed identification',
                'description': 'Changed description',
                'duration_value': 2,
                'component_type': 'Changed component type',
            }
        )
        self.assertEqual(resp_put.status_code, status.HTTP_200_OK)

        # And finally we test protocol_component updated
        updated_protocol_component = ProtocolComponent.objects.get(
            nes_id=new_protocol_component.nes_id, owner=owner2)
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

    def test_POSTing_protocolcomponent_associates_last_experiment_version(self):
        # First we post a new experiment to creates version
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        study = create_study(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        self.client.post(
            reverse('api_experiments-list'),
            {
                'title': 'New experiment',
                'description': 'Some description',
                'nes_id': 1,
                'study': study.id
            }
        )

        # Now we post a protocol component to test association with last
        # experiment version
        experiment = Experiment.objects.first()
        self.client.post(
            self.list_url,
            {
                'identification': 'An identification',
                'description': 'A description',
                'duration_value': 4,
                'component_type': 'A component type',
                'nes_id': 1,
                'experiment': experiment.nes_id
            }
        )
        self.client.logout()

        pro_component = ProtocolComponent.objects.first()

        # Assert pro_component revision created is in ExperimentVersionMeta
        version = Version.objects.get_for_object(pro_component).first()
        exp_version_meta = ExperimentVersionMeta.objects.filter(
            revision_id=version.revision_id)
        self.assertIn(exp_version_meta, ExperimentVersion.objects.all())

        # Assert pro_component has correct experiment version associated
        self.assertEqual(1, exp_version_meta.experiment_version_id)
