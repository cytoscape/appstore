import datetime
from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.http import Http404

from util.view_util import html_response, json_response, ipaddr_str_to_long, ipaddr_long_to_str
from apps.models import App, Release, ServiceRelease, WebBundleRelease, Platform
from download.models import ReleaseDownloadsByDate, AppDownloadsByGeoLoc, Download, GeoLoc, WebBundleDownload, ServiceDownload
from download.models import ServiceReleaseDownloadsByDate, WebBundleReleaseDownloadsByDate

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

def _record_download(request, app, release, download_model, by_date_model):
    ip4addr = _client_ipaddr(request)
    when = datetime.date.today()
    app.downloads += 1
    app.save()
    download_model.objects.create(release=release, ip4addr=ip4addr, when=when)
    _increment_count(by_date_model, release=release, when=when)
    _increment_count(by_date_model, release=None, when=when)

def release_download(request, app_name, version):
    app = get_object_or_404(App, name=app_name, platform=Platform.DESKTOP)
    release = get_object_or_404(Release, app=app, version=version, active=True)
    _record_download(request, app, release, Download, ReleaseDownloadsByDate)
    return HttpResponseRedirect(release.release_file_url)


def release_install(request, app_name, version): #need to add functionality for desktop apps as well or make new function (or use release_download)
    app = get_object_or_404(App, name=app_name)
    if app.platform == 'service':
        release = get_object_or_404(ServiceRelease, app=app, version=version, active=True)
        _record_download(request, app, release, ServiceDownload, ServiceReleaseDownloadsByDate)
        return HttpResponseRedirect(release.install_url)
    elif app.platform == 'web':
        release = get_object_or_404(WebBundleRelease, app=app, version=version, active=True)
        _record_download(request, app, release, WebBundleDownload, WebBundleReleaseDownloadsByDate)
        return HttpResponseRedirect(release.install_url)
    else:
        raise Http404

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
    totals_by_date = defaultdict(int)

    for by_date_model in (ReleaseDownloadsByDate, ServiceReleaseDownloadsByDate, WebBundleReleaseDownloadsByDate):
        for dl in by_date_model.objects.filter(release=None):
            totals_by_date[dl.when] += dl.count

    response = {
        'Total': [[when.isoformat(), count] for when, count in sorted(totals_by_date.items())]
    }

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
    response = dict()

    if app.platform == 'desktop':
        release = app.release_set.all()
        by_date_model = ReleaseDownloadsByDate
    elif app.platform == 'service':
        release = app.servicereleases_set.all()
        by_date_model = ServiceReleaseDownloadsByDate
    elif app.platform == 'web':
        release = app.webbundlereleases_set.all()
        by_date_model = WebBundleReleaseDownloadsByDate
    else:
        raise Http404

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
