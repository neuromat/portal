from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from experiments import appclasses
from experiments.models import Experiment
from nep import settings


def home_page(request):
    if request.user.is_authenticated and \
            request.user.groups.filter(name='trustees').exists():
        all_experiments = \
            appclasses.CurrentExperiments().get_current_experiments_trustees()
        # We put experiments in following order:
        # TO_BE_ANALYSED, UNDER_ANALYSIS, NOT_APPROVED and APPROVED
        to_be_analysed = all_experiments.filter(
            status=Experiment.TO_BE_ANALYSED)
        under_analysis = all_experiments.filter(
            status=Experiment.UNDER_ANALYSIS)
        not_approved = all_experiments.filter(status=Experiment.NOT_APPROVED)
        approved = all_experiments.filter(status=Experiment.APPROVED)
        experiments = to_be_analysed | under_analysis | not_approved | approved
    else:
        experiments = appclasses.CurrentExperiments().get_current_experiments()

    for experiment in experiments:
        experiment.total_participants = \
            sum([len(group.participants.all())
                 for group in experiment.groups.all()])

    return render(request, 'experiments/home.html',
                  {'experiments': experiments})


def experiment_detail(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)

    gender_grouping = {}
    age_grouping = {}
    for group in experiment.groups.all():
        for participant in group.participants.all():
            # gender
            if participant.gender.name not in gender_grouping:
                gender_grouping[participant.gender.name] = 0
            gender_grouping[participant.gender.name] += 1
            # age
            if int(participant.age) not in age_grouping:
                age_grouping[int(participant.age)] = 0
            age_grouping[int(participant.age)] += 1

    return render(
        request, 'experiments/detail.html', {'experiment': experiment,
                                             'gender_grouping': gender_grouping,
                                             'age_grouping': age_grouping}
    )


def change_status(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)
    experiment.status = request.POST.get('status')
    experiment.save()

    # if status changed was to APPROVED send email to experiment study
    # researcher
    if experiment.status == Experiment.APPROVED:
        url = 'http://' + request.get_host()
        send_mail(
            'Your experiment was approved in ODEN portal',
            'Congratulations, your experiment ' +
            experiment.title +
            'was approved by the Portal committee. Now it is '
            'available public under license Creative Commons '
            'Share Alike.\n'
            'You can view your experiment data in ' + url,
            'noreplay@nep.prp.usp.br',
            [experiment.study.researcher.email]
        )
        messages.success(
            request,
            'An email was sent to ' + experiment.study.researcher.name +
            ' warning that the experiment was approved.'
        )

    return HttpResponseRedirect('/')


def ajax_to_be_analysed(request):
    to_be_analysed = Experiment.objects.filter(status=Experiment.TO_BE_ANALYSED).count()

    return HttpResponse(to_be_analysed, content_type='application/json')
