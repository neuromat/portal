# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-29 17:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0024_auto_20170529_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='sent_date',
            field=models.DateField(auto_now=True),
        ),
    ]