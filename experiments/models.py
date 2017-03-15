from django.db import models
from django.contrib.auth.models import User


class Study(models.Model):
    title = models.CharField(max_length=150, default='')
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)


class Experiment(models.Model):
    title = models.CharField(max_length=150, default='')
    description = models.TextField(default='')
    is_public = models.BooleanField(default=False)
    data_acquisition_done = models.BooleanField(default=False)
    study = models.ForeignKey(Study, default='')
    user = models.ForeignKey(User, default='')

