from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve
from django.views.i18n import javascript_catalog

from rest_framework.documentation import include_docs_urls

from experiments import views
from experiments import api_urls
from experiments.views import NepSearchView
from downloads import urls

# internationalization
js_info_dict = {
    'domain': 'djangojs',
    'packages': ('experiments',),
}

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include(api_urls)),
    url(r'^api/docs/', include_docs_urls(title='NEP API')),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^downloads/', include(urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^$', views.home_page, name='home'),

    # override login url to include extra context
    url(r'^login/$', views.NepLoginView.as_view(), name='login'),

    url(r'^experiments/(?P<slug>[\w-]+)/$',
        views.experiment_detail, name='experiment-detail'),
    url(r'^experiments/(?P<experiment_id>[0-9]+)/change_status',
        views.change_status, name='change-status'),
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, }),
    url(r'^language/change/(?P<language_code>(?:(?:\w{2})|(?:\w{2}\-\w{2})))$', views.language_change,
        name='language_change'),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),

    # Ajax
    # url(r'^experiments/to_be_analysed/count/$', views.ajax_to_be_analysed,
    #     name='ajax-to_be_analysed'),
    url(r'^experiments/questionnaire_language/(?P<questionnaire_id>[0-9]+)/(?P<lang_code>.+)/$',
        views.ajax_questionnaire_languages,
        name='ajax-questionnaire_language'),

    # Haystack search
    url(r'^search/', NepSearchView.as_view(), name='search_view')
]


