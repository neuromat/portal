from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from experiments import api

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'experiments', api.ExperimentViewSet,
                base_name='api_experiments')

# Groups
api_experiment_groups_list = api.GroupViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
api_groups_list = api.GroupViewSet.as_view({
    'get': 'list',
})

# Publications
api_experiment_publications_list = api.PublicationViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
api_publications_list = api.PublicationViewSet.as_view({
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

# Amplifier
api_experiment_amplifier =\
    api.AmplifierViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Amplifier Setting
api_experiment_eeg_amplifier_setting =\
    api.EEGAmplifierSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Solution Setting
api_experiment_eeg_solution_setting =\
    api.EEGSolutionSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Filter Setting
api_experiment_eeg_filter_setting =\
    api.EEGFilterSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Electrode Net Setting
api_experiment_eeg_electrode_net_setting =\
    api.EEGElectrodeNetSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Surface Electrode
api_experiment_surface_electrode =\
    api.SurfaceElectrodeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Needle Electrode
api_experiment_needle_electrode =\
    api.NeedleElectrodeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Intramuscular Electrode
api_experiment_intramuscular_electrode =\
    api.IntramuscularElectrodeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Electrode Localization System
api_experiment_eeg_electrode_localization_system =\
    api.EEGElectrodeLocalizationSystemViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EEG Electrode Position
api_experiment_eeg_electrode_position =\
    api.EEGElectrodePositionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG setting
api_experiment_emg_setting_list =\
    api.EMGSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Digital Filter Setting
api_experiment_emg_digital_filter_setting =\
    api.EMGDigitalFilterSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# AD Converter
api_experiment_ad_converter =\
    api.ADConverterViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG AD Converter Setting
api_experiment_emg_ad_converter_setting =\
    api.EMGADConverterSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Electrode Setting
api_experiment_emg_electrode_setting =\
    api.EMGElectrodeSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Preamplifier Setting
api_experiment_emg_preamplifier_setting =\
    api.EMGPreamplifierSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Amplifier Setting
api_experiment_emg_amplifier_setting =\
    api.EMGAmplifierSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Preamplifier Filter Setting
api_experiment_emg_preamplifier_filter_setting =\
    api.EMGPreamplifierFilterSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Amplifier Filter Setting
api_experiment_emg_analog_filter_setting =\
    api.EMGAnalogFilterSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Electrode Placement Setting
api_experiment_emg_electrode_placement_setting =\
    api.EMGElectrodePlacementSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Electrode Placement
api_experiment_emg_surface_placement =\
    api.EMGSurfacePlacementViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Electrode Placement
api_experiment_emg_intramuscular_placement =\
    api.EMGIntramuscularPlacementViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# EMG Electrode Placement
api_experiment_emg_needle_placement =\
    api.EMGNeedlePlacementViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# TMS setting
api_experiment_tms_setting_list =\
    api.TMSSettingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# TMS device
api_experiment_tms_device =\
    api.TMSDeviceViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# Coil Model
api_experiment_coil_model =\
    api.CoilModelViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })

# TMS Device Setting
api_experiment_tms_device_setting =\
    api.TMSDeviceSettingViewSet.as_view({
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

# Questionnaire Language
api_questionnaire_language_list =\
    api.QuestionnaireLanguageViewSet.as_view({
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
    # Publications
    url(r'^publications/$', api_publications_list,
        name='api_publications-list'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/publications/$',
        api_experiment_publications_list,
        name='api_experiment_publications-list'),
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
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/amplifier/$',
        api_experiment_amplifier, name='api_experiment_amplifier'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_amplifier_setting/$',
        api_experiment_eeg_amplifier_setting, name='api_experiment_eeg_amplifier_setting'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_solution_setting/$',
        api_experiment_eeg_solution_setting, name='api_experiment_eeg_solution_setting'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_filter_setting/$',
        api_experiment_eeg_filter_setting, name='api_experiment_eeg_filter_setting'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_electrode_net_setting/$',
        api_experiment_eeg_electrode_net_setting, name='api_experiment_eeg_electrode_net_setting'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/surface_electrode/$',
        api_experiment_surface_electrode, name='api_experiment_surface_electrode'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/needle_electrode/$',
        api_experiment_needle_electrode, name='api_experiment_needle_electrode'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/intramuscular_electrode/$',
        api_experiment_intramuscular_electrode, name='api_experiment_intramuscular_electrode'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_electrode_localization_system/$',
        api_experiment_eeg_electrode_localization_system, name='api_experiment_eeg_electrode_localization_system'),
    url(r'^eeg_setting/(?P<pk>[0-9]+)/eeg_electrode_position/$',
        api_experiment_eeg_electrode_position, name='api_experiment_eeg_electrode_position'),

    # EMG setting
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/emg_setting/$',
        api_experiment_emg_setting_list, name='api_experiment_emg_setting-list'),
    url(r'^emg_setting/(?P<pk>[0-9]+)/emg_digital_filter_setting/$',
        api_experiment_emg_digital_filter_setting, name='api_experiment_emg_digital_filter_setting'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/ad_converter/$',
        api_experiment_ad_converter, name='api_experiment_ad_converter'),
    url(r'^emg_setting/(?P<pk>[0-9]+)/emg_ad_converter_setting/$',
        api_experiment_emg_ad_converter_setting, name='api_experiment_emg_ad_converter_setting'),
    url(r'^emg_setting/(?P<pk>[0-9]+)/emg_electrode_setting/$',
        api_experiment_emg_electrode_setting, name='api_experiment_emg_electrode_setting_setting'),
    url(r'^emg_electrode_setting/(?P<pk>[0-9]+)/emg_preamplifier_setting/$',
        api_experiment_emg_preamplifier_setting, name='api_experiment_emg_preamplifier_setting'),
    url(r'^emg_electrode_setting/(?P<pk>[0-9]+)/emg_amplifier_setting/$',
        api_experiment_emg_amplifier_setting, name='api_experiment_emg_amplifier_setting'),
    url(r'^emg_electrode_setting/(?P<pk>[0-9]+)/emg_preamplifier_filter_setting/$',
        api_experiment_emg_preamplifier_filter_setting, name='api_experiment_emg_preamplifier_filter_setting'),
    url(r'^emg_electrode_setting/(?P<pk>[0-9]+)/emg_analog_filter_setting/$',
        api_experiment_emg_analog_filter_setting, name='api_experiment_emg_analog_filter_setting'),

    url(r'^emg_electrode_setting/(?P<pk>[0-9]+)/emg_electrode_placement_setting/$',
        api_experiment_emg_electrode_placement_setting, name='api_experiment_emg_electrode_placement_setting'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/emg_surface_placement/$',
        api_experiment_emg_surface_placement, name='api_experiment_emg_surface_placement'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/emg_intramuscular_placement/$',
        api_experiment_emg_intramuscular_placement, name='api_experiment_emg_intramuscular_placement'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/emg_needle_placement/$',
        api_experiment_emg_needle_placement, name='api_experiment_emg_needle_placement'),

    # TMS setting
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/tms_setting/$',
        api_experiment_tms_setting_list, name='api_experiment_tms_setting-list'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/tms_device/$',
        api_experiment_tms_device, name='api_experiment_tmd_device'),
    url(r'^experiments/(?P<experiment_nes_id>[0-9]+)/coil_model/$',
        api_experiment_coil_model, name='api_experiment_coil_model'),
    url(r'^tms_setting/(?P<pk>[0-9]+)/tms_device_setting/$',
        api_experiment_tms_device_setting, name='api_experiment_tms_device_setting'),

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

    # Questionnaire Language
    url(r'^questionnaire_step/(?P<pk>[0-9]+)/questionnaire_language/$',
        api_questionnaire_language_list,
        name='api_questionnaire_language-list'),

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
