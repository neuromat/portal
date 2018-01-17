import os

import shutil
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError

from experiments.models import Experiment
from nep import settings


def get_input(text):
    return input(text)


class Command(BaseCommand):
    help = 'Remove all experiments based on API client external code or ' \
           'just the last version'

    def clear_media_download_subdirs(self):
        for root, dirs, files in os.walk(os.path.join(
                settings.MEDIA_ROOT, 'download')
        ):
            if not dirs:  # it's in a path tree leaf (e.g. '2018/01/15')
                if not files:
                    os.rmdir(root)

    def clear_media_uploads_subdirs(self):
        uploads_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
        for root, dirs, files in os.walk(uploads_path):
            if not dirs and not files:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'uploads'))

    def remove_experiment_and_media_subdirs(self, experiment):
        experiment_id = experiment.id
        experiment.delete()
        self.clear_media_uploads_subdirs()
        experiment_media_download_path = os.path.join(
            settings.MEDIA_ROOT, 'download', str(experiment_id)
        )
        if os.path.exists(experiment_media_download_path):
            shutil.rmtree(experiment_media_download_path)
        # if is the only experiment that has download subdir remove it
        self.clear_media_download_subdirs()

    def add_arguments(self, parser):
        parser.add_argument('nes_id', type=int)
        parser.add_argument('owner', type=str)

        # remove only last version if has this option
        parser.add_argument(
            '--last', action='store_true', dest='last', default=False,
            help='Remove only last version'
        )

    def handle(self, *args, **options):
        try:
            owner = User.objects.get(username=options['owner'])
            experiment = Experiment.lastversion_objects.get(
                nes_id=options['nes_id'], owner=owner
            )
        except User.DoesNotExist:
            raise CommandError(
                'Owner "%s" does not exist' % options['owner']
            )
        except Experiment.DoesNotExist:
            raise CommandError(
                'Experiment with nes_id "%d" and owner "%s" does not exist'
                % (options['nes_id'], options['owner'])
            )

        if options['last']:
            answer = get_input(self.style.WARNING(
                'Last version of experiment "%s" will be destroyed and '
                'cannot be recovered. Are you sure? (Yes/n) ' %
                experiment.title
            ))
            if answer == 'Yes':
                self.stdout.write(
                    'Removing last version of experiment "%s" data and '
                    'files...'
                    % experiment.title
                )
                self.remove_experiment_and_media_subdirs(experiment)
                self.stdout.write(self.style.SUCCESS(
                    'Last version of experiment "%s" successfully removed' %
                    experiment.title
                ))
            else:
                self.stdout.write('Aborted')
        else:
            answer = get_input(self.style.WARNING(
                'All versions of experiment "%s" will be destroyed and '
                'cannot be recovered. Are you sure? (Yes/n) ' %
                experiment.title
            ))
            if answer == 'Yes':
                self.stdout.write(
                    'Removing all versions of experiment "%s" data and '
                    'files... '
                    % experiment.title
                )
                for experiment in Experiment.objects.filter(
                        nes_id=options['nes_id'], owner=owner
                ):
                    self.remove_experiment_and_media_subdirs(experiment)
                self.stdout.write(self.style.SUCCESS(
                    'All versions of experiment "%s" successfully removed' %
                    experiment.title
                ))
            else:
                self.stdout.write('Aborted')
