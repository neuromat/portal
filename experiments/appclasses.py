from django.db.models import Max

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


