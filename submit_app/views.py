from zipfile import ZipFile
from os.path import basename
from urllib.request import urlopen
from urllib.parse import urlparse
import re
import logging
import socket
import ipaddress
import json
import requests
import zipfile
import hashlib
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.storage import storages
from django.shortcuts import get_object_or_404
from django import forms

from util.view_util import html_response, json_response, get_object_or_none, is_ajax
from util.id_util import fullname_to_name
from apps.models import Release, ServiceRelease, WebBundleRelease, App, Author, OrderedAuthor, Platform
from apps.views import _parse_iso_date
from .models import AppPending, ServiceAppPending, WebBundlePending
from .pomparse import PomAttrNames, parse_pom
from .processjar import process_jar

from .servicechecker import check_reachable, ServiceCheckError
from .bundle_storage import _copy_bundle_to_storage, write_manifest_json


from django.views.decorators.csrf import csrf_exempt

LOGGER = logging.getLogger('django')   

LOGGER = logging.getLogger(__name__)


def platform_select(request):
    platforms = [
        ('desktop', 'Cytoscape Desktop App'),
        #('web-url', 'Cytoscape Web - Github/Repo URL'),
        ('web-bundle', 'Cytoscape Web - Bundle File/Manifest'),
        ('service', 'Cytoscape Web - Service App URL'),
    ]
    if request.method == 'POST':
        platform = request.POST.get('platform')
        if not platform:
            return HttpResponseBadRequest('platform is required')

        platform_map = {
            'desktop': 'submit-app',
            'web-url': 'submit-web-url',
            'web-bundle': 'submit-web-bundle',
            'service': 'submit-service-app',
        }
        target = platform_map.get(platform)
        if target:
            return HttpResponseRedirect(reverse(target))

        return HttpResponseRedirect(reverse('submit-app') + '?platform=' + platform)

    context = {
        'platforms' : platforms
    }

    return html_response('platform_select.html', context, request)

def platform_select_help(request):
    return render(request, "platform_select_help.html")

# Presents an app submission form and accepts app submissions.
@login_required
def submit_app(request):
    context = dict()
    if request.method == 'POST':
        expect_app_name = request.POST.get('expect_app_name')
        f = request.FILES.get('file')
        if f:
            try:
                fullname, version, works_with, app_dependencies, has_export_pkg = process_jar(f, expect_app_name)
                pending = _create_pending(request.user, fullname, version, works_with, app_dependencies, f)
                server_url = _get_server_url(request)
                _send_email_for_pending(pending, server_url=server_url)
                version_pattern1 ="^[0-9].[0-9].[0-9]+"
                version_pattern1 = re.compile(version_pattern1)
                version_pattern2 = "^[0-9].[0-9]+"
                version_pattern2 = re.compile(version_pattern2)
                if (bool(version_pattern1.match(version))!=True and bool(version_pattern2.match(version))!=True):
                    raise ValueError("The version is not in proper pattern. It should have 2 order version numbering (e.g: x.y) or 3 order version numbering (e.g: x.y.z)")
                if has_export_pkg:
                    return HttpResponseRedirect(reverse('submit-api', args=[pending.id]))
                else:
                    return HttpResponseRedirect(reverse('confirm-submission', args=[pending.id]))
            except ValueError as e:
                context['error_msg'] = str(e)
    else:
        expect_app_name = request.GET.get('expect_app_name')
        if expect_app_name:
            context['expect_app_name'] = expect_app_name
    return html_response('upload_form.html', context, request)


def _user_cancelled(request, pending):
    pending.delete_files()
    pending.delete()
    return HttpResponseRedirect(reverse('submit-app'))

def _user_accepted(request, pending):
    app = get_object_or_none(App, name = fullname_to_name(pending.fullname))
    if app and app.platform == 'desktop':
        if not app.is_editor(request.user):
            return HttpResponseForbidden('You are not authorized to add releases, because you are not an editor')
        if not app.active:
            app.active = True
            app.save()
        pending.make_release(app)
        pending.delete_files()
        pending.delete()
        return HttpResponseRedirect(reverse('app_page_edit', args=[app.name]) + '?upload_release=true')
    else:
        return html_response('submit_done.html', {'app_name': pending.fullname}, request)


def confirm_submission(request, id):
    """
    Loads AppPending object corresponding to 'id' passed in and
    verifies user is allowed to view this page and if
    the pom.xml file is found it is examined and key attributes
    are returned

    :param request:
    :param id: id of AppPending entry in database
    :return: html response
    """
    pending = get_object_or_404(AppPending, id=int(id))
    if not pending.can_confirm(request.user):
        return HttpResponseForbidden('You are not authorized to view this page')
    action = request.POST.get('action')
    if action:
        if action == 'cancel':
            return _user_cancelled(request, pending)
        elif action == 'accept':
            return _user_accepted(request, pending)
    pom_attrs = None
    if pending.pom_xml_file:
        pending.pom_xml_file.open(mode='r')
        pom_attrs = parse_pom(pending.pom_xml_file)
        pending.pom_xml_file.close()
    return html_response('confirm.html',
                         {'pending': pending,
                          'pom_attrs': pom_attrs},
                         request)


def _create_pending(submitter, fullname, version, cy_works_with,
                    app_dependencies, release_file):
    """
    Creates an AppPending object with information passed in and
    saves it to the database

    :param submitter: User that made request.
    :param fullname: Full name of app
    :type fullname: str
    :param version:
    :type version: str
    :param cy_works_with:
    :type cy_works_with: str
    :param app_dependencies: Release objects
    :type app_dependencies: list
    :param release_file: release jar file
    :type :py:class:`django.core.files.base.File`
    :return: Pending App object
    :rtype :py:class:`submit_app.models.AppPending`
    :raises ValueError: If App already exists and 'submitter' is not allowed
                        to edit. Will also be raised if Release matching name
                        exists that is active.
    """
    name = fullname_to_name(fullname)
    app = get_object_or_none(App, name=name)
    if app:
        if not app.is_editor(submitter):
            raise ValueError('cannot be accepted because you are not '
                             'an editor')
        release = get_object_or_none(Release, app=app, version=version)
        if release and release.active:
            raise ValueError('cannot be accepted because the app %s already'
                             ' has a release with version %s. You can delete '
                             'this version by going to the Release History '
                             'tab in the app edit page' % (app.fullname,
                                                           version))

    pending = AppPending.objects.create(submitter=submitter,
                                        fullname=fullname,
                                        version=version,
                                        cy_works_with=cy_works_with)
    for dependency in app_dependencies:
        pending.dependencies.add(dependency)
    pending.release_file.save(basename(release_file.name), release_file)
    pending.save()
    return pending


def _send_email_for_pending(pending, server_url='Unknown'):
    msg = u"""
The following app has been submitted:
    ID: {id}
    Server: {server_url}
    Name: {fullname}
    Version: {version}
    Submitter: {submitter_name} {submitter_email}
""".format(id=pending.id, server_url=server_url, fullname=pending.fullname,
           version=pending.version, submitter_name=pending.submitter.username,
           submitter_email=pending.submitter.email)
    try:
        send_mail('Cytoscape App Store - App Submitted', msg, settings.EMAIL_ADDR, settings.CONTACT_EMAILS, fail_silently=False)
    except Exception as e:
        LOGGER.exception('Error sending email for pending App')


def _verify_javadocs_jar(file):
    """
    Checks if 'file' passed in is a valid zip file by attempting to load
    it via ZipFile and verify there are no paths that start with / or
    have .. anywhere in the path

    :param file: file like object
    :return: None if 'file' is valid zip file otherwise str with error
    :rtype str
    """
    error_msg = None
    try:
        zip = ZipFile(file, 'r')
        for name in zip.namelist():
            pathpieces = name.split('/')
            if name.startswith('/') or '..' in pathpieces:
                error_msg = 'The zip archive has a file ' \
                            'path that is illegal: %s' % name
                break
        zip.close()
    except Exception:
        error_msg = 'The Javadocs Jar file you submitted is ' \
                    'not a valid jar/zip file'
    return error_msg


def submit_api(request, id):
    pending = get_object_or_404(AppPending, id=int(id))
    if not pending.can_confirm(request.user):
        return HttpResponseForbidden('You are not authorized to view this page')

    error_msg = None

    if request.POST.get('dont_submit') is not None:
        return HttpResponseRedirect(reverse('confirm-submission',
                                            args=[pending.id]))
    if request.POST.get('submit') is not None:
        pom_xml_f = request.FILES.get('pom_xml')
        javadocs_jar_f = request.FILES.get('javadocs_jar')
        if pom_xml_f and javadocs_jar_f:
            try:
                # verify pom.xml file has appropriate attributes
                pom_xml_f.open(mode='r')
                pom_attrs = parse_pom(pom_xml_f)
                if len(pom_attrs) != len(PomAttrNames):
                    error_msg = str(pom_xml_f.name) +\
                                ' is not valid; it must have these ' \
                                'tags under &lt;project&gt;: ' +\
                                ', '.join(PomAttrNames)

                if not error_msg:
                    # no error earlier so check the javadoc jar file
                    javadocs_jar_f.open(mode='r')
                    error_msg = _verify_javadocs_jar(javadocs_jar_f)

                if not error_msg:
                    # success cause we did not get any errors
                    # save the pom.xml and javadoc jar file and
                    # redirect to confirm submission
                    pom_xml_f.open(mode='r')
                    javadocs_jar_f.open(mode='r')
                    pending.pom_xml_file.save(basename(pom_xml_f.name),
                                              pom_xml_f)
                    pending.javadocs_jar_file.save(basename(javadocs_jar_f.name),
                                                   javadocs_jar_f)
                    return HttpResponseRedirect(reverse('confirm-submission',
                                                        args=[pending.id]))
            finally:
                # attempt to close the pom.xml and javadocjar files
                try:
                    pom_xml_f.close()
                except Exception as e:
                    LOGGER.info('Not critical, but caught exception '
                                'attempting to close pom.xml file : ' +
                                str(e))
                try:
                    javadocs_jar_f.close()
                except Exception as e:
                    LOGGER.info('Not critical, but caught exception '
                                'attempting to close javadoc jar file : ' +
                                str(e))

    # If something went wrong, the error is in error_msg
    # otherwise 'submit' was not in POST so nothing changed
    return html_response('submit_api.html',
                         {'pending': pending,
                          'error_msg': error_msg},
                         request)


def _send_email_for_accepted_app(to_email, from_email, app_fullname, app_name, server_url):
    subject = u'Cytoscape App Store - {app_fullname} Has Been Approved'.format(app_fullname = app_fullname)
    app_url = reverse('app_page', args=[app_name])
    msg = u"""Your app has been approved! Here is your app page:

  {server_url}{app_url}

To edit your app page:
 1. Go to {server_url}{app_url}
 2. Sign in as {author_email}
 3. Under the "Editor's Actions" yellow button on the top-right, choose "Edit this page".

Make sure to add some tags to your app and a short app description, which is located
right below the app name. You can also add screenshots, details about your app,
and an icon to make your app distinguishable.

If you would like other people to be able to edit the app page, have them sign in
to the App Store, then add their email addresses to the Editors box, located in
the top-right.

- Cytoscape App Store Team
""".format(app_url = app_url, author_email = to_email, server_url = server_url)
    try:
        send_mail(subject, msg, from_email, (to_email,))
    except Exception as e:
        LOGGER.exception('Error sending email for pending App')


def _get_server_url(request):
    name = request.META['SERVER_NAME']
    port = request.META['SERVER_PORT']
    if port == '80':
        return 'http://%s' % name

    if request.is_secure():
        if port == '443':
            return 'https://' + name
        else:
            prefix = 'https'
    else:
        prefix = 'http'

    return '%s://%s:%s' % (prefix, name, port)

@csrf_exempt
def _pending_app_accept(pending, request):
    name = fullname_to_name(pending.fullname)
    # we always create a new app, because only new apps require accepting
    app = App.objects.create(fullname = pending.fullname, name = name, platform=Platform.DESKTOP)
    app.active = True
    app.editors.add(pending.submitter)
    app.save()

    pending.make_release(app)
    pending.delete_files()
    pending.delete()

    server_url = _get_server_url(request)
    _send_email_for_accepted_app(pending.submitter.email, settings.CONTACT_EMAIL, app.fullname, app.name, server_url)

def _pending_app_decline(pending_app, request):
    pending_app.delete_files()
    pending_app.delete()


@csrf_exempt
def _pending_web_accept(pending, request):
    name = fullname_to_name(pending.fullname)
    # we always create a new app, because only new apps require accepting
    app = App.objects.create(fullname = pending.fullname, name = name, platform=Platform.WEB)
    app.active = True
    app.editors.add(pending.submitter)
    app.save()  

    try:
        pending.make_bundle_release(app)
    except Exception as e:
        print(e)
        raise  # re-raise so you still see it fail — just now with a full traceback in the console

    pending.delete_files()
    pending.delete()

    server_url = _get_server_url(request)
    #_send_email_for_accepted_app(pending.submitter.email, settings.CONTACT_EMAIL, app.fullname, app.name, server_url)

def _pending_service_accept(pending, request):
    name = fullname_to_name(pending.fullname)
    app = App.objects.create(fullname = pending.fullname, name = name, platform=Platform.SERVICE)
    app.active = True
    app.editors.add(pending.submitter)
    app.save()

    pending.make_service_release(app)
    submitter_email = pending.submitter.email
    pending.delete()

    server_url = _get_server_url(request)
    _send_email_for_accepted_app(submitter_email, settings.CONTACT_EMAIL, app.fullname, app.name, server_url)

def _pending_service_decline(pending_app, request):
    pending_app.delete()


def _pending_instance_decline(pending_app, request):
    if isinstance(pending_app, AppPending):
        return _pending_app_decline(pending_app, request)
    if isinstance(pending_app, ServiceAppPending):
        return _pending_service_decline(pending_app, request)
    if isinstance(pending_app, WebBundlePending):
        return _pending_app_decline(pending_app, request)

def _pending_instance_accept(pending_app, request):
    if isinstance(pending_app, AppPending):
        return _pending_app_accept(pending_app, request)
    if isinstance(pending_app, ServiceAppPending):
        return _pending_service_accept(pending_app, request)
    if isinstance(pending_app, WebBundlePending):
        return _pending_web_accept(pending_app, request)

_PendingAppsActions = {
    'accept': _pending_instance_accept,
    'decline': _pending_instance_decline,
}

@login_required
@csrf_exempt
def pending_apps(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if not action:
            return HttpResponseBadRequest('action must be specified')
        if not action in _PendingAppsActions:
            return HttpResponseBadRequest('invalid action--must be: %s' % ', '.join(_PendingAppsActions.keys()))
        pending_id = request.POST.get('pending_id')
        pending_platform = request.POST.get('pending_platform')
        if not pending_id:
            return HttpResponseBadRequest('pending_id must be specified')
        try:
            pending_id = int(pending_id)
        except ValueError:
            return HttpResponseBadRequest('invalid pending_id')

        platform_map = {
            'desktop' : AppPending,
            'service' : ServiceAppPending,
            'web-bundle': WebBundlePending,
        } 

        model = platform_map.get(pending_platform)
        if model is None:
            return HttpResponseBadRequest(f'invalid platform: {pending_platform}')

        pending_app = model.objects.filter(id=pending_id).first()
        if pending_app is None:
            return HttpResponseBadRequest('invalid pending_id')
        
        result = _PendingAppsActions[action](pending_app, request)
        if is_ajax(request):
            return json_response(True)

        if isinstance(result, HttpResponse):
            return result

        return HttpResponseRedirect(reverse('pending-apps'))

    pending_apps = AppPending.objects.all()
    pending_service = ServiceAppPending.objects.all()
    pending_web_bundle = WebBundlePending.objects.all()
    return html_response('pending_apps.html', {'pending_apps': pending_apps, 'pending_service': pending_service, 'pending_web_bundle': pending_web_bundle}, request)

AppRepoUrl = 'http://code.cytoscape.org/nexus/content/repositories/apps'

def _get_deploy_url(groupId, artifactId, version):
    return '/'.join((AppRepoUrl, groupId.replace('.', '/'), artifactId, version))

def _url_exists(url):
    try:
        reader = urlopen(url)
        if reader.getcode() == 200:
            return True
    except:
        pass
    return False

@csrf_exempt
def artifact_exists(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('no data')
    postLookup = request.POST.get
    groupId, artifactId, version = postLookup('groupId'), postLookup('artifactId'), postLookup('version')
    if not groupId or not artifactId or not version:
        return HttpResponseBadRequest('groupId, artifactId, or version not specified')
    deployUrl = _get_deploy_url(groupId, artifactId, version)
    return json_response(_url_exists(deployUrl))

#
# 2.x plugin management page
#

_PluginXmlUrl = 'http://chianti.ucsd.edu/cyto_web/plugins/plugins.xml'
def _forward_plugins_xml(request_post):
    try:
        reader = urlopen(_PluginXmlUrl)
        if reader.getcode() != 200:
            raise Error('retrieve failed')
        r = HttpResponse(content_type = 'application/xml')
        r.write(reader.read())
        return r
    except:
        return HttpResponse('Unable to retrieve: %s' % PluginXmlUrl, content_type='text/plain', status=503)

def _app_info(request_post):
    fullname = request_post.get('app_fullname')
    name = fullname_to_name(fullname)
    url = reverse('app_page', args=(name,))
    exists = App.objects.filter(name = name, active = True).count() > 0
    return json_response({'url': url, 'exists': exists})

def _update_app_page(request_post):
    fullname = request_post.get('fullname')
    if not fullname:
        return HttpResponseBadRequest('"fullname" not specified')
    name = fullname_to_name(fullname)
    app = get_object_or_none(App, name = name)
    if app:
        app.active = True
    else:
        app = App.objects.create(name = name, fullname = fullname)

    details = request_post.get('details')
    if details:
        app.details = details

    cy2x_plugin_download = request_post.get('cy2x_plugin_download')
    if cy2x_plugin_download:
        app.cy_2x_plugin_download = cy2x_plugin_download

    cy2x_plugin_version = request_post.get('cy2x_plugin_version')
    if cy2x_plugin_download:
        app.cy_2x_plugin_version = cy2x_plugin_version

    cy_versions = request_post.get('cy_versions')
    if cy2x_plugin_download:
        app.cy_2x_versions = cy_versions

    release_date = request_post.get('release_date')
    if cy2x_plugin_download:
        app.cy_2x_plugin_release_date = _parse_iso_date(release_date)

    author_count = request_post.get('author_count')
    if author_count:
        author_count = int(author_count)
        for i in range(author_count):
            name = request_post.get('author_' + str(i))
            if not name:
                return HttpResponseBadRequest('no such author at index ' + str(i))
            institution = request_post.get('institution_' + str(i))
            author, _ = Author.objects.get_or_create(name = name, institution = institution)
            author_order = OrderedAuthor.objects.create(app = app, author = author, author_order = i)

    app.save()
    return json_response(True)

_Cy2xPluginsActions = {
    'plugins_xml': _forward_plugins_xml,
    'app_info': _app_info,
    'update': _update_app_page,}

@login_required
def cy2x_plugins(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if not action:
            return HttpResponseBadRequest('action must be specified')
        if not action in _Cy2xPluginsActions:
            return HttpResponseBadRequest('invalid action--must be: %s' % ', '.join(_Cy2xPluginsActions.keys()))
        return _Cy2xPluginsActions[action](request.POST)
    else:
        return html_response('cy2x_plugins.html', {}, request)


#---------------------- SERVICE APP SUBMISSION ----------------------
@login_required
def submit_service_app(request):
    LOGGER.info("submit_service_app called, method=%s POST=%s", request.method, dict(request.POST))
    context = {}

    if request.method != 'POST':
        return html_response('service_upload_form.html', context, request)
    
    service_url = request.POST.get('service-url')

    if not service_url:
        context['error'] = "Service URL is required"
        return html_response('service_upload_form.html', context, request)

    try:
        metadata = check_reachable(service_url)
    except ServiceCheckError as e:
        LOGGER.info("submit_service_app service check error: %s", e)
        context['error'] = str(e)
        return html_response('service_upload_form.html', context, request)
    except Exception as e:
        context['error'] = 'Error fetching server metadata: %s' % str(e)
        return html_response('service_upload_form.html', context, request)

    fullname = metadata.get('name', '')
    version = metadata.get('version', '')
    author = metadata.get('author', '')
    name = fullname_to_name(fullname)

    if version and not re.match(r'^\d+\.\d+(\.\d+)?$', version):
        context['error'] = "Version must does not match required pattern. It should have 2 order version numbering (e.g: x.y) or 3 order version numbering (e.g: x.y.z)"
        return html_response('service_upload_form.html', context, request)


    existing = get_object_or_none(App, name=name)
    if existing and not existing.is_editor(request.user):
        context['error'] = 'An app with that name already exists and you are not an editor'
        return html_response('service_upload_form.html', context, request)

    if ServiceAppPending.objects.filter(name=name).exists():
        context['error'] = 'A submission with that name is already pending review. Please wait for review or contact support.'
        return html_response('service_upload_form.html', context, request)

    try:
        pending = ServiceAppPending.objects.create(
        submitter=request.user,
        fullname=fullname,
        author = author,
        version=version,
        service_endpoint=service_url,
        metadata=metadata,
        name=name
        )

    except IntegrityError:
        context['error'] = 'A submission with that name is already pending review. Please wait for review.'
        return html_response('service_upload_form.html', context, request)

    """
    try:
        pending = _create_pending_service(request.user, fullname, version, service_url, metadata)
    except ValueError as e:
        context['error'] = str(e)
        LOGGER.info("Created ServiceAppPending id=%s fullname=%r", pending.id, pending.fullname)
        return html_response('service_upload_form.html', context, request)
    """

    return HttpResponseRedirect(reverse('confirm-service', args=[pending.id])) 

def _service_user_cancel(request, pending):
    pending.delete()
    return HttpResponseRedirect(reverse('submit-service-app'))

def _service_user_accepted(request, pending):
    app = get_object_or_none(App, name = fullname_to_name(pending.fullname))
    if app and app.platform == 'service':
        if not app.is_editor(request.user):
            return HttpResponseForbidden('You are not authorized to make changes or add new releases to this app')
        if not app.active:
            app.active = True
            app.save()
           
        pending.delete()
        return HttpResponseRedirect(reverse('app_page_edit', args=[app.name]) + '?upload_release=true')
    else:
        app_name = pending.fullname
        #pending.delete()
        return html_response('submit_done.html', {'app_name': app_name}, request)

def service_app_confirm(request, id):
    pending = get_object_or_404(ServiceAppPending, id=int(id))

    if not (request.user.is_staff or request.user == pending.submitter):
        return HttpResponseForbidden('You are not authorized to view this page')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action:
            if action == 'cancel':
                return _service_user_cancel(request, pending)
            elif action == 'accept':
                pending.status = ServiceAppPending.Status.PENDING_CHECKER
                pending.save()
                return  _service_user_accepted(request, pending)
                

    return html_response('confirm_service.html', {'pending': pending}, request)

#---------------------- WEB APP URL SUBMISSION ----------------------
"""
def classify_ref(value):
    if re.match(r'^[0-9a-f]{40}$', value):
        return 'full-sha'
    elif re.match(r'[0-9a-f]{7,39}$', value):
        return 'short-sha'
    elif re.match(r'^[\w\.\-]+$', value):
        return 'tag_or_branch'
    else:
        return 'invalid'

@login_required
def submit_web_url(request):
    context = {}
    if request.method == 'POST':
        #url = request.POST.get('url')
        form = web_submission_form(request.POST, request.FILES)
        if form.is_valid():
            repo_url = form.cleaned_data['repo_url']
            commit_ref = form.cleaned_data['commit_ref']
            app_version = form.cleaned_data['app_version']
            app_store_json = form.cleaned_data['app_store_json']

            try:
                resolved_commit = resolve_commit_ref(repo_url, commit_ref)
            except ValueError as e:
                form.add_error('ref', str(e))
                return html_response('web_url_upload_form.html', {'form': form}, request)

            ref_type = classify_ref(commit_ref)
            if ref_type == "full_sha" and resolved_commit != commit_ref:
                form.add_error('commit_ref', f"The provided commit SHA does not match the resolved commit SHA. Please Retry.")
                return html_response('web_url_upload_form.html', {'form': form}, request)

    else:
        form = web_submission_form(request.POST, request.FILES)

    return html_response('web_url_upload_form.html', {'form': form}, request)


class web_submission_form(forms.Form):
    repo_url = forms.URLField(label='Web App Github URL*', required=True, error_messages={'required': ''}, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/user/repo'}))
    commit_ref = forms.CharField(label="Commit Reference/Tag*", required=True, error_messages={'required': ''},  help_text="A commit SHA is preferred for reproducibility. Tags and branches will be resolved to their current commit SHA at submission time.",widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'v1.2.0, main, or a1b2c3d...'}))
    app_version = forms.CharField(label="App Version*", required=True, error_messages={'required': ''}, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0.0'}))
    app_store_json = forms.FileField(label="app-store.json File", required=False,  widget=forms.FileInput(attrs={'class': 'form-control-file'}))


def resolve_commit_ref(repo_url, commit_ref):

    repo_path = urlparse(repo_url)
    if repo_path.hostname not in ['github.com', 'www.github.com']:
        raise ValueError("Only GitHub URLs are supported.")

    url_segments = repo_path.path.strip('/').split('/')

    if len(url_segments) < 2:
        raise ValueError("Invalid GitHub repository URL.")

    owner, repo = url_segments[0], url_segments[1].removesuffix('.git')

    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_ref}", timeout=10)

    if response.status_code != 200:
        if response.status_code == 404:
            raise ValueError(f"Commit reference '{commit_ref}' not found in the repository.")
        elif response.status_code == 403:
            raise ValueError("Repository if private or inaccessable. Please check your access permissions.")
        else:
            raise ValueError(f"Failed to fetch commit information. Status code: {response.status_code}")
    response.raise_for_status()

    return response.json().get('sha')
"""
        


#---------------------- WEB APP BUNDLE SUBMISSION ----------------------
@login_required
def submit_web_bundle(request):
    if request.method != "POST":
        form = web_bundle_submission()
        return html_response('web_bundle_upload_form.html', {'form': form}, request)

    form = web_bundle_submission(request.POST, request.FILES)
    if not form.is_valid():
        return html_response('web_bundle_upload_form.html', {'form': form}, request)

    bundle = form.cleaned_data['bundle']

    try:
        _validate_bundle(bundle)
    except ValidationError as e:
        form.add_error(None, str(e))
        return html_response('web_bundle_upload_form.html', {'form': form}, request)

    pending = _create_web_bundle_pending(form, bundle, request.user)

    return HttpResponseRedirect(reverse('confirm-web-bundle', args=[pending.id]))
    

class web_bundle_submission(forms.Form):
    bundle = forms.FileField(label="*Web App Bundle File (.zip)", required=True, error_messages={'required': ''}, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    #remote_entry = forms.FileField(label="*Web App Bundle File (remoteEntry.js)", required=True, error_messages={'required': ''}, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    app_fullname = forms.CharField(label="*App Name", required=True, error_messages={'required': ''}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    version = forms.CharField(label="*Version", required=True, error_messages={'required': ''}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    authors = forms.CharField(label="*Author(s)", required=True, error_messages={'required': ''}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label="App Description", required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}))
    license = forms.CharField(label="license", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tags = forms.CharField(label="Tags", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        return [
            tag.strip()
            for tag in tags.split(',')
            if tag.strip()
        ]


def _validate_bundle(bundle):
    max_bundle_size = 50 * 1024 * 1024  
    if bundle.size > max_bundle_size:
        raise ValidationError(f"Bundle file size exceeds the maximum limit of {max_bundle_size / (1024 * 1024)} MB.")

    if not bundle.name.endswith('.zip'):
        raise ValidationError("Bundle file must be a .zip file.")

    try:
        with zipfile.ZipFile(bundle) as zf:
            names = zf.namelist()

            for name in names:
                if name.startswith('/') or '..' in name.split('/'):
                    raise ValidationError(f"Bundle file contains an unsafe path: {name}")
                
            if not any(n.endswith('remoteEntry.js') for n in names):
                raise ValidationError("Bundle file must contain a remoteEntry.js file.")

    except zipfile.BadZipFile:
        raise ValidationError("Bundle file is not a valid zip file.")

    finally:
        bundle.seek(0)  # Reset the file pointer to the beginning of the file

def _bundle_user_cancelled(request, pending):
    pending.delete_files()
    pending.delete()
    return HttpResponseRedirect(reverse('submit-web-bundle'))

def _bundle_user_accepted(request, pending):
    app = get_object_or_none(App, name = fullname_to_name(pending.fullname))
    print(app)
    if app and app.platform == 'web':
        if not app.is_editor(request.user):
            return HttpResponseForbidden('You are not authorized to make changes or add new releases to this app')
        if not app.active:
            app.active = True
            app.save()
            print(app)

        pending.delete_files()
        pending.delete()
        return HttpResponseRedirect(reverse('app_page_edit', args=[app.name]) + '?upload_release=true')
    else:
        app_name = pending.fullname
        print(app)
        return html_response('submit_done.html', {'app_name': app_name}, request)

def confirm_web_bundle(request, id):
    pending = get_object_or_404(WebBundlePending, id = int(id))
    if not (request.user.is_staff or request.user == pending.submitter):
        return HttpResponseForbidden('You are not authorized to view this page')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'cancel':
            return _bundle_user_cancelled(request, pending)
        elif action == 'accept':
            pending.status = WebBundlePending.Status.PENDING_REVIEW
            pending.save()
            return _bundle_user_accepted(request, pending)

    return html_response("confirm_web_bundle.html", {'pending':pending}, request)


def _hash_file(file) -> str:
    bundle_sha = hashlib.sha256()
    file.seek(0) #go back to start of file
    for chunk in file.chunks():
        bundle_sha.update(chunk)
    file.seek(0)
    return bundle_sha.hexdigest()

def _create_web_bundle_pending(form, bundle, submitter) -> WebBundlePending:
    pending = WebBundlePending(
        submitter=submitter,
        fullname=form.cleaned_data['app_fullname'],
        version=form.cleaned_data['version'],
        author=form.cleaned_data['authors'],
        description=form.cleaned_data['description'],
        license=form.cleaned_data['license'],        
        tags=form.cleaned_data['tags'],
        bundle = bundle,
        bundle_hash=_hash_file(bundle),
        #bundle_file=bundle_file,
        #bundle_hash=_hash_file(bundle_file),
        status=WebBundlePending.Status.PENDING_REVIEW, #CHANGE TO PENDING_AUTOMATED_CHECKS ONCE IMPLEMENTED
    )

    pending.save()

    _copy_bundle_to_storage(bundle, pending.bundle_path)

    return pending

def publish_web_bundle(pending: WebBundlePending) -> WebBundleRelease:
    name = fullname_to_name(pending.fullname)
    app, _ = App.objects.get_or_create(
        name = name,
        defaults = {'fullname': pending.fullname, 'platform': Platform.WEB}
    )

    return pending.make_bundle_release(app)
