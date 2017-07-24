# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-24 16:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0043_remove_experiment_ethics_committee_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ethicscommitteeinfo',
            name='experiment',
        ),
        migrations.AddField(
            model_name='experiment',
            name='ethics_committee_file',
            field=models.FileField(null=True, upload_to='uploads/%Y/%m/%d/', verbose_name='Project file approved by the ethics committee'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='ethics_committee_url',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='experiment',
            name='project_url',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='EthicsCommitteeInfo',
        ),
    ]
