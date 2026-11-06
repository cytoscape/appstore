from django.core.management.base import BaseCommand, CommandError

from apps.models import App, Platform


class Command(BaseCommand):
    help = """
    Says which platform an app was on before other platforms were added to it, so that platform
    keeps the app's content and each other platform gets empty content of its own (#155).

    Accepting a new platform does this by itself. This is for apps that gained a platform
    without that, e.g. on a server that ran an earlier build of #155. It shows what it would
    change, and changes it only with --apply. A platform that already has content of its own
    is left as is.
    """

    def add_arguments(self, parser):
        parser.add_argument('app', help="the app's name, as in its page's URL")
        parser.add_argument('platform', choices=Platform.values,
                            help='the platform the app was on before the others were added')
        parser.add_argument('--apply', action='store_true', help='make the changes (without it, only show them)')

    def handle(self, *args, **options):
        try:
            app = App.objects.get(name=options['app'])
        except App.DoesNotExist:
            raise CommandError('No app named "%s"' % options['app'])
        try:
            changes = app.separate_platform_content(options['platform'], apply=options['apply'])
        except ValueError as e:
            raise CommandError(str(e))

        if not changes:
            self.stdout.write('%s: nothing to change' % app.name)
            return
        prefix = '' if options['apply'] else '(not applied) '
        for change in changes:
            self.stdout.write('%s: %s%s' % (app.name, '' if change.startswith('left as is') else prefix, change))
        if not options['apply']:
            self.stdout.write('Nothing changed; run again with --apply to make these changes.')
