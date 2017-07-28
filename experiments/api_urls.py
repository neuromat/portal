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
    'get': 'list'
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

# Steps
api_step_list =\
    api.StepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Steps
api_eeg_step_list =\
    api.EEGStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# EMG Steps
api_emg_step_list =\
    api.EMGStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# TMS Steps
api_tms_step_list =\
    api.TMSStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Instruction Steps
api_instruction_step_list =\
    api.InstructionStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Pause Steps
api_pause_step_list =\
    api.PauseStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Task Steps
api_task_step_list =\
    api.TaskStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Task for Experimenter Steps
api_task_for_experimenter_step_list =\
    api.TaskForExperimenterStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Task for Experimenter Steps
api_generic_data_collection_step_list =\
    api.GenericDataCollectionStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Stimulus Steps
api_stimulus_step_list =\
    api.StimulusStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Goalkeeper Game Steps
api_goalkeeper_game_step_list =\
    api.GoalkeeperGameStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Set of Steps
api_set_of_step_list =\
    api.SetOfStepViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Questionnaire Step
api_questionnaire_step_list =\
    api.QuestionnaireStepViewSet.as_view({
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


# EMG data
api_emg_data_list =\
    api.EMGDataViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# TMS data
api_tms_data_list =\
    api.TMSDataViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# Additional data
api_additional_data_list =\
    api.AdditionalDataViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })


# Generic Data Collection data
api_generic_data_collection_data_list =\
    api.GenericDataCollectionDataViewSet.as_view({
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

    # EEG Step
    url(r'^groups/(?P<pk>[0-9]+)/eeg_step/$', api_eeg_step_list, name='api_eeg_step-list'),

    # EMG Step
    url(r'^groups/(?P<pk>[0-9]+)/emg_step/$', api_emg_step_list, name='api_emg_step-list'),

    # TMS Step
    url(r'^groups/(?P<pk>[0-9]+)/tms_step/$', api_tms_step_list, name='api_tms_step-list'),

    # Instruction Step
    url(r'^groups/(?P<pk>[0-9]+)/instruction_step/$', api_instruction_step_list, name='api_instruction_step-list'),

    # Pause Step
    url(r'^groups/(?P<pk>[0-9]+)/pause_step/$', api_pause_step_list, name='api_pause_step-list'),

    # Task Step
    url(r'^groups/(?P<pk>[0-9]+)/task_step/$', api_task_step_list, name='api_task_step-list'),

    # Task For Experimenter Step
    url(r'^groups/(?P<pk>[0-9]+)/task_for_experimenter_step/$',
        api_task_for_experimenter_step_list, name='api_task_for_experimenter_step-list'),

    # Generic Data Collection Step
    url(r'^groups/(?P<pk>[0-9]+)/generic_data_collection_step/$',
        api_generic_data_collection_step_list, name='api_generic_data_collection_step-list'),

    # Stimulus Step
    url(r'^groups/(?P<pk>[0-9]+)/stimulus_step/$',
        api_stimulus_step_list, name='api_stimulus_step-list'),

    # Goalkeeper Game Step
    url(r'^groups/(?P<pk>[0-9]+)/goalkeeper_game_step/$',
        api_goalkeeper_game_step_list, name='api_goalkeeper_game_step-list'),

    # Set of Steps
    url(r'^groups/(?P<pk>[0-9]+)/set_of_step/$',
        api_set_of_step_list, name='api_set_of_step-list'),

    # Questionnaire Step
    url(r'^groups/(?P<pk>[0-9]+)/questionnaire_step/$',
        api_questionnaire_step_list, name='api_questionnaire_step-list'),

    # File
    url(r'^files/$', api_file_list, name='api_file-list'),

    # EEG data
    url(r'^eeg_data/$', api_eeg_data_list, name='api_eeg_data-list'),

    # EMG data
    url(r'^emg_data/$', api_emg_data_list, name='api_emg_data-list'),

    # TMS data
    url(r'^tms_data/$', api_tms_data_list, name='api_tms_data-list'),

    # Goalkeeper game data
    url(r'^goalkeeper_game_data/$', api_goalkeeper_game_data_list, name='api_goalkeeper_game_data-list'),

    # Questionnaire response
    url(r'^questionnaire_response/$', api_questionnaire_response_list, name='api_questionnaire_response-list'),

    # Additional data
    url(r'^additional_data/$',
        api_additional_data_list, name='api_additional_data-list'),

    # Generic Data Collection data
    url(r'^generic_data_collection_data/$',
        api_generic_data_collection_data_list, name='api_generic_data_collection_data-list'),

]
