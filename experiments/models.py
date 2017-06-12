from django.db import models
from django.contrib.auth.models import User


class Experiment(models.Model):
    RECEIVING = 'receiving'
    TO_BE_ANALYSED = 'to_be_analysed'
    UNDER_ANALYSIS = 'under_analysis'
    APPROVED = 'approved'
    NOT_APPROVED = 'not_approved'
    STATUS_OPTIONS = (
        (RECEIVING, 'Receiving'),
        (TO_BE_ANALYSED, 'To be analysed'),
        (UNDER_ANALYSIS, 'Under analysis'),
        (APPROVED, 'Approved'),
        (NOT_APPROVED, 'Not approved'),
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


class Keyword(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, primary_key=True)

    def __str__(self):
        return self.name


class Study(models.Model):
    experiment = models.OneToOneField(Experiment)

    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    keywords = models.ManyToManyField(Keyword, null=True, blank=True)


class Researcher(models.Model):
    study = models.OneToOneField(Study, related_name='researcher')
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Collaborator(models.Model):
    name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    coordinator = models.BooleanField(default=False)
    study = models.ForeignKey(Study, related_name='collaborators')


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


class Gender(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name


class Participant(models.Model):
    group = models.ForeignKey(Group, related_name='participants')
    code = models.CharField(max_length=150)

    gender = models.ForeignKey(Gender)
    age = models.DecimalField(decimal_places=4, max_digits=8)

    class Meta:
        unique_together = ('group', 'code')
