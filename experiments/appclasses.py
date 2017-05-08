from experiments import models


class ExperimentVersion:

    def __init__(self, experiment):
        self.exp = experiment

    def get_last_version(self):
        last_version = models.ExperimentVersion.objects.filter(
                    experiment=self.exp).last()
        if not last_version:
            return 0
        else:
            return last_version + 1

    def create_version(self):
        last_version = self.get_last_version()
        return models.ExperimentVersion.objects.create(
            version=last_version+1, experiment=self.exp
        )
