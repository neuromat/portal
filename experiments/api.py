from django.http import HttpResponse
from rest_framework import status
import json

from experiments.models import Experiment, Study, User


def experiment(request):
    if request.method == 'POST':
        study = Study.objects.get(id=request.POST['study'])
        user = User.objects.get(id=request.POST['user'])
        Experiment.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            study=study,
            user=user
        )
        return HttpResponse(status=status.HTTP_201_CREATED)
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
