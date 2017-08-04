from django.db import models
from django.db.models import Max, Q
from django.contrib.auth.models import User


class CurrentExperimentManager(models.Manager):
    def get_queryset(self):
        experiment_max_version_set = \
            Experiment.objects.values('owner', 'nes_id').annotate(
                max_version=Max('version'))
        q_statement = Q()
        for experiment in experiment_max_version_set:
            q_statement |= (Q(owner=experiment['owner']) &
                            Q(nes_id=experiment['nes_id']) &
                            Q(version=experiment['max_version']))

        return super(CurrentExperimentManager, self).get_queryset()\
            .filter(q_statement)


class Experiment(models.Model):
    RECEIVING = 'receiving'
    TO_BE_ANALYSED = 'to_be_analysed'
    UNDER_ANALYSIS = 'under_analysis'
    APPROVED = 'approved'
    NOT_APPROVED = 'not_approved'
    STATUS_OPTIONS = (
        (RECEIVING, 'Receiving'),
        (TO_BE_ANALYSED, 'To be analysed'),
        (UNDER_ANALYSIS, 'Under analysis'),
        (APPROVED, 'Approved'),
        (NOT_APPROVED, 'Not approved'),
    )

    owner = models.ForeignKey(User)
    nes_id = models.PositiveIntegerField()
    version = models.PositiveIntegerField()

    title = models.CharField(max_length=150)
    description = models.TextField()
    data_acquisition_done = models.BooleanField(default=False)
    sent_date = models.DateField(auto_now=True)
    project_url = models.CharField(max_length=255, blank=True, null=True)
    ethics_committee_url = models.CharField(max_length=255, blank=True,
                                            null=True)
    ethics_committee_file = models.FileField(
        'Project file approved by the ethics committee',
        upload_to='uploads/%Y/%m/%d/', blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_OPTIONS, default=RECEIVING
    )
    trustee = models.ForeignKey(User, null=True,
                                blank=True, related_name='experiments')

    # Managers
    objects = models.Manager()
    lastversion_objects = CurrentExperimentManager()

    class Meta:
        unique_together = ('nes_id', 'owner', 'version')


class ClassificationOfDiseases(models.Model):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=300)
    abbreviated_description = models.CharField(max_length=190)
    parent = models.ForeignKey('self', null=True, related_name='children')

    def __str__(self):
        return self.abbreviated_description


class Keyword(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name


class Study(models.Model):
    experiment = models.OneToOneField(Experiment, related_name='study')

    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    keywords = models.ManyToManyField(Keyword, blank=True)


class Researcher(models.Model):
    study = models.OneToOneField(Study, related_name='researcher')
    name = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Collaborator(models.Model):
    name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    coordinator = models.BooleanField(default=False)
    study = models.ForeignKey(Study, related_name='collaborators')

    def __str__(self):
        return self.name


class ProtocolComponent(models.Model):
    experiment = models.ForeignKey(
        Experiment, related_name='protocol_components'
    )
    nes_id = models.PositiveIntegerField()

    identification = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    duration_value = models.IntegerField(null=True)
    component_type = models.CharField(max_length=30)

    class Meta:
        unique_together = ('nes_id', 'experiment')


class Group(models.Model):
    experiment = models.ForeignKey(Experiment, related_name='groups')
    title = models.CharField(max_length=50)
    description = models.TextField()
    inclusion_criteria = \
        models.ManyToManyField(ClassificationOfDiseases, blank=True)
    protocol_component = models.ForeignKey(
        ProtocolComponent, null=True, blank=True
    )  # TODO: define if Group has ProtocolComponent


class Gender(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name


class Participant(models.Model):
    group = models.ForeignKey(Group, related_name='participants')
    code = models.CharField(max_length=150)

    gender = models.ForeignKey(Gender)
    age = models.DecimalField(decimal_places=4, max_digits=8)

    class Meta:
        unique_together = ('group', 'code')


class ExperimentSetting(models.Model):
    experiment = models.ForeignKey(Experiment)
    name = models.CharField(max_length=150)
    description = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class EEGSetting(ExperimentSetting):
    pass


class EMGSetting(ExperimentSetting):
    acquisition_software_version = models.CharField(max_length=150)


class TMSSetting(ExperimentSetting):
    pass


class ContextTree(ExperimentSetting):
    setting_text = models.TextField(null=True, blank=True)
    setting_file = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)


class Step(models.Model):
    STEP_TYPES = (
        ("block", "Set of steps"),
        ("instruction", "Instruction"),
        ("pause", "Pause"),
        ("questionnaire", "Questionnaire"),
        ("stimulus", "Stimulus"),
        ("task", "Task for participant"),
        ("task_experiment", "Task for experimenter"),
        ("eeg", "EEG"),
        ("emg", "EMG"),
        ("tms", "TMS"),
        ("goalkeeper_game", "Goalkeeper game phase"),
        ("generic_data_collection", "Generic data collection"),
    )
    group = models.ForeignKey(Group)
    identification = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    duration_value = models.IntegerField(null=True, blank=True)
    duration_unit = models.CharField(null=True, blank=True, max_length=15)
    numeration = models.CharField(max_length=50)
    type = models.CharField(max_length=30, choices=STEP_TYPES)
    parent = models.ForeignKey('self', null=True, related_name='children')
    order = models.IntegerField()
    number_of_repetitions = models.IntegerField(null=True, blank=True, default=1)
    interval_between_repetitions_value = models.IntegerField(null=True, blank=True)
    interval_between_repetitions_unit = models.CharField(null=True, blank=True, max_length=15)
    random_position = models.NullBooleanField(blank=True)


class EEG(Step):
    eeg_setting = models.ForeignKey(EEGSetting)


class EMG(Step):
    emg_setting = models.ForeignKey(EMGSetting)


class TMS(Step):
    tms_setting = models.ForeignKey(TMSSetting)


class Questionnaire(Step):
    survey_name = models.CharField(max_length=255)
    survey_metadata = models.TextField(null=True, blank=True)


class Instruction(Step):
    text = models.TextField(null=False, blank=False)


class Stimulus(Step):
    stimulus_type_name = models.CharField(null=False, blank=False, max_length=30)
    media_file = models.FileField(null=True, blank=True, upload_to='uploads/%Y/%m/%d/')


class GoalkeeperGame(Step):
    software_name = models.CharField(max_length=150)
    software_description = models.TextField(null=True, blank=True)
    software_version = models.CharField(max_length=150)
    context_tree = models.ForeignKey(ContextTree)


class GenericDataCollection(Step):
    information_type_name = models.CharField(max_length=150)
    information_type_description = models.TextField(null=True, blank=True)


class Pause(Step):
    pass


class Task(Step):
    pass


class TaskForTheExperimenter(Step):
    pass


class SetOfStep(Step):
    number_of_mandatory_steps = models.IntegerField(null=True, blank=True)
    is_sequential = models.BooleanField(default=False)


class ExperimentalProtocol(models.Model):
    group = models.OneToOneField(Group, related_name='experimental_protocol')
    image = models.FileField(null=True, blank=True, upload_to='uploads/%Y/%m/%d/')
    textual_description = models.TextField(null=True, blank=True)
    root_step = models.ForeignKey(Step, null=True, blank=True)


class DataCollection(models.Model):
    step = models.ForeignKey(Step, null=True, blank=True)
    participant = models.ForeignKey(Participant)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    class Meta:
        abstract = True


class File(models.Model):
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')


class DataFile(models.Model):
    description = models.TextField()
    file = models.ForeignKey(File)
    file_format = models.CharField(max_length=50)

    class Meta:
        abstract = True


class EEGData(DataCollection, DataFile):
    eeg_setting = models.ForeignKey(EEGSetting)
    eeg_setting_reason_for_change = models.TextField(null=True, blank=True, default='')
    eeg_cap_size = models.CharField(max_length=30, null=True, blank=True)


class EMGData(DataFile, DataCollection):
    emg_setting = models.ForeignKey(EMGSetting)
    emg_setting_reason_for_change = models.TextField(null=True, blank=True, default='')


class TMSData(DataCollection):
    # main data
    tms_setting = models.ForeignKey(TMSSetting)
    resting_motor_threshold = models.FloatField(null=True, blank=True)
    test_pulse_intensity_of_simulation = models.FloatField(null=True, blank=True)
    second_test_pulse_intensity = models.FloatField(null=True, blank=True)
    interval_between_pulses = models.IntegerField(null=True, blank=True)
    interval_between_pulses_unit = models.CharField(null=True, blank=True, max_length=15)
    time_between_mep_trials = models.IntegerField(null=True, blank=True)
    time_between_mep_trials_unit = models.CharField(null=True, blank=True, max_length=15)
    repetitive_pulse_frequency = models.IntegerField(null=True, blank=True)
    coil_orientation = models.CharField(null=True, blank=True, max_length=150)
    coil_orientation_angle = models.IntegerField(null=True, blank=True)
    direction_of_induced_current = models.CharField(null=True, blank=True, max_length=150)
    description = models.TextField(null=False, blank=False)
    # hotspot data
    hotspot_name = models.CharField(max_length=50)
    coordinate_x = models.IntegerField(null=True, blank=True)
    coordinate_y = models.IntegerField(null=True, blank=True)
    hot_spot_map = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    # localization system info
    localization_system_name = models.CharField(null=False, max_length=50, blank=False)
    localization_system_description = models.TextField(null=True, blank=True)
    localization_system_image = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    # brain area info
    brain_area_name = models.CharField(null=False, max_length=50, blank=False)
    brain_area_description = models.TextField(null=True, blank=True)
    # brain area system info
    brain_area_system_name = models.CharField(null=False, max_length=50, blank=False)
    brain_area_system_description = models.TextField(null=True, blank=True)


class GoalkeeperGameData(DataCollection, DataFile):
    sequence_used_in_context_tree = models.TextField(null=True, blank=True)


class RejectJustification(models.Model):
    message = models.CharField(max_length=500)
    experiment = models.OneToOneField(Experiment,
                                      related_name='justification')


class QuestionnaireResponse(DataCollection):
    limesurvey_response = models.TextField()


class GenericDataCollectionData(DataFile, DataCollection):
    pass


class AdditionalData(DataFile, DataCollection):
    pass
