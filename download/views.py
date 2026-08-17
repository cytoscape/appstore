import datetime

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.http import Http404

from util.view_util import html_response, json_response, ipaddr_str_to_long, ipaddr_long_to_str
from apps.models import App, Release, ServiceRelease, WebBundleRelease, Platform
from download.models import ReleaseDownloadsByDate, AppDownloadsByGeoLoc, Download, GeoLoc, WebBundleDownload, ServiceDownload
from download.models import ServiceReleaseDownloadsByDate, WebBundleReleaseDonwloadsByDate

# ===================================
#   Download release
# ===================================


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
    app = get_object_or_404(App, name=app_name)

    if app.platform == Platform.DESKTOP:
        release = get_object_or_404(Release, app__name = app_name, version = version, active = True)
        target_url = release. release_file_url
    elif app.plaftorm == Platform.SERVICE:
        release = get_object_or_404(ServiceRelease, app=app, version=version, active=True)
        target_url = release.service_endpoint
    elif app.platform == Platform.WEB:
        release = get_object_or_404(WebBundleRelease, app=app, version=version, active=True) #gonna have to change to a general webapp release model
        target_url = release.install_url
    else:
        raise Http404

    ip4addr = _client_ipaddr(request)
    when    = datetime.date.today()

    # Update the App object
    release.app.downloads += 1
    release.app.save()

    # Record the download as a Download object
    if app.platform == Platform.DESKTOP:
        Download.objects.create(release = release, ip4addr = ip4addr, when = when)
        _increment_count(ReleaseDownloadsByDate, release = release, when = when)
        _increment_count(ReleaseDownloadsByDate, release = None,    when = when)
    elif app.platform == Platform.WEB:
        WebBundleDonwload.objects.create(release = release, ip4addr = ip4addr, when = when)
        _increment_count(SServiceReleaseDownloadsByDate, release = release, when = when)
        _increment_count(ReleaseDownloadsByDate, release = None,    when = when)
    elif app.platform == Platform.SERVICE:
        ServiceDonwload.objects.create(release=release, ip4addr=ip4addr, when=when)


    return HttpResponseRedirect(target_url)

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
