# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-28 14:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0061_copying_files_to_new_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='additionaldata',
            name='file',
        ),
        migrations.RemoveField(
            model_name='eegdata',
            name='file',
        ),
        migrations.RemoveField(
            model_name='emgdata',
            name='file',
        ),
        migrations.RemoveField(
            model_name='genericdatacollectiondata',
            name='file',
        ),
        migrations.RemoveField(
            model_name='goalkeepergamedata',
            name='file',
        ),
    ]