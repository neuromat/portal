# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-02 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0017_auto_20170501_2043'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtocolComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
    ]
