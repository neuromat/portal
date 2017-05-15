from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from experiments import api

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'researchers', api.ResearcherViewSet,
                base_name='api_researchers')
router.register(r'studies', api.StudyViewSet, base_name='api_studies')
router.register(r'experiments', api.ExperimentViewSet,
                base_name='api_experiments')
router.register(r'protocol_components', api.ProtocolComponentViewSet,
                base_name='api_protocol_components')
router.register(r'groups', api.GroupViewSet,
                base_name='api_groups')

urlpatterns = [
    url(r'^', include(router.urls)),
]
