from django.conf.urls import url
from experiments import views

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
]
