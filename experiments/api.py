from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers, permissions, viewsets

from experiments import appclasses
from experiments.models import Experiment, Study, User, ProtocolComponent, \
    Group, ExperimentalProtocol, Researcher, Participant, Collaborator, Keyword, ClassificationOfDiseases, \
    EEGSetting, EMGSetting, TMSSetting, ContextTree, Step, File, EEGData, GoalkeeperGameData, QuestionnaireResponse


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
                  'nes_id', 'ethics_committee_file', 'owner',
                  'status', 'protocol_components', 'sent_date')


class UserSerializer(serializers.ModelSerializer):
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Experiment.objects.all()
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'experiments')


class KeywordSerializer(serializers.Serializer):
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
                keyword, created = Keyword.objects.get_or_create(name=keyword_data['name'])
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


class TMSSettingSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = TMSSetting
        fields = ('id', 'experiment', 'name', 'description')


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
                  'eeg_setting', 'eeg_cap_size')


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

    def perform_update(self, serializer):
        nes_id = self.kwargs['experiment_nes_id']
        owner = self.request.user
        exp_version = appclasses.ExperimentVersion(nes_id, owner)
        serializer.save(
            owner=owner, version=exp_version.get_last_version(), nes_id=nes_id
        )


class StudyViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'  # TODO: see if not more used
    serializer_class = StudySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if 'experiment_nes_id' in \
                self.kwargs and \
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
        # TODO: created yet"
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        # TODO: breaks when posting from the api template.
        # Doesn't have researcher field to enter a valid r.
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

# class ProtocolComponentViewSet(viewsets.ModelViewSet):
#     lookup_field = 'nes_id'
#     serializer_class = ProtocolComponentSerializer
#     permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
#
#     def get_queryset(self):
#         # TODO: don't filter by owner if not logged (gets TypeError)
#         # exception when trying to get an individual experiment
#         if 'nes_id' in self.kwargs:
#             return ProtocolComponent.objects.filter(owner=self.request.user)
#         else:
#             return ProtocolComponent.objects.all()
#
#     def perform_create(self, serializer):
#         # TODO: we must create protocol_component for the last experiment
#         # version
#         experiment_nes_id = self.request.data['experiment']
#         experiment = Experiment.objects.filter(
#             experiment_nes_id=experiment_nes_id, owner=self.request.user).get()
#         serializer.save(experiment=experiment, owner=self.request.user)
#
#     def perform_update(self, serializer):
#         # TODO: save in with last experiment version
#         experiment_nes_id = self.request.data['experiment']
#         experiment = Experiment.objects.filter(
#             experiment_nes_id=experiment_nes_id, owner=self.request.user
#         ).get()
#         serializer.save()
