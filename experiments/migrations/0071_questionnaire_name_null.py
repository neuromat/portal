# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-19 18:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0070_populate_questionnaire_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaire',
            name='survey_name',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
