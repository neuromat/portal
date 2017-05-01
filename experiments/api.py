from django.http import HttpResponse
from rest_framework import status, serializers, generics, permissions
import json

from experiments.models import Experiment, Study, User, Researcher


# API Serializers
class ExperimentSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Experiment
        fields = ('id', 'title', 'description', 'data_acquisition_done',
                  'study', 'owner')


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
                  'researcher', 'owner', 'experiments')


class ResearcherSerializer(serializers.ModelSerializer):
    studies = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Researcher
        fields = ('id', 'first_name', 'surname', 'email', 'studies',
                  'nes_id', 'owner')


# API Views
class ExperimentList(generics.ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        study_id = self.kwargs.get('pk')
        study = Study.objects.filter(id=study_id).get()
        serializer.save(study=study, owner=self.request.user)


class StudyList(generics.ListCreateAPIView):
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        researcher_id = self.kwargs.get('pk')
        researcher = Researcher.objects.filter(id=researcher_id).get()
        serializer.save(researcher=researcher, owner=self.request.user)


class ResearcherList(generics.ListCreateAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
