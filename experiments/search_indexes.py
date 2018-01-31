from haystack import indexes

from experiments.models import Experiment, Study, Group, \
    ExperimentalProtocol, TMSSetting, TMSDeviceSetting, TMSDevice, \
    CoilModel, TMSData, EEGSetting, Questionnaire, Step, \
    QuestionnaireLanguage, Publication, EMGSetting, GoalkeeperGame, \
    ContextTree, EEGElectrodeNet, EEGSolution, EEGFilterSetting, \
    EEGElectrodeLocalizationSystem, EMGDigitalFilterSetting, Stimulus, \
    GenericDataCollection, EMGElectrodePlacementSetting, EMGElectrodeSetting


class ExperimentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    owner = indexes.CharField(model_attr='owner')

    def get_model(self):
        return Experiment

    def index_queryset(self, using=None):
        return self.get_model().lastversion_objects.filter(
            status=Experiment.APPROVED
        )


class StudyIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')
    keywords = indexes.CharField(model_attr='keywords__name')
    # Requires exist researcher associated with the study. Otherwise
    # haystack will complain about researcher not being a model_attr of Study
    researcher = indexes.CharField(model_attr='researcher__id')
    collaborators = indexes.CharField(model_attr='collaborators__name')

    def get_model(self):
        return Study

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class GroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')
    inclusion_criteria = indexes.CharField(model_attr='inclusion_criteria__id')

    def get_model(self):
        return Group

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class PublicationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return Publication

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class ExperimentalProtocolIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    group = indexes.CharField(model_attr='group__id')

    def get_model(self):
        return ExperimentalProtocol

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        groups = Group.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(group__in=groups)


class StepIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    group = indexes.CharField(model_attr='group__id')

    def get_model(self):
        return Step

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        groups = Group.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(group__in=groups)


class GoalkeeperGameIndex(StepIndex):

    def get_model(self):
        return GoalkeeperGame


class StimulusIndex(StepIndex):

    def get_model(self):
        return Stimulus


class GenericDataCollectionIndex(StepIndex):

    def get_model(self):
        return GenericDataCollection


class ContextTreeIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return ContextTree

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class EMGElectrodePlacementSettingIndex(indexes.SearchIndex,
                                        indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    emg_electrode_setting = indexes.CharField(
        model_attr='emg_electrode_setting__id'
    )
    emg_electrode_placement = indexes.CharField(
        model_attr='emg_electrode_placement__id'
    )

    def get_model(self):
        return EMGElectrodePlacementSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        emg_settings = EMGSetting.objects.filter(experiment__in=experiments)
        emg_electrode_settings = EMGElectrodeSetting.objects.filter(
            emg_setting__in=emg_settings
        )
        return self.get_model().objects.filter(
            emg_electrode_setting__in=emg_electrode_settings
        )


class TMSSettingIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return TMSSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class TMSDeviceSettingIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tms_setting = indexes.CharField(model_attr='tms_setting__id')

    def get_model(self):
        return TMSDeviceSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        tms_settings = TMSSetting.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(tms_setting__in=tms_settings)


class TMSDeviceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tms_device_settings = indexes.CharField(
        model_attr='tms_device_settings__tms_setting'
    )

    def get_model(self):
        return TMSDevice

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        tms_settings = TMSSetting.objects.filter(experiment__in=experiments)
        tms_device_settings = TMSDeviceSetting.objects.filter(
            tms_setting__in=tms_settings
        )
        return self.get_model().objects.filter(
            tms_device_settings__in=tms_device_settings
        ).distinct()


class CoilModelIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tms_device_settings = indexes.CharField(
        model_attr='tms_device_settings__tms_setting'
    )

    def get_model(self):
        return CoilModel

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        tms_settings = TMSSetting.objects.filter(experiment__in=experiments)
        tms_device_settings = TMSDeviceSetting.objects.filter(
            tms_setting__in=tms_settings
        )
        return self.get_model().objects.filter(
            tms_device_settings__in=tms_device_settings
        ).distinct()


class TMSDataIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tms_setting = indexes.CharField(model_attr='tms_setting__id')

    def get_model(self):
        return TMSData

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        tms_settings = TMSSetting.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(
            tms_setting__in=tms_settings
        )


class EEGSettingIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return EEGSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class EEGElectrodeNetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    eeg_setting = indexes.CharField(model_attr='eeg_setting__id')

    def get_model(self):
        return EEGElectrodeNet

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        eeg_settings = EEGSetting.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(eeg_setting__in=eeg_settings)


class EEGSolutionIndex(EEGElectrodeNetIndex):

    def get_model(self):
        return EEGSolution


class EEGFilterSettingIndex(EEGElectrodeNetIndex):

    def get_model(self):
        return EEGFilterSetting


class EEGElectrodeLocalizationSystemIndex(EEGElectrodeNetIndex):

    def get_model(self):
        return EEGElectrodeLocalizationSystem


class EMGSettingIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return EMGSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        return self.get_model().objects.filter(experiment__in=experiments)


class EMGDigitalFilterSettingIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    emg_setting = indexes.CharField(model_attr='emg_setting__id')

    def get_model(self):
        return EMGDigitalFilterSetting

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        emg_settings = EMGSetting.objects.filter(experiment__in=experiments)
        return self.get_model().objects.filter(emg_setting__in=emg_settings)


class QuestionnaireLanguageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return QuestionnaireLanguage

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        groups = Group.objects.filter(experiment__in=experiments)
        steps = Step.objects.filter(
            group__in=groups
        ).filter(type=Step.QUESTIONNAIRE)
        questionnaire_steps = Questionnaire.objects.filter(step_ptr__in=steps)
        return self.get_model().objects.filter(
            questionnaire__in=questionnaire_steps
        )
