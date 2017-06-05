from django.db import models
from django.contrib.auth.models import User


class Experiment(models.Model):
    RECEIVING = 'receiving'
    TO_BE_ANALYSED = 'to_be_analysed'
    UNDER_ANALYSIS = 'under_analysis'
    APPROVED = 'approved'
    NOT_APPROVED = 'not_approved'
    STATUS_OPTIONS = (
        (RECEIVING, 'receiving'),
        (TO_BE_ANALYSED, 'to_be_analysed'),
        (UNDER_ANALYSIS, 'under_analysis'),
        (APPROVED, 'approved'),
        (NOT_APPROVED, 'not_approved'),
    )

    owner = models.ForeignKey(User)
    nes_id = models.PositiveIntegerField()
    version = models.PositiveIntegerField()

    title = models.CharField(max_length=150)
    description = models.TextField()
    data_acquisition_done = models.BooleanField(default=False)
    ethics_committee_file = models.FileField(
        'Project file approved by the ethics committee', blank=True
    )
    sent_date = models.DateField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_OPTIONS, default=RECEIVING
    )

    class Meta:
        unique_together = ('nes_id', 'owner', 'version')


class Study(models.Model):
    experiment = models.OneToOneField(Experiment)

    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)


class Researcher(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    study = models.OneToOneField(Study)


class ProtocolComponent(models.Model):
    experiment = models.ForeignKey(
        Experiment, related_name='protocol_components'
    )
    nes_id = models.PositiveIntegerField()

    identification = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    duration_value = models.IntegerField(null=True)
    component_type = models.CharField(max_length=30)

    class Meta:
        unique_together = ('nes_id', 'experiment')


class Group(models.Model):
    experiment = models.ForeignKey(Experiment, related_name='groups')

    title = models.CharField(max_length=50)
    description = models.TextField()
    protocol_component = models.ForeignKey(
        ProtocolComponent, null=True, blank=True
    )  # TODO: define if Group has ProtocolComponent


class ExperimentalProtocol(models.Model):
    group = models.OneToOneField(Group, related_name='experimental_protocol')
    image = models.FileField(null=True, blank=True)
    textual_description = models.TextField(null=True, blank=True)
