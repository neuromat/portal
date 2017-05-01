from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from experiments.models import Experiment, Researcher, Study


class ResearcherAPITest(APITestCase):
    base_url = reverse('api_researchers')

    def test_get_returns_all_researchers(self):
        owner = User.objects.create_user(username='lab1')
        researcher1 = Researcher.objects.create(nes_id=1, owner=owner)
        researcher2 = Researcher.objects.create(nes_id=2, owner=owner)

        response = self.client.get(self.base_url)
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
            self.base_url,
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


class StudyAPITest(APITestCase):
    base_url = reverse('api_studies')

    def test_get_returns_all_studies(self):
        owner = User.objects.create_user(username='lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        study1 = Study.objects.create(
            title='Um estudo', description='Uma descrição',
            start_date=datetime.utcnow(), researcher=researcher, owner=owner
        )
        study2 = Study.objects.create(
            title='Outro estudo', description='Outra descrição',
            start_date=datetime.utcnow(), researcher=researcher, owner=owner
        )
        response = self.client.get(self.base_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': study1.id,
                    'title': study1.title,
                    'description': study1.description,
                    'start_date': study1.start_date.strftime('%Y-%m-%d'),
                    'end_date': study1.end_date,
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
                    'researcher': study2.researcher.first_name,
                    'experiments': [],
                    'owner': study1.owner.username
                },
            ]
        )

    def test_POSTing_a_new_study(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        self.client.login(username=owner.username, password='nep-lab1')
        url = reverse('api_studies_post', args=[researcher.id])
        response = self.client.post(
            url,
            {
                'title': 'New study',
                'description': 'Some description',
                'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_study = Study.objects.first()
        self.assertEqual(new_study.title, 'New study')

    # TODO: IMPORTANT! Test client can't POST (PUT etc.) to a model without
        # been its owner. This requires adds, at first, an owner to all
        # models, and ensure that only same client can POST to that model.


class ExperimentAPITest(APITestCase):
    base_url = reverse('api_experiments')

    # This test is following tutorial. Not necessary because is
    # django-rest-framework. By default object returned is json.
    def test_get_returns_json_200(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_all_experiments(self):
        owner = User.objects.create_user(username='lab1')
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        # TODO: What a strange behavior. Maybe post question in Stackoverflow.
        # When trying to create our_user User instance without username, test
        # doesn't pass. But in the first User instance created (other_user
        # above), without username, test pass.
        study = Study.objects.create(
            start_date=datetime.utcnow(), researcher=researcher, owner=owner
        )

        experiment1 = Experiment.objects.create(
            title='Our title', description='Our description',
            study=study, owner=owner
        )
        experiment2 = Experiment.objects.create(
            title='Our second title', description='Our second description',
            study=study, owner=owner
        )
        response = self.client.get(self.base_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': experiment1.id,
                    'title': experiment1.title,
                    'description': experiment1.description,
                    'data_acquisition_done':
                        experiment1.data_acquisition_done,
                    'study': experiment1.study.title,
                    'owner': experiment1.owner.username
                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'study': experiment2.study.title,
                    'owner': experiment2.owner.username
                }
            ]
        )

    def test_POSTing_a_new_experiment_to_an_existing_study(self):
        owner = User.objects.create_user(
            username='lab1', password='nep-lab1'
        )
        researcher = Researcher.objects.create(nes_id=1, owner=owner)
        study = Study.objects.create(
            start_date=datetime.utcnow(), researcher=researcher, owner=owner
        )
        self.client.login(username=owner.username, password='nep-lab1')
        url = reverse('api_experiments_post', args=[study.id])
        response = self.client.post(
            url,
            {
                'title': 'New experiment',
                'description': 'Some description'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_experiment = Experiment.objects.first()
        self.assertEqual(new_experiment.title, 'New experiment')

    # TODO: os testes de validações ainda não foram implementados.
    # Ver:
    # http://www.obeythetestinggoat.com/book/appendix_rest_api.html#_data_validation_an_exercise_for_the_reader

