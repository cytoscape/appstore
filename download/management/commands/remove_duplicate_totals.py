from django.core.management.base import BaseCommand
from download.models import GeoLoc, AppDownloadsByGeoLoc

def get_dup_names():
    dup_names = set()
    country_objs = GeoLoc.objects.filter(region = '', city = '')
    for country_obj in country_objs:
      country_name = country_obj.country
      city_objs = GeoLoc.objects.filter(country = country_name)
      for city_obj in city_objs:
        region_name = city_obj.region
        city_name = city_obj.city
        dup_cities = GeoLoc.objects.filter(country = country_name, region = region_name, city = city_name)
        if dup_cities.count() <= 1: continue
        dup_names.add((country_name, region_name, city_name))
    return dup_names


class Command(BaseCommand):
  def handle(self, *args, **options):
    dup_names = get_dup_names()
    for country, region, city in dup_names:
      dup_geolocs = GeoLoc.objects.filter(country = country, region = region, city = city)
      for dup_geoloc in dup_geolocs:
        #print 'GeoLoc', dup_geoloc, dup_geoloc.id, ', dls:',
        for dl in AppDownloadsByGeoLoc.objects.filter(geoloc = dup_geoloc):
          #print (dl.app.name if dl.app else 'none'), dl.id, ' | ',
          dl.delete()
        dup_geoloc.delete()

