from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from experiments import api

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'experiments', api.ExperimentViewSet,
                base_name='api_experiments')
# router.register(r'protocol_components', api.ProtocolComponentViewSet,
#                 base_name='api_protocol_components')

# Groups
api_experiment_groups_list = api.GroupViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
api_groups_list = api.GroupViewSet.as_view({
    'get': 'list',
})

# Studies
api_experiment_studies_list = api.StudyViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
api_studies_list = api.StudyViewSet.as_view({
    'get': 'list',
})

# Experimental protocols
api_group_experimental_protocol_list =\
    api.ExperimentalProtocolViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Researchers
api_studies_researcher_list = api.ResearcherViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
api_researcher_list = api.ResearcherViewSet.as_view({
    'get': 'list'
})


# Get rest framework schema view
schema_view = get_schema_view(title='NEP API')

urlpatterns = [
    url(r'^schema/$', schema_view),
    url(r'^', include(router.urls)),
    # Studies
    url(r'^studies/$', api_studies_list, name='api_studies-list'),
    # TODO: uniformizar nomenclatura (singular X plural quando camo é um
    # para um)
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/studies/$',
        api_experiment_studies_list, name='api_experiment_studies-list'),
    # Groups
    url(r'^groups/$', api_groups_list, name='api_groups-list'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/groups/$',
        api_experiment_groups_list, name='api_experiment_groups-list'),
    # Experimental protocols
    url(r'^groups/(?P<pk>[0-9]+)/experimental_protocol/$',
        api_group_experimental_protocol_list,
        name='api_group_experimental_protocol-list'),
    # Researchers
    url(r'^researchers/$', api_researcher_list, name='api_researchers-list'),
    url(r'^studies/(?P<pk>[0-9]+)/researcher/$', api_studies_researcher_list,
        name='api_study_researcher-list')
]
