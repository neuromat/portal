# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-03 16:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0092_researcher_first_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='first_name',
            field=models.CharField(max_length=100),
        ),
    ]
