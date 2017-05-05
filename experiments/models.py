from django.db import models
from django.contrib.auth.models import User


class Researcher(models.Model):
    first_name = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    nes_id = models.PositiveIntegerField()
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner')


class Study(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    nes_id = models.PositiveIntegerField()
    researcher = models.ForeignKey(Researcher, related_name='studies',
                                   default=None)
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner')


class Experiment(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    data_acquisition_done = models.BooleanField(default=False)
    nes_id = models.PositiveIntegerField()
    study = models.ForeignKey(Study, related_name='experiments')
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner')


class ExperimentVersion(models.Model):
    version = models.PositiveIntegerField()
    experiment = models.ForeignKey(Experiment, related_name='versions')


class ProtocolComponent(models.Model):
    identification = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    duration_value = models.IntegerField(null=True)
    component_type = models.CharField(max_length=30)
    nes_id = models.PositiveIntegerField()
    experiment = models.ForeignKey(Experiment,
                                   related_name='protocol_components')
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner')
