from django import template
from django.contrib.auth.models import Group
import json

from experiments.models import Experiment
from django.utils.translation import ugettext as _


register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter(name='statuses_to_json')
def statuses_to_json(statuses, experiment_status):
    # We are 'eager' translating experiment statuses because it's breaking
    # when json dumps statuses_dict on return because of lazy translation in
    # Experiment model
    statuses_dict = dict(statuses)
    for key, value in statuses_dict.items():
        statuses_dict[key] = _(statuses_dict[key])
    # First we remove receiving status because this is only used when
    # Portal is receiving experiment data from API clients
    del statuses_dict[Experiment.RECEIVING]
    # Now, we render in template only the statuses allowed to be changed by
    # trustee based in current experiment status
    if experiment_status == Experiment.TO_BE_ANALYSED:
        del statuses_dict[Experiment.APPROVED],\
            statuses_dict[Experiment.NOT_APPROVED]
    elif experiment_status == Experiment.APPROVED or \
            experiment_status == Experiment.NOT_APPROVED:
        statuses_dict = {}
    return json.dumps(statuses_dict)
