# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-06 15:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0083_stepadditionalfile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experiment',
            options={'permissions': (('change_slug', 'Can change experiment slug'),)},
        ),
    ]