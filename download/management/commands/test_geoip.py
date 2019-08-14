from django.core.management.base import BaseCommand
from django.conf import settings
from os.path import isfile, join as pathjoin

geoip_files = (
  pathjoin(settings.GEOIP_PATH, 'GeoIP.dat'),
  pathjoin(settings.GEOIP_PATH, 'GeoLiteCity.dat'),
  settings.GEOIP_LIBRARY_PATH
  )

def test_geoip_files():
  satisfied = True
  for geoip_file in geoip_files:
    if isfile(geoip_file):
      print '[  ok  ] File exists:', geoip_file
    else:
      print '[ FAIL ] File not found:', geoip_file
      satisfied = False
  return satisfied

class Command(BaseCommand):
  def handle(self, *args, **options):
    if not test_geoip_files(): return
    try:
      from django.contrib.gis.geoip import GeoIP
      print '[  ok  ] Imported GeoIP'
    except ImportError:
      print "[ FAIL ] Unable to import 'django.contrib.gis.geoip'"

    g = GeoIP()
    g.city('206.86.95.58')
    print '[  ok  ] Successfully mapped IP address to geographical location'

