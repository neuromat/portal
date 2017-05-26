from django.db import models
from django.contrib.auth.models import User


# class Researcher(models.Model):
#     first_name = models.CharField(max_length=150, blank=True)
#     surname = models.CharField(max_length=150, blank=True)
#     email = models.EmailField(blank=True)
#     nes_id = models.PositiveIntegerField()
#     owner = models.ForeignKey(User)
#
#     class Meta:
#         unique_together = ('nes_id', 'owner')


class Experiment(models.Model):
    STATUS_OPTIONS = (
        ("receiving", "receiving"),
        ("to_be_analysed", "to be analysed"),
        ("under_analysis", "under analysis"),
        ("approved", "approved"),
        ("not_approved", "not approved"),
    )

    nes_id = models.PositiveIntegerField()
    title = models.CharField(max_length=150)
    description = models.TextField()
    data_acquisition_done = models.BooleanField(default=False)
    ethics_committee_file = models.FileField('Project file approved by the ethics committee', blank=True)
    sent_date = models.DateField(auto_now=True, blank=True)
    version = models.PositiveIntegerField()

    status = models.CharField(max_length=20, default="receiving")

    # has id 1.
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner', 'version')


class Study(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    experiment = models.OneToOneField(Experiment)
    nes_id = models.PositiveIntegerField()
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner', 'experiment')


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
        unique_together = ('nes_id', 'owner', 'experiment')


class Group(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    protocol_component = models.ForeignKey(
        ProtocolComponent, null=True, blank=True
    )  # TODO: define if Group has ProtocolComponent
    experiment = models.ForeignKey(Experiment, related_name='groups')
    nes_id = models.PositiveIntegerField()
    owner = models.ForeignKey(User)

    class Meta:
        unique_together = ('nes_id', 'owner', 'experiment')
