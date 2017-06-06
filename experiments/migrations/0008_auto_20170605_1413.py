# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-05 17:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0007_collaborator'),
    ]

    operations = [
        migrations.AddField(
            model_name='collaborator',
            name='coordinator',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='collaborator',
            name='name',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='collaborator',
            name='study',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='collaborators', to='experiments.Study'),
        ),
        migrations.AddField(
            model_name='collaborator',
            name='team',
            field=models.CharField(default='', max_length=200),
        ),
    ]