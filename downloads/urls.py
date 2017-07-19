from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.download_view, name='download_view'),
]

