from django.db import models


class Experiment(models.Model):
    title = models.CharField(max_length=150, default='')
