from django.db import models


class Experiment(models.Model):
    title = models.CharField(max_length=150, default='')
    description = models.TextField(default='')
    is_public = models.BooleanField(default=False)
    data_acquisition_done = models.BooleanField(default=False)
