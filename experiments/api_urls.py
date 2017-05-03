from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from experiments import api

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'researchers', api.ResearcherViewSet,
                base_name='api_researchers')

urlpatterns = [
    url(r'^', include(router.urls)),
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
