# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-02 11:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0018_protocolcomponent'),
    ]

    operations = [
        migrations.AddField(
            model_name='protocolcomponent',
            name='identification',
            field=models.CharField(default='', max_length=50),
        ),
    ]
