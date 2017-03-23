from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from experiments.models import Experiment, Researcher, Study


class ExperimentAPITest(APITestCase):
    base_url = reverse('api_experiments')

    # This test is following tutorial. Not necessary because is
    # django-rest-framework. By default object returned is json.
    def test_get_returns_json_200(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_all_experiments(self):
        researcher = Researcher.objects.create()
        # TODO: What a strange behavior. Maybe post question in Stackoverflow.
        # When trying to create our_user User instance without username, test
        # doesn't pass. But in the first User instance created (other_user
        # above), without username, test pass.
        user = User.objects.create(username='joao')
        study = Study.objects.create(
            start_date=datetime.utcnow(), researcher=researcher
        )

        experiment1 = Experiment.objects.create(
            title='Our title', description='Our description',
            study=study, user=user
        )
        experiment2 = Experiment.objects.create(
            title='Our second title', description='Our second description',
            study=study, user=user
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
                    'user': experiment1.user.username
                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'study': experiment2.study.title,
                    'user': experiment2.user.username
                }
            ]
        )

    def test_POSTing_a_new_experiment_to_an_existing_study(self):
            researcher = Researcher.objects.create()
            study = Study.objects.create(
                start_date=datetime.utcnow(), researcher=researcher
            )
            user = User.objects.create_user(username='Pedro',
                                            password='nep-lab1')
            self.client.login(username=user.username, password='nep-lab1')
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


class ResearcherAPITest(APITestCase):
    base_url = reverse('api_researchers')

    def test_get_returns_all_researchers(self):
        researcher1 = Researcher.objects.create(
            first_name='Researcher1', surname='dos Santos'
        )
        researcher2 = Researcher.objects.create(
            first_name='Researcher2', surname='da Silva'
        )

        response = self.client.get(self.base_url)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            [
                {
                    'id': researcher1.id,
                    'first_name': researcher1.first_name,
                    'surname': researcher1.surname,
                    'email': researcher1.email,
                    'studies': []
                },
                {
                    'id': researcher2.id,
                    'first_name': researcher2.first_name,
                    'surname': researcher2.surname,
                    'email': researcher2.email,
                    'studies': []
                }
            ]
        )

    def test_POSTing_a_new_researcher(self):
        user = User.objects.create_user(username='lab1', password='nep-lab1')
        self.client.login(username=user.username, password='nep-lab1')
        response = self.client.post(
            self.base_url,
            {
                'first_name': 'João',
                'surname': 'das Rosas',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        new_researcher = Researcher.objects.first()
        self.assertEqual(new_researcher.first_name, 'João')


class StudyAPITest(APITestCase):
    base_url = reverse('api_studies')

    def test_get_returns_all_studies(self):
        researcher = Researcher.objects.create()
        study1 = Study.objects.create(
            title='Um estudo', description='Uma descrição',
            start_date=datetime.utcnow(), researcher=researcher
        )
        study2 = Study.objects.create(
            title='Outro estudo', description='Outra descrição',
            start_date=datetime.utcnow(), researcher=researcher
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
                    'experiments': []
                },
                {
                    'id': study2.id,
                    'title': study2.title,
                    'description': study2.description,
                    'start_date': study2.start_date.strftime('%Y-%m-%d'),
                    'end_date': study2.end_date,
                    'researcher': study2.researcher.first_name,
                    'experiments': []
                },
            ]
        )
