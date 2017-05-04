from rest_framework import serializers, generics, permissions, viewsets

from experiments.models import Experiment, Study, User, Researcher, \
    ProtocolComponent


###################
# API Serializers #
###################
class ExperimentSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')
    owner = serializers.ReadOnlyField(source='owner.username')
    protocol_components = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    class Meta:
        model = Experiment
        fields = ('id', 'title', 'description', 'data_acquisition_done',
                  'nes_id', 'study', 'owner', 'protocol_components')


class UserSerializer(serializers.ModelSerializer):
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Experiment.objects.all()
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'experiments')


class StudySerializer(serializers.ModelSerializer):
    researcher = serializers.ReadOnlyField(source='researcher.first_name')
    owner = serializers.ReadOnlyField(source='owner.username')
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    class Meta:
        model = Study
        fields = ('id', 'title', 'description', 'start_date', 'end_date',
                  'nes_id', 'researcher', 'owner', 'experiments')


class ResearcherSerializer(serializers.ModelSerializer):
    studies = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Researcher
        fields = ('id', 'first_name', 'surname', 'email', 'studies',
                  'nes_id', 'owner')


class ProtocolComponentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = ProtocolComponent
        fields = ('id', 'identification', 'description', 'duration_value',
                  'component_type', 'nes_id', 'experiment', 'owner')


#############
# API Views #
#############
class ResearcherViewSet(viewsets.ModelViewSet):
    lookup_field = 'nes_id'
    serializer_class = ResearcherSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError
        # exception when trying to get an individual researcher
        if 'nes_id' in self.kwargs:
            return Researcher.objects.filter(owner=self.request.user)
        else:
            return Researcher.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StudyViewSet(viewsets.ModelViewSet):
    lookup_field = 'nes_id'
    serializer_class = StudySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError
        # exception when trying to get an individual researcher
        if 'nes_id' in self.kwargs:
            return Study.objects.filter(owner=self.request.user)
        else:
            return Study.objects.all()

    def perform_create(self, serializer):
        researcher_id = self.request.data['researcher']
        researcher = Researcher.objects.get(id=researcher_id)
        serializer.save(researcher=researcher, owner=self.request.user)


class ExperimentList(generics.ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        study_id = self.kwargs.get('pk')
        study = Study.objects.filter(id=study_id).get()
        serializer.save(study=study, owner=self.request.user)


class ProtocolComponentList(generics.ListCreateAPIView):
    queryset = ProtocolComponent.objects.all()
    serializer_class = ProtocolComponentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        experiment_id = self.kwargs.get('pk')
        experiment = Experiment.objects.filter(id=experiment_id).get()
        serializer.save(experiment=experiment, owner=self.request.user)
