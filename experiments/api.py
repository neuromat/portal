from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers, permissions, viewsets

from experiments import appclasses
from experiments.models import Experiment, Study, User, ProtocolComponent, \
    Group, ExperimentalProtocol, Researcher


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


class StudySerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = Study
        fields = ('id', 'title', 'description', 'start_date',
                  'end_date', 'experiment')


class ResearcherSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')

    class Meta:
        model = Researcher
        fields = ('id', 'name', 'email', 'study')


# class ProtocolComponentSerializer(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source='owner.username')
#     experiment = serializers.ReadOnlyField(source='experiment.title')
#
#     class Meta:
#         model = ProtocolComponent
#         fields = ('id', 'experiment_nes_id', 'identification', 'description',
#                   'duration_value', 'component_type', 'experiment', 'owner')


class GroupSerializer(serializers.ModelSerializer):
    experiment = serializers.ReadOnlyField(source='experiment.title')

    class Meta:
        model = Group
        fields = ('id', 'title', 'description', 'experiment')


class ExperimentalProtocolSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.title')

    class Meta:
        model = ExperimentalProtocol
        fields = ('id', 'image', 'textual_description', 'group')


#############
# API Views #
#############
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
        # created yet"
        experiment = Experiment.objects.get(
            nes_id=exp_nes_id, owner=owner, version=last_version
        )
        # TODO: breaks when posting from the api template.
        # Doesn't have researcher field to enter a valid reseacher.
        serializer.save(experiment=experiment)


class GroupViewSet(viewsets.ModelViewSet):
    lookup_field = 'experiment_nes_id'  # TODO: see if not more used
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
