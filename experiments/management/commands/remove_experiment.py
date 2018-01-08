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
        if options['last']:
            try:
                user = User.objects.get(username=options['owner'])
                experiment = Experiment.lastversion_objects.get(
                    nes_id=options['nes_id'], owner=user
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

            experiment.delete()
            self.stdout.write(self.style.SUCCESS(
                'Last version of experiment "%s" successfully removed' %
                experiment.title
            ))
        else:
            # TODO: remove all experiments
            pass
