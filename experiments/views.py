from django.shortcuts import render
from django.db.models import Max, Q

from experiments.models import Experiment


# TODO: make method in appclasses.ExperimentVersion
def get_current_experiments():
    experiment_max_version_set = \
        Experiment.objects.values('owner', 'nes_id').annotate(
            max_version=Max('version'))
    q_statement = Q()
    for experiment in experiment_max_version_set:
        q_statement |= (Q(owner=experiment['owner']) &
                        Q(nes_id=experiment['nes_id']) &
                        Q(version=experiment['max_version']))
    return Experiment.objects.filter(q_statement)


def home_page(request):
    experiments = get_current_experiments()

    return render(request, 'experiments/home.html',
                  {'experiments': experiments})
