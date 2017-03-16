from django.conf.urls import url
from experiments import api

urlpatterns = [
    url('^experiments/', api.experiment, name='api_experiments')
]