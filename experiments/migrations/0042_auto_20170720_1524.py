# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-20 18:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0041_ethicscommitteeinfo_experiment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethicscommitteeinfo',
            name='experiment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ethics_committee_info', to='experiments.Experiment'),
        ),
    ]