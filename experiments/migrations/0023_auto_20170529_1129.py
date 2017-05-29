# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-29 11:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiments', '0022_experiment_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='experiment',
            old_name='nes_id',
            new_name='experiment_nes_id',
        ),
        migrations.AlterUniqueTogether(
            name='experiment',
            unique_together=set([('experiment_nes_id', 'owner', 'version')]),
        ),
    ]