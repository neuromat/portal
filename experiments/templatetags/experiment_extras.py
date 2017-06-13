from django import template
from django.contrib.auth.models import Group
import json

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter(name='statuses_to_json')
def statuses_to_json(statuses):
    return json.dumps(statuses)
