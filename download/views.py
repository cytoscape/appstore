import datetime

from django.shortcuts import get_object_or_404
from django.contrib.gis.geoip import GeoIP
from django.http import HttpResponseRedirect

from util.view_util import html_response, json_response, ipaddr_str_to_long, ipaddr_long_to_str
from apps.models import App, Release
from download.models import ReleaseDownloadsByDate, AppDownloadsByGeoLoc, Download, GeoLoc

# ===================================
#   Download release
# ===================================

geoIP = GeoIP()

def _client_ipaddr(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        ipaddr_str = forwarded_for.split(',')[0]
    else:
        ipaddr_str = request.META.get('REMOTE_ADDR')
    return ipaddr_str_to_long(ipaddr_str)

def _increment_count(klass, **args):
    obj, created = klass.objects.get_or_create(**args)
    obj.count += 1
    obj.save()

def release_download(request, app_name, version):
    release = get_object_or_404(Release, app__name = app_name, version = version, active = True)
    ip4addr = _client_ipaddr(request)
    when    = datetime.date.today()

    # Update the App object
    release.app.downloads += 1
    release.app.save()

    # Record the download as a Download object
    Download.objects.create(release = release, ip4addr = ip4addr, when = when)

    # Record the download in the timeline
    _increment_count(ReleaseDownloadsByDate, release = release, when = when)
    _increment_count(ReleaseDownloadsByDate, release = None,    when = when)

    # Look up geographical information about the user's IP address
    geoinfo = geoIP.city(ipaddr_long_to_str(ip4addr))
    if geoinfo:
        # Record the download in the user's country
        country_geoloc, _ = GeoLoc.objects.get_or_create(country = geoinfo['country_code'], region = '', city = '')
        _increment_count(AppDownloadsByGeoLoc, app = release.app, geoloc = country_geoloc)
        _increment_count(AppDownloadsByGeoLoc, app = None,        geoloc = country_geoloc)

        if geoinfo.get('city'):
            # Record the download in the user's city
            city_geoloc, _ = GeoLoc.objects.get_or_create(country = geoinfo['country_code'], region = geoinfo['region'], city = geoinfo['city'])
            _increment_count(AppDownloadsByGeoLoc, app = release.app,  geoloc = city_geoloc)
            _increment_count(AppDownloadsByGeoLoc, app = None,         geoloc = city_geoloc)

    return HttpResponseRedirect(release.release_file_url)

# ===================================
#   Download statistics
# ===================================

def all_stats(request):
    return html_response('all_stats.html', {}, request)

def _all_geography_downloads(app):
    dls = AppDownloadsByGeoLoc.objects.filter(app = app)
    response = [[dl.geoloc.country, dl.geoloc.region, dl.geoloc.city, dl.count] for dl in dls]
    response.insert(0, ['Country', 'Region', 'City', 'Downloads'])
    return json_response(response)

def _world_downloads(app):
    countries = AppDownloadsByGeoLoc.objects.filter(app = app, geoloc__region = '', geoloc__city = '')
    response = [[country.geoloc.country, country.count] for country in countries]
    response.insert(0, ['Country', 'Downloads'])
    return json_response(response)

def _country_downloads(app, country_code):
    cities = AppDownloadsByGeoLoc.objects.filter(app = app, geoloc__country = country_code, geoloc__city__gt = '')
    response = [[city.geoloc.city, city.count] for city in cities]
    response.insert(0, ['City', 'Downloads'])
    return json_response(response)

def all_stats_geography_all(request):
    return _all_geography_downloads(None)

def all_stats_geography_world(request):
    return _world_downloads(None)

def all_stats_geography_country(request, country_code):
    return _country_downloads(None, country_code)

def all_stats_timeline(request):
    dls = ReleaseDownloadsByDate.objects.filter(release = None)
    response = {'Total': [[dl.when.isoformat(), dl.count] for dl in dls]}
    return json_response(response)

def app_stats(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    app_downloads_by_country = AppDownloadsByGeoLoc.objects.filter(app = app, geoloc__region = '', geoloc__city = '')
    releases = app.release_set.all()
    release_downloads_by_date = [dl for release in releases for dl in ReleaseDownloadsByDate.objects.filter(release = release)]
    c = {
            'app': app,
            'app_downloads_by_country': app_downloads_by_country,
            'release_downloads_by_date': release_downloads_by_date,
         }
    return html_response('app_stats.html', c, request)

def app_stats_timeline(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    releases = app.release_set.all()
    response = dict()
    for release in releases:
        dls = ReleaseDownloadsByDate.objects.filter(release = release)
        response[release.version] = [[dl.when.isoformat(), dl.count] for dl in dls]
    return json_response(response)
        
def app_stats_geography_all(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    return _all_geography_downloads(app)

def app_stats_geography_world(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    return _world_downloads(app)

def app_stats_country(request, app_name, country_code):
    app = get_object_or_404(App, active = True, name = app_name)
    return _country_downloads(app, country_code)
