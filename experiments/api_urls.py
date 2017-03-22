from django.conf.urls import url
from experiments import api

urlpatterns = [
    url(r'^experiments/$', api.experiment, name='api_experiments'),
    url(r'^researchers/$', api.ResearcherList.as_view(),
        name='api_researchers'),
]
