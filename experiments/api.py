from django.http import HttpResponse
from django.core import serializers
import json

from experiments.models import Experiment


def experiment(request):
    experiment_dicts = [
        {'id': experiment.id, 'title': experiment.title, 'description':
            experiment.description, 'data_acquisition_done':
            experiment.data_acquisition_done, 'study': experiment.study.id,
         'user': experiment.user.id}
        for experiment in Experiment.objects.all()
        ]
    return HttpResponse(
        json.dumps(experiment_dicts),
        content_type='application/json'
    )
