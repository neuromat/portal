import shlex

from django.db.models import Max
from haystack.utils import Highlighter

from experiments import models


class ExperimentVersion:

    def __init__(self, nes_id, owner):
        self.nes_id = nes_id
        self.owner = owner

    def get_last_version(self):
        last_exp_version = models.Experiment.objects.filter(
            nes_id=self.nes_id, owner=self.owner
        ).aggregate(Max('version'))
        if not last_exp_version['version__max']:
            return 0
        else:
            return last_exp_version['version__max']


class NepHighlighter(Highlighter):

    def __init__(self, query, **kwargs):
        """
        Defines a query word as a simple word or a string inside quotes.
        Default split in Highlighter doesn't do that.
        :param query: from Highlighter
        :param kwargs: from Highligther
        """
        super(NepHighlighter, self).__init__(query, **kwargs)
        self.query_words = set([word.lower() for word in shlex.split(query)
                                if not word.startswith('-')])
