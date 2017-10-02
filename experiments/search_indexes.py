from haystack import indexes

from experiments.models import Experiment, Study, Group, ExperimentalProtocol, \
    TMSSetting, TMSDeviceSetting, TMSDevice, CoilModel, TMSData, EEGSetting, \
    Questionnaire, Step


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
    # haystack will complain about researcher not being a modell_attr of Study
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


class QuestionnaireIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Questionnaire

    def index_queryset(self, using=None):
        experiments = Experiment.lastversion_objects.filter(
            status=Experiment.APPROVED
        )
        groups = Group.objects.filter(experiment__in=experiments)
        steps = Step.objects.filter(
            group__in=groups
        ).filter(type=Step.QUESTIONNAIRE)
        return self.get_model().objects.filter(step_ptr__in=steps)
