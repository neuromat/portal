import reversion
from rest_framework import serializers, generics, permissions, viewsets

from experiments import appclasses
from experiments.models import Experiment, Study, User, Researcher, \
    ProtocolComponent, ExperimentVersion, ExperimentVersionMeta


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
    queryset = Researcher.objects.all()
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
        # TODO: don't filter by owner if not logged (gets TypeError)
        # exception when trying to get an individual study
        if 'nes_id' in self.kwargs:
            return Study.objects.filter(owner=self.request.user)
        else:
            return Study.objects.all()

    def perform_create(self, serializer):
        # TODO: breaks when posting from the api template.
        # Doesn't have researcher field to enter a valid reseacher.
        researcher_id = self.request.data['researcher']
        researcher = Researcher.objects.get(id=researcher_id)
        serializer.save(researcher=researcher, owner=self.request.user)


class ExperimentViewSet(viewsets.ModelViewSet):
    lookup_field = 'nes_id'
    serializer_class = ExperimentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError)
        # exception when trying to get an individual experiment
        if 'nes_id' in self.kwargs:
            return Experiment.objects.filter(owner=self.request.user)
        else:
            return Experiment.objects.all()

    def perform_create(self, serializer):
        study_id = self.request.data['study']
        study = Study.objects.get(id=study_id)
        with reversion.create_revision():
            exp_serializer = serializer.save(study=study,
                                             owner=self.request.user)
            experiment = Experiment.objects.get(id=exp_serializer.id)
            reversion.set_user(self.request.user)
            exp_version = appclasses.ExperimentVersion(
                experiment
            ).create_version()
            reversion.add_meta(ExperimentVersionMeta,
                               experiment_version=exp_version)

    def perform_update(self, serializer):
        with reversion.create_revision():
            exp_serializer = serializer.save()
            experiment = Experiment.objects.get(id=exp_serializer.id)
            reversion.set_user(self.request.user)
            exp_version = appclasses.ExperimentVersion(
                experiment).create_version()
            reversion.add_meta(ExperimentVersionMeta,
                               experiment_version=exp_version)


class ProtocolComponentViewSet(viewsets.ModelViewSet):
    lookup_field = 'nes_id'
    serializer_class = ProtocolComponentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # TODO: don't filter by owner if not logged (gets TypeError)
        # exception when trying to get an individual experiment
        if 'nes_id' in self.kwargs:
            return ProtocolComponent.objects.filter(owner=self.request.user)
        else:
            return ProtocolComponent.objects.all()

    def perform_create(self, serializer):
        experiment_id = self.request.data['experiment']
        experiment = Experiment.objects.filter(
            nes_id=experiment_id, owner=self.request.user).get()
        serializer.save(experiment=experiment, owner=self.request.user)
