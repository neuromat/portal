import os
import tempfile
from django.contrib.auth.models import User
from django.test import override_settings, TestCase

from downloads.views import download_create
from experiments.models import Experiment
from experiments.tests.tests_helper import create_experiment, create_study

TEMP_MEDIA_ROOT = os.path.join(tempfile.mkdtemp())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DownloadCreateView(TestCase):

    def test_create_download_subdir_if_not_exist(self):
        owner = User.objects.create_user(username='lab1', password='nep-lab1')
        experiment = create_experiment(1, owner, Experiment.TO_BE_ANALYSED)
        create_study(experiment)

        download_create(experiment.id, '')

        self.assertTrue(
            os.path.exists(os.path.join(TEMP_MEDIA_ROOT, 'download'))
        )
