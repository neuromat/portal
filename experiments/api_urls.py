from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from experiments import api

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'researchers', api.ResearcherViewSet,
                base_name='api_researchers')
router.register(r'studies', api.StudyViewSet, base_name='api_studies')

urlpatterns = [
    url(r'^', include(router.urls)),
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
