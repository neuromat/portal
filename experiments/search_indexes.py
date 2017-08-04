from haystack import indexes

from experiments.models import Experiment, Study, Group, ExperimentalProtocol


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
    keywords = indexes.CharField(model_attr='keywords__name')
    researcher = indexes.CharField(model_attr='researcher__id')
    collaborators = indexes.CharField(model_attr='collaborators__name')

    def get_model(self):
        return Study

    def get_queryset(self):
        return self.get_model().objects.all()


class GroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    experiment = indexes.CharField(model_attr='experiment__id')
    inclusion_criteria = indexes.CharField(model_attr='inclusion_criteria__id')

    def get_model(self):
        return Group

    def get_queryset(self):
        return self.get_model().objects.all()


class ExperimentalProtocolIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    group = indexes.CharField(model_attr='group__id')

    def get_model(self):
        return ExperimentalProtocol

    def get_queryset(self):
        return self.get_model().objects.all()
