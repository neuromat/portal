from django.conf.urls import url
from experiments import api

api_researchers = api.ResearcherViewSet.as_view({
    'get': 'list', 'post': 'create'
})


urlpatterns = [
    url(r'^researchers/$', api_researchers,
        name='api_researchers'),
    url(r'^studies/$', api.StudyList.as_view(), name='api_studies'),
    url(r'^researchers/(?P<pk>[0-9]+)/studies/$', api.StudyList.as_view(),
        name='api_studies_post'),
    url(r'^experiments/$', api.ExperimentList.as_view(),
        name='api_experiments'),
    url(r'^studies/(?P<pk>[0-9]+)/experiments/$',
        api.ExperimentList.as_view(), name='api_experiments_post'),
    url(r'^protocol_components/$', api.ProtocolComponentList.as_view(),
        name='api_protocolcomponents'),
    url(r'^experiments/(?P<pk>[0-9]+)/protocol_components/$',
        api.ProtocolComponentList.as_view(),
        name='api_protocolcomponents_post')
]
