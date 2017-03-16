from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from experiments.models import Experiment


class ExperimentAPITest(APITestCase):

    def test_get_returns_json_200(self):
        url = reverse('api_experiments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
