# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-05 19:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0095_merge_20180824_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='release_notes',
            field=models.TextField(default=''),
        ),
    ]
