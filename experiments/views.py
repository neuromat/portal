import csv
import math
import pandas
import tempfile

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils.translation import activate, LANGUAGE_SESSION_KEY, \
    ugettext as _
from django.template.defaultfilters import slugify

from haystack.generic_views import SearchView
from experiments.forms import NepSearchForm, ChangeSlugForm
from experiments.models import Experiment, RejectJustification, Step, \
    Questionnaire, QuestionnaireDefaultLanguage, QuestionnaireLanguage
from experiments.tasks import rebuild_haystack_index


def _get_nested_rec(key, group):
    rec = dict()
    rec['question_code'] = key[0]
    rec['question_limesurvey_type'] = key[1]
    rec['question_description'] = key[2]

    for field in ['subquestion_description', 'option_description']:
        if isinstance(group[field].unique()[0], float) and \
                math.isnan(group[field].unique()[0]):
            rec[field] = None
        else:
            rec[field] = list(group[field].unique())

    return rec


def _isvalid(source_path):
    # tests for number of columns
    with open(source_path, 'r') as source:
        reader = csv.reader(source, skipinitialspace=True)
        for row in reader:
            # the number of columns in csv file must be 14
            if len(row) != 14:
                return False

    # tests for column titles
    with open(source_path, 'r') as source:
        reader = csv.reader(source, skipinitialspace=True)
        for row in reader:
            if row[0] != 'questionnaire_code' or \
                    row[1] != 'questionnaire_title' or \
                    row[2] != 'question_group' or \
                    row[3] != 'question_type' or \
                    row[4] != 'question_type_description' or \
                    row[5] != 'question_index' or \
                    row[6] != 'question_code' or \
                    row[7] != 'question_description' or \
                    row[8] != 'subquestion_code' or \
                    row[9] != 'subquestion_description' or \
                    row[10] != 'question_scale' or \
                    row[11] != 'question_scale_label' or \
                    row[12] != 'option_code' or \
                    row[13] != 'option_description':
                return False
            break

    return True


def _get_questionnaire_metadata(metadata):
    # put the questionnaire data into a temporary csv file
    temp_dir = tempfile.mkdtemp()
    file = open(temp_dir + '/questionnaire.csv', 'w')
    file.write(metadata)
    file.close()

    if not _isvalid(temp_dir + '/questionnaire.csv'):
        return 'invalid_questionnaire'

    # remove the columns that won't be used and save in another temporary file
    with open(temp_dir + '/questionnaire.csv', 'r') as source:
        reader = csv.reader(source, skipinitialspace=True)
        with open(temp_dir + '/questionnaire_cleaned.csv', 'w') as result:
            writer = csv.writer(result)
            for r in reader:
                writer.writerow((r[2], r[3], r[6], r[7], r[9], r[13]))

    q_cleaned = pandas.read_csv(temp_dir + '/questionnaire_cleaned.csv')

    records = []

    # first, group questions by question_code
    for key, grp in q_cleaned.groupby(['question_code',
                                       'question_type',
                                       'question_description']):
        rec = _get_nested_rec(key, grp)
        records.append(rec)

    # now, build one level above, the question groups level
    q_groups = dict()
    for key, grp in q_cleaned.groupby(['question_group']):
        q_groups[key] = []
        q_unique = grp['question_code'].unique()
        for record in records:
            if record['question_code'] in q_unique:
                q_groups[key].append(record)

    # make dictionnaire to ease diplaying in template
    for q_group in q_groups:
        q_groups[q_group] = dict(data=q_groups[q_group])
    return q_groups


def _get_q_default_language_or_first(questionnaire):
    # TODO: correct this to adapt to unique QuestionnaireDefaultLanguage
    # TODO: model with OneToOne relation with Questionnaire
    qdl = QuestionnaireDefaultLanguage.objects.filter(
        questionnaire=questionnaire
    ).first()
    if qdl:
        return qdl.questionnaire_language
    else:
        return QuestionnaireLanguage.objects.filter(
            questionnaire=questionnaire
        ).first()


def _get_available_languages(questionnaire):
    q_languages = QuestionnaireLanguage.objects.filter(
        questionnaire=questionnaire
    )
    lang_code = []
    for q_language in q_languages:
        lang_code.append(q_language.language_code)

    return lang_code


def home_page(request):
    # will be None if home contains the list of normal user
    to_be_analysed_count = None
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
                   'table_title': 'List of Experiments',
                   'search_form': NepSearchForm()})


def experiment_detail(request, slug):
    # will be None if home contains the list for common user
    to_be_analysed_count = None
    if request.user.is_authenticated and \
            request.user.groups.filter(name='trustees').exists():
        all_experiments = Experiment.lastversion_objects.all()
        to_be_analysed_count = all_experiments.filter(
            status=Experiment.TO_BE_ANALYSED).count()

    experiment = Experiment.objects.get(slug=slug)

    gender_grouping = {}
    age_grouping = {}
    for group in experiment.groups.all():
        for participant in group.participants.all():
            # gender
            if participant.gender.name not in gender_grouping:
                gender_grouping[participant.gender.name] = 0
            gender_grouping[participant.gender.name] += 1
            # age
            if participant.age:
                if int(participant.age) not in age_grouping:
                    age_grouping[int(participant.age)] = 0
                age_grouping[int(participant.age)] += 1

    # get default (language) questionnaires (or first) for all groups
    questionnaires = {}
    for group in experiment.groups.all():
        if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
            questionnaires[group.title] = {}
            for step in group.steps.filter(type=Step.QUESTIONNAIRE):
                q = Questionnaire.objects.get(step_ptr=step)
                questionnaires[group.title][q.id] = {}
                # get questionnaire default language data or first
                # questionnaire language
                questioinnaire_default = _get_q_default_language_or_first(q)

                questionnaires[group.title][q.id]['survey_name'] = \
                    questioinnaire_default.survey_name
                questionnaires[group.title][q.id]['survey_metadata'] = \
                    _get_questionnaire_metadata(
                        questioinnaire_default.survey_metadata
                    )
                questionnaires[group.title][q.id]['language_code'] = \
                    questioinnaire_default.language_code
                questionnaires[group.title][q.id]['language_codes'] = \
                    _get_available_languages(q)

    return render(
        request, 'experiments/detail.html', {
            'experiment': experiment,
            'gender_grouping': gender_grouping,
            'age_grouping': age_grouping,
            'to_be_analysed_count': to_be_analysed_count,
            'questionnaires': questionnaires,
            'form': ChangeSlugForm(),
            'has_setting': experiment.has_setting()
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
    if status == Experiment.NOT_APPROVED and not justification:
        messages.warning(
            request,
            _('Please provide a reason justifying the change of the status '
              'of the experiment ') +
            experiment.title + _('to "Not approved". '))
        return HttpResponseRedirect('/')

    if status == Experiment.NOT_APPROVED and justification:
        experiment.status = status
        experiment.save()
        # if has justification send email to researcher
        subject = _('Your experiment was rejected')
        message = \
            _('We regret to inform you that your experiment, ') + \
            experiment.title + \
            _(
                ', has not been acceptted to be published in the '
                'NeuroMat Open Database. Please check the reasons '
                'providing by the Neuromat Open Database Evaluation '
                'Committee:') + justification + \
            _(
                '.\nWith best regards,\n The Neuromat Open Database '
                'Evaluation Committee'
            )

        send_mail(subject, message, from_email,
                  [experiment.study.researcher.email])
        messages.success(
            request,
            _('An email was sent to ') + experiment.study.researcher.name +
            _(' warning that the experiment was rejected.')
        )
        # Save the justification message
        RejectJustification.objects.create(
            message=justification, experiment=experiment
        )

    # If status changed to UNDER_ANALYSIS or APPROVED, send email to
    # experiment study researcher
    if status == Experiment.APPROVED:
        experiment.status = status
        experiment.save()
        subject = _('Your experiment was approved')
        message = \
            _('We are pleased to inform you that your experiment ') + \
            experiment.title + \
            _(
                ' was approved by Neuromat Open Database Evaluation '
                'Committee. All data of the submitted experiment will be '
                'available freely to the public consultation and shared '
                'under Creative Commons Share Alike license.\n You can '
                'access your experiment data by clicking on the link '
                'below\n'
            ) + 'http://' + request.get_host() + \
            _(
                '\nWith best regards,\n The NeuroMat Open Database '
                'Evaluation Committee.')

        send_mail(subject, message, from_email,
                  [experiment.study.researcher.email])
        messages.success(
            request,
            _('An email was sent to ') + experiment.study.researcher.name +
            _(' warning that the experiment changed status to Approved.')
        )

        # After experiment has been approved reindex data base including
        # this new experiment.
        rebuild_haystack_index.delay()

    if status == Experiment.UNDER_ANALYSIS:
        experiment.status = status
        # associate experiment with trustee
        experiment.trustee = request.user
        experiment.save()
        subject = _('Your experiment is now under analysis')
        message = \
            _(
                'Thank you for submitting your experiment ') + \
            experiment.title + \
            _(
                '. The NeuroMat Open Database Evaluation Committee will '
                'be analyze your data and will try to respond as soon '
                'as possible.\n With best regards,\n The NeuroMat Open '
                'Database Evaluation Committee'
            )
        send_mail(subject, message, from_email,
                  [experiment.study.researcher.email])
        messages.success(
            request,
            _('An email was sent to ') + experiment.study.researcher.name +
            _(' warning that the experiment is under analysis.')
        )

    # If status posted is TO_BE_ANALYSED and current experiment status is
    # UNDER_ANALYSIS disassociate trustee from experiment and warning
    # trustee that the experiment is going to be free for other trustee
    # analyse it
    if status == Experiment.TO_BE_ANALYSED and \
            experiment.status == Experiment.UNDER_ANALYSIS:
            experiment.status = Experiment.TO_BE_ANALYSED
            experiment.trustee = None
            experiment.save()
            messages.warning(
                request,
                _('The experiment data ') + experiment.title + _(
                    ' was made available to be analysed by other trustee.')
            )

    return HttpResponseRedirect('/')


def change_slug(request, experiment_id):

    if not request.user.has_perm('experiments.change_slug'):
        raise PermissionDenied

    # TODO: move validation logic to ChangeSlugForm form; implement
    # TODO: validation in model too
    experiment = Experiment.objects.get(pk=experiment_id)

    new_slug = request.POST.get('slug')

    if experiment.slug == new_slug:
        pass
    elif not new_slug:
        messages.error(
            request,
            _('Empty slugs is not allowed. Please enter a valid slug')
        )
    elif new_slug != slugify(new_slug):
        messages.error(
            request,
            _('The slug entered is not allowed. Please enter a valid slug. '
              'Type only lowcase letters without accents, numbers, dash, '
              'and underscore signs')
        )
    elif len(new_slug) < 3:
        messages.error(
            request,
            _('The slug entered is two small. Please enter at least 3 '
              'characters')
        )
    elif Experiment.objects.filter(slug=new_slug).exists():
        messages.error(
            request,
            _('The slug entered is equal to other experiment slug. Please try '
              'again.')
        )
    else:
        experiment_versions = Experiment.objects.filter(
            nes_id=experiment.nes_id, owner=experiment.owner
        )
        for experiment in experiment_versions:
            version = experiment.version
            version_suffix = '-v' + str(version) if version > 1 else ''
            experiment.slug = request.POST.get('slug') + version_suffix
            experiment.save()
        messages.success(
            request,
            _('The experiment\'s slug was modified')
        )

    return HttpResponseRedirect('/experiments/' + experiment.slug + '/')


def ajax_to_be_analysed(request):
    to_be_analysed = Experiment.objects.filter(
        status=Experiment.TO_BE_ANALYSED
    ).count()

    return HttpResponse(to_be_analysed, content_type='application/json')


def ajax_questionnaire_languages(request, questionnaire_id, lang_code):
    questionnaire_language = QuestionnaireLanguage.objects.get(
        questionnaire=questionnaire_id, language_code=lang_code
    )

    q_language = dict()
    q_language['survey_name'] = questionnaire_language.survey_name
    q_language['survey_metadata'] = _get_questionnaire_metadata(
        questionnaire_language.survey_metadata)

    q_language_tmpl = render_to_string(
        'experiments/questionnaires/questionnaire_language.html',
        {'q_language': q_language, 'questionnaire_id': questionnaire_id})
    return HttpResponse(q_language_tmpl)


def language_change(request, language_code):
    activate(language_code)
    request.session[LANGUAGE_SESSION_KEY] = language_code

    return HttpResponseRedirect(request.GET['next'])


##
# Class based views
#
class NepSearchView(SearchView):
    form_class = NepSearchForm
    form_name = 'search_form'

    def get(self, request, *args, **kwargs):
        if not self.request.GET.get('q') and \
                not self.request.GET.get('filter'):
            return HttpResponseRedirect('/')
        return super(NepSearchView, self).get(self, request)

    # TODO: see if it's necessary
    def get_queryset(self):
        queryset = super(NepSearchView, self).get_queryset()
        return queryset.all()

    def get_context_data(self, *args, **kwargs):
        context = super(NepSearchView, self).get_context_data(**kwargs)

        if 'filter' in self.request.GET:
            self.filter(context, self.request.GET.getlist('filter'))

        # Related to the badge with number of experiments to be analysed in
        # page top. It's displayed only if a trustee is logged.
        to_be_analysed_count = None
        if self.request.user.is_authenticated and \
                self.request.user.groups.filter(name='trustees').exists():
            to_be_analysed = Experiment.lastversion_objects.filter(
                status=Experiment.TO_BE_ANALYSED)
            to_be_analysed_count = to_be_analysed.count()

        context['to_be_analysed_count'] = to_be_analysed_count

        # We exclude search modifiers: OR, AND, NOT to query element from
        # context dict. That's for avoid highlight this words in search
        # templates
        words_wo_modifiers = str.replace(context['query'], 'OR', '')
        words_wo_modifiers = str.replace(words_wo_modifiers, 'AND', '')
        words_wo_modifiers = str.replace(words_wo_modifiers, 'NOT', '')

        context['query'] = words_wo_modifiers

        return context

    @staticmethod
    def filter(context, search_filters):
        """
        Filters search results by type of data collected in the experiment.
        :param context: object_list returned by haystack search
        :param search_filters: the filters chosen by the user
        """
        old_object_list = context['page_obj'].object_list
        indexes_to_remove = []
        # If context['query'] is empty the search is only by filter,
        # so we search for matches only in experiments
        if not context['query']:
            for i in range(0, len(old_object_list)):
                if old_object_list[i].model_name == 'experiment':
                    # print(old_object_list[i].object.id)  # DEBUG. See TODO
                    # in tests_helper
                    groups = old_object_list[i].object.groups.all()
                    count = 0
                    for search_filter in search_filters:
                        for group in groups:
                            # print(group.steps.all())  # DEBUG. See TODO
                            # in tests_helper
                            if group.steps.filter(
                                    type=search_filter
                            ).count() > 0:
                                count = count + 1
                                break
                    if count < len(search_filters):
                        indexes_to_remove.append(i)
                else:
                    indexes_to_remove.append(i)
        else:
            for i in range(0, len(old_object_list)):
                if old_object_list[i].model_name == 'experiment':
                    groups = old_object_list[i].object.groups.all()
                elif old_object_list[i].model_name == 'study':
                    groups = old_object_list[i].object.experiment.groups.all()
                elif old_object_list[i].model_name == 'experimentalprotocol':
                    groups = [old_object_list[i].object.group]
                elif old_object_list[i].model_name == 'group':
                    groups = [old_object_list[i].object]
                else:
                    # TODO: generates exception: object not indexed
                    pass
                count = 0
                for group in groups:  # TODO
                    for search_filter in search_filters:
                        if group.steps.filter(type=search_filter).count() > 0:
                            count = count + 1
                if count < len(search_filters):
                    indexes_to_remove.append(i)

        context['page_obj'].object_list = \
            [v for i, v in enumerate(old_object_list)
             if i not in indexes_to_remove]


# inherit from LoginView to include search form besides login form
class NepLoginView(LoginView):
    search_form = NepSearchForm()
    extra_context = {'search_form': search_form}
