# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-26 16:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0085_auto_20180307_1252'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentResearcher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('institution', models.CharField(max_length=200)),
            ],
        ),
    ]
