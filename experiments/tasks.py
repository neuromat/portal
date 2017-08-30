# Create your tasks here
from __future__ import absolute_import, unicode_literals
from nep.celery import app
from django.core.management import call_command


@app.task()
def rebuild_haystack_index():
    call_command('rebuild_index', verbosity=0, interactive=False)
