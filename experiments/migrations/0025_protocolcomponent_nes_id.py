# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-02 11:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0024_auto_20170502_1153'),
    ]

    operations = [
        migrations.AddField(
            model_name='protocolcomponent',
            name='nes_id',
            field=models.PositiveIntegerField(default=None),
        ),
    ]
