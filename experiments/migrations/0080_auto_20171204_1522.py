# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-04 17:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0079_publication_experiment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='experiment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.Experiment'),
        ),
    ]
