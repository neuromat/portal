# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-08 18:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0098_auto_20180925_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentresearcher',
            name='citation_order',
            field=models.PositiveIntegerField(null=True),
        ),
    ]