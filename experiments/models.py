from django.db import models
from django.contrib.auth.models import User


class Researcher(models.Model):
    first_name = models.CharField(max_length=150, default='')
    surname = models.CharField(max_length=150, default='')
    email = models.EmailField(null=True)


class Study(models.Model):
    title = models.CharField(max_length=150, default='')
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    researcher = models.ForeignKey(Researcher, related_name='studies',
                                   default=None)


class Experiment(models.Model):
    title = models.CharField(max_length=150, default='')
    description = models.TextField(default='')
    data_acquisition_done = models.BooleanField(default=False)
    study = models.ForeignKey(Study, default=None, related_name='experiments')
    user = models.ForeignKey(User, default=None)
