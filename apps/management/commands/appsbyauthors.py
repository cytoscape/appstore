
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
    Generates report that takes a list of authors and
    outputs the following statistics on apps whose one
    or more co-authors is in the list of authors:
    
    Number of apps, Total download count for all those apps,
    Total download counts for all apps regardless of author  

    """

    def get_apps(self):
        """
        Gets all apps with at least 1 release
        :return:
        """
        app_set = set()
        for a_app in App.objects.all():
            # if an app lacks a release, ignore
            if Release.objects.filter(app=a_app).count() == 0:
                continue

                continue
            app_set.add(a_app)
        return app_set

    def add_arguments(self, parser):
        """
        Called by Django to get command line options for this tool

        :param parser:
        :return:
        """
        parser.add_argument('--authors', nargs='+',
                            help='Keep only apps whose co-author is one of the '
                                 'names passed in')

    def is_app_created_by_authors(self, author_name=None, authors=None):
        """
        Checks if **author_name** is in **authors**

        :param authors:
        :type authors: set or list
        :return: True if author is in **authors**
        :rtype: bool
        """
        for a in authors:
            if a in author_name:
                return True
        return False

    def get_report_as_str(self, authors=None):
        """
        Creates report listing all released apps along
        with their authors along with count of apps that
        have **authors** in their author list

        :param authors: str of author names
        :type authors: list
        :return: report
        :rtype: str
        """
        report_str = 'List of Apps with authors. \n'
        report_str += 'Co-authors of interest have ** next to name\n'
        report_str += datetime.today().strftime('%Y-%m-%d %H:%M:%S') + '\n'

        a_last_name = set()

        for a in authors:
            a_last_name.add(a.split(' ')[-1])
        app_set = self.get_apps()
        unique_authors = set()
        apps_by_authors = set()
        total_downloads = 0
        total_count = 0
        for app in app_set:
            total_downloads += app.downloads
            total_count += 1
            app_authors_all = app.authors.all()
            if len(app_authors_all) == 0:
                continue
            report_str += '\n' + str(app.name) + '\n' + '=' * len(str(app.name)) + '\n'
            for auth_item in app_authors_all:
                report_str += '\t' + str(auth_item.name)
                unique_authors.add(auth_item.name)
                if self.is_app_created_by_authors(author_name=auth_item.name,
                                                  authors=authors) is True:
                    apps_by_authors.add(app)
                    report_str += ' **'

                report_str += '\n'

        report_str += '\n\n-----------------------------------------\n'
        report_str += '\nNumber of Apps co-authored by authors: ' +\
                      str(len(apps_by_authors)) + '\n'
        report_str += 'Number of Apps with active release: ' + str(total_count) + '\n'

        total_coauthor_downloads = 0
        for app in apps_by_authors:
            total_coauthor_downloads += app.downloads

        report_str += 'Number of downloads for Apps co-authored by authors: ' +\
                      str(total_coauthor_downloads) + '\n'

        report_str += 'Number of downloads for all Apps with active release: ' + \
                      str(total_downloads) + '\n'

        return report_str

    def handle(self, *args, **options):
        """
        Called by Django. Method queries database to generate report

        :param args:
        :param options:
        :return:
        """
        report_str = self.get_report_as_str(authors=options['authors'])
        self.stdout.write(report_str)

