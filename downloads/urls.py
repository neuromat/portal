from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'(?P<experiment_id>[0-9]+)/$', views.download_view, name='download_view'),
]

