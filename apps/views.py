import re
import datetime
from urllib.parse import unquote
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.text import unescape_entities
from util.view_util import json_response, html_response, obj_to_dict, get_object_or_none
from util.img_util import scale_img
from util.id_util import fullname_to_name
from apps.models import Tag, App, Author, OrderedAuthor, Screenshot, Release

# Returns a unicode string encoded in a cookie
def _unescape_and_unquote(s):
	if not s: return s
	return unescape_entities(unquote(s))

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
	try:
		tag = get_object_or_404(Tag, name = 'collections')
		idx = sorted_tags.index(tag)
		sorted_tags.pop(idx)
		sorted_tags.insert(0, tag)
	except Http404:
    		idx = 0
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
	apps = App.objects.filter(active=True).order_by('name')
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
	apps = App.objects.filter(active = True, tags = tag).order_by('name')
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
	releases = app.releases
	if not releases: return None
	return releases[0] # go by the ordering provided by Release.Meta

def _mk_app_page(app, user, request):
	c = {
		'app': app,
		'is_editor': (user and app.is_editor(user)),
		'cy3_latest_release': _latest_release(app),
		'go_back_to_title': _unescape_and_unquote(request.COOKIES.get('go_back_to_title')),
		'go_back_to_url':   _unescape_and_unquote(request.COOKIES.get('go_back_to_url')),
	}
	return html_response('app_page.html', c, request)

_AppActions = {
	'rate':                _app_rate,
	'ratings_delete_all':  _app_ratings_delete_all,
}


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
		if request.is_ajax():
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

	app.tags.clear()
	for tag in tags:
		tag_obj, _ = Tag.objects.get_or_create(fullname = tag, name = fullname_to_name(tag))
		app.tags.add(tag_obj)

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
	f = scale_img(f, f.name, _AppPageEditConfig.max_icon_dim_px, 'both')
	app.icon.save(f.name, f)

def _upload_screenshot(app, request):
	screenshot_f = request.FILES.get('file')
	if not screenshot_f:
		raise ValueError('no file submitted')
	if screenshot_f.size > _AppPageEditConfig.max_img_size_b:
		raise ValueError('image file is %d bytes but can be at most %d bytes' % (screenshot_f.size, _AppPageEditConfig.max_img_size_b))
	thumbnail_f = scale_img(screenshot_f, screenshot_f.name, _AppPageEditConfig.thumbnail_height_px, 'h')
	screenshot = Screenshot.objects.create(app = app)
	screenshot.screenshot.save(screenshot_f.name, screenshot_f)
	screenshot.thumbnail.save(thumbnail_f.name, thumbnail_f)
	screenshot.save()

def _delete_screenshot(app, request):
	screenshot_id = request.POST.get('screenshot_id')
	if not screenshot_id:
		raise ValueError('no screenshot_id specified')

	try:
		screenshot_id = int(screenshot_id)
		screenshot = Screenshot.objects.get(id = screenshot_id)
	except (ValueError, Screenshot.DoesNotExist) as e:
		raise ValueError('invalid screenshot_id')
	screenshot.delete()

def _check_editor(app, request):
	editor_email = request.POST.get('editor_email')
	if not editor_email:
		raise ValueError('no editor_email specified')
	user = get_object_or_none(User, email=editor_email).last()
	return user.username if user else False

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

	app.authors.clear()
	for name, institution, author_order in authors:
		author, _ = Author.objects.get_or_create(name = name, institution = institution)
		ordered_author = OrderedAuthor.objects.create(app = app, author = author, author_order = author_order)

def _save_release_notes(app, request):
	release_count = request.POST.get('release_count')
	if not release_count:
		raise ValueError('no release_count specified')
	try:
		release_count = int(release_count)
	except ValueError:
		raise ValueError('release_count is not an integer')

	for i in range(release_count):
		key = 'release_id_' + str(i)
		release_id = request.POST.get(key)
		if not release_id:
			raise ValueError('expected ' + key)
		try:
			release = Release.objects.get(id = int(release_id))
		except (Release.DoesNotExist, ValueError) as e:
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

	for i in range(release_count):
		key = 'release_id_' + str(i)
		release_id = request.POST.get(key)
		if not release_id:
			raise ValueError('expected ' + key)
		try:
			release = Release.objects.get(id = int(release_id))
		except (Release.DoesNotExist, ValueError) as e:
			raise ValueError('release_id "%s" is invalid' % release_id)
		release.active = False
		release.save()
	app.update_has_releases()

_AppEditActions = {
	'save_cy_2x_plugin_download':     _mk_basic_field_saver('cy_2x_plugin_download'),
	'save_cy_2x_plugin_version':      _mk_basic_field_saver('cy_2x_plugin_version'),
	'save_cy_2x_plugin_release_date': _mk_basic_field_saver('cy_2x_plugin_release_date', func=_parse_iso_date),
	'save_cy_2x_versions':            _mk_basic_field_saver('cy_2x_versions'),
	'save_description':   _mk_basic_field_saver('description'),
	'save_license_text':  _mk_basic_field_saver('license_text'),
	'save_license_confirm':  _mk_basic_field_saver('license_confirm', func = lambda s: s.lower() == 'true'),
	'save_website':       _mk_basic_field_saver('website'),
	'save_tutorial':      _mk_basic_field_saver('tutorial'),
	'save_citation':      _mk_basic_field_saver('citation'),
	'save_coderepo':      _mk_basic_field_saver('coderepo'),
        'save_automation':  _mk_basic_field_saver('automation'),
	'save_contact':       _mk_basic_field_saver('contact'),
	'save_details':       _mk_basic_field_saver('details'),
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
		if request.is_ajax():
			return json_response(result)

	all_tags = [tag.fullname for tag in Tag.objects.all()]
	c = {
		'app': app,
		'all_tags': all_tags,
		'max_file_img_size_b': _AppPageEditConfig.max_img_size_b,
		'max_icon_dim_px': _AppPageEditConfig.max_icon_dim_px,
		'thumbnail_height_px': _AppPageEditConfig.thumbnail_height_px,
		'app_description_maxlength': _AppPageEditConfig.app_description_maxlength,
        'release_uploaded': request.GET.get('upload_release') == 'true',
	}
	return html_response('app_page_edit.html', c, request)
