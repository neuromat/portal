from django.contrib.auth.models import AnonymousUser
from django.core.mail import send_mail
from rest_framework import serializers, permissions, viewsets

from experiments import appclasses
from experiments.models import Experiment, Study, User, ProtocolComponent, \
    Group, ExperimentalProtocol, Researcher, Participant, Collaborator, \
    Keyword, ClassificationOfDiseases, \
    EEGSetting, EMGSetting, TMSSetting, ContextTree, Step, File, \
    EEGData, EMGData, TMSData, GoalkeeperGameData, QuestionnaireResponse, \
    AdditionalData, GenericDataCollectionData, EEG, EMG, TMS, Instruction, Pause, Task, TaskForTheExperimenter, \
    GenericDataCollection, Stimulus, GoalkeeperGame, SetOfStep, Questionnaire, \
    EEGAmplifierSetting, Amplifier, EEGSolution, EEGFilterSetting, EEGElectrodeNet, \
    SurfaceElectrode, NeedleElectrode, IntramuscularElectrode, EEGElectrodeLocalizationSystem, EEGElectrodePosition, \
    TMSDeviceSetting, TMSDevice, CoilModel, \
    EMGDigitalFilterSetting, ADConverter, EMGADConverterSetting, EMGElectrodeSetting, \
    EMGPreamplifierSetting, EMGAmplifierSetting, EMGPreamplifierFilterSetting, EMGAnalogFilterSetting, \
    EMGElectrodePlacementSetting, \
    EMGSurfacePlacement, EMGIntramuscularPlacement, EMGNeedlePlacement


###################
# API Serializers #
###################
class ExperimentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    protocol_components = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    class Meta:
        model = Experiment
        fields = ('id', 'title', 'description', 'data_acquisition_done',
                  'nes_id', 'owner', 'status', 'protocol_components',
                  'sent_date', 'project_url', 'ethics_committee_url',
                  'ethics_committee_file')


class UserSerializer(serializers.ModelSerializer):
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Experiment.objects.all()
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'experiments')


class KeywordSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)

    class Meta:
        model = Keyword
        fields = ('name',)


class StudySerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')
    keywords = KeywordSerializer(many=True, read_only=False)

    class Meta:
        model = Study
        fields = ('id', 'title', 'description', 'start_date',
                  'end_date', 'experiment', 'keywords')

    def create(self, validated_data):
        if 'end_date' in validated_data:
            study = Study.objects.create(experiment=validated_data['experiment'],
                                         title=validated_data['title'],
                                         description=validated_data['description'],
                                         start_date=validated_data['start_date'],
                                         end_date=validated_data['end_date'])
        else:
            study = Study.objects.create(experiment=validated_data['experiment'],
                                         title=validated_data['title'],
                                         description=validated_data['description'],
                                         start_date=validated_data['start_date'])
        if 'keywords' in self.initial_data:
            keywords_data = self.initial_data['keywords']
            for keyword_data in keywords_data:
                keyword, created = \
                    Keyword.objects.get_or_create(name=keyword_data['name'])
                study.keywords.add(keyword)
        return study


class ResearcherSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')

    class Meta:
        model = Researcher
        fields = ('id', 'name', 'email', 'study')


class CollaboratorSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')

    class Meta:
        model = Collaborator
        fields = ('id', 'name', 'team', 'coordinator', 'study')


class AmplifierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Amplifier
        fields = (
            'id',
            'manufacturer_name',
            'equipment_type',
            'identification',
            'description',
            'serial_number',
            'gain',
            'number_of_channels',
            'common_mode_rejection_ratio',
            'input_impedance',
            'input_impedance_unit',
            'amplifier_detection_type_name',
            'tethering_system_name'
        )


class EEGAmplifierSettingSerializer(serializers.ModelSerializer):
    eeg_setting = serializers.ReadOnlyField(source='eeg_setting.name')

    class Meta:
        model = EEGAmplifierSetting
        fields = ('eeg_setting', 'eeg_amplifier', 'gain', 'sampling_rate', 'number_of_channels_used')


class EEGSolutionSettingSerializer(serializers.ModelSerializer):
    eeg_setting = serializers.ReadOnlyField(source='eeg_setting.name')

    class Meta:
        model = EEGSolution
        fields = ('eeg_setting', 'manufacturer_name', 'name', 'components')


class EEGFilterSettingSerializer(serializers.ModelSerializer):
    eeg_setting = serializers.ReadOnlyField(source='eeg_setting.name')

    class Meta:
        model = EEGFilterSetting
        fields = ('eeg_setting', 'eeg_filter_type_name', 'eeg_filter_type_description', 'high_pass', 'low_pass',
                  'high_band_pass', 'low_band_pass', 'high_notch', 'low_notch', 'order')


class SurfaceElectrodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurfaceElectrode
        fields = (
            'id',

            'name',
            'description',
            'material',
            'usability',
            'impedance',
            'impedance_unit',
            'inter_electrode_distance',
            'inter_electrode_distance_unit',
            'electrode_configuration_name',
            'electrode_type',

            'conduction_type',
            'electrode_mode',
            'electrode_shape_name',
            'electrode_shape_measure_value',
            'electrode_shape_measure_unit'
        )


class NeedleElectrodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeedleElectrode
        fields = (
            'id',

            'name',
            'description',
            'material',
            'usability',
            'impedance',
            'impedance_unit',
            'inter_electrode_distance',
            'inter_electrode_distance_unit',
            'electrode_configuration_name',
            'electrode_type',

            'size',
            'size_unit',
            'number_of_conductive_contact_points_at_the_tip',
            'size_of_conductive_contact_points_at_the_tip'
        )


class IntramuscularElectrodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntramuscularElectrode
        fields = (
            'id',

            'name',
            'description',
            'material',
            'usability',
            'impedance',
            'impedance_unit',
            'inter_electrode_distance',
            'inter_electrode_distance_unit',
            'electrode_configuration_name',
            'electrode_type',

            'strand',
            'insulation_material_name',
            'insulation_material_description',
            'length_of_exposed_tip'
        )


class EEGElectrodeLocalizationSystemSerializer(serializers.ModelSerializer):
    eeg_setting = serializers.ReadOnlyField(source='eeg_setting.name')

    class Meta:
        model = EEGElectrodeLocalizationSystem
        fields = ('eeg_setting', 'name', 'description', 'map_image_file')


class EEGElectrodePositionSerializer(serializers.ModelSerializer):
    eeg_electrode_localization_system = serializers.ReadOnlyField(source='eeg_electrode_localization_system.name')

    class Meta:
        model = EEGElectrodePosition
        fields = ('eeg_electrode_localization_system', 'electrode_model',
                  'name', 'coordinate_x', 'coordinate_y', 'channel_index')


class EEGElectrodeNetSettingSerializer(serializers.ModelSerializer):
    eeg_setting = serializers.ReadOnlyField(source='eeg_setting.name')

    class Meta:
        model = EEGElectrodeNet
        fields = ('eeg_setting',
                  'manufacturer_name', 'equipment_type', 'identification', 'description', 'serial_number')


class EEGSettingSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = EEGSetting
        fields = ('id', 'experiment', 'name', 'description')


class EMGSettingSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = EMGSetting
        fields = ('id', 'experiment', 'name', 'description', 'acquisition_software_version')


class EMGDigitalFilterSettingSerializer(serializers.ModelSerializer):
    emg_setting = serializers.ReadOnlyField(source='emg_setting.name')

    class Meta:
        model = EMGDigitalFilterSetting
        fields = ('emg_setting', 'filter_type_name', 'filter_type_description', 'low_pass', 'high_pass',
                  'low_band_pass', 'high_band_pass', 'low_notch', 'high_notch', 'order')


class ADConverterSerializer(serializers.ModelSerializer):

    class Meta:
        model = ADConverter
        fields = (
            'id',
            'manufacturer_name',
            'equipment_type',
            'identification',
            'description',
            'serial_number',
            'signal_to_noise_rate',
            'sampling_rate',
            'resolution')


class EMGADConverterSettingSerializer(serializers.ModelSerializer):
    emg_setting = serializers.ReadOnlyField(source='emg_setting.name')

    class Meta:
        model = EMGADConverterSetting
        fields = ('emg_setting', 'ad_converter', 'sampling_rate')


class EMGElectrodeSettingSerializer(serializers.ModelSerializer):
    emg_setting = serializers.ReadOnlyField(source='emg_setting.name')

    class Meta:
        model = EMGElectrodeSetting
        fields = ('id', 'emg_setting', 'electrode_model')


class EMGPreamplifierSettingSerializer(serializers.ModelSerializer):
    emg_electrode_setting = serializers.ReadOnlyField(source='emg_electrode_setting.name')

    class Meta:
        model = EMGPreamplifierSetting
        fields = ('emg_electrode_setting', 'amplifier', 'gain')


class EMGAmplifierSettingSerializer(serializers.ModelSerializer):
    emg_electrode_setting = serializers.ReadOnlyField(source='emg_electrode_setting.name')

    class Meta:
        model = EMGAmplifierSetting
        fields = ('emg_electrode_setting', 'amplifier', 'gain')


class EMGPreamplifierFilterSettingSerializer(serializers.ModelSerializer):
    emg_electrode_setting = serializers.ReadOnlyField(source='emg_electrode_setting.name')

    class Meta:
        model = EMGPreamplifierFilterSetting
        fields = ('emg_electrode_setting',
                  'low_pass', 'high_pass',
                  'low_band_pass', 'low_notch',
                  'high_band_pass', 'high_notch', 'order')


class EMGAnalogFilterSettingSerializer(serializers.ModelSerializer):
    emg_electrode_setting = serializers.ReadOnlyField(source='emg_electrode_setting.name')

    class Meta:
        model = EMGAnalogFilterSetting
        fields = ('emg_electrode_setting',
                  'low_pass', 'high_pass',
                  'low_band_pass', 'low_notch',
                  'high_band_pass', 'high_notch', 'order')


class EMGElectrodePlacementSettingSerializer(serializers.ModelSerializer):
    emg_electrode_setting = serializers.ReadOnlyField(source='emg_electrode_setting.name')

    class Meta:
        model = EMGElectrodePlacementSetting
        fields = ('emg_electrode_setting', 'emg_electrode_placement', 'muscle_side', 'muscle_name', 'remarks')


class EMGSurfacePlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EMGSurfacePlacement
        fields = (
            'id',
            'standardization_system_name',
            'standardization_system_description',
            'muscle_anatomy_origin',
            'muscle_anatomy_insertion',
            'muscle_anatomy_function',
            'photo',
            'location',
            'placement_type',

            'start_posture',
            'orientation',
            'fixation_on_the_skin',
            'reference_electrode',
            'clinical_test')


class EMGIntramuscularPlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EMGIntramuscularPlacement
        fields = (
            'id',
            'standardization_system_name',
            'standardization_system_description',
            'muscle_anatomy_origin',
            'muscle_anatomy_insertion',
            'muscle_anatomy_function',
            'photo',
            'location',
            'placement_type',

            'method_of_insertion',
            'depth_of_insertion')


class EMGNeedlePlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EMGNeedlePlacement
        fields = (
            'id',
            'standardization_system_name',
            'standardization_system_description',
            'muscle_anatomy_origin',
            'muscle_anatomy_insertion',
            'muscle_anatomy_function',
            'photo',
            'location',
            'placement_type',

            'depth_of_insertion')


class TMSSettingSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = TMSSetting
        fields = ('id', 'experiment', 'name', 'description')


class TMSDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = TMSDevice
        fields = (
            'id',
            'manufacturer_name',
            'equipment_type',
            'identification',
            'description',
            'serial_number',
            'pulse_type'
        )


class CoilModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoilModel
        fields = (
            'id',

            'name',
            'description',
            'coil_shape_name',
            'material_name',
            'material_description',
            'coil_design'
        )


class TMSDeviceSettingSerializer(serializers.ModelSerializer):
    tms_setting = serializers.ReadOnlyField(source='tms_setting.name')

    class Meta:
        model = TMSDeviceSetting
        fields = ('tms_setting', 'tms_device', 'pulse_stimulus_type', 'coil_model')


class ContextTreeSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = ContextTree
        fields = ('id', 'experiment', 'name', 'description', 'setting_text', 'setting_file')


class ProtocolComponentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = ProtocolComponent
        fields = ('id', 'experiment_nes_id', 'identification', 'description',
                  'duration_value', 'component_type', 'experiment', 'owner')


class ClassificationOfDiseasesSerializer(serializers.Serializer):
    class Meta:
        model = ClassificationOfDiseases
        fields = ('code',)


class GroupSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')
    inclusion_criteria = ClassificationOfDiseasesSerializer(many=True, read_only=False)

    class Meta:
        model = Group
        fields = ('id', 'title', 'description', 'experiment', 'inclusion_criteria')

    def create(self, validated_data):
        group = Group.objects.create(experiment=validated_data['experiment'],
                                     title=validated_data['title'],
                                     description=validated_data['description'])
        if 'inclusion_criteria' in self.initial_data:
            inclusion_criteria = self.initial_data['inclusion_criteria']
            for criteria in inclusion_criteria:
                classification_of_diseases = ClassificationOfDiseases.objects.filter(code=criteria['code'])
                if classification_of_diseases:
                    group.inclusion_criteria.add(classification_of_diseases.first())
        return group


class ExperimentalProtocolSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = ExperimentalProtocol
        fields = ('id', 'image', 'textual_description', 'group', 'root_step')


class ParticipantSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Participant
        fields = ('id', 'group', 'code', 'gender', 'age')


class StepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Step
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position')


class EEGStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = EEG
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'eeg_setting')


class EMGStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = EMG
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'emg_setting')


class TMSStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = TMS
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'tms_setting')


class InstructionStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Instruction
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'text')


class PauseStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Pause
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position')


class TaskStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Task
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position')


class TaskForExperimenterStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = TaskForTheExperimenter
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position')


class GenericDataCollectionStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = GenericDataCollection
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'information_type_name', 'information_type_description')


class StimulusStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Stimulus
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'stimulus_type_name', 'media_file')


class GoalkeeperGameStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = GoalkeeperGame
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'software_name', 'software_description', 'software_version', 'context_tree')


class SetOfStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = SetOfStep
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'number_of_mandatory_steps', 'is_sequential')


class QuestionnaireStepSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = Questionnaire
        fields = ('id', 'group', 'identification', 'description',
                  'duration_value', 'duration_unit', 'numeration',
                  'type', 'parent', 'order',
                  'number_of_repetitions',
                  'interval_between_repetitions_value',
                  'interval_between_repetitions_unit',
                  'random_position',
                  'survey_name', 'survey_metadata')


class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = ('id', 'file',)


class EEGDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = EEGData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'description', 'file', 'file_format',
                  'eeg_setting', 'eeg_cap_size', 'eeg_setting_reason_for_change')


class EMGDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = EMGData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'description', 'file', 'file_format',
                  'emg_setting', 'emg_setting_reason_for_change')


class TMSDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = TMSData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'tms_setting', 'resting_motor_threshold', 'test_pulse_intensity_of_simulation',
                  'second_test_pulse_intensity', 'interval_between_pulses', 'interval_between_pulses_unit',
                  'time_between_mep_trials', 'time_between_mep_trials_unit', 'repetitive_pulse_frequency',
                  'coil_orientation', 'coil_orientation_angle', 'direction_of_induced_current', 'description',
                  'hotspot_name', 'coordinate_x', 'coordinate_y', 'hot_spot_map',
                  'localization_system_name', 'localization_system_description', 'localization_system_image',
                  'brain_area_name', 'brain_area_description',
                  'brain_area_system_name', 'brain_area_system_description')


class GoalkeeperGameDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalkeeperGameData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'description', 'file', 'file_format',
                  'sequence_used_in_context_tree')


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionnaireResponse
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'limesurvey_response')


class AdditionalDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'description', 'file', 'file_format')


class GenericDataCollectionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericDataCollectionData
        fields = ('id',
                  'step', 'participant', 'date', 'time',
                  'description', 'file', 'file_format')

#############
# API Views #
#############


class ExperimentViewSet(viewsets.ModelViewSet):
    lookup_url_kwarg = 'experiment_nes_id'
    lookup_field = 'nes_id'
    serializer_class = ExperimentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError
        # exception when trying to get an individual experiment)
        if 'experiment_nes_id' in self.kwargs:
            owner = self.request.user
            nes_id = self.kwargs['experiment_nes_id']
            exp_version = appclasses.ExperimentVersion(nes_id, owner)
            return Experiment.objects.filter(
                owner=owner,
                nes_id=nes_id,
                version=exp_version.get_last_version()
            )
        else:
            return Experiment.objects.all()

    def perform_create(self, serializer):
        nes_id = self.request.data['nes_id']
        owner = self.request.user
        exp_version = appclasses.ExperimentVersion(nes_id, owner)
        serializer.save(
            owner=owner, version=exp_version.get_last_version() + 1
        )

        # Send email to trustees telling them that new experiment has arrived
        # TODO: Specify if that is a new experiment, or a new version
        trustees = User.objects.filter(groups__name='trustees')
        emails = []
        for trustee in trustees:
            if trustee.email:
                emails.append(trustee.email)

        from_email = 'noreplay@nep.prp.usp.br'
        subject = 'New experiment "' + self.request.data['title'] + \
                  '" has arrived in NEDP portal.'
        message = 'New experiment arrived in NEDP portal:\n' + \
                  'Title:\n' + self.request.data['title'] + '\n' + \
                  'Description:\n' + self.request.data['description'] + '\n' + \
                  'Owner: ' + str(self.request.user) + '\n'

        send_mail(subject, message, from_email, emails)

    def perform_update(self, serializer):
        nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        exp_version = appclasses.ExperimentVersion(nes_id, owner)
        serializer.save(
            owner=owner, version=exp_version.get_last_version(), nes_id=nes_id
        )


class StudyViewSet(viewsets.ModelViewSet):
    serializer_class = StudySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in self.kwargs and \
                (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return Study.objects.filter(experiment=experiment)
        else:
            return Study.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        # TODO: if last_version == 0 generates exception: "no experiment was
        # created yet"
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        # TODO: breaks when posting from the api template.
        # Doesn't have researcher field to enter a valid researcher.
        serializer.save(experiment=experiment)


class ResearcherViewSet(viewsets.ModelViewSet):
    serializer_class = ResearcherSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError
        # exception when trying to get an individual researcher)
        if 'pk' in self.kwargs:
            return Researcher.objects.filter(study_id=self.kwargs['pk'])
        else:
            return Researcher.objects.all()

    def perform_create(self, serializer):
        study = Study.objects.get(pk=self.kwargs['pk'])
        serializer.save(study=study)


class CollaboratorViewSet(viewsets.ModelViewSet):
    serializer_class = CollaboratorSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'pk' in self.kwargs:
            return Collaborator.objects.filter(study_id=self.kwargs['pk'])
        else:
            return Collaborator.objects.all()

    def perform_create(self, serializer):
        study = Study.objects.get(pk=self.kwargs['pk'])
        serializer.save(study=study)


class GroupViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in \
                self.kwargs and \
                (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return Group.objects.filter(experiment=experiment)
        else:
            return Group.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        # TODO: if last_version == 0 generates exception: "no experiment was
        # created yet"
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        serializer.save(experiment=experiment)


class ExperimentalProtocolViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentalProtocolSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return ExperimentalProtocol.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class ParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipantSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Participant.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class EEGSettingViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'
    serializer_class = EEGSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in self.kwargs and (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return EEGSetting.objects.filter(experiment=experiment)
        else:
            return EEGSetting.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        serializer.save(experiment=experiment)


class AmplifierViewSet(viewsets.ModelViewSet):
    serializer_class = AmplifierSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Amplifier.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class EEGAmplifierSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EEGAmplifierSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGAmplifierSetting.objects.filter(eeg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_setting = EEGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(eeg_setting=eeg_setting)


class EEGSolutionSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EEGSolutionSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGSolution.objects.filter(eeg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_setting = EEGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(eeg_setting=eeg_setting)


class EEGFilterSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EEGFilterSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGFilterSetting.objects.filter(eeg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_setting = EEGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(eeg_setting=eeg_setting)


class EEGElectrodeNetSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EEGElectrodeNetSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGElectrodeNet.objects.filter(eeg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_setting = EEGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(eeg_setting=eeg_setting)


class SurfaceElectrodeViewSet(viewsets.ModelViewSet):
    serializer_class = SurfaceElectrodeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return SurfaceElectrode.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class NeedleElectrodeViewSet(viewsets.ModelViewSet):
    serializer_class = NeedleElectrodeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return NeedleElectrode.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class IntramuscularElectrodeViewSet(viewsets.ModelViewSet):
    serializer_class = IntramuscularElectrodeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return IntramuscularElectrode.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class EEGElectrodeLocalizationSystemViewSet(viewsets.ModelViewSet):
    serializer_class = EEGElectrodeLocalizationSystemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGElectrodeLocalizationSystem.objects.filter(eeg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_setting = EEGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(eeg_setting=eeg_setting)


class EEGElectrodePositionViewSet(viewsets.ModelViewSet):
    serializer_class = EEGElectrodePositionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGElectrodePosition.objects.filter(eeg_electrode_localization_system_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        eeg_electrode_localization_system = EEGElectrodeLocalizationSystem(pk=self.kwargs['pk'])
        serializer.save(eeg_electrode_localization_system=eeg_electrode_localization_system)


class EMGSettingViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'
    serializer_class = EMGSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in self.kwargs and (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return EMGSetting.objects.filter(experiment=experiment)
        else:
            return EMGSetting.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        serializer.save(experiment=experiment)


class EMGDigitalFilterSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGDigitalFilterSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGDigitalFilterSetting.objects.filter(emg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_setting = EMGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_setting=emg_setting)


class ADConverterViewSet(viewsets.ModelViewSet):
    serializer_class = ADConverterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return ADConverter.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class EMGADConverterSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGADConverterSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGADConverterSetting.objects.filter(emg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_setting = EMGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_setting=emg_setting)


class EMGElectrodeSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGElectrodeSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGElectrodeSetting.objects.filter(emg_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_setting = EMGSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_setting=emg_setting)


class EMGPreamplifierSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGPreamplifierSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGPreamplifierSetting.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_electrode_setting = EMGElectrodeSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_electrode_setting=emg_electrode_setting)


class EMGAmplifierSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGAmplifierSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGAmplifierSetting.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_electrode_setting = EMGElectrodeSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_electrode_setting=emg_electrode_setting)


class EMGPreamplifierFilterSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGPreamplifierFilterSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGPreamplifierFilterSetting.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_preamplifier_setting = EMGPreamplifierSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_preamplifier_setting=emg_preamplifier_setting)


class EMGAnalogFilterSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGAnalogFilterSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGAnalogFilterSetting.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_amplifier_setting = EMGAmplifierSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_amplifier_setting=emg_amplifier_setting)


class EMGElectrodePlacementSettingViewSet(viewsets.ModelViewSet):
    serializer_class = EMGElectrodePlacementSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGElectrodePlacementSetting.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        emg_electrode_setting = EMGElectrodeSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(emg_electrode_setting=emg_electrode_setting)


class EMGSurfacePlacementViewSet(viewsets.ModelViewSet):
    serializer_class = EMGSurfacePlacementSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGSurfacePlacement.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class EMGIntramuscularPlacementViewSet(viewsets.ModelViewSet):
    serializer_class = EMGIntramuscularPlacementSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGIntramuscularPlacement.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class EMGNeedlePlacementViewSet(viewsets.ModelViewSet):
    serializer_class = EMGNeedlePlacementSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGNeedlePlacement.objects.filter(id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class TMSSettingViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'
    serializer_class = TMSSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in self.kwargs and (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return TMSSetting.objects.filter(experiment=experiment)
        else:
            return TMSSetting.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        serializer.save(experiment=experiment)


class TMSDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = TMSDeviceSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return TMSDevice.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class CoilModelViewSet(viewsets.ModelViewSet):
    serializer_class = CoilModelSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return CoilModel.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class TMSDeviceSettingViewSet(viewsets.ModelViewSet):
    serializer_class = TMSDeviceSettingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return TMSDeviceSetting.objects.filter(tms_setting_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        tms_setting = TMSSetting.objects.get(pk=self.kwargs['pk'])
        serializer.save(tms_setting=tms_setting)


class ContextTreeViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'
    serializer_class = ContextTreeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in self.kwargs and (self.request.user != AnonymousUser()):
            experiment = Experiment.objects.filter(
                nes_id=self.kwargs['experiment_nes_id'],
                owner=self.request.user
            )
            return ContextTree.objects.filter(experiment=experiment)
        else:
            return ContextTree.objects.all()

    def perform_create(self, serializer):
        exp_nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        last_version = appclasses.ExperimentVersion(
            exp_nes_id, owner
        ).get_last_version()
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        serializer.save(experiment=experiment)


class StepViewSet(viewsets.ModelViewSet):
    serializer_class = StepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Step.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class EEGStepViewSet(viewsets.ModelViewSet):
    serializer_class = EEGStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEG.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class EMGStepViewSet(viewsets.ModelViewSet):
    serializer_class = EMGStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMG.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class TMSStepViewSet(viewsets.ModelViewSet):
    serializer_class = TMSStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return TMS.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class InstructionStepViewSet(viewsets.ModelViewSet):
    serializer_class = InstructionStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Instruction.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class PauseStepViewSet(viewsets.ModelViewSet):
    serializer_class = PauseStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Pause.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class TaskStepViewSet(viewsets.ModelViewSet):
    serializer_class = TaskStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Task.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class TaskForExperimenterStepViewSet(viewsets.ModelViewSet):
    serializer_class = TaskForExperimenterStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return TaskForTheExperimenter.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class GenericDataCollectionStepViewSet(viewsets.ModelViewSet):
    serializer_class = GenericDataCollectionStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return GenericDataCollection.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class StimulusStepViewSet(viewsets.ModelViewSet):
    serializer_class = StimulusStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Stimulus.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class GoalkeeperGameStepViewSet(viewsets.ModelViewSet):
    serializer_class = GoalkeeperGameStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return GoalkeeperGame.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class SetOfStepViewSet(viewsets.ModelViewSet):
    serializer_class = SetOfStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return SetOfStep.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class QuestionnaireStepViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireStepSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Questionnaire.objects.filter(group_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['pk'])
        serializer.save(group=group)


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return File.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class EEGDataViewSet(viewsets.ModelViewSet):
    serializer_class = EEGDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EEGData.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class EMGDataViewSet(viewsets.ModelViewSet):
    serializer_class = EMGDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return EMGData.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class TMSDataViewSet(viewsets.ModelViewSet):
    serializer_class = TMSDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return TMSData.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class GoalkeeperGameDataViewSet(viewsets.ModelViewSet):
    serializer_class = GoalkeeperGameDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return GoalkeeperGameData.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class QuestionnaireResponseViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireResponseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return QuestionnaireResponse.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class AdditionalDataViewSet(viewsets.ModelViewSet):
    serializer_class = AdditionalDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return AdditionalData.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class GenericDataCollectionDataViewSet(viewsets.ModelViewSet):
    serializer_class = GenericDataCollectionDataSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return GenericDataCollectionData.objects.all()

    def perform_create(self, serializer):
        serializer.save()
