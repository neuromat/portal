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

# Participants
api_participant_list =\
    api.ParticipantViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Researchers (of studies)
api_researcher_list = api.ResearcherViewSet.as_view({
    'get': 'list'
})
api_studies_researcher_list = api.ResearcherViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

# Collaborators (of studies)
api_collaborators_list = api.CollaboratorViewSet.as_view({
    'get': 'list',
})
api_study_collaborators_list = api.CollaboratorViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

# EEG setting
api_experiment_eeg_setting_list =\
    api.EEGSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG setting
api_experiment_emg_setting_list =\
    api.EMGSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# TMS setting
api_experiment_tms_setting_list =\
    api.TMSSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Context tree
api_experiment_context_tree_list =\
    api.ContextTreeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Participants
api_step_list =\
    api.StepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Files
api_file_list =\
    api.FileViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG data
api_eeg_data_list =\
    api.EEGDataViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# Goalkeeper game data
api_goalkeeper_game_data_list =\
    api.GoalkeeperGameDataViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# Questionnaire response
api_questionnaire_response_list =\
    api.QuestionnaireResponseViewSet.as_view({
        'get': 'list',
        'post': 'create'
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
    # Participants
    url(r'^groups/(?P<pk>[0-9]+)/participant/$',
        api_participant_list,
        name='api_participant-list'),
    # Researchers
    url(r'^researchers/$', api_researcher_list, name='api_researchers-list'),
    url(r'^studies/(?P<pk>[0-9]+)/researcher/$', api_studies_researcher_list,
        name='api_study_researcher-list'),
    # Collaborators
    url(r'^collaborators/$', api_collaborators_list,
        name='api_collaborators-list'),
    url(r'^studies/(?P<pk>[0-9]+)/collaborators/$',
        api_study_collaborators_list, name='api_study_collaborators-list'),

    # EEG setting
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/eeg_setting/$',
        api_experiment_eeg_setting_list, name='api_experiment_eeg_setting-list'),
    # EMG setting
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/emg_setting/$',
        api_experiment_emg_setting_list, name='api_experiment_emg_setting-list'),
    # TMS setting
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/tms_setting/$',
        api_experiment_tms_setting_list, name='api_experiment_tms_setting-list'),
    # Context tree
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/context_tree/$',
        api_experiment_context_tree_list, name='api_experiment_context_tree-list'),

    # Step
    url(r'^groups/(?P<pk>[0-9]+)/step/$', api_step_list, name='api_step-list'),

    # File
    url(r'^files/$', api_file_list, name='api_file-list'),

    # EEG data
    url(r'^eeg_data/$', api_eeg_data_list, name='api_eeg_data-list'),

    # Goalkeeper game data
    url(r'^goalkeeper_game_data/$', api_goalkeeper_game_data_list, name='api_goalkeeper_game_data-list'),

    # Questionnaire response
    url(r'^questionnaire_response/$', api_questionnaire_response_list, name='api_questionnaire_response-list'),

]
