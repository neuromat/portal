from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError

from experiments.models import Experiment


class Command(BaseCommand):
    help = 'Remove all experiments based on API client external code or ' \
           'just the last version'

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
            experiment.delete()
            self.stdout.write(self.style.SUCCESS(
                'Last version of experiment "%s" successfully removed' %
                experiment.title
            ))
        else:
            for experiment in Experiment.objects.filter(
                    nes_id=options['nes_id'], owner=owner
            ):
                experiment.delete()
                self.stdout.write(self.style.SUCCESS(
                    'All version of experiment "%s" successfully removed' %
                    experiment.title
                ))
