# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-09-25 20:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0097_auto_20180906_0836'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentresearcher',
            name='citation_name',
            field=models.CharField(blank=True, default='', max_length=252),
        ),
        migrations.AddField(
            model_name='researcher',
            name='citation_name',
            field=models.CharField(blank=True, default='', max_length=302),
        ),
    ]