
import sys
import re
from datetime import date, datetime, timedelta

from django.core.mail import EmailMessage
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
    Generates a report denoting total Apps in AppStore for
    each month as
    """

    def get_count_of_apps_with_releases(self, end_date=None):
        """
        Gets count of apps with released where
        created is < end_date

        NOTE: Method does NOT check if App is active or not

        :param end_date: End date in format of YYYY-MM-DD
        :type end_date: str
        :return: Number of apps with one or more releases during time frame
        :rtype: int
        """
        app_set = set()
        for rel in Release.objects.filter(created__lt=end_date):
            try:
                cur_app = App.objects.get(id=rel.app.id)
            except Exception as e:
                print(e)
                continue
            app_set.add(cur_app.name)
        return len(app_set)

    def get_date_of_oldest_app_release(self):
        """
        Looks at all releases and finds the date of the
        oldest release. This sets the starting month/year for
        the report

        :return: date of oldest release
        :rtype: `py:class:datetime.datetime`
        """
        oldest = None
        for rel in Release.objects.all():
            try:
                if oldest is None:
                    oldest = rel.created
                elif rel.created < oldest:
                    oldest = rel.created
            except Exception as e:
                print(e)
                continue
        return oldest

    def add_arguments(self, parser):
        """
        Called by Django to get command line options for this tool

        :param parser:
        :return:
        """
        parser.add_argument('--monthlyreport', action='store_true',
                            help='If set, generates report of new Apps broken down '
                                 'by month as well as by year')
        parser.add_argument('--emailreport', default=None,
                            help='If set, sends report via email to comma delimited '
                                 'recipients using Django configuration')

    def get_report_as_str(self, report_monthly=False):
        """

        :param start_date:
        :param end_date:
        :return:
        """
        oldest_release = self.get_date_of_oldest_app_release()
        month_year_tuples = self.generate_month_tuples(oldest_release)

        month_report = ''

        if report_monthly is True:
            month_report = 'Date,Number of Apps\n'
        year_report = 'Year,Number of Apps\n'
        for month_year in month_year_tuples:
            if report_monthly is True or month_year[0].month == 12:
                app_cnt = self.get_count_of_apps_with_releases(month_year[1])
            if report_monthly is True:
                month_report += str(month_year[0].month) + '/' +\
                          str(month_year[0].year) + ',' +\
                          str(app_cnt) + '\n'
            if month_year[0].month == 12:
                year_report += str(month_year[0].year) + ',' +\
                      str(app_cnt) + '\n'
        return month_report + '\n----------\n' + year_report

    def generate_month_tuples(self, oldest_release):
        """

        :param oldest_release:
        :return:
        """
        cur_year = datetime.now().year
        cur_month = datetime.now().month
        oldest_year = oldest_release.year
        oldest_month = oldest_release.month
        month_year_tuples = []
        for the_year in range(oldest_year, cur_year+1):

            for the_month in range(1, 13):
                if the_year == oldest_year and the_month < oldest_month:
                    continue
                if the_year == cur_year and the_month >= cur_month:
                    continue
                start_date = datetime.strptime(str(the_year) + '-' +
                                               str(the_month) +
                                               '-01 00:00:00',
                                               '%Y-%m-%d %H:%M:%S')
                e_month = the_month + 1
                e_year = the_year
                if e_month > 12:
                    e_month = 1
                    e_year += 1
                end_date = datetime.strptime(str(e_year) + '-' +
                                             str(e_month) +
                                             '-01 00:00:00',
                                             '%Y-%m-%d %H:%M:%S')
                month_year_tuples.append((start_date, end_date))
        return month_year_tuples

    def handle(self, *args, **options):
        """
        Called by Django. Method queries database to generate report

        :param args:
        :param options:
        :return:
        """
        time_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.stdout.write(self.style.SUCCESS('NOTE: This report takes several minutes to run.'))
        report_str = self.get_report_as_str(report_monthly=options['monthlyreport'])
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
        email = EmailMessage(subject='Cytoscape App Tally Report ' + time_str,
                             body=report_str +
                             '\n\nGenerated by,\n\npython manage.py apptally\n',
                             from_email=settings.EMAIL_ADDR,
                             to=email_addresses)
        if email.send() == 1:
            self.stdout.write(self.style.SUCCESS('Email sent successfully.'))
        else:
            self.stdout.write(self.style.ERROR('Error sending email'))
