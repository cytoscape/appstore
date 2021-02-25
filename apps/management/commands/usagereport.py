
import sys
import re
from datetime import date, datetime, timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.models import App
from apps.models import Release
from download.models import ReleaseDownloadsByDate
from apps.models import OrderedAuthor
from apps.models import Author


class Command(BaseCommand):
    """
    Command
    """
    help = """
    Generates a report that provides usage
    statistics for a given range of time. If no arguments 
    are passed, the previous 30 days are examined not 
    including today.
    """

    def get_count_of_apps_updated_since(self, start_date, end_date):
        """
        Count of apps where latest_release_date is
        >= start_date and < end_date

        :param start_date: starting date in YYYY-MM-DD format
        :type start_date: str
        :param end_date: end date in YYYY-MM-DD format
        :type end_date: str
        :return: Number of apps found in date range
        :rtype: int
        """
        return App.objects.filter(latest_release_date__gte=start_date,
                                  latest_release_date__lt=end_date).count()

    def get_downloads_for_apps(self, start_date, end_date):
        """
        Gets all the ReleaseDownloadsByDate objects with a NULL release
        found from start_date up to, but not including end_date.
        NOTE: There is NO check as to whether the App is active or not

        :param start_date:
        :param end_date:
        :return: sum of the count value from all ReleaseDownloadsByDate that
                 passed date range filter
        :rtype: int
        """
        total = 0
        for rdd in ReleaseDownloadsByDate.objects.filter(when__gte=start_date,
                                                         when__lt=end_date,
                                                         release=None):
            total += rdd.count
        return total

    def get_count_of_active_apps(self):
        """
        Number of active apps as denoted by active field in apps_app table

        :return:
        :rtype: int
        """
        return App.objects.filter(active=1).count()

    def get_number_of_users(self):
        """
        Count of number of users on system
        :return:
        """
        return User.objects.filter(is_active=1).count()

    def get_number_of_users_added(self, start_date=None, end_date=None):
        """

        :param start_date:
        :param end_date:
        :return:
        """
        return User.objects.filter(is_active=1,
                                   date_joined__gte=start_date,
                                   date_joined__lt=end_date).count()

    def get_count_of_authors_with_active_apps(self):
        """
        Gets all OrderedAuthor objects found keeping only ones
        associated with an active App. The author name and institution
        are lowercased and then concatenated with spaces and added
        to a set to attempt to get a unique list of authors.

        :return: unique count of authors who are listed as an
                 author on one or more active apps
        :rtype: int
        """
        author_set = set()
        for o_author in OrderedAuthor.objects.all():
            try:
                App.objects.get(id=o_author.app.id, active=1)
            except Exception as e:
                # basically if the app is not active an
                # exception is thrown so we just skip
                # this OrderedAuthor entry
                continue
            author = Author.objects.get(id=o_author.author_id)

            a_name = self.get_author_as_str(author)

            if a_name not in author_set:
                author_set.add(a_name)

        return len(author_set)

    def get_author_as_str(self, author):
        """
        Concatenates author name if there with author institution
        This combined string is then lower cased and any
        white space characters are removed

        :param author: Author to extract name and institution from
        :type author: :py:class:`apps.models.Author`
        :return:
        :rtype: str
        """
        combined_a = ''
        if author.name is not None:
            combined_a += author.name
        if author.institution is not None:
            combined_a += author.institution
        return re.sub('\\s+', '', combined_a).lower()

    def get_count_of_apps_with_releases(self, start_date, end_date):
        """
        Gets count of apps with released where
        created is >= start_date and < end_date

        NOTE: Method does NOT check if App is active or not

        :param start_date: Start date in format of YYYY-MM-DD
        :type start_date: str
        :param end_date: End date in format of YYYY-MM-DD
        :type end_date: str
        :return: Number of apps with one or more releases during time frame
        :rtype: int
        """
        app_set = set()
        for rel in Release.objects.filter(created__gte=start_date,
                                          created__lt=end_date):
            try:
                cur_app = App.objects.get(id=rel.app.id)
            except Exception as e:
                continue
            app_set.add(cur_app.name)
        return len(app_set)

    def get_new_apps(self, start_date=None, end_date=None):
        """
        Gets count of new apps by looking at created timestamp on
        releases. An App is considered new in the date range when its
        earliest release falls within the date range passed in

        :param start_date:
        :param end_date:
        :return:
        """
        app_set = set()
        for a_app in App.objects.all():
            # if an app has a release before start date ignore
            if Release.objects.filter(app=a_app,
                                      created__lt=start_date).count() > 0:
                continue

            # if app only has releases on or after end date ignore
            if Release.objects.filter(app=a_app,
                                      created__lt=end_date).count() == 0:
                continue
            app_set.add(a_app.name)
        return app_set

    def add_arguments(self, parser):
        """
        Called by Django to get command line options for this tool

        :param parser:
        :return:
        """
        parser.add_argument('--window', default='30',
                            help='Window in days to look back for report generation. '
                                 'A value of 5 means the report will examine the '
                                 'previous 5 days when tabulating results')
        parser.add_argument('--end_date',
                            help='End date for generating report (NOT '
                                 'included in tabulation). '
                                 'If unset, today\'s date will be used. '
                                 'Format: YYYY-MM-DD. Example: 2021-02-15')
        parser.add_argument('--emailreport', default=None,
                            help='If set, sends report via email to comma delimited '
                                 'recipients using Django configuration')
        parser.add_argument('--newappcontacts', action='store_true',
                            help='If set, includes a list of new apps and'
                                 'their authors with contact info')

    def get_start_and_end_date(self, window=None,
                               end_date=None):
        if end_date is None:
            end_date = date.today()
        else:
            end_date = date.fromisoformat(end_date)
        if window is None:
            raise Exception('Window cannot be None')
        num_days = int(re.sub('m$', '', window))
        start_date = end_date - timedelta(num_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), num_days

    def get_report_as_str(self, start_date=None,
                          end_date=None, num_days=None,
                          time_str=datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                          new_app_contacts=False):
        """

        :param start_date:
        :param end_date:
        :return:
        """
        active_app_cnt = self.get_count_of_active_apps()
        active_author_count = self.get_count_of_authors_with_active_apps()
        res = 'Summary report run on ' +\
              time_str + '\n'
        res += '\t' + str(self.get_number_of_users()) + ' active user accounts\n'
        res += '\t' + str(active_app_cnt) +\
               ' active Apps with ' +\
               str(active_author_count) +\
               ' people listed as authors\n\n'

        res += 'For dates from ' + start_date +\
               ' up to, but not including, ' +\
               end_date + ' (' + str(num_days) +\
               ' days)\n'

        res += '\t' +\
               str(self.get_number_of_users_added(start_date=start_date,
                                                  end_date=end_date)) +\
               ' new user accounts\n'
        update_app_cnt = self.get_count_of_apps_with_releases(start_date,
                                                              end_date)
        res += '\t' + str(update_app_cnt) + ' Apps were updated\n'

        new_app_cnt = 0
        new_apps = self.get_new_apps(start_date=start_date,
                                     end_date=end_date)
        if new_apps is not None:
            new_app_cnt = len(new_apps)
        res += '\t' + str(new_app_cnt) + ' new Apps\n'

        total_downloads = self.get_downloads_for_apps(start_date,
                                                      end_date)
        res += '\t' + str(total_downloads) + ' (' +\
               str(round((float(total_downloads) / float(num_days)))) +\
               ' per day) App downloads\n'

        if new_app_contacts is not None and new_app_contacts is True:
            # iterate through apps and get authors and their email
            # addresses
            res += self.get_new_app_contacts(new_apps)

        return res

    def get_new_app_contacts(self, new_apps):
        """

        :param new_apps: name of apps that are new
        :type new_apps: list
        :return:
        """
        res = '\n'

        for app_name in new_apps:
            app = App.objects.filter(name=app_name)[0]
            res += 'App:'
            res += '\t' + str(app.fullname) + ' (' + str(app_name) + ')'
            if app.citation is not None:
                res += ' citation: ' + app.citation + '\n'
            else:
                res += '\n'

            res += 'Authors:\n'
            for auth in app.authors.all():
                # auth = Author.objects.filter(id=o_a.author.id)[0]
                res += '\t' + str(auth.name) + '\n'
            res += 'Editors:\n'
            for u in app.editors.all():
                res += '\t<' + str(u.first_name) + ' ' + str(u.last_name) + '> ' + str(u.email) + '\n'
        return res

    def handle(self, *args, **options):
        """
        Called by Django. Method queries database to generate report

        :param args:
        :param options:
        :return:
        """
        start_date,\
        end_date,\
        num_days = self.get_start_and_end_date(window=options['window'],
                                               end_date=options['end_date'])

        time_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        report_str = self.get_report_as_str(start_date=start_date, end_date=end_date,
                                            num_days=num_days, time_str=time_str,
                                            new_app_contacts=options['newappcontacts'])
        self.stdout.write(report_str)

        if options['emailreport'] is None:
            return

        if len(options['emailreport'].strip()) == 0:
            raise CommandError('Command line option --emailreport '+
                               'appears to be empty. '
                               'No email report sent.')
            return

        email_addresses = re.sub('\\s+', '',
                                 options['emailreport']).split(',')
        self.stdout.write('Sending email to ' + str(email_addresses) + '\n')
        send_mail('Cytoscape App Store Report ' + time_str,
                  report_str +
                  '\n\nGenerated by,\n\npython manage.py usagereport\n',
                  settings.EMAIL_ADDR, email_addresses,
                  fail_silently=False)
        self.stdout.write(self.style.SUCCESS('Email sent successfully.'))
