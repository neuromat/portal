# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-18 17:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0013_auto_20170515_1944'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='sent_date',
            field=models.DateField(default='2017-05-22'),
        ),
    ]