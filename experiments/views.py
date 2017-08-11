from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from haystack.generic_views import SearchView
from django.utils.translation import activate, LANGUAGE_SESSION_KEY, ugettext as _

from experiments.models import Experiment, RejectJustification


def home_page(request):
    to_be_analysed_count = None  # will be None if home contains the list of
    # normal user
    if request.user.is_authenticated and \
            request.user.groups.filter(name='trustees').exists():
        all_experiments = \
            Experiment.lastversion_objects.all()
        # We put experiments in following order:
        # TO_BE_ANALYSED, UNDER_ANALYSIS, NOT_APPROVED and APPROVED
        to_be_analysed = all_experiments.filter(
            status=Experiment.TO_BE_ANALYSED)
        under_analysis = all_experiments.filter(
            status=Experiment.UNDER_ANALYSIS)
        not_approved = all_experiments.filter(status=Experiment.NOT_APPROVED)
        approved = all_experiments.filter(status=Experiment.APPROVED)
        experiments = to_be_analysed | under_analysis | not_approved | approved
        to_be_analysed_count = to_be_analysed.count()
    else:
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )

    for experiment in experiments:
        experiment.total_participants = \
            sum([len(group.participants.all())
                 for group in experiment.groups.all()])

    return render(request, 'experiments/home.html',
                  {'experiments': experiments,
                   'to_be_analysed_count': to_be_analysed_count,
                   })


def experiment_detail(request, experiment_id):
    to_be_analysed_count = None  # will be None if home contains the list of
    # normal user
    if request.user.is_authenticated and \
            request.user.groups.filter(name='trustees').exists():
        all_experiments = Experiment.lastversion_objects.all()
        to_be_analysed_count = all_experiments.filter(
                status=Experiment.TO_BE_ANALYSED).count()

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
        request, 'experiments/detail.html', {
            'experiment': experiment,
            'gender_grouping': gender_grouping,
            'age_grouping': age_grouping,
            'to_be_analysed_count': to_be_analysed_count
        }
    )


def change_status(request, experiment_id):
    from_email = 'noreplay@nep.prp.usp.br'
    status = request.POST.get('status')
    justification = request.POST.get('justification')
    experiment = Experiment.objects.get(pk=experiment_id)

    # If status posted is the same as current simply redirect to home page
    if status == experiment.status:
        return HttpResponseRedirect('/')

    # If status postted is NOT_APPROVED verify if a justification message
    # was postted too. If not redirect to home page with warning message.
    if status == Experiment.NOT_APPROVED:
        if not justification:
            messages.warning(
                request, 'Please provide a reason justifying the change of the status of the experiment ' +
                         experiment.title + 'to "Not approved". ')

            return HttpResponseRedirect('/')
        else:
            # if has justification send email to researcher
            subject = 'Your experiment was rejected'
            message = 'We regret to inform you that your experiment, ' + experiment.title + \
                      ', has not been accepted to be published in the NeuroMat Open Database. Please check the ' \
                      'reasons providing by the Neuromat Open Database Evaluation Committee:' + justification + '.\n' \
                      'With best regards,\n' \
                      'The Neuromat Open Database Evaluation Committee'

            send_mail(subject, message, from_email,
                      [experiment.study.researcher.email])
            messages.success(
                request,
                'An email was sent to ' + experiment.study.researcher.name +
                ' warning that the experiment was rejected.'
            )
            # Save the justification message
            RejectJustification.objects.create(message=justification,
                                               experiment=experiment)

    # if status changed to UNDER_ANALYSIS or APPROVED, send email
    # to experiment study researcher
    if status == Experiment.APPROVED:
        subject = 'Your experiment was approved'
        message = 'We are pleased to inform you that your experiment ' + experiment.title + ' was approved by ' \
                  'NeuroMat Open Database Evaluation Committee. All data of the submitted experiment will be ' \
                  'available freely to the public consultation and shared under ' \
                  'Creative Commons Share Alike license.\n' \
                  'You can access your experiment data by clicking on the link below \n http://' + request.get_host()\
                  + '\n With best regards,\n' \
                  'The NeuroMat Open Database Evaluation Committee'

        send_mail(subject, message, from_email,
                  [experiment.study.researcher.email])
        messages.success(
            request,
            'An email was sent to ' + experiment.study.researcher.name +
            ' warning that the experiment changed status to Approved.'
        )
    if status == Experiment.UNDER_ANALYSIS:
        subject = 'Your experiment is now under analysis'
        message = 'Thank you for submitting your experiment ' + experiment.title + \
                  '. The NeuroMat Open Database Evaluation Committee will be analyze your data and will try to ' \
                  'respond as soon as possible.\n' \
                  'With best regards,\n' \
                  'The NeuroMat Open Database Evaluation Committee'
        send_mail(subject, message, from_email,
                  [experiment.study.researcher.email])
        messages.success(
            request,
            'An email was sent to ' + experiment.study.researcher.name +
            ' warning that the experiment is under analysis.'
        )
        # Associate experiment with trustee
        experiment.trustee = request.user

    # If status posted is TO_BE_ANALYSED and current experiment status is
    # UNDER_ANALYSIS disassociate trustee from experiment and warning
    # trustee that the experiment is going to be free for other trustee
    # analysis
    if status == Experiment.TO_BE_ANALYSED:
        if experiment.status == Experiment.UNDER_ANALYSIS:
            experiment.trustee = None
            messages.warning(
                request,
                'The experiment data ' + experiment.title + ' was made available to be analysed by other trustee.'
            )

    experiment.status = status
    experiment.save()

    return HttpResponseRedirect('/')


def ajax_to_be_analysed(request):
    to_be_analysed = Experiment.objects.filter(
        status=Experiment.TO_BE_ANALYSED
    ).count()

    return HttpResponse(to_be_analysed, content_type='application/json')


class NepSearchView(SearchView):
    # TODO: not working. See
    # https://stackoverflow.com/questions/45556274/custom-view-does-not-show-results-in-django-haystack-with-elastic-search

    def get_queryset(self):
        queryset = super(NepSearchView, self).get_queryset()
        if not self.request.user.is_authenticated and \
                self.request.user.groups.filter(name='trustees').exists():
            return queryset
        else:
            return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(NepSearchView, self).get_context_data(**kwargs)
        # do something
        return context


def language_change(request, language_code):

    activate(language_code)
    request.session[LANGUAGE_SESSION_KEY] = language_code

    return HttpResponseRedirect(request.GET['next'])
