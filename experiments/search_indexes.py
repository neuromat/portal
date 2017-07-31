from haystack import indexes

from experiments.models import Experiment, Study


class ExperimentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    owner = indexes.CharField(model_attr='owner')

    def get_model(self):
        return Experiment

    def get_queryset(self):
        return self.get_model().objects.all()


class StudyIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')

    def get_model(self):
        return Study

    def get_queryset(self):
        return self.get_model().objects.all()
