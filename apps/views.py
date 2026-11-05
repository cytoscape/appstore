import re
import datetime
import html
from urllib.parse import unquote
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.db.models import Q
from util.view_util import json_response, html_response, obj_to_dict, get_object_or_none
from util.img_util import scale_img
from util.id_util import fullname_to_name
from apps.models import Tag, App, Platform, Author, OrderedAuthor, Screenshot, Release
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from util.view_util import is_ajax
# Returns a unicode string encoded in a cookie
def _unescape_and_unquote(s):
    if not s: return s
    return html.unescape(unquote(s))

# ============================================
#      Nav Panel
# ============================================

class _NavPanelConfig:
    min_tag_count = 3
    num_of_top_tags = 20
    tag_cloud_max_font_size_em = 2.0
    tag_cloud_min_font_size_em = 1.0
    tag_cloud_delta_font_size_em = tag_cloud_max_font_size_em - tag_cloud_min_font_size_em

def _all_tags_of_count(min_count):
    return filter(lambda tag: tag.count >= min_count, Tag.objects.all())

_NavPanelContextCache = None

def _nav_panel_context(request):
    global _NavPanelContextCache
    if _NavPanelContextCache:
        return _NavPanelContextCache
    all_tags = _all_tags_of_count(_NavPanelConfig.min_tag_count)
    sorted_tags = sorted(all_tags, key=lambda tag: tag.count)
    sorted_tags.reverse()

    if len(sorted_tags) > 0:
        max_count = sorted_tags[0].count
        min_count = sorted_tags[-1].count
    else:
        max_count, min_count = (0, 0)
    count_delta = float(max_count - min_count)
    top_tags = sorted_tags[:_NavPanelConfig.num_of_top_tags]
    not_top_tags = sorted_tags[_NavPanelConfig.num_of_top_tags:]

    for tag in all_tags:
        try:
            rel_count = (tag.count - min_count) / count_delta
        except ZeroDivisionError:
            rel_count = 1
        font_size_em = rel_count * _NavPanelConfig.tag_cloud_delta_font_size_em + _NavPanelConfig.tag_cloud_min_font_size_em
        tag.font_size_em = '%.2f' % font_size_em

    result = {
        'all_tags': all_tags,
        'top_tags': top_tags,
        'not_top_tags': not_top_tags
    }
    _NavPanelContextCache = result
    return result

def _flush_tag_caches():
    global _NavPanelContextCache
    global _TagCountCache
    _NavPanelContextCache = None
    _TagCountCache = dict()

# ============================================
#      Navigating Apps & Tags
# ============================================

class _DefaultConfig:
    num_of_top_apps = 6

def apps_default(request):
    latest_apps = App.objects.filter(active=True).order_by('-latest_release_date')[:_DefaultConfig.num_of_top_apps]
    downloaded_apps = App.objects.filter(active=True).order_by('downloads').reverse()[:_DefaultConfig.num_of_top_apps]

    c = {
        'latest_apps': latest_apps,
        'downloaded_apps': downloaded_apps,
        'go_back_to': 'home',
    }
    return html_response('apps_default.html', c, request, processors = (_nav_panel_context, ))

def all_apps(request):
    apps = App.objects.filter(active=True).order_by('name').prefetch_related('platform_contents')
    c = {
        'apps': apps,
        'navbar_selected_link': 'all',
        'go_back_to': 'All Apps',
    }
    return html_response('all_apps.html', c, request, processors = (_nav_panel_context, ))

def all_apps_newest(request):
    apps = App.objects.filter(active=True).order_by('-latest_release_date')
    c = {
        'apps': apps,
        'navbar_selected_link': 'all',
        'go_back_to': 'All Apps',
    }
    return html_response('all_apps.html', c, request, processors = (_nav_panel_context, ))


def all_apps_downloads(request):
    apps = App.objects.filter(active=True).order_by('downloads').reverse()
    c = {
        'apps': apps,
        'navbar_selected_link': 'all',
        'go_back_to': 'All Apps',
    }
    return html_response('all_apps.html', c, request, processors = (_nav_panel_context, ))

def wall_of_apps(request):
    nav_panel_context = _nav_panel_context(request)
    tags = [(tag.fullname, tag.app_set.all()) for tag in nav_panel_context['top_tags']]
    apps_in_not_top_tags = set()
    for not_top_tag in nav_panel_context['not_top_tags']:
        apps_in_not_top_tags.update(not_top_tag.app_set.all())
    tags.append(('other', apps_in_not_top_tags))
    c = {
        'total_apps_count': App.objects.filter(active=True).count,
        'tags': tags,
        'go_back_to': 'Wall of Apps',
    }
    return html_response('wall_of_apps.html', c, request)

def apps_with_tag(request, tag_name):
    tag = get_object_or_404(Tag, name = tag_name)
    # the category may be on the app or on one of its platforms' content (#155)
    apps = App.objects.filter(Q(tags = tag) | Q(platform_contents__tags = tag), active = True) \
                      .distinct().order_by('name').prefetch_related('platform_contents')
    c = {
        'tag': tag,
        'apps': apps,
        'selected_tag_name': tag_name,
        'go_back_to': '&ldquo;%s&rdquo; category' % tag.fullname,
    }
    return html_response('apps_with_tag.html', c, request, processors = (_nav_panel_context, ))

def apps_with_author(request, author_name):
    apps = App.objects.filter(active = True, authors__name__exact = author_name).order_by('name')
    if not apps:
        raise Http404('No such author "%s".' % author_name)

    c = {
        'author_name': author_name,
        'apps': apps,
        'go_back_to': '%s\'s author page' % author_name,
        'go_back_to_title': _unescape_and_unquote(request.COOKIES.get('go_back_to_title')),
        'go_back_to_url':   _unescape_and_unquote(request.COOKIES.get('go_back_to_url')),
    }
    return html_response('apps_with_author.html', c, request, processors = (_nav_panel_context, ))

def apps_with_platform(request, platform):
    if platform not in Platform.values:
        raise Http404('No such platform "%s"' % platform)
    apps = list(App.objects.filter(active=True).on_platform(platform).prefetch_related('platform_contents'))
    for app in apps:
        # tiles describe the app as this platform's page does
        app.listing_platform = platform

    c = {
        'platform': platform,
        'apps' : apps,
        'go_back_to_title': _unescape_and_unquote(request.COOKIES.get('go_back_to_title')),
        'go_back_to_url':   _unescape_and_unquote(request.COOKIES.get('go_back_to_url')),
    }

    return html_response('apps_with_platform.html', c, request, processors = (_nav_panel_context, ))

def cy2x_plugins_page(request):
    c = {
        'apps': App.objects.filter(active=True).legacy_plugins().order_by('name'),
        'cy2x_plugins_selected': True,
        'go_back_to_title': _unescape_and_unquote(request.COOKIES.get('go_back_to_title')),
        'go_back_to_url':   _unescape_and_unquote(request.COOKIES.get('go_back_to_url')),
    }
    return html_response('apps_cy2x_plugins.html', c, request, processors = (_nav_panel_context, ))

# ============================================
#      App Pages
# ============================================

# -- App Rating

def _app_rate(app, user, post):
    rating_n = post.get('rating')
    try:
        rating_n = int(rating_n)
        if not (0 <= rating_n <= 5):
            raise ValueError()
    except ValueError:
        raise ValueError('rating is "%s" but must be an integer between 0 and 5' % rating_n)
    app.votes += 1
    app.stars += rating_n
    app.save()
    return obj_to_dict(app, ('votes', 'stars_percentage'))

def _app_ratings_delete_all(app, user, post):
    if not app.is_editor(user):
        return HttpResponseForbidden()
    app.stars = 0
    app.votes = 0
    app.save()

# -- General app stuff

def _latest_release(app):
    releases = app.get_releases(Platform.DESKTOP)
    if not releases: return None
    return releases[0] # go by the ordering provided by Release.Meta

# what the app page calls each platform
_PLATFORM_NAMES = {
    Platform.DESKTOP: 'Cytoscape Desktop',
    Platform.WEB: 'Cytoscape Web',
    Platform.SERVICE: 'Service',
}

def _mk_app_page(app, user, request):
    """
    One page for every platform the app is on (#155). ?platform= picks the
    platform whose panel comes first and whose releases Release History lists.
    """
    platforms = app.platforms
    selected_platform = request.GET.get('platform')
    if selected_platform not in platforms:
        selected_platform = app.primary_platform
    panel_order = sorted(platforms, key=lambda platform: platform != selected_platform)
    # each platform's content: the selected one fills the page, and each panel shows its own licence
    contents = {platform: app.content(platform) for platform in platforms}
    content = contents.get(selected_platform) or app.content()

    c = {
        'app': app,
        'content': content,
        'contents': contents,
        'license_modals': [(platform, contents[platform]) for platform in (Platform.DESKTOP, Platform.SERVICE)
                           if platform in contents and contents[platform].license_confirm
                           and contents[platform].license_text],
        'platform_chips': [(platform, _PLATFORM_NAMES[platform]) for platform in platforms],
        'selected_platform': selected_platform,
        'panel_order': panel_order,
        'selected_platform_name': _PLATFORM_NAMES.get(selected_platform),
        'selected_releases': app.releases_for_display(selected_platform) if selected_platform else [],
        'is_editor': (user and app.is_editor(user)),
        'go_back_to_title': _unescape_and_unquote(request.COOKIES.get('go_back_to_title')),
        'go_back_to_url':   _unescape_and_unquote(request.COOKIES.get('go_back_to_url')),
    }
    if app.has_desktop:
        c['cy3_latest_release'] = _latest_release(app)
    if app.has_web:
        c['bundle_latest_release'] = _latest_bundle_release(app)
    if app.has_service:
        service_release = _latest_service_release(app)
        c['service_latest_release'] = service_release
        c['service_install_name'] = _service_install_name(app, service_release)
        c['desktop_service_app_name'] = settings.DESKTOP_SERVICE_APP_NAME
    return html_response('app_page.html', c, request)

_AppActions = {
    'rate':                _app_rate,
    'ratings_delete_all':  _app_ratings_delete_all,
}

@csrf_exempt
def app_page(request, app_name):
    app = get_object_or_404(App, active=True, name=app_name)
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        action = request.POST.get('action')
        if not action:
            return HttpResponseBadRequest('no action specified')
        if not action in _AppActions:
            return HttpResponseBadRequest('action "%s" invalid--must be: %s' % (action, ', '.join(_AppActions)))
        try:
            result = _AppActions[action](app, user, request.POST)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        if isinstance(result, HttpResponse):
            return result
        if is_ajax(request):
            return json_response(result)


    return _mk_app_page(app, user, request)

# ============================================
#      App Page Editing
# ============================================

@login_required
def author_names(app, request):
    names = [a.name for a in Author.objects.exclude(name__isnull=True)]
    return json_response(names)

@login_required
def institution_names(app, request):
    names = [a.institution for a in Author.objects.exclude(institution__isnull=True)]
    return json_response(names)

isoDateRe = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
def _parse_iso_date(string):
    matches = isoDateRe.match(string)
    if not matches:
        raise ValueError('date does not follow format: yyyy-mm-dd')
    year, month, day = matches.groups()
    try:
        return datetime.date(int(year), int(month), int(day))
    except ValueError:
        return None

def _mk_basic_field_saver(field, func = None):
    def saver(app, request):
        value = request.POST.get(field)
        if value == None:
            raise ValueError('no %s specified' % field)
        if value == '':
            value = None
        elif func:
            value = func(value)
        setattr(app, field, value)
    return saver

def _content_platform(app, request):
    """
    The platform whose content a content edit changes (#155): the POST's 'platform',
    which must be one the app is on, or none for the app's own (Desktop's) content.
    """
    platform = request.POST.get('platform')
    if not platform:
        return None
    if platform not in app.platforms:
        raise ValueError('platform must be one this app is on: %s' % ', '.join(app.platforms))
    return platform

def _content_target(app, request):
    """Where a content edit is saved: the app, or the platform's own content (see App.content_for_edit)."""
    return app.content_for_edit(_content_platform(app, request))

def _own_platform(target):
    """The 'platform' of the screenshots and authors that belong with 'target': None for the app's own."""
    return None if isinstance(target, App) else target.platform

def _mk_content_field_saver(field, func = None):
    save_field = _mk_basic_field_saver(field, func)
    def saver(app, request):
        target = _content_target(app, request)
        save_field(target, request)
        target.save()
    return saver

def _save_tags(app, request):
    tag_count = request.POST.get('tag_count')
    if not tag_count:
        raise ValueError('no tag_count specified')
    try:
        tag_count = int(tag_count)
    except ValueError:
        raise ValueError('tag_count is not an integer')

    tags = []
    for i in range(tag_count):
        tag_key = 'tag_' + str(i)
        tag = request.POST.get(tag_key)
        if not tag:
            raise ValueError('expected ' + tag_key)
        tags.append(tag)

    target = _content_target(app, request)
    target.tags.clear()
    for tag in tags:
        tag_obj, _ = Tag.objects.get_or_create(fullname = tag, name = fullname_to_name(tag))
        target.tags.add(tag_obj)

    _flush_tag_caches()

class _AppPageEditConfig:
    max_img_size_b = 2 * 1024 * 1024
    max_icon_dim_px = 64
    thumbnail_height_px = 150
    app_description_maxlength = 140

def _upload_icon(app, request):
    f = request.FILES.get('file')
    if not f:
        raise ValueError('no file submitted')
    if f.size > _AppPageEditConfig.max_img_size_b:
        raise ValueError('image file is %d bytes but can be at most %d bytes' % (f.size, _AppPageEditConfig.max_img_size_b))
    f = scale_img(f, f.name, _AppPageEditConfig.max_icon_dim_px, scale_on_height=False)
    app.icon.save(f.name, f)


def _upload_screenshot(app, request):
    screenshot_f = request.FILES.get('file')
    if not screenshot_f:
        raise ValueError('no file submitted')
    if screenshot_f.size > _AppPageEditConfig.max_img_size_b:
        raise ValueError('image file is %d bytes but can be at '
                         'most %d bytes' % (screenshot_f.size,
                                            _AppPageEditConfig.max_img_size_b))
    thumbnail_f = scale_img(screenshot_f, screenshot_f.name,
                            _AppPageEditConfig.thumbnail_height_px,
                            scale_on_height=True)
    screenshot = Screenshot.objects.create(app=app, platform=_own_platform(_content_target(app, request)))
    screenshot.screenshot.save(screenshot_f.name, screenshot_f)
    screenshot.thumbnail.save(thumbnail_f.name, thumbnail_f)
    screenshot.save()


def _delete_screenshot(app, request):
    screenshot_id = request.POST.get('screenshot_id')
    if not screenshot_id:
        raise ValueError('no screenshot_id specified')
    platform = _own_platform(_content_target(app, request))
    try:
        screenshot = Screenshot.objects.get(id = int(screenshot_id), app = app)
    except (ValueError, Screenshot.DoesNotExist) as e:
        raise ValueError('invalid screenshot_id')
    if screenshot.platform is None and platform is not None:
        # the page showed the app's screenshot, which this platform's first edit has just copied
        screenshot = Screenshot.objects.filter(app = app, platform = platform,
                                               screenshot = screenshot.screenshot.name).first()
    if screenshot is None or screenshot.platform != platform:
        raise ValueError('invalid screenshot_id')
    screenshot.delete()

def _check_editor(app, request):
    """
    Takes email address 'editor_email' in POST request
    and finds the `User` with highest primary key
    that matches the email. This search is because
    there can be multiple users with the same email
    so we will just take the latest user.

    .. note::

        This assumes that only users that actually have access to the
        email address in question have been added to the
        app store

    :param app: The app in question (not used)
    :param request: the POST call
    :return: username of user
    """
    editor_email = request.POST.get('editor_email')
    if not editor_email:
        raise ValueError('no editor_email specified')
    try:
        user = User.objects.filter(email=editor_email).order_by('id').last()
        if user is None:
            return False
        return user.username
    except Exception as e:
        raise ValueError('Got an exception: ' + str(e))
    return False


def _save_editors(app, request):
    editors_count = request.POST.get('editors_count')
    if not editors_count:
        raise ValueError('no editors_count specified')
    try:
        editors_count = int(editors_count)
    except ValueError:
        raise ValueError('editors_count is not an integer')

    usernames = list()
    for i in range(editors_count):
        key = 'editor_' + str(i)
        username = request.POST.get(key)
        if not username:
            raise ValueError('expected ' + key)
        usernames.append(username)

    app.editors.clear()
    for username in usernames:
        user = get_object_or_none(User, username = username)
        if not user:
            raise ValueError('invalid username: ' + username)
        app.editors.add(user)

def _save_authors(app, request):
    authors_count = request.POST.get('authors_count')
    if not authors_count:
        raise ValueError('no authors_count specified')
    try:
        authors_count = int(authors_count)
    except ValueError:
        raise ValueError('authors_count is not an integer')

    authors = list()
    for i in range(authors_count):
        key = 'author_' + str(i)
        name = request.POST.get(key)
        if not name:
            raise ValueError('expected ' + key)
        institution = request.POST.get('institution_' + str(i))
        if not institution:
            institution = None
        authors.append((name, institution, i))

    # replaces only this platform's authors; the other platforms keep theirs
    platform = _own_platform(_content_target(app, request))
    OrderedAuthor.objects.filter(app = app, platform = platform).delete()
    for name, institution, author_order in authors:
        author, _ = Author.objects.get_or_create(name = name, institution = institution)
        OrderedAuthor.objects.create(app = app, platform = platform, author = author, author_order = author_order)

def _posted_platform_releases(app, request):
    """
    The releases a release-notes or delete-release edit applies to: those of the
    platform named in its 'platform' field. Without that field, the platform is the
    one the app has releases on; an app with releases on several platforms must
    name one, since release ids are only unique within a platform.
    """
    platform = request.POST.get('platform')
    if platform is None:
        platforms = app.platforms
        if len(platforms) != 1:
            raise ValueError('platform is required when an app has releases on more than one platform')
        platform = platforms[0]
    if platform not in Platform.values:
        raise ValueError('platform must be one of: %s' % ', '.join(Platform.values))
    return app.get_releases(platform)

def _save_release_notes(app, request):
    release_count = request.POST.get('release_count')
    if not release_count:
        raise ValueError('no release_count specified')
    try:
        release_count = int(release_count)
    except ValueError:
        raise ValueError('release_count is not an integer')

    releases = _posted_platform_releases(app, request)
    release_model = releases.model
    for i in range(release_count):
        key = 'release_id_' + str(i)
        release_id = request.POST.get(key)
        if not release_id:
            raise ValueError('expected ' + key)
        try:
            release = releases.get(id=int(release_id))
        except (release_model.DoesNotExist, ValueError) as e:
            raise ValueError('release_id "%s" is invalid' % release_id)
        notes_key = 'notes_' + str(i)
        notes = request.POST.get(notes_key)
        if notes == None:
            raise ValueError('expected ' + notes_key)
        release.notes = notes
        release.save()

def _delete_release(app, request):
    release_count = request.POST.get('release_count')
    if not release_count:
        raise ValueError('no release_count specified')
    try:
        release_count = int(release_count)
    except ValueError:
        raise ValueError('release_count is not an integer')

    releases = _posted_platform_releases(app, request)
    release_model = releases.model
    for i in range(release_count):
        key = 'release_id_' + str(i)
        release_id = request.POST.get(key)
        if not release_id:
            raise ValueError('expected ' + key)
        try:
            release = releases.get(id=int(release_id))
        except (release_model.DoesNotExist, ValueError) as e:
            raise ValueError('release_id "%s" is invalid' % release_id)
        release.active = False
        release.save()
    app.update_has_releases()

_AppEditActions = {
    'save_cy_2x_plugin_download':     _mk_basic_field_saver('cy_2x_plugin_download'),
    'save_cy_2x_plugin_version':      _mk_basic_field_saver('cy_2x_plugin_version'),
    'save_cy_2x_plugin_release_date': _mk_basic_field_saver('cy_2x_plugin_release_date', func=_parse_iso_date),
    'save_cy_2x_versions':            _mk_basic_field_saver('cy_2x_versions'),
    'save_description':   _mk_content_field_saver('description'),
    'save_license_text':  _mk_content_field_saver('license_text'),
    'save_license_confirm':  _mk_content_field_saver('license_confirm', func = lambda s: s.lower() == 'true'),
    'save_website':       _mk_content_field_saver('website'),
    'save_tutorial':      _mk_content_field_saver('tutorial'),
    'save_citation':      _mk_content_field_saver('citation'),
    'save_coderepo':      _mk_content_field_saver('coderepo'),
    'save_automation':  _mk_content_field_saver('automation'),
    'save_contact':       _mk_content_field_saver('contact'),
    'save_details':       _mk_content_field_saver('details'),
    'save_tags':          _save_tags,
    'upload_icon':        _upload_icon,
    'upload_screenshot':  _upload_screenshot,
    'delete_screenshot':  _delete_screenshot,
    'check_editor':       _check_editor,
    'save_editors':       _save_editors,
    'save_authors':       _save_authors,
    'save_release_notes': _save_release_notes,
    'delete_release':     _delete_release,
}

@login_required
@csrf_exempt
def app_page_edit(request, app_name):
    app = get_object_or_404(App, active = True, name = app_name)
    if not app.is_editor(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        action = request.POST.get('action')
        if not action:
            return HttpResponseBadRequest('no action specified')
        if not action in _AppEditActions:
            return HttpResponseBadRequest('action "%s" invalid--must be: %s' % (action, ', '.join(_AppEditActions)))
        try:
            result = _AppEditActions[action](app, request)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        app.save()
        if is_ajax(request):
            return json_response(result)

    # ?platform= picks the platform whose content and releases the page edits (#155)
    platforms = app.platforms
    selected_platform = request.GET.get('platform')
    if selected_platform not in platforms:
        selected_platform = app.primary_platform
    all_tags = [tag.fullname for tag in Tag.objects.all()]
    c = {
        'app': app,
        'content': app.content(selected_platform),
        'platform_chips': [(platform, _PLATFORM_NAMES[platform]) for platform in platforms],
        'selected_platform': selected_platform,
        'selected_platform_name': _PLATFORM_NAMES.get(selected_platform),
        'selected_releases': app.releases_for_display(selected_platform) if selected_platform else [],
        'all_tags': all_tags,
        'max_file_img_size_b': _AppPageEditConfig.max_img_size_b,
        'max_icon_dim_px': _AppPageEditConfig.max_icon_dim_px,
        'thumbnail_height_px': _AppPageEditConfig.thumbnail_height_px,
        'app_description_maxlength': _AppPageEditConfig.app_description_maxlength,
        'release_uploaded': request.GET.get('upload_release') == 'true',
    }
    return html_response('app_page_edit.html', c, request)

#---------------------------SERVICE APPS----------------------------

def _latest_service_release(app):
    releases = app.servicereleases_by_version
    if not releases:
        return None
    return releases[0]

def _service_install_name(app, release):
    # serviceapps install requires the name the service reports in its metadata
    metadata = release.metadata if isinstance(release.metadata, dict) else {}
    return metadata.get('name') or app.fullname

#---------------------------WEB APPS (BUNDLE)----------------------------

def _latest_bundle_release(app):
    releases = app.webbundlereleases
    if not releases:
        return None
    return releases[0]
