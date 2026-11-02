import datetime
from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
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
    app = get_object_or_404(App, name=app_name)
    release = get_object_or_404(Release, app=app, version=version, active=True)
    _record_download(request, app, release, Download, ReleaseDownloadsByDate)
    return HttpResponseRedirect(release.release_file_url)


# the release types release_install installs, in the order a bare install URL tries them
_INSTALL_RELEASE_MODELS = {
    Platform.SERVICE: ServiceRelease,
    Platform.WEB: WebBundleRelease,
}

def _install_platform(request, app, version):
    """
    The platform an install URL installs: its ?platform=, or else whichever of service
    and web has that version, so links made before apps had several platforms still work.
    """
    platform = request.GET.get('platform')
    if platform:
        if platform not in _INSTALL_RELEASE_MODELS:
            raise Http404('No install for platform "%s"' % platform)
        return platform
    for platform, release_model in _INSTALL_RELEASE_MODELS.items():
        if release_model.objects.filter(app=app, version=version, active=True).exists():
            return platform
    raise Http404('No such release')

def release_install(request, app_name, version):
    # ?client=desktop is the store page reporting a service app it installed into
    # Cytoscape Desktop: record the install and reply 204 instead of redirecting.
    client = request.GET.get('client')
    app = get_object_or_404(App, name=app_name)
    platform = _install_platform(request, app, version)
    if platform == Platform.SERVICE:
        release = get_object_or_404(ServiceRelease, app=app, version=version, active=True)
        _record_download(request, app, release, ServiceDownload, ServiceReleaseDownloadsByDate)
        if client == 'desktop':
            return HttpResponse(status=204)
        return HttpResponseRedirect(release.install_url)
    else:
        if client == 'desktop':
            raise Http404
        release = get_object_or_404(WebBundleRelease, app=app, version=version, active=True)
        _record_download(request, app, release, WebBundleDownload, WebBundleReleaseDownloadsByDate)
        return HttpResponseRedirect(release.install_url)

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

# each platform's releases and the model counting their downloads per day
_PLATFORM_DOWNLOADS = {
    Platform.DESKTOP: ('release_set', ReleaseDownloadsByDate),
    Platform.WEB: ('webbundlerelease_set', WebBundleReleaseDownloadsByDate),
    Platform.SERVICE: ('servicerelease_set', ServiceReleaseDownloadsByDate),
}

def _stats_platforms(app):
    """
    Platforms the app has ever released on. Unlike app.platforms, inactive releases
    count: their downloads stay in the app's stats after the releases are deleted.
    """
    return [platform for platform, (release_set, _) in _PLATFORM_DOWNLOADS.items()
            if getattr(app, release_set).exists()]

def _downloads_by_release(app):
    """(platform, release, its downloads by date) for every release, active or not, on each platform the app released on."""
    for platform in _stats_platforms(app):
        release_set, by_date_model = _PLATFORM_DOWNLOADS[platform]
        for release in getattr(app, release_set).all():
            yield platform, release, by_date_model.objects.filter(release=release)

def app_stats(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    app_downloads_by_country = AppDownloadsByGeoLoc.objects.filter(app = app, geoloc__region = '', geoloc__city = '')
    release_downloads_by_date = [dl for _, _, dls in _downloads_by_release(app) for dl in dls]
    c = {
            'app': app,
            'app_downloads_by_country': app_downloads_by_country,
            'release_downloads_by_date': release_downloads_by_date,
         }
    return html_response('app_stats.html', c, request)

def app_stats_timeline(request, app_name):
    """Downloads by date per release, keyed by version, or by "<platform> <version>" when the app released on several platforms."""
    app = get_object_or_404(App, active = True, name = app_name)
    several_platforms = len(_stats_platforms(app)) > 1
    response = dict()
    for platform, release, dls in _downloads_by_release(app):
        key = '%s %s' % (platform, release.version) if several_platforms else release.version
        response[key] = [[dl.when.isoformat(), dl.count] for dl in dls]
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
