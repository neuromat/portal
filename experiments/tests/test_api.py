from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime
import json

from experiments.models import Experiment, Researcher, Study


class ExperimentAPITest(APITestCase):
    base_url = reverse('api_experiments')

    def test_get_returns_json_200(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_all_experiments(self):
        researcher = Researcher.objects.create()
        # TODO: What a strange behavior. Maybe post question in Stackoverflow.
        # When trying to create our_user User instance without user name, test
        # doesn't pass. But in the first User instance created (other_user
        # above), without user name, test pass.
        user = User.objects.create(username='João')
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
                    'study': experiment1.study.id,
                    'user': experiment1.user.id
                },
                {
                    'id': experiment2.id,
                    'title': experiment2.title,
                    'description': experiment2.description,
                    'data_acquisition_done':
                        experiment2.data_acquisition_done,
                    'study': experiment2.study.id,
                    'user': experiment2.user.id
                }
            ]
        )
