from os import path

from django.db import models
from django.db.models import Max, Q
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _


# custom methods
def _delete_file_instance(instance):
    for file in instance.files.all():
        file.file.delete()
        file.delete()


def _create_slug(experiment):
    """
    Create experiment slug attribute if is the first time saving
    Obs.: method to be used only with Experiment model instances
    :param experiment: the Experiment model instance
    """
    older_versions = Experiment.objects.filter(
        nes_id=experiment.nes_id, owner=experiment.owner
    )
    # if it is not first version
    if older_versions.count() > 0:
        # adds '-v#' to the end of slugfield title, where '#' is the
        # version number of the new experiment
        experiment.slug = older_versions.first().slug + '-v' + \
                          str(older_versions.count() + 1)
    else:
        # filter and count by slug = <slug> or slug = <slug>-<#>
        # Slugs can be one of:
        # 1) <slug>
        # 2) <slug>-<#>
        # 3) <slug>-<#>-v<#>
        # we're filter and counting 1º and 2º form of slugs. Those
        # forms determine if slug base, <slug>, conflicts with slug from a new
        # experiment created.
        slugs = Experiment.objects.filter(
            slug__regex=r'^' + slugify(experiment.title) + '($|-[0-9]+$)'
        )
        if slugs.count() > 0:
            experiment.slug = slugify(experiment.title) + \
                              '-' + str(slugs.count() + 1)
        else:
            experiment.slug = slugify(experiment.title)


def get_data_file_dir(instance, filename):
    directory = "download"
    if isinstance(instance, Experiment):
        directory = path.join(directory, str(instance.id))

    return path.join(directory, filename)


# custom query sets
class LastVersionExperimentQuerySet(models.QuerySet):

    @staticmethod
    def _q_statement(queryset):
        q_statement = Q()
        for experiment in queryset:
            q_statement |= (Q(owner=experiment['owner']) &
                            Q(nes_id=experiment['nes_id']) &
                            Q(version=experiment['max_version']))
        return q_statement

    def all(self):
        max_version_set = \
            Experiment.objects.values('owner', 'nes_id').annotate(
                max_version=Max('version')
            )
        q_statement = self._q_statement(max_version_set)

        return self.filter(q_statement)

    def approved(self):
        max_version_set = \
            Experiment.objects.filter(status=Experiment.APPROVED).values(
                'owner', 'nes_id'
            ).annotate(max_version=Max('version'))
        q_statement = self._q_statement(max_version_set)

        return self.filter(q_statement)

    # Implement methods for other experiment statuses if necessary


# custom managers
class LastVersionExperimentManager(models.Manager):
    def get_queryset(self):
        return LastVersionExperimentQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset().all()

    def approved(self):
        return self.get_queryset().approved()

    # Implement methods for other experiment statuses if necessary


# models
class Experiment(models.Model):  # indexed for search
    RECEIVING = 'receiving'
    TO_BE_ANALYSED = 'to_be_analysed'
    UNDER_ANALYSIS = 'under_analysis'
    APPROVED = 'approved'
    NOT_APPROVED = 'not_approved'
    STATUS_OPTIONS = (
        (RECEIVING, _('Receiving')),
        (TO_BE_ANALYSED, _('To be analysed')),
        (UNDER_ANALYSIS, _('Under analysis')),
        (APPROVED, _('Approved')),
        (NOT_APPROVED, _('Not approved')),
    )

    owner = models.ForeignKey(User)
    nes_id = models.PositiveIntegerField()
    version = models.PositiveIntegerField()

    title = models.CharField(max_length=150)
    description = models.TextField()
    data_acquisition_done = models.BooleanField(default=False)
    sent_date = models.DateField(auto_now_add=True)
    project_url = models.CharField(max_length=255, blank=True, null=True)
    # TODO: remove this attribute. It's not necessary anymore
    download_url = models.FileField(
        upload_to=get_data_file_dir, null=True, blank=True
    )
    downloads = models.PositiveIntegerField(default=0)
    ethics_committee_url = models.CharField(max_length=255, blank=True,
                                            null=True)
    ethics_committee_file = models.FileField(
        'Project file approved by the ethics committee',
        upload_to='uploads/%Y/%m/%d/', blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_OPTIONS, default=RECEIVING
    )
    trustee = models.ForeignKey(
        User, null=True, blank=True, related_name='experiments'
    )
    # TODO: We want slug field do not save empty string.
    # TODO: This implies that the experiments are being
    # TODO: saved in tests, with slug='', what we don't want. The tests should
    # TODO: regret when saving experiments with slug=''.
    slug = models.SlugField(max_length=100, unique=True)
    release_notes = models.TextField(blank=True, default='')

    objects = models.Manager()
    lastversion_objects = LastVersionExperimentManager()

    class Meta:
        unique_together = ('nes_id', 'owner', 'version')
        permissions = (('change_slug', 'Can change experiment slug'),)

    # save slug field if it's first time save
    def save(self, *args, **kwargs):
        if not self.id:
            _create_slug(self)

        super(Experiment, self).save()

    def has_setting(self):
        return self.eegsetting_set.all() or self.emgsetting_set.all() or \
                self.tmssetting_set.all() or self.contexttree_set.all()


# TODO: delete parent subdirs if they are empty after post_delete. Example:
# TODO: uploads/2018/01/10
@receiver(post_delete, sender=Experiment)
def experiment_delete(instance, **kwargs):
    instance.ethics_committee_file.delete(save=False)


class ClassificationOfDiseases(models.Model):  # indirectly indexed for search
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=300)
    abbreviated_description = models.CharField(max_length=190)
    parent = models.ForeignKey('self', null=True, related_name='children')

    def __str__(self):
        return self.abbreviated_description


class Keyword(models.Model):  # indirectly indexed for search
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name


class Study(models.Model):  # indexed for search
    experiment = models.OneToOneField(Experiment, related_name='study')

    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    keywords = models.ManyToManyField(Keyword, blank=True)


class Researcher(models.Model):  # indirectly indexed for search
    study = models.OneToOneField(Study, related_name='researcher')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=200)
    email = models.EmailField()
    citation_name = models.CharField(max_length=302, default='', blank=True)

    def __str__(self):
        if not self.citation_name:
            return self.last_name + ', ' + self.first_name
        return self.citation_name


class ExperimentResearcher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    institution = models.CharField(max_length=200, blank=True)
    experiment = models.ForeignKey(Experiment, related_name='researchers')
    citation_name = models.CharField(max_length=252, default='', blank=True)

    def __str__(self):
        if not self.citation_name:
            return self.last_name + ', ' + self.first_name
        return self.citation_name


class Group(models.Model):  # indexed for search
    experiment = models.ForeignKey(Experiment, related_name='groups')
    title = models.CharField(max_length=50)
    description = models.TextField()
    inclusion_criteria = \
        models.ManyToManyField(ClassificationOfDiseases, blank=True)


class Gender(models.Model):  # not indexed for search
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name


class Participant(models.Model):  # not indexed for search
    group = models.ForeignKey(Group, related_name='participants')
    code = models.CharField(max_length=150)
    gender = models.ForeignKey(Gender)
    age = models.DecimalField(decimal_places=4, max_digits=8, null=True)

    class Meta:
        unique_together = ('group', 'code')

    def has_data_collection(self):
        return self.eegdata_set.all() or self.emgdata_set.all() or \
                self.tmsdata_set.all() or \
                self.additionaldata_set.all() or \
                self.genericdatacollectiondata_set.all() or \
                self.goalkeepergamedata_set.all() or \
                self.questionnaireresponse_set.all()


class Publication(models.Model):  # indexed for search
    title = models.CharField(max_length=255)
    citation = models.TextField()
    url = models.URLField(null=True, blank=True)
    experiment = models.ForeignKey(Experiment, related_name='publications')


class Equipment(models.Model):  # not indexed for search (abstract)
    EQUIPMENT_TYPES = (
        ("amplifier", "Amplifier"),
        ("eeg_solution", "EEG Solution"),
        ("filter", "Filter"),
        ("eeg_electrode_net", "EEG Electrode Net"),
        ("ad_converter", "A/D Converter"),
        ("tms_device", "TMS device")
    )
    manufacturer_name = models.CharField(max_length=150)
    equipment_type = models.CharField(null=True, blank=True, max_length=50,
                                      choices=EQUIPMENT_TYPES)
    identification = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    serial_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        abstract = True


class ExperimentSetting(models.Model):  # not indexed for search (abstract)
    experiment = models.ForeignKey(Experiment)
    name = models.CharField(max_length=150)
    description = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class EEGSetting(ExperimentSetting):  # indexed for search
    pass


# not indexed for search (objects that has ForeignKey for this model don't
# have text type attributes)
class Amplifier(Equipment):
    gain = models.FloatField(null=True, blank=True)
    number_of_channels = models.IntegerField(null=True, blank=True)
    common_mode_rejection_ratio = models.FloatField(null=True, blank=True)
    input_impedance = models.FloatField(null=True, blank=True)
    input_impedance_unit = models.CharField(null=True, blank=True, max_length=15)
    amplifier_detection_type_name = models.CharField(
        null=True, blank=True, max_length=150
    )
    tethering_system_name = models.CharField(
        null=True, blank=True, max_length=150
    )


# not indexed for search (no text type attributes)
class EEGAmplifierSetting(models.Model):
    eeg_setting = models.OneToOneField(
        EEGSetting, primary_key=True, related_name='eeg_amplifier_setting'
    )
    eeg_amplifier = models.ForeignKey(Amplifier)
    gain = models.FloatField(null=True, blank=True)
    sampling_rate = models.FloatField(null=True, blank=True)
    number_of_channels_used = models.IntegerField(null=True)


class EEGSolution(models.Model):  # indexed for search
    eeg_setting = models.OneToOneField(
        EEGSetting, primary_key=True, related_name='eeg_solution'
    )
    manufacturer_name = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    components = models.TextField(null=True, blank=True)


class EEGFilterSetting(models.Model):  # indexed for search
    eeg_setting = models.OneToOneField(EEGSetting, primary_key=True, related_name='eeg_filter_setting')
    eeg_filter_type_name = models.CharField(max_length=150)
    eeg_filter_type_description = models.TextField(null=True, blank=True)
    high_pass = models.FloatField(null=True, blank=True)
    low_pass = models.FloatField(null=True, blank=True)
    high_band_pass = models.FloatField(null=True, blank=True)
    low_band_pass = models.FloatField(null=True, blank=True)
    high_notch = models.FloatField(null=True, blank=True)
    low_notch = models.FloatField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)


class EEGElectrodeNet(Equipment):  # indexed for search
    eeg_setting = models.OneToOneField(
        EEGSetting, primary_key=True, related_name='eeg_electrode_net'
    )
    pass


class EEGElectrodeLocalizationSystem(models.Model):  # indexed for search
    eeg_setting = models.OneToOneField(
        EEGSetting, primary_key=True,
        related_name='eeg_electrode_localization_system'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    map_image_file = models.FileField(
        upload_to="uploads/%Y/%m/%d/", null=True, blank=True
    )


@receiver(post_delete, sender=EEGElectrodeLocalizationSystem)
def eeg_electrode_localization_system_delete(instance, **kwargs):
    instance.map_image_file.delete(save=False)


class ElectrodeModel(models.Model):  # indexed for search (as foreing key)
    USABILITY_TYPES = (
        ("disposable", "Disposable"),
        ("reusable", "Reusable"),
    )
    ELECTRODE_TYPES = (
        ("surface", "Surface"),
        ("intramuscular", "Intramuscular"),
        ("needle", "Needle"),
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    material = models.CharField(null=True, blank=True, max_length=150)
    usability = models.CharField(
        null=True, blank=True, max_length=50, choices=USABILITY_TYPES
    )
    impedance = models.FloatField(null=True, blank=True)
    impedance_unit = models.CharField(null=True, blank=True, max_length=15)
    inter_electrode_distance = models.FloatField(null=True, blank=True)
    inter_electrode_distance_unit = models.CharField(
        null=True, blank=True, max_length=10
    )
    electrode_configuration_name = models.CharField(
        max_length=150, null=True, blank=True
    )
    electrode_type = models.CharField(max_length=50, choices=ELECTRODE_TYPES)

    def __str__(self):
        return self.name


class SurfaceElectrode(ElectrodeModel):  # indexed for search
    CONDUCTION_TYPES = (
        ("gelled", "Gelled"),
        ("dry", "Dry"),
    )
    MODE_OPTIONS = (
        ("active", "Active"),
        ("passive", "Passive"),
    )
    conduction_type = models.CharField(
        max_length=20, choices=CONDUCTION_TYPES, null=True, blank=True
    )
    electrode_mode = models.CharField(
        max_length=20, choices=MODE_OPTIONS, null=True, blank=True
    )
    electrode_shape_name = models.CharField(
        max_length=150, null=True, blank=True
    )
    electrode_shape_measure_value = models.FloatField(null=True, blank=True)
    electrode_shape_measure_unit = models.CharField(
        max_length=150, null=True, blank=True
    )


class EEGElectrodePosition(models.Model):  # indexed for search
    eeg_electrode_localization_system = models.ForeignKey(
        EEGElectrodeLocalizationSystem,
        related_name="electrode_positions"
    )
    electrode_model = models.ForeignKey(ElectrodeModel)
    name = models.CharField(max_length=150)
    coordinate_x = models.IntegerField(null=True, blank=True)
    coordinate_y = models.IntegerField(null=True, blank=True)
    channel_index = models.IntegerField()


class IntramuscularElectrode(ElectrodeModel):  # indexed for search
    STRAND_TYPES = (
        ("single", "Single"),
        ("multi", "Multi"),
    )
    strand = models.CharField(max_length=20, choices=STRAND_TYPES)
    insulation_material_name = models.CharField(
        max_length=150, null=True, blank=True
    )
    insulation_material_description = models.TextField(null=True, blank=True)
    length_of_exposed_tip = models.FloatField(null=True, blank=True)


class NeedleElectrode(ElectrodeModel):  # not indexed for search
    SIZE_UNIT = (
        ("mm", "millimeter(s)"),
        ("cm", "centimeter(s)"),
    )
    size = models.FloatField(null=True, blank=True)
    size_unit = models.CharField(
        max_length=10, choices=SIZE_UNIT, null=True, blank=True
    )
    number_of_conductive_contact_points_at_the_tip = models.IntegerField(
        null=True, blank=True
    )
    size_of_conductive_contact_points_at_the_tip = models.FloatField(
        null=True, blank=True
    )


class EMGSetting(ExperimentSetting):  # indexed for search
    acquisition_software_version = models.CharField(max_length=150)


class EMGDigitalFilterSetting(models.Model):  # indexed for search
    emg_setting = models.OneToOneField(EMGSetting, primary_key=True, related_name='emg_digital_filter_setting')
    filter_type_name = models.CharField(max_length=150)
    filter_type_description = models.TextField(null=True, blank=True)
    low_pass = models.FloatField(null=True, blank=True)
    high_pass = models.FloatField(null=True, blank=True)
    low_band_pass = models.FloatField(null=True, blank=True)
    high_band_pass = models.FloatField(null=True, blank=True)
    low_notch = models.FloatField(null=True, blank=True)
    high_notch = models.FloatField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)


class ADConverter(Equipment):  # not indexed for search
    signal_to_noise_rate = models.FloatField(null=True, blank=True)
    sampling_rate = models.FloatField(null=True, blank=True)
    resolution = models.FloatField(null=True, blank=True)


class EMGADConverterSetting(models.Model):  # not indexed for search
    emg_setting = models.OneToOneField(EMGSetting, primary_key=True, related_name='emg_ad_converter_setting')
    ad_converter = models.ForeignKey(ADConverter)
    sampling_rate = models.FloatField(null=True, blank=True)


# not indexed for search (only foreign keys)
class EMGElectrodeSetting(models.Model):
    emg_setting = models.ForeignKey(
        EMGSetting, related_name='emg_electrode_settings'
    )
    electrode_model = models.ForeignKey(ElectrodeModel)


class EMGPreamplifierSetting(models.Model):  # not indexed for search
    emg_electrode_setting = models.OneToOneField(EMGElectrodeSetting,
                                                 primary_key=True, related_name='emg_preamplifier_setting')
    amplifier = models.ForeignKey(Amplifier)
    gain = models.FloatField(null=True, blank=True)


class EMGPreamplifierFilterSetting(models.Model):  # not indexed for search
    emg_preamplifier_setting = models.OneToOneField(EMGPreamplifierSetting,
                                                    primary_key=True,
                                                    related_name='emg_preamplifier_filter_setting')
    low_pass = models.FloatField(null=True, blank=True)
    high_pass = models.FloatField(null=True, blank=True)
    low_band_pass = models.FloatField(null=True, blank=True)
    low_notch = models.FloatField(null=True, blank=True)
    high_band_pass = models.FloatField(null=True, blank=True)
    high_notch = models.FloatField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)


class EMGAmplifierSetting(models.Model):  # not indexed for search
    emg_electrode_setting = models.OneToOneField(EMGElectrodeSetting,
                                                 primary_key=True, related_name='emg_amplifier_setting')
    amplifier = models.ForeignKey(Amplifier)
    gain = models.FloatField(null=True, blank=True)


# not indexed for search (only foreign key and number attributes)
class EMGAnalogFilterSetting(models.Model):
    emg_amplifier_setting = models.OneToOneField(
        EMGAmplifierSetting, primary_key=True,
        related_name='emg_analog_filter_setting'
    )
    low_pass = models.FloatField(null=True, blank=True)
    high_pass = models.FloatField(null=True, blank=True)
    low_band_pass = models.FloatField(null=True, blank=True)
    low_notch = models.FloatField(null=True, blank=True)
    high_band_pass = models.FloatField(null=True, blank=True)
    high_notch = models.FloatField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)


class EMGElectrodePlacement(models.Model):  # not indexed for search (parent)
    SURFACE = 'surface'
    INTRAMUSCULAR = "intramuscular"
    NEEDLE = "needle"
    PLACEMENT_TYPES = (
        (SURFACE, "Surface"),
        (INTRAMUSCULAR, "Intramuscular"),
        (NEEDLE, "Needle"),
    )
    standardization_system_name = models.CharField(max_length=150)
    standardization_system_description = models.TextField(
        null=True, blank=True
    )
    muscle_anatomy_origin = models.TextField(null=True, blank=True)
    muscle_anatomy_insertion = models.TextField(null=True, blank=True)
    muscle_anatomy_function = models.TextField(null=True, blank=True)
    photo = models.FileField(
        upload_to='uploads/%Y/%m/%d/', null=True, blank=True
    )
    location = models.TextField(null=True, blank=True)
    placement_type = models.CharField(max_length=50, choices=PLACEMENT_TYPES)


@receiver(post_delete, sender=EMGElectrodePlacement)
def emg_electrode_placement(instance, **kwargs):
    instance.photo.delete(save=False)


class EMGSurfacePlacement(EMGElectrodePlacement):
    start_posture = models.TextField(null=True, blank=True)
    orientation = models.TextField(null=True, blank=True)
    fixation_on_the_skin = models.TextField(null=True, blank=True)
    reference_electrode = models.TextField(null=True, blank=True)
    clinical_test = models.TextField(null=True, blank=True)


class EMGIntramuscularPlacement(EMGElectrodePlacement):
    method_of_insertion = models.TextField(null=True, blank=True)
    depth_of_insertion = models.TextField(null=True, blank=True)


class EMGNeedlePlacement(EMGElectrodePlacement):
    depth_of_insertion = models.TextField(null=True, blank=True)


class EMGElectrodePlacementSetting(models.Model):  # indexed for search
    emg_electrode_setting = models.OneToOneField(
        EMGElectrodeSetting, primary_key=True,
        related_name='emg_electrode_placement_setting'
    )
    emg_electrode_placement = models.ForeignKey(EMGElectrodePlacement)
    muscle_side = models.CharField(max_length=150, null=True, blank=True)
    muscle_name = models.CharField(max_length=150, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)


class TMSSetting(ExperimentSetting):  # indexed for search
    pass


class TMSDevice(Equipment):  # indexed for search
    PULSE_TYPES = (
        ("monophase", "Monophase"),
        ("biphase", "Biphase"),
    )
    pulse_type = models.CharField(
        null=True, blank=True, max_length=50, choices=PULSE_TYPES
    )


class CoilModel(models.Model):  # indexed for search
    COIL_DESIGN_OPTIONS = (
        ("air_core_coil", "Air core coil"),
        ("solid_core_coil", "Solid core coil"),
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    coil_shape_name = models.CharField(max_length=150)
    material_name = models.CharField(null=True, blank=True, max_length=150)
    material_description = models.TextField(null=True, blank=True)
    coil_design = models.CharField(null=True, blank=True, max_length=50, choices=COIL_DESIGN_OPTIONS)


class TMSDeviceSetting(models.Model):  # indexed for search
    PULSE_STIMULUS_TYPES = (
        ("single_pulse", "Single pulse"),
        ("paired_pulse", "Paired pulse"),
        ("repetitive_pulse", "Repetitive pulse")
    )
    tms_setting = models.OneToOneField(
        TMSSetting, primary_key=True, related_name='tms_device_setting'
    )
    tms_device = models.ForeignKey(
        TMSDevice, related_name='tms_device_settings'
    )
    pulse_stimulus_type = models.CharField(
        null=True, blank=True, max_length=50, choices=PULSE_STIMULUS_TYPES
    )
    coil_model = models.ForeignKey(CoilModel,
                                   related_name='tms_device_settings')


class ContextTree(ExperimentSetting):  # indexed for search
    setting_text = models.TextField(null=True, blank=True)
    setting_file = models.FileField(
        upload_to='uploads/%Y/%m/%d/', null=True, blank=True
    )


@receiver(post_delete, sender=ContextTree)
def context_tree_delete(instance, **kwargs):
    instance.setting_file.delete(save=False)


# indexed for search (despite being parent, some children has only its
# attributes besides on or other foreign key)
class Step(models.Model):
    BLOCK = 'block'
    INSTRUCTION = 'instruction'
    PAUSE = 'pause'
    QUESTIONNAIRE = 'questionnaire'
    STIMULUS = 'stimulus'
    TASK = 'task'
    TASK_EXPERIMENT = 'task_experiment'
    EEG = 'eeg'
    EMG = 'emg'
    TMS = 'tms'
    GOALKEEPER = 'goalkeeper_game'
    GENERIC = 'generic_data_collection'
    STEP_TYPES = (
        (BLOCK, "Set of steps"),
        (INSTRUCTION, "Instruction"),
        (PAUSE, "Pause"),
        (QUESTIONNAIRE, "Questionnaire"),
        (STIMULUS, "Stimulus"),
        (TASK, "Task for participant"),
        (TASK_EXPERIMENT, "Task for experimenter"),
        (EEG, "EEG"),
        (EMG, "EMG"),
        (TMS, "TMS"),
        (GOALKEEPER, "Goalkeeper game phase"),
        (GENERIC, "Generic data collection"),
    )
    group = models.ForeignKey(Group, related_name='steps')
    identification = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    duration_value = models.IntegerField(null=True, blank=True)
    duration_unit = models.CharField(null=True, blank=True, max_length=15)
    numeration = models.CharField(max_length=50)
    type = models.CharField(max_length=30, choices=STEP_TYPES)
    parent = models.ForeignKey('self', null=True, related_name='children')
    order = models.IntegerField()
    number_of_repetitions = models.IntegerField(
        null=True, blank=True, default=1
    )
    interval_between_repetitions_value = models.IntegerField(
        null=True, blank=True
    )
    interval_between_repetitions_unit = models.CharField(
        null=True, blank=True, max_length=15
    )
    random_position = models.NullBooleanField(blank=True)

    def __str__(self):
        return self.type


# not indexed for search (indexed Step)
class StepAdditionalFile(models.Model):
    step = models.ForeignKey(Step, related_name="step_additional_files")
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')


@receiver(post_delete, sender=StepAdditionalFile)
def step_additional_file_delete(instance, **kwargs):
    instance.file.delete(save=False)


class EEG(Step):  # not indexed for search (indexed Step)
    eeg_setting = models.ForeignKey(EEGSetting)


class EMG(Step):  # not indexed for search (indexed Step)
    emg_setting = models.ForeignKey(EMGSetting)


class TMS(Step):  # not indexed for search (indexed Step)
    tms_setting = models.ForeignKey(TMSSetting)


class Questionnaire(Step):  # not indexed for search (indexed Step)
    code = models.CharField(max_length=150)


class QuestionnaireLanguage(models.Model):  # indexed for search
    questionnaire = models.ForeignKey(
        Questionnaire, related_name='q_languages'
    )
    language_code = models.CharField(max_length=30)
    survey_name = models.CharField(max_length=255)
    survey_metadata = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('questionnaire', 'language_code')


class QuestionnaireDefaultLanguage(models.Model):  # not indexed for search
    questionnaire = models.OneToOneField(
        Questionnaire, related_name='questionnaire_default_language'
    )
    questionnaire_language = models.ForeignKey(QuestionnaireLanguage)


class Instruction(Step):  # indexed for search
    text = models.TextField(null=False, blank=False)


class Stimulus(Step):  # indexed for search
    stimulus_type_name = models.CharField(
        null=False, blank=False, max_length=30
    )
    media_file = models.FileField(
        null=True, blank=True, upload_to='uploads/%Y/%m/%d/'
    )


@receiver(post_delete, sender=Stimulus)
def stimulus_delete(instance, **kwargs):
    instance.media_file.delete(save=False)


class GoalkeeperGame(Step):  # indexed for search
    software_name = models.CharField(max_length=150)
    software_description = models.TextField(null=True, blank=True)
    software_version = models.CharField(max_length=150)
    context_tree = models.ForeignKey(ContextTree)


class GenericDataCollection(Step):  # indexed for search
    information_type_name = models.CharField(max_length=150)
    information_type_description = models.TextField(null=True, blank=True)


class Pause(Step):  # not indexed for search (indexed Step)
    pass


class Task(Step):  # not indexed for search (indexed Step)
    pass


class TaskForTheExperimenter(Step):  # not indexed for search (indexed Step)
    pass


class SetOfStep(Step):  # not indexed for search (indexed Step)
    number_of_mandatory_steps = models.IntegerField(null=True, blank=True)
    is_sequential = models.BooleanField(default=False)


class ExperimentalProtocol(models.Model):  # indexed for search
    group = models.OneToOneField(Group, related_name='experimental_protocol')
    image = models.FileField(null=True, blank=True,
                             upload_to='uploads/%Y/%m/%d/')
    textual_description = models.TextField()
    root_step = models.ForeignKey(Step, null=True, blank=True)


@receiver(post_delete, sender=ExperimentalProtocol)
def experimental_protocol_delete(instance, **kwargs):
    instance.image.delete(save=False)


class DataCollection(models.Model):  # not indexed for search
    # step == null means data collection is associated to whole experimental
    # protocol.
    step = models.ForeignKey(Step, null=True, blank=True)
    participant = models.ForeignKey(Participant)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    class Meta:
        abstract = True


class File(models.Model):  # not indexed for search
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')


class DataFile(models.Model):  # not indexed for search (abstract)
    description = models.TextField()
    file_format = models.CharField(max_length=50)

    class Meta:
        abstract = True


class EEGData(DataCollection, DataFile):  # not indexed for search
    eeg_setting = models.ForeignKey(EEGSetting)
    eeg_setting_reason_for_change = models.TextField(
        null=True, blank=True, default=''
    )
    eeg_cap_size = models.CharField(max_length=30, null=True, blank=True)
    files = models.ManyToManyField(File, related_name='eeg_data_list')


@receiver(pre_delete, sender=EEGData)
def eeg_data_delete(instance, **kwargs):
    _delete_file_instance(instance)


class EMGData(DataCollection, DataFile):  # not indexed for search
    emg_setting = models.ForeignKey(EMGSetting)
    emg_setting_reason_for_change = models.TextField(null=True, blank=True, default='')
    files = models.ManyToManyField(File, related_name='emg_data_list')


@receiver(pre_delete, sender=EMGData)
def emg_data_delete(instance, **kwargs):
    _delete_file_instance(instance)


class TMSData(DataCollection):  # indexed for search
    # main data
    tms_setting = models.ForeignKey(TMSSetting)
    resting_motor_threshold = models.FloatField(null=True, blank=True)
    test_pulse_intensity_of_simulation = models.FloatField(
        null=True, blank=True
    )
    second_test_pulse_intensity = models.FloatField(null=True, blank=True)
    interval_between_pulses = models.IntegerField(null=True, blank=True)
    interval_between_pulses_unit = models.CharField(
        null=True, blank=True, max_length=15
    )
    time_between_mep_trials = models.IntegerField(null=True, blank=True)
    time_between_mep_trials_unit = models.CharField(
        null=True, blank=True, max_length=15
    )
    repetitive_pulse_frequency = models.IntegerField(null=True, blank=True)
    coil_orientation = models.CharField(null=True, blank=True, max_length=150)
    coil_orientation_angle = models.IntegerField(null=True, blank=True)
    direction_of_induced_current = models.CharField(
        null=True, blank=True, max_length=150
    )
    description = models.TextField(null=False, blank=False)
    # hotspot data
    hotspot_name = models.CharField(max_length=50)
    coordinate_x = models.IntegerField(null=True, blank=True)
    coordinate_y = models.IntegerField(null=True, blank=True)
    hot_spot_map = models.FileField(
        upload_to='uploads/%Y/%m/%d/', null=True, blank=True
    )
    # localization system info
    localization_system_name = models.CharField(
        null=False, max_length=50, blank=False
    )
    localization_system_description = models.TextField(null=True, blank=True)
    localization_system_image = models.FileField(
        upload_to='uploads/%Y/%m/%d/', null=True, blank=True
    )
    # brain area info
    brain_area_name = models.CharField(null=False, max_length=50, blank=False)
    brain_area_description = models.TextField(null=True, blank=True)
    # brain area system info
    brain_area_system_name = models.CharField(
        null=False, max_length=50, blank=False
    )
    brain_area_system_description = models.TextField(null=True, blank=True)


@receiver(post_delete, sender=TMSData)
def tms_data_delete(instance, **kwargs):
    instance.hot_spot_map.delete(save=False)
    instance.localization_system_image.delete(save=False)


class GoalkeeperGameData(DataCollection, DataFile):  # not indexed for search
    sequence_used_in_context_tree = models.TextField(null=True, blank=True)
    files = models.ManyToManyField(
        File, related_name='goalkeeper_game_data_list'
    )


@receiver(pre_delete, sender=GoalkeeperGameData)
def gkg_data_delete(instance, **kwargs):
    _delete_file_instance(instance)


class RejectJustification(models.Model):  # not indexed for search
    message = models.CharField(max_length=500)
    experiment = models.OneToOneField(Experiment,
                                      related_name='justification')


class QuestionnaireResponse(DataCollection):  # not indexed for search
    limesurvey_response = models.TextField()


# not indexed for search
class GenericDataCollectionData(DataCollection, DataFile):
    files = models.ManyToManyField(
        File, related_name='generic_data_collection_data_list'
    )


@receiver(pre_delete, sender=GenericDataCollectionData)
def gdc_data_delete(instance, **kwargs):
    _delete_file_instance(instance)


class AdditionalData(DataCollection, DataFile): # not indexed for search
    files = models.ManyToManyField(File, related_name='additional_data_list')


@receiver(pre_delete, sender=AdditionalData)
def additional_data_delete(instance, **kwargs):
    _delete_file_instance(instance)
