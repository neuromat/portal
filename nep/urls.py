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

# internationalization in javascript
js_info_dict = {
    'packages': ('experiments',),
}

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include(api_urls)),
    url(r'^api/docs/', include_docs_urls(title='NEP API')),
    # override login method from django.contrib.auth.urls.LoginView to include
    # extra context
    url(r'^login/$', views.NepLoginView.as_view(), name='login'),
    url(r'^password_reset/$', views.NepPasswordResetView.as_view(),
        name='password_reset'
        ),
    url(r'^password_reset/done/$', views.NepPasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.NepPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^downloads/', include(urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^$', views.home_page, name='home'),

    url(r'^experiments/(?P<slug>[\w-]+)/$',
        views.experiment_detail, name='experiment-detail'),
    url(r'^experiments/(?P<experiment_id>[0-9]+)/change_status',
        views.change_status, name='change-status'),
    url(r'^experiments/(?P<experiment_id>[0-9]+)/change_slug',
        views.change_slug, name='change-slug'),
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, }),
    url(r'^language/change/(?P<language_code>(?:(?:\w{2})|(?:\w{2}\-\w{'
        r'2})))$', views.language_change,
        name='language_change'),

    # javascript internationalization
    url(r'^jsi18n/$', javascript_catalog, js_info_dict,
        name='javascript-catalog'),

    url(r'^experiments/questionnaire_language/(?P<questionnaire_id>[0-9]+)/'
        r'(?P<lang_code>.+)/$',
        views.ajax_questionnaire_languages,
        name='ajax-questionnaire_language'),

    # haystack search
    url(r'^search/', NepSearchView.as_view(), name='search_view')
]
