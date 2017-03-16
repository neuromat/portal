from django.conf.urls import url, include
from experiments import views
from experiments import api_urls

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^api/', include(api_urls))
]
