from django.shortcuts import render

from experiments.models import Experiment


def home_page(request):
    experiments = Experiment.objects.all()
    return render(request, 'experiments/home.html',
                  {'experiments': experiments})
