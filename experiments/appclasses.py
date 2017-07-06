from django.db.models import Max, Q

from experiments import models
from experiments.models import Experiment


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


class CurrentExperiments:

    def get_current_experiments(self):
        experiment_max_version_set = \
            Experiment.objects.values('owner', 'nes_id').annotate(
                max_version=Max('version'))
        q_statement = Q()
        for experiment in experiment_max_version_set:
            q_statement |= (Q(owner=experiment['owner']) &
                            Q(nes_id=experiment['nes_id']) &
                            Q(version=experiment['max_version']) &
                            Q(status=Experiment.APPROVED))

        return Experiment.objects.filter(q_statement)

    def get_current_experiments_trustees(self):
        experiment_max_version_set = \
            Experiment.objects.values('owner', 'nes_id').annotate(
                max_version=Max('version'))
        q_statement = Q()
        for experiment in experiment_max_version_set:
            q_statement |= (Q(owner=experiment['owner']) &
                            Q(nes_id=experiment['nes_id']) &
                            Q(version=experiment['max_version']))

        return Experiment.objects.filter(q_statement)
