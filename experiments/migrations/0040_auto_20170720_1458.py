# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-20 17:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0039_auto_20170720_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethicscommitteeinfo',
            name='ethics_committee_url',
            field=models.CharField(max_length=255),
        ),
    ]
