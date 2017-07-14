from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve

from rest_framework.documentation import include_docs_urls

from experiments import views
from experiments import api_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include(api_urls)),
    url(r'^api/docs/', include_docs_urls(title='NEP API')),
    url(r'^$', views.home_page, name='home'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^experiments/(?P<experiment_id>[0-9]+)/$',
        views.experiment_detail, name='experiment-detail'),
    url(r'^experiments/(?P<experiment_id>[0-9]+)/change_status',
        views.change_status, name='change-status'),
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, }),

    # Ajax
    url(r'^experiments/to_be_analysed/count/$', views.ajax_to_be_analysed,
        name='ajax-to_be_analysed'),

    # Search
    url(r'^search_experiments/$', views.search_experiments,
        name='search-experiments')
]
