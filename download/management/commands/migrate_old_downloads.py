import sys
from django.db import connection
from django.core.management.base import BaseCommand
from django.contrib.gis.geoip import GeoIP

from apps.models import Release
from download.models import GeoLoc, ReleaseDownloadsByDate, AppDownloadsByGeoLoc, Download
from util.view_util import ipaddr_long_to_str

def increment_count(klass, **args):
    print klass.__name__, args, ';',
    sys.stdout.flush()
    obj, created = klass.objects.get_or_create(**args)
    obj.count += 1
    obj.save()

class Command(BaseCommand):
    def handle(self, *args, **options):
        cur = connection.cursor()
        g = GeoIP()
        cur.execute("SELECT id, release_id, created, ip4addr FROM apps_download")
        for id, release_id, created, ip4addr in cur.fetchall():
            release = Release.objects.get(id = release_id)
            app     = release.app
            when    = created.date()

            print '{0:5} {1:30} {2:15} {3:10} {4:15}'.format(id, app.fullname, release.version, str(when), ipaddr_long_to_str(ip4addr)),
            sys.stdout.flush()

            dl = Download.objects.create(release = release, when = when, ip4addr = ip4addr)
            dl.save()

            increment_count(ReleaseDownloadsByDate, release = release, when = when)
            increment_count(ReleaseDownloadsByDate, release = None,    when = when)

            geoinfo = g.city(ipaddr_long_to_str(ip4addr))
            if geoinfo:
                country_geoloc, _ = GeoLoc.objects.get_or_create(country = geoinfo['country_code'], region = '', city = '')
                increment_count(AppDownloadsByGeoLoc, app = app,  geoloc = country_geoloc)
                increment_count(AppDownloadsByGeoLoc, app = None, geoloc = country_geoloc)

                if geoinfo.get('city'):
                    city_geoloc, _ = GeoLoc.objects.get_or_create(country = geoinfo['country_code'], region = geoinfo['region'], city = geoinfo['city'])
                    increment_count(AppDownloadsByGeoLoc, app = app,  geoloc = city_geoloc)
                    increment_count(AppDownloadsByGeoLoc, app = None, geoloc = city_geoloc)
                    
            print
                    
