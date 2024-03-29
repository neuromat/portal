# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-03-18 16:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0099_experimentresearcher_citation_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='experiment',
            name='title',
            field=models.CharField(max_length=255),
        ),
    ]
