from django.http import HttpResponse
from rest_framework import status, serializers, generics, permissions
import json

from experiments.models import Experiment, Study, User, Researcher


# API Serializers
class ExperimentSerializer(serializers.ModelSerializer):
    study = serializers.ReadOnlyField(source='study.title')
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Experiment
        fields = ('id', 'title', 'description', 'data_acquisition_done',
                  'study', 'user')


class UserSerializer(serializers.ModelSerializer):
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Experiment.objects.all()
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'experiments')


class StudySerializer(serializers.ModelSerializer):
    researcher = serializers.ReadOnlyField(source='researcher.first_name')
    experiments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Experiment.objects.all()
    )

    class Meta:
        model = Study
        fields = ('id', 'title', 'description', 'start_date', 'end_date',
                  'researcher', 'experiments')


class ResearcherSerializer(serializers.ModelSerializer):
    studies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Study.objects.all()
    )

    class Meta:
        model = Researcher
        fields = ('id', 'first_name', 'surname', 'email', 'studies')


# API Views
def experiment(request):
    if request.method == 'POST':
        study = Study.objects.get(id=request.POST['study'])
        user = User.objects.get(id=request.POST['user'])
        Experiment.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            study=study,
            user=user
        )
        return HttpResponse(status=status.HTTP_201_CREATED)
    experiment_dicts = [
        {'id': experiment.id, 'title': experiment.title, 'description':
            experiment.description, 'data_acquisition_done':
            experiment.data_acquisition_done, 'study': experiment.study.id,
         'user': experiment.user.id}
        for experiment in Experiment.objects.all()
        ]
    return HttpResponse(
        json.dumps(experiment_dicts),
        content_type='application/json'
    )


class ResearcherList(generics.ListCreateAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

