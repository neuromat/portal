# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-16 12:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0093_auto_20180703_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='sent_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
