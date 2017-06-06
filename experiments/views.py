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

    for experiment in experiments:
        experiment.total_participants = sum([len(group.participants.all()) for group in experiment.groups.all()])

    return render(request, 'experiments/home.html',
                  {'experiments': experiments})


def experiment_detail(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)

    gender_grouping = {}
    for group in experiment.groups.all():
        for participant in group.participants.all():
            if participant.gender.code not in gender_grouping:
                gender_grouping[participant.gender.code] = 0
            gender_grouping[participant.gender.code] += 1

    return render(
        request, 'experiments/detail.html', {'experiment': experiment, 'gender_grouping': gender_grouping}
    )
