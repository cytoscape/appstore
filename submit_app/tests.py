"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os
import zipfile
import io
import tempfile
import shutil

import json

from unittest.mock import MagicMock, patch
from django.core import mail
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.staticfiles import finders

from django.conf import settings
from django.core.files.storage import storages

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.http import HttpRequest
from django.contrib.auth.models import User
from apps.models import App
from apps.models import Platform
from apps.models import Release
from apps.models import WebBundleRelease
from apps.models import ServiceRelease
from submit_app.models import AppPending
from submit_app.models import ServiceAppPending
from submit_app.models import WebBundlePending
from submit_app.models import WebUrlPending
from submit_app import bundle_storage
from submit_app import models as submit_models
from util.id_util import fullname_to_name
from submit_app import processjar
from submit_app import mfparse
from submit_app import views
from submit_app import pomparse


TEST_VALID_MANIFEST_ONE = b'Manifest-Version: 1.0\r\nBnd-LastModified: 1592239529972\r\nBuild-Jdk: 11.0.4\r\nBuilt-By: churas\r\nBundle-Activator: org.cytoscape.app.communitydetection.CyActivator\r\nBundle-ClassPath: .,httpclient-4.5.9.jar,httpcore-4.4.11.jar,commons-l\r\n ogging-1.2.jar,commons-codec-1.11.jar,httpmime-4.5.9.jar,gson-2.8.5.j\r\n ar,communitydetection-rest-model-0.8.1.jar,swagger-annotations-2.0.0.\r\n jar,logback-classic-1.2.3.jar,logback-core-1.2.3.jar,slf4j-api-1.7.25\r\n .jar,jackson-databind-2.10.1.jar,jackson-annotations-2.10.1.jar,jacks\r\n on-core-2.10.1.jar,jackson-jaxrs-base-2.10.1.jar,ndex-object-model-2.\r\n 5.0-20200508.163437-2.jar\r\nBundle-ManifestVersion: 2\r\nBundle-Name: CyCommunityDetectionTest\r\nBundle-SymbolicName: org.cytoscape.app.communitydetection\r\nBundle-Version: 1.11.0\r\nCreated-By: Apache Maven Bundle Plugin\r\nEmbed-Dependency: *;scope=!provided|test;groupId=!org.cytoscape\r\nEmbed-Transitive: true\r\nEmbedded-Artifacts: httpclient-4.5.9.jar;g="org.apache.httpcomponents"\r\n ;a="httpclient";v="4.5.9",httpcore-4.4.11.jar;g="org.apache.httpcompo\r\n nents";a="httpcore";v="4.4.11",commons-logging-1.2.jar;g="commons-log\r\n ging";a="commons-logging";v="1.2",commons-codec-1.11.jar;g="commons-c\r\n odec";a="commons-codec";v="1.11",httpmime-4.5.9.jar;g="org.apache.htt\r\n pcomponents";a="httpmime";v="4.5.9",gson-2.8.5.jar;g="com.google.code\r\n .gson";a="gson";v="2.8.5",communitydetection-rest-model-0.8.1.jar;g="\r\n org.ndexbio.communitydetection.rest.model";a="communitydetection-rest\r\n -model";v="0.8.1",swagger-annotations-2.0.0.jar;g="io.swagger.core.v3\r\n ";a="swagger-annotations";v="2.0.0",logback-classic-1.2.3.jar;g="ch.q\r\n os.logback";a="logback-classic";v="1.2.3",logback-core-1.2.3.jar;g="c\r\n h.qos.logback";a="logback-core";v="1.2.3",slf4j-api-1.7.25.jar;g="org\r\n .slf4j";a="slf4j-api";v="1.7.25",jackson-databind-2.10.1.jar;g="com.f\r\n asterxml.jackson.core";a="jackson-databind";v="2.10.1",jackson-annota\r\n tions-2.10.1.jar;g="com.fasterxml.jackson.core";a="jackson-annotation\r\n s";v="2.10.1",jackson-core-2.10.1.jar;g="com.fasterxml.jackson.core";\r\n a="jackson-core";v="2.10.1",jackson-jaxrs-base-2.10.1.jar;g="com.fast\r\n erxml.jackson.jaxrs";a="jackson-jaxrs-base";v="2.10.1",ndex-object-mo\r\n del-2.5.0-20200508.163437-2.jar;g="org.ndexbio";a="ndex-object-model"\r\n ;v="2.5.0-SNAPSHOT"\r\nExport-Package: org.cytoscape.app.communitydetection.subnetwork;uses:=\r\n "javax.swing,org.cytoscape.app.communitydetection.util,org.cytoscape.\r\n application.swing,org.cytoscape.model,org.cytoscape.model.subnetwork,\r\n org.cytoscape.session,org.cytoscape.task,org.cytoscape.view.layout,or\r\n g.cytoscape.view.model,org.cytoscape.view.vizmap,org.cytoscape.work";\r\n version="1.11.0",org.cytoscape.app.communitydetection.hierarchy;uses:\r\n ="javax.swing,org.cytoscape.app.communitydetection.cx2,org.cytoscape.\r\n app.communitydetection.edgelist,org.cytoscape.app.communitydetection.\r\n event,org.cytoscape.app.communitydetection.rest,org.cytoscape.app.com\r\n munitydetection.util,org.cytoscape.application.swing,org.cytoscape.mo\r\n del,org.cytoscape.model.subnetwork,org.cytoscape.session,org.cytoscap\r\n e.task,org.cytoscape.task.read,org.cytoscape.view.layout,org.cytoscap\r\n e.view.model,org.cytoscape.view.vizmap,org.cytoscape.work";version="1\r\n .11.0",org.cytoscape.app.communitydetection.util;uses:="javax.swing,o\r\n rg.cytoscape.model";version="1.11.0",org.cytoscape.app.communitydetec\r\n tion.cx2;version="1.11.0",org.cytoscape.app.communitydetection;uses:=\r\n "javax.swing,org.cytoscape.app.communitydetection.event,org.cytoscape\r\n .app.communitydetection.hierarchy,org.cytoscape.app.communitydetectio\r\n n.util,org.cytoscape.application.swing,org.cytoscape.model,org.cytosc\r\n ape.property,org.cytoscape.service.util,org.cytoscape.task,org.cytosc\r\n ape.work,org.osgi.framework";version="1.11.0",org.cytoscape.app.commu\r\n nitydetection.iquery;uses:="org.cytoscape.app.communitydetection.util\r\n ,org.cytoscape.application.swing,org.cytoscape.model,org.cytoscape.ta\r\n sk,org.cytoscape.view.model,org.cytoscape.work";version="1.11.0",org.\r\n cytoscape.app.communitydetection.termmap;uses:="org.cytoscape.app.com\r\n munitydetection.hierarchy,org.cytoscape.application.swing,org.cytosca\r\n pe.model,org.cytoscape.task,org.cytoscape.view.model,org.cytoscape.wo\r\n rk";version="1.11.0",org.cytoscape.app.communitydetection.edgelist;us\r\n es:="org.cytoscape.io.write,org.cytoscape.model,org.cytoscape.work";v\r\n ersion="1.11.0",org.cytoscape.app.communitydetection.event;version="1\r\n .11.0",org.cytoscape.app.communitydetection.rest;uses:="org.cytoscape\r\n .work";version="1.11.0"\r\nImport-Package: groovy.lang;resolution:=optional,javax.crypto;resoluti\r\n on:=optional,javax.crypto.spec;resolution:=optional,javax.mail;resolu\r\n tion:=optional,javax.mail.internet;resolution:=optional,javax.managem\r\n ent;resolution:=optional,javax.naming;resolution:=optional,javax.nami\r\n ng.directory;resolution:=optional,javax.naming.ldap;resolution:=optio\r\n nal,javax.net;resolution:=optional,javax.net.ssl;resolution:=optional\r\n ,javax.security.auth.x500;resolution:=optional,javax.servlet;resoluti\r\n on:=optional,javax.servlet.http;resolution:=optional,javax.sql;resolu\r\n tion:=optional,javax.swing;resolution:=optional,javax.swing.border;re\r\n solution:=optional,javax.swing.event;resolution:=optional,javax.ws.rs\r\n .core;resolution:=optional,javax.ws.rs.ext;resolution:=optional,javax\r\n .xml.datatype;resolution:=optional,javax.xml.namespace;resolution:=op\r\n tional,javax.xml.parsers;resolution:=optional,javax.xml.stream;resolu\r\n tion:=optional,javax.xml.stream.events;resolution:=optional,org.apach\r\n e.avalon.framework.logger;resolution:=optional;version="[4.3,5)",org.\r\n apache.log;resolution:=optional,org.apache.log4j;resolution:=optional\r\n ;version="[1.2,2)",org.codehaus.commons.compiler;resolution:=optional\r\n ,org.codehaus.groovy.control;resolution:=optional,org.codehaus.groovy\r\n .control.customizers;resolution:=optional,org.codehaus.groovy.reflect\r\n ion;resolution:=optional,org.codehaus.groovy.runtime;resolution:=opti\r\n onal,org.codehaus.groovy.runtime.callsite;resolution:=optional,org.co\r\n dehaus.groovy.runtime.typehandling;resolution:=optional,org.codehaus.\r\n groovy.runtime.wrappers;resolution:=optional,org.codehaus.groovy.tran\r\n sform;resolution:=optional,org.codehaus.janino;resolution:=optional,o\r\n rg.cytoscape.app.communitydetection.event;resolution:=optional,org.cy\r\n toscape.application.swing;resolution:=optional;version="[3.7,4)",org.\r\n cytoscape.io.write;resolution:=optional;version="[3.7,4)",org.cytosca\r\n pe.model;resolution:=optional;version="[3.7,4)",org.cytoscape.model.s\r\n ubnetwork;resolution:=optional;version="[3.7,4)",org.cytoscape.proper\r\n ty;resolution:=optional;version="[3.7,4)",org.cytoscape.service.util;\r\n resolution:=optional;version="[3.7,4)",org.cytoscape.session;resoluti\r\n on:=optional;version="[3.7,4)",org.cytoscape.task;resolution:=optiona\r\n l;version="[3.7,4)",org.cytoscape.task.read;resolution:=optional;vers\r\n ion="[3.7,4)",org.cytoscape.view.layout;resolution:=optional;version=\r\n "[3.7,4)",org.cytoscape.view.model;resolution:=optional;version="[3.7\r\n ,4)",org.cytoscape.view.vizmap;resolution:=optional;version="[3.7,4)"\r\n ,org.cytoscape.work;resolution:=optional;version="[3.7,4)",org.ietf.j\r\n gss;resolution:=optional,org.osgi.framework;resolution:=optional;vers\r\n ion="[1.8,2)",org.w3c.dom;resolution:=optional,org.w3c.dom.bootstrap;\r\n resolution:=optional,org.w3c.dom.ls;resolution:=optional,org.xml.sax;\r\n resolution:=optional,org.xml.sax.helpers;resolution:=optional,sun.mis\r\n c;resolution:=optional,sun.reflect;resolution:=optional\r\nRequire-Capability: osgi.ee;filter:="(&(osgi.ee=JavaSE)(version=1.8))"\r\nTool: Bnd-4.2.0.201903051501\r\n\r\n'


def clear_media_root():
    shutil.rmtree(settings.MEDIA_ROOT)
    os.makedirs(settings.MEDIA_ROOT, mode=0o755)


class ViewsTest(TestCase):

    def setUp(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def test_create_pending_app_not_found(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                          is_superuser=True)
        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)

        self.assertEqual(userobj, pending.submitter)
        self.assertEqual('SomeApp', pending.fullname)
        self.assertEqual('1.0.0', pending.version)

    def test_create_pending_user_not_editor(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                          is_superuser=False)
        userobj.save()
        appobj = App.objects.create(name='someapp', fullname='SomeApp',
                                    active=True)
        appobj.save()
        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        try:
            views._create_pending(userobj, 'SomeApp', '1.0.0',
                                  'workswith', [], jarfile)
        except ValueError as ve:
            self.assertEqual('cannot be accepted because '
                             'you are not an editor', str(ve))

    def test_create_pending_existing_release(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                          is_superuser=True)
        userobj.save()
        appobj = App.objects.create(name='someapp', fullname='SomeApp',
                                    active=True)
        appobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')

        myrel = Release.objects.create(app=appobj,
                                       version='1.0.0',
                                       release_file=jarfile,
                                       active=True)
        myrel.save()
        try:
            views._create_pending(userobj, 'SomeApp', '1.0.0',
                                  'workswith', [], jarfile)
        except ValueError as ve:
            self.assertEqual('cannot be accepted because the '
                             'app SomeApp already has a release '
                             'with version 1.0.0. You can delete '
                             'this version by going to the Release '
                             'History tab in the app edit page', str(ve))

    def test_confirm_submission_pending_app_not_found(self):
        response = self.client.post('/submit/confirm/12345',
                                    follow=True)
        self.assertEqual(404, response.status_code)

    def test_confirm_submission_user_not_authorized(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        testuser = User.objects.create_user(username='joe', password='secret',
                                           is_superuser=False)
        testuser.save()
        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='joe', password='secret')
        self.assertTrue(res)
        response = self.client.post('/submit/confirm/' + str(pending.id)
                                    ,follow=True)
        self.assertEqual(403, response.status_code)

    def test_confirm_submission_success_noaction_nopom(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/submit/confirm/' + str(pending.id),
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Cytoscape App Store - '
                        b'Confirm Submission' in response.content)

    def test_confirm_submission_success_noaction_withpom(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')

        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)

        testpomfile = SimpleUploadedFile('pom.xml',
                                         PomParseTest.get_valid_pom_as_bytes(),
                                         content_type='text/xml')
        testpomfile.open(mode='r')
        pending.pom_xml_file.save(os.path.basename(testpomfile.name),
                                  testpomfile)
        testpomfile.close()

        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/submit/confirm/' + str(pending.id),
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Cytoscape App Store - '
                        b'Confirm Submission' in response.content)
        self.assertTrue(b'es.imim' in response.content)
        self.assertTrue(b'DisGeNET' in response.content)
        self.assertTrue(b'6.3.2' in response.content)

    def test_confirm_submission_user_canceled(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/submit/confirm/' + str(pending.id),
                                    {'action': 'cancel'},
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Submit an App' in response.content)
        checkpending = AppPending.objects.filter(id=pending.id).first()
        self.assertEqual(None, checkpending)

    def test_confirm_submission_user_accept_no_existing_app(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/submit/confirm/' + str(pending.id),
                                    {'action': 'accept'},
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Submit an App' in response.content)
        checkpending = AppPending.objects.filter(id=pending.id).first()
        self.assertEqual(pending, checkpending)

    def test_submit_api_with_javadoc_and_pom(self):
        temp_dir = tempfile.mkdtemp()
        try:
            userobj = User.objects.create_user(username='bob', password='secret',
                                               is_superuser=True)
            userobj.save()

            temp_zip = os.path.join(temp_dir, 'foo.jar')
            zf = zipfile.ZipFile(temp_zip, mode='w')
            zf.writestr('hi.xml', 'somedata')
            zf.close()
            with open(temp_zip, 'rb') as f:
                zipdata = f.read()
            javadocfile = SimpleUploadedFile('javadoc.jar', zipdata,
                                             content_type='application/zip')
            jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                         content_type='application/zip')
            testpomfile = SimpleUploadedFile('pom.xml',
                                             PomParseTest.get_valid_pom_as_bytes(),
                                             content_type='text/xml')
            pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                            'workswith', [], jarfile)
            res = self.client.login(username='bob', password='secret')
            self.assertTrue(res)

            response = self.client.post('/submit/submit_api/' +
                                        str(pending.id),
                                        {'submit': 'true',
                                         'pom_xml': testpomfile,
                                         'javadocs_jar': javadocfile},
                                        follow=True)
            self.assertEqual(200, response.status_code)
            self.assertTrue(b'Confirm Submission' in response.content)
        finally:
            shutil.rmtree(temp_dir)

    def test_submit_api_with_invalidjavadoc_and_validpomfile(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        testpomfile = SimpleUploadedFile('pom.xml',
                                         PomParseTest.get_valid_pom_as_bytes(),
                                         content_type='text/xml')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        response = self.client.post('/submit/submit_api/' +
                                    str(pending.id),
                                    {'submit': 'true',
                                     'pom_xml': testpomfile,
                                     'javadocs_jar': jarfile},
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Submit an API' in response.content)
        self.assertTrue(b'Javadocs Jar file you submitted is not a valid jar')

    def test_submit_api_with_invalidjavadoc_and_invalid_pomfile(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()

        javadocfile = SimpleUploadedFile('javadoc.jar', b'invalid',
                                         content_type='application/zip')
        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        testpomfile = SimpleUploadedFile('pom.xml',
                                         b'haha',
                                         content_type='text/xml')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        response = self.client.post('/submit/submit_api/' +
                                    str(pending.id),
                                    {'submit': 'true',
                                     'pom_xml': testpomfile,
                                     'javadocs_jar': javadocfile},
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Submit an API' in response.content)
        self.assertTrue(b'pom.xml is not valid; '
                        b'it must have' in response.content)

    def test_submit_api_page_passes_artifact_exists_url_to_js(self):
        userobj = User.objects.create_user(username='bob', password='secret',
                                           is_superuser=True)
        userobj.save()
        jarfile = SimpleUploadedFile('SomeApp-1.0.0.jar', b'data',
                                     content_type='application/zip')
        pending = views._create_pending(userobj, 'SomeApp', '1.0.0',
                                        'workswith', [], jarfile)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        response = self.client.get('/submit/submit_api/' + str(pending.id))
        self.assertEqual(200, response.status_code)
        self.assertEqual('/submit/artifact_exists', reverse('artifact-exists'))
        self.assertTrue(b"SubmitAPI.setupInputFiles('/submit/artifact_exists')"
                        in response.content)
        # version query string forces browsers to drop a cached old submit_api.js
        self.assertTrue(b'submit_app/js/submit_api.js?v=148' in response.content)

    def test_artifact_exists_url_is_routed(self):
        with patch('submit_app.views._url_exists', return_value=False) as mock_exists:
            response = self.client.post(reverse('artifact-exists'),
                                        {'groupId': 'es.imim',
                                         'artifactId': 'DisGeNET-app',
                                         'version': '8.2.6'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(False, json.loads(response.content))
        mock_exists.assert_called_once_with(
            views.AppRepoUrl + '/es/imim/DisGeNET-app/8.2.6')

    def test_artifact_exists_missing_coordinates(self):
        response = self.client.post(reverse('artifact-exists'),
                                    {'groupId': 'es.imim'})
        self.assertEqual(400, response.status_code)

    def test_submit_api_js_does_not_hardcode_artifact_exists_url(self):
        js_path = finders.find('submit_app/js/submit_api.js')
        self.assertIsNotNone(js_path)
        with open(js_path, 'r') as f:
            js = f.read()
        self.assertFalse('artifact_exists' in js)
        self.assertFalse('verifyFailed(' in js)

    def test_submit_api_js_accepts_xml_mime_types_and_escapes_filename(self):
        js_path = finders.find('submit_app/js/submit_api.js')
        self.assertIsNotNone(js_path)
        with open(js_path, 'r') as f:
            js = f.read()
        self.assertTrue("'application/xml'" in js)
        self.assertFalse('verifyPomFailed(file.name' in js)
        self.assertTrue("$('<span>').text(file.name).html()" in js)


class ViewsHelperMethodsTest(TestCase):

    def test_get_server_url_with_basic_http_req(self):
        req = MagicMock()
        req.META = {'SERVER_NAME': 'foo.com',
                    'SERVER_PORT': '80'}
        req.is_secure = MagicMock(return_value=False)
        res = views._get_server_url(req)
        self.assertEqual('http://foo.com', res)

    def test_get_server_url_with_http_alt_port(self):
        req = MagicMock()
        req.META = {'SERVER_NAME': 'foo.com',
                    'SERVER_PORT': '8000'}
        req.is_secure = MagicMock(return_value=False)
        res = views._get_server_url(req)
        self.assertEqual('http://foo.com:8000', res)

    def test_get_server_url_with_https(self):
        req = MagicMock()
        req.META = {'SERVER_NAME': 'foo.com',
                    'SERVER_PORT': '443'}
        req.is_secure = MagicMock(return_value=True)
        res = views._get_server_url(req)
        self.assertEqual('https://foo.com', res)

    def test_get_server_url_with_https_and_port(self):
        req = MagicMock()
        req.META = {'SERVER_NAME': 'foo.com',
                    'SERVER_PORT': '8443'}
        req.is_secure = MagicMock(return_value=True)
        res = views._get_server_url(req)
        self.assertEqual('https://foo.com:8443', res)

    def test_verify_javadocs_jar_invalid_zip(self):
        testzipfile = SimpleUploadedFile('javadoc.jar', b'invalidzip',
                                         content_type='application/zip')
        testzipfile.open(mode='rb')
        res = views._verify_javadocs_jar(testzipfile)
        self.assertTrue('not a valid jar' in res)
        testzipfile.close()

    def test_verify_javadocs_jar_valid_zip(self):
        temp_dir = tempfile.mkdtemp()
        try:
            temp_zip = os.path.join(temp_dir, 'foo.jar')
            zf = zipfile.ZipFile(temp_zip, mode='w')
            zf.writestr('hi.xml', 'somedata')
            zf.close()
            with open(temp_zip, 'rb') as f:
                zipdata = f.read()
            testzipfile = SimpleUploadedFile('javadoc.jar', zipdata,
                                             content_type='application/zip')
            testzipfile.open(mode='rb')
            res = views._verify_javadocs_jar(testzipfile)
            self.assertEqual(None, res)
            testzipfile.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_javadocs_jar_with_invalid_slash_at_start_of_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            temp_zip = os.path.join(temp_dir, 'foo.jar')
            zf = zipfile.ZipFile(temp_zip, mode='w')
            zf.writestr('/hi.xml', 'somedata')
            zf.close()
            with open(temp_zip, 'rb') as f:
                zipdata = f.read()
            testzipfile = SimpleUploadedFile('javadoc.jar', zipdata,
                                             content_type='application/zip')
            testzipfile.open(mode='rb')
            res = views._verify_javadocs_jar(testzipfile)
            self.assertTrue('path that is illegal: /hi.xml' in res)
            testzipfile.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_javadocs_jar_with_double_dot_in_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            temp_zip = os.path.join(temp_dir, 'foo.jar')
            zf = zipfile.ZipFile(temp_zip, mode='w')
            zf.writestr('yo/../hi.xml', 'somedata')
            zf.close()
            with open(temp_zip, 'rb') as f:
                zipdata = f.read()
            testzipfile = SimpleUploadedFile('javadoc.jar', zipdata,
                                             content_type='application/zip')
            testzipfile.open(mode='rb')
            res = views._verify_javadocs_jar(testzipfile)
            self.assertTrue('path that is illegal: yo/../hi.xml' in res)
            testzipfile.close()
        finally:
            shutil.rmtree(temp_dir)


class PomParseTest(TestCase):

    @staticmethod
    def get_valid_pom_as_bytes():
        return b"""
        <project xmlns="http://maven.apache.org/POM/4.0.0" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                 http://maven.apache.org/maven-v4_0_0.xsd">

        <modelVersion>4.0.0</modelVersion>
        <groupId>es.imim</groupId>
        <artifactId>DisGeNET-app</artifactId>
        <version>6.3.2</version>


        <properties>
                <cytoscape.api.version>3.6.1</cytoscape.api.version>
                <maven-compiler-plugin.version>2.3.2</maven-compiler-plugin.version>
                <maven-bundle-plugin.version>2.3.7</maven-bundle-plugin.version>
                <maven-surefire-plugin>2.7.1</maven-surefire-plugin>
                <osgi.api.version>4.2.0</osgi.api.version>
                <slf4jVersion>1.6.1</slf4jVersion>
        </properties>

        <packaging>bundle</packaging>

        <build>
                <plugins>
                        <!-- The maven-compiler-plugin configures the Java compiler Maven uses
                to build the project. -->
                        <plugin>
                                <groupId>org.apache.maven.plugins</groupId>
                                <artifactId>maven-compiler-plugin</artifactId>
                                <version>${maven-compiler-plugin.version}</version>
                                <configuration>
                                        <!-- These options indicate the source code is Java 1.8-compliant and
                        the resulting class files should be Java 1.8-compatible. -->
                                        <source>1.8</source>
                                        <target>1.8</target>
                                </configuration>
                        </plugin>

                        <!-- The maven-bundle-plugin creates the metadata that's necessary for
                an OSGi bundle. You can customize the OSGi options in the "instructions"
                section below. -->
                        <plugin>
                                <groupId>org.apache.felix</groupId>
                                <artifactId>maven-bundle-plugin</artifactId>
                                <version>${maven-bundle-plugin.version}</version>
                                <extensions>true</extensions>
                                <configuration>
                                        <instructions>
                                                <Bundle-SymbolicName>es.imim.DisGeNET-app</Bundle-SymbolicName>
                                                <Bundle-Version>${project.version}</Bundle-Version>
                                                <!-- This tells the bundle plugin which packages should not be exported. -->
                                                <Private-Package>es.imim.*</Private-Package>
                                                <Embed-Dependency>commons-lang3;scope=compile|runtime</Embed-Dependency>
                                                <Bundle-Activator>es.imim.DisGeNET.internal.CyActivator</Bundle-Activator>
                                                <Embed-Dependency>sqlite-jdbc|mysql-connector-java</Embed-Dependency>
                                                <Import-Package>org.sqlite.*;version:=3.25.2,*;resolution:=optional</Import-Package>
                                                <Import-Package>com.mysql.jdbc;version:=5.1.25,*;resolution:=optional</Import-Package>
                                        </instructions>
                                </configuration>
                        </plugin>
                </plugins>
        </build>

        <!-- Links to the Cytoscape Maven repositories. -->
        <repositories>
                <repository>
                        <id>cytoscape_snapshots</id>
                        <snapshots>
                        </snapshots>
                        <releases>
                                <enabled>false</enabled>
                        </releases>
                        <name>Cytoscape Snapshots</name>
                        <url>http://code.cytoscape.org/nexus/content/repositories/snapshots/</url>
                </repository>
                <repository>
                        <id>cytoscape_releases</id>
                        <snapshots>
                                <enabled>false</enabled>
                        </snapshots>
                        <releases>
                        </releases>
                        <name>Cytoscape Releases</name>
                        <url>http://code.cytoscape.org/nexus/content/repositories/releases/</url>
                </repository>
        </repositories>

        <!-- Dependencies needed to compile this project. -->
        <dependencies>
                <dependency>
                        <groupId>org.osgi</groupId>
                        <artifactId>org.osgi.core</artifactId>
                        <version>4.2.0</version>
                </dependency>

                <dependency>
                        <groupId>org.cytoscape</groupId>
                        <artifactId>service-api</artifactId>
                        <version>3.6.1</version>
                </dependency>
                <dependency>
                        <groupId>org.cytoscape</groupId>
                        <artifactId>layout-api</artifactId>
                        <version>3.6.1</version>
                </dependency>
                <dependency>
                        <groupId>org.cytoscape</groupId>
                        <artifactId>swing-application-api</artifactId>
                        <version>3.6.1</version>
                </dependency>
                <dependency>
                        <groupId>org.cytoscape</groupId>
                        <artifactId>session-api</artifactId>
                        <version>3.6.1</version>
                </dependency>
                <dependency>
                        <groupId>org.cytoscape</groupId>
                                                <artifactId>swing-util-api</artifactId>
                        <version>3.6.1</version>
                </dependency>
                <dependency>
                        <groupId>javax.ws.rs</groupId>
                        <artifactId>javax.ws.rs-api</artifactId>
                        <version>2.0</version>
                </dependency>
                <dependency>
                        <groupId>io.swagger</groupId>
                        <artifactId>swagger-annotations</artifactId>
                        <version>1.5.7</version>
                </dependency>

                <!--javi additional for using tar... -->
                <dependency>
                        <groupId>org.apache.ant</groupId>
                        <artifactId>ant</artifactId>
                        <version>1.8.1</version>
                        <scope>provided</scope>
                </dependency>

                <!--javi additional for using sqllite -->
                <dependency>
                        <groupId>org.xerial</groupId>
                        <artifactId>sqlite-jdbc</artifactId>
                        <version>3.25.2</version>
                </dependency>

                <dependency>
                        <groupId>mysql</groupId>
                        <artifactId>mysql-connector-java</artifactId>
                        <version>5.1.25</version>
                        <optional>true</optional>
                </dependency>

                <dependency>
                        <groupId>org.swinglabs</groupId>
                        <artifactId>swingx</artifactId>
                        <version>1.6.1</version>
                </dependency>
        </dependencies>

</project>
        """

    def test_parse_ns_tag(self):
        res, _ = pomparse._parse_ns_tag('{hi}')
        self.assertEqual(None, res)
        res, _ = pomparse._parse_ns_tag('{hi}x')
        self.assertEqual('hi', res)

    def test_parse_pom_empty_in_memory_file(self):
        testpomfile = SimpleUploadedFile('pom.xml', b'',
                                         content_type='text/xml')
        res = pomparse.parse_pom(testpomfile)
        self.assertEqual({}, res)

    def test_parse_pom_empty_temp_file(self):
        testpomfile = TemporaryUploadedFile('pom.xml',
                                            'text/xml',
                                            0,
                                            0)
        with open(testpomfile.temporary_file_path(), 'wb') as f:
            f.write(b'')
        res = pomparse.parse_pom(testpomfile)
        self.assertEqual({}, res)

    def test_parse_valid_pom_in_memory_file(self):
        testpomfile = SimpleUploadedFile('pom.xml',
                                         self.get_valid_pom_as_bytes(),
                                         content_type='text/xml')
        res = pomparse.parse_pom(testpomfile)
        self.assertEqual({'artifactId': 'DisGeNET-app',
                          'groupId': 'es.imim',
                          'version': '6.3.2'}, res)

    def test_parse_valid_pom_temp_file(self):
        pombytes = self.get_valid_pom_as_bytes()
        testpomfile = TemporaryUploadedFile('pom.xml',
                                            'text/xml',
                                            len(pombytes),
                                            0)
        with open(testpomfile.temporary_file_path(), 'wb') as f:
            f.write(self.get_valid_pom_as_bytes())
        res = pomparse.parse_pom(testpomfile)
        self.assertEqual({'artifactId': 'DisGeNET-app',
                          'groupId': 'es.imim',
                          'version': '6.3.2'}, res)


class ProcessJarTest(TestCase):

    def test_process_jar_invalid_zipfile(self):
        testjarfile = SimpleUploadedFile('foo.jar',
                                         b'invalidzipfilehehehe',
                                         content_type='application/java-archive')
        try:
            processjar.process_jar(testjarfile, 'someAppName')
            self.fail('Expected ValueError')
        except ValueError as ve:
            self.assertEqual('is not a valid zip file', str(ve))

    def test_process_jar_on_in_memory_file(self):
        fake_jar_file = io.BytesIO()
        with zipfile.ZipFile(fake_jar_file, mode='w') as zf:
            zf.writestr('META-INF/MANIFEST.MF', TEST_VALID_MANIFEST_ONE)

        testjarfile = SimpleUploadedFile('foo.jar',
                                         fake_jar_file.getvalue(),
                                         content_type='application/java-archive')
        (a_name, a_ver,
         a_works, a_dep,
         has_exp) = processjar.process_jar(testjarfile,
                                           'CyCommunityDetectionTest')

        self.assertEqual('CyCommunityDetectionTest', a_name)
        self.assertEqual('1.11.0', a_ver)
        self.assertEqual('3.7', a_works)
        self.assertEqual([], a_dep)
        self.assertEqual(True, has_exp)

    def test_process_jar_on_in_memory_file_expect_name_mismatch(self):
        fake_jar_file = io.BytesIO()
        with zipfile.ZipFile(fake_jar_file, mode='w') as zf:
            zf.writestr('META-INF/MANIFEST.MF', TEST_VALID_MANIFEST_ONE)

        testjarfile = SimpleUploadedFile('foo.jar',
                                         fake_jar_file.getvalue(),
                                         content_type='application/java-archive')
        try:
            processjar.process_jar(testjarfile, 'expectedname')
            self.fail('Expected ValueError')
        except ValueError as ve:
            self.assertEqual('has app name as '
                             '<tt>CyCommunityDetectionTest</tt> '
                             'but must be <tt>expectedname</tt>', str(ve))

    def test_process_jar_on_temporary_uploaded_file(self):
        fake_jar_file = io.BytesIO()
        with zipfile.ZipFile(fake_jar_file, mode='w') as zf:
            zf.writestr('META-INF/MANIFEST.MF', TEST_VALID_MANIFEST_ONE)

        testjarfile = TemporaryUploadedFile('foo.jar',
                                            'application/java-archive',
                                            100,
                                            0)
        with open(testjarfile.temporary_file_path(), 'wb') as f:
            f.write(fake_jar_file.getvalue())

        (a_name, a_ver,
         a_works, a_dep,
         has_exp) = processjar.process_jar(testjarfile,
                                           'CyCommunityDetectionTest')

        self.assertEqual('CyCommunityDetectionTest', a_name)
        self.assertEqual('1.11.0', a_ver)
        self.assertEqual('3.7', a_works)
        self.assertEqual([], a_dep)
        self.assertEqual(True, has_exp)


class MFParseTestCase(TestCase):

    def test_parse_version_range_where_bracket_at_front(self):

        (start_range,
         start_version,
         end_version, end_range) = mfparse._parse_version_range('"[3.8,4)"')

        self.assertEqual('[', start_range)
        self.assertEqual(('3', '8', None, None), start_version)
        self.assertEqual(('4', None, None, None), end_version)
        self.assertEqual(')', end_range)

    def test_parse_version_range(self):

        (start_range,
         start_version,
         end_version, end_range) = mfparse._parse_version_range('"(3.7,4]"')

        self.assertEqual('(', start_range)
        self.assertEqual(('3', '7', None, None), start_version)
        self.assertEqual(('4', None, None, None), end_version)
        self.assertEqual(']', end_range)

    def test_lower_version(self):
        res = mfparse._lower_version('"[3.8,4)"')
        self.assertEqual(('3', '8', None, None), res)

        res = mfparse._lower_version('"(3.6,4]"')
        self.assertEqual(('3', '6', None, None), res)

    def test_lower_cytoscape_pkg_versions(self):
        the_str = 'org.cytoscape.model.subnetwork;resolution:=optional;' \
                  'version="[3.7,4)",org.cytoscape.property;resolution:' \
                  '=optional;version="[3.6,4)"'
        res = mfparse.max_of_lower_cytoscape_pkg_versions(the_str)
        self.assertEqual(('3', '7', None, None), res)

        the_str = 'org.cytoscape.model.subnetwork;resolution:=optional;' \
                  'version="[3.27,4)",org.cytoscape.property;resolution:' \
                  '=optional;version="[3.16,4)"'
        res = mfparse.max_of_lower_cytoscape_pkg_versions(the_str)
        self.assertEqual(('3', '27', None, None), res)


class WebBundleManifestIdTest(TestCase):
    """The published manifest id must be the bundle's Module Federation
    container name, not the store's URL slug (issue #144)."""

    def setUp(self):
        self.app = App.objects.create(fullname='C3 App', name='c3app')

    def test_catalog_entry_uses_cy_app_id_not_the_slug(self):
        release = WebBundleRelease.objects.create(app=self.app,
                                                  cy_app_id='c3App',
                                                  version='0.1.0')
        entry = bundle_storage.bundle_catalog_entry(release)
        self.assertEqual('c3App', entry['id'])
        self.assertEqual('C3 App', entry['name'])

    def test_catalog_entry_never_substitutes_the_slug(self):
        # An empty cy_app_id means make_bundle_release did not run, which is a
        # bug. Publishing the slug instead would hide it behind an id that is
        # wrong but well-formed.
        release = WebBundleRelease.objects.create(app=self.app, version='0.1.0')
        entry = bundle_storage.bundle_catalog_entry(release)
        self.assertNotEqual('c3app', entry['id'])

    def test_slug_would_not_match_the_container_name(self):
        # The regression this guards: the slug is derived from the display
        # name and cannot round-trip a camelCase id.
        self.assertEqual('c3app', fullname_to_name('C3 App'))
        self.assertEqual('cytoscapewebsubmissiontest',
                         fullname_to_name('Cytoscape Web Submission Test'))

    def test_make_bundle_release_carries_the_pending_id(self):
        user = User.objects.create_user(username='submitter',
                                        password='password')
        pending = WebBundlePending.objects.create(submitter=user,
                                                  fullname='C3 App',
                                                  cy_app_id='c3App',
                                                  version='0.1.0',
                                                  bundle_hash='abc')
        with patch.object(submit_models, '_copy_bundle_to_storage'), \
             patch.object(submit_models, 'write_manifest_json'):
            pending.make_bundle_release(self.app)

        release = WebBundleRelease.objects.get(app=self.app, version='0.1.0')
        self.assertEqual('c3App', release.cy_app_id)

    def test_make_bundle_release_falls_back_for_pre_cy_manifest_uploads(self):
        user = User.objects.create_user(username='submitter2',
                                        password='password')
        pending = WebBundlePending.objects.create(submitter=user,
                                                  fullname='C3 App',
                                                  cy_app_id=None,
                                                  version='0.2.0',
                                                  bundle_hash='abc')
        with patch.object(submit_models, '_copy_bundle_to_storage'), \
             patch.object(submit_models, 'write_manifest_json'):
            pending.make_bundle_release(self.app)

        release = WebBundleRelease.objects.get(app=self.app, version='0.2.0')
        self.assertEqual('c3app', release.cy_app_id)

    def test_pending_manifest_uses_the_stored_id(self):
        user = User.objects.create_user(username='submitter3',
                                        password='password')
        pending = WebBundlePending.objects.create(submitter=user,
                                                  fullname='C3 App',
                                                  cy_app_id='c3App',
                                                  version='0.1.0',
                                                  bundle_hash='abc')
        saved = {}
        storage = MagicMock()
        storage.exists.return_value = False
        storage.save.side_effect = lambda path, content: saved.update(
            path=path, body=json.loads(content.read()))

        with patch.object(bundle_storage, 'storages',
                          {'webbundles': storage}):
            bundle_storage.write_pending_manifest_json(pending)

        self.assertEqual('c3App', saved['body'][0]['id'])


class SubmissionFixtureMixin:
    """Foo, a desktop app edited by 'editor', and helpers that submit service apps and web bundles."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        storages = dict(settings.STORAGES)
        storages['webbundles'] = {**storages['webbundles'],
                                  'OPTIONS': {**storages['webbundles']['OPTIONS'],
                                              'location': os.path.join(self.tmp, 'webbundles')}}
        self.overrides = self.settings(MEDIA_ROOT=self.tmp, STORAGES=storages)
        self.overrides.enable()

        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.other = User.objects.create_user('other', 'other@example.org', 'secret')
        self.desktop_app = App.objects.create(name='foo', fullname='Foo', active=True)
        self.desktop_app.editors.add(self.editor)
        Release.objects.create(app=self.desktop_app, version='1.0', works_with='3.10')

    def tearDown(self):
        self.overrides.disable()
        shutil.rmtree(self.tmp)

    def bundle(self, name='Foo', version='1.0'):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as zf:
            zf.writestr('dist/remoteEntry.js', 'var foo;')
            zf.writestr('dist/cy-manifest.json', json.dumps({'id': 'foo', 'name': name, 'version': version}))
        return SimpleUploadedFile('foo.zip', data.getvalue(), content_type='application/zip')

    def submit_bundle(self, user, expect_app_name=None, **bundle):
        self.client.force_login(user)
        data = {'bundle': self.bundle(**bundle)}
        if expect_app_name:
            data['expect_app_name'] = expect_app_name
        return self.client.post(reverse('submit-web-bundle'), data)

    def submit_service(self, user, name='Foo', expect_app_name=None, version='1.0'):
        self.client.force_login(user)
        data = {'service-url': 'https://service.example.org/foo'}
        if expect_app_name:
            data['expect_app_name'] = expect_app_name
        metadata = {'name': name, 'version': version, 'author': 'Someone'}
        with patch('submit_app.views.check_reachable', return_value=metadata):
            return self.client.post(reverse('submit-service-app'), data)


class SubmissionIdentityTest(SubmissionFixtureMixin, TestCase):
    """Every platform's submission resolves its name to an app the submitter may extend (#155)."""

    def test_non_editor_cannot_submit_an_existing_name_on_any_platform(self):
        jar = SimpleUploadedFile('Foo-2.0.jar', b'data', content_type='application/zip')
        with self.assertRaisesRegex(ValueError, 'not an editor'):
            views._create_pending(self.other, 'Foo', '2.0', '3.10', [], jar)
        self.assertContains(self.submit_service(self.other), 'you are not one of its editors')
        self.assertContains(self.submit_bundle(self.other), 'you are not one of its editors')
        self.assertFalse(AppPending.objects.exists())
        self.assertFalse(ServiceAppPending.objects.exists())
        self.assertFalse(WebBundlePending.objects.exists())

    def test_editor_adding_a_platform_creates_a_new_platform_pending(self):
        response = self.submit_service(self.editor)
        pending = ServiceAppPending.objects.get()
        self.assertRedirects(response, reverse('confirm-service', args=[pending.id]))
        self.assertTrue(pending.is_new_platform)
        self.assertFalse(pending.is_new_app)

        response = self.submit_bundle(self.editor)
        pending = WebBundlePending.objects.get()
        self.assertRedirects(response, reverse('confirm-web-bundle', args=[pending.id]))
        self.assertTrue(pending.is_new_platform)
        self.assertContains(self.client.get(reverse('confirm-web-bundle', args=[pending.id])),
                            'this adds Cytoscape Web to the existing app Foo')

        web_app = App.objects.create(name='bar', fullname='Bar', active=True)
        web_app.editors.add(self.editor)
        WebBundleRelease.objects.create(app=web_app, version='1.0', active=True, bundle_hash='0')
        jar = SimpleUploadedFile('Bar-1.0.jar', b'data', content_type='application/zip')
        pending = views._create_pending(self.editor, 'Bar', '1.0', '3.10', [], jar)
        self.assertTrue(pending.is_new_platform)
        self.assertContains(self.client.get(reverse('confirm-submission', args=[pending.id])),
                            'this adds Cytoscape Desktop to the existing app Bar')

    def test_existing_platform_and_new_app_are_not_new_platforms(self):
        jar = SimpleUploadedFile('Foo-2.0.jar', b'data', content_type='application/zip')
        pending = views._create_pending(self.editor, 'Foo', '2.0', '3.10', [], jar)
        self.assertFalse(pending.is_new_platform)
        self.assertFalse(pending.is_new_app)

        self.submit_bundle(self.other, name='Brand New')
        pending = WebBundlePending.objects.get()
        self.assertTrue(pending.is_new_app)
        self.assertFalse(pending.is_new_platform)

    def test_duplicate_web_bundle_version_is_rejected(self):
        WebBundleRelease.objects.create(app=self.desktop_app, version='1.0', active=True, bundle_hash='0')
        self.assertContains(self.submit_bundle(self.editor, version='1.0'),
                            'already has a Cytoscape Web release with version 1.0')
        self.assertFalse(WebBundlePending.objects.exists())

    def test_expect_app_name_must_match_for_service_and_web(self):
        self.assertContains(self.submit_service(self.editor, name='Bar', expect_app_name='Foo'),
                            'is named Bar but must be Foo')
        self.assertContains(self.submit_bundle(self.editor, name='Bar', expect_app_name='Foo'),
                            'is named Bar but must be Foo')
        self.assertFalse(ServiceAppPending.objects.exists())
        self.assertFalse(WebBundlePending.objects.exists())

        self.submit_service(self.editor, name='FOO', expect_app_name='Foo')
        self.assertTrue(ServiceAppPending.objects.exists())

    def test_forms_carry_expect_app_name(self):
        self.client.force_login(self.editor)
        for url in (reverse('submit-web-bundle'), reverse('submit-service-app')):
            self.assertContains(self.client.get(url + '?expect_app_name=Foo'),
                                '<input type="hidden" name="expect_app_name" value="Foo">', html=True)


class PlatformAcceptTest(SubmissionFixtureMixin, TestCase):
    """Accepting a submission for a new platform adds it to the app already holding the name (#155)."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user('admin', 'admin@example.org', 'secret', is_staff=True)

    def confirm(self, url_name, pending):
        return self.client.post(reverse(url_name, args=[pending.id]), {'action': 'accept'})

    def admin_accept(self, pending, pending_platform):
        self.client.force_login(self.admin)
        # TestCase never commits, so run what the accept defers to its commit
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse('pending-apps'), {'action': 'accept', 'pending_id': pending.id,
                                                              'pending_platform': pending_platform})

    def assert_one_app_on(self, name, *platforms):
        app = App.objects.get(name=name)
        self.assertEqual(list(platforms), app.platforms)
        self.assertEqual(['editor'], [u.username for u in app.editors.all()])
        self.assertTrue(app.active)
        return app

    def subjects(self):
        return [message.subject for message in mail.outbox]

    def test_service_added_to_a_desktop_app(self):
        self.submit_service(self.editor)
        pending = ServiceAppPending.objects.get()
        self.assertTemplateUsed(self.confirm('confirm-service', pending), 'submit_done.html')
        self.assertRedirects(self.admin_accept(pending, 'service'), reverse('pending-apps'))

        self.assert_one_app_on('foo', Platform.DESKTOP, Platform.SERVICE)
        self.assertFalse(ServiceAppPending.objects.exists())
        self.assertIn('Cytoscape App Store - App Submitted (new platform for existing app Foo)', self.subjects())
        self.assertIn('Cytoscape App Store - The service version of Foo Has Been Approved', self.subjects())
        self.assertIn('now appears on your existing app page', mail.outbox[-1].body)

    def test_web_bundle_added_to_a_desktop_app(self):
        self.submit_bundle(self.editor)
        pending = WebBundlePending.objects.get()
        self.assertTemplateUsed(self.confirm('confirm-web-bundle', pending), 'submit_done.html')
        self.admin_accept(pending, 'web-bundle')

        app = self.assert_one_app_on('foo', Platform.DESKTOP, Platform.WEB)
        self.assertEqual(['1.0'], [r.version for r in app.webbundlereleases])
        self.assertFalse(WebBundlePending.objects.exists())
        self.assertIn('Cytoscape App Store - The Cytoscape Web version of Foo Has Been Approved', self.subjects())

    def test_web_bundle_added_to_a_service_app(self):
        service_app = App.objects.create(name='baz', fullname='Baz', active=True)
        service_app.editors.add(self.editor)
        ServiceRelease.objects.create(app=service_app, version='1.0', service_endpoint='https://example.org/baz')

        self.submit_bundle(self.editor, name='Baz')
        pending = WebBundlePending.objects.get()
        self.confirm('confirm-web-bundle', pending)
        self.admin_accept(pending, 'web-bundle')

        self.assert_one_app_on('baz', Platform.WEB, Platform.SERVICE)

    def test_inactive_app_is_reactivated_by_its_new_platform(self):
        App.objects.filter(name='foo').update(active=False)
        self.submit_service(self.editor)
        self.admin_accept(ServiceAppPending.objects.get(), 'service')
        self.assert_one_app_on('foo', Platform.DESKTOP, Platform.SERVICE)

    def test_release_on_an_existing_platform_publishes_without_review(self):
        self.submit_service(self.editor)
        self.admin_accept(ServiceAppPending.objects.get(), 'service')

        self.submit_service(self.editor, version='2.0')
        pending = ServiceAppPending.objects.get()
        self.assertFalse(pending.is_new_platform)
        response = self.confirm('confirm-service', pending)
        self.assertRedirects(response, reverse('app_page_edit', args=['foo']) + '?upload_release=true',
                             fetch_redirect_response=False)
        self.assertEqual(['2.0', '1.0'], [r.version for r in App.objects.get(name='foo').servicereleases_by_version])
        self.assertFalse(ServiceAppPending.objects.exists())

    def test_new_app_is_created_on_accept(self):
        self.submit_service(self.other, name='Brand New')
        pending = ServiceAppPending.objects.get()
        self.confirm('confirm-service', pending)
        self.admin_accept(pending, 'service')

        app = App.objects.get(name='brandnew')
        self.assertEqual([Platform.SERVICE], app.platforms)
        self.assertEqual(['other'], [u.username for u in app.editors.all()])
        self.assertIn('Cytoscape App Store - Brand New Has Been Approved', self.subjects())


class PendingQueueTest(SubmissionFixtureMixin, TestCase):
    """The admin queue says whether each submission is a new app or a new platform for an existing one (#155)."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user('admin', 'admin@example.org', 'secret', is_staff=True)
        self.new_app = AppPending.objects.create(submitter=self.other, fullname='Brand New', version='1.0',
                                                 cy_works_with='3.10')
        self.new_app.release_file.save('brandnew-1.0.jar', SimpleUploadedFile('brandnew-1.0.jar', b'data'))
        self.new_platform = ServiceAppPending.objects.create(
            submitter=self.editor, fullname='Foo', name='foo', version='1.0',
            service_endpoint='https://service.example.org/foo')
        self.web_url = WebUrlPending.objects.create(submitter=self.other, fullname='Url App', version='1.0',
                                                    repo_url='https://github.com/example/url-app')
        self.client.force_login(self.admin)

    def post(self, action, pending_id, pending_platform, **headers):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse('pending-apps'), {'action': action, 'pending_id': pending_id,
                                                              'pending_platform': pending_platform}, **headers)

    def test_rows_say_new_app_or_new_platform(self):
        response = self.client.get(reverse('pending-apps'))
        self.assertContains(response, '<th>Type</th>', html=True)
        self.assertContains(response, 'New app')
        self.assertContains(response, 'New platform &rarr; <a href="%s">Foo</a>' % reverse('app_page', args=['foo']))

    def test_accept_for_desktop_service_and_web_bundle(self):
        self.post('accept', self.new_app.id, 'desktop')
        self.assertEqual([Platform.DESKTOP], App.objects.get(name='brandnew').platforms)

        self.post('accept', self.new_platform.id, 'service')
        self.assertEqual([Platform.DESKTOP, Platform.SERVICE], App.objects.get(name='foo').platforms)

        self.submit_bundle(self.editor, name='Foo')
        self.client.force_login(self.admin)
        self.post('accept', WebBundlePending.objects.get().id, 'web-bundle')
        self.assertEqual([Platform.DESKTOP, Platform.WEB, Platform.SERVICE], App.objects.get(name='foo').platforms)

    def test_web_url_cannot_be_accepted_yet(self):
        for headers in ({}, {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}):
            response = self.post('accept', self.web_url.id, 'web-url', **headers)
            self.assertContains(response, 'Approving GitHub-URL web submissions is not supported yet', status_code=400)
        self.assertTrue(WebUrlPending.objects.filter(id=self.web_url.id).exists())
        self.assertFalse(App.objects.filter(name='urlapp').exists())

    def test_decline_for_every_platform(self):
        self.submit_bundle(self.editor, name='Foo')
        self.client.force_login(self.admin)
        for pending, pending_platform in ((self.new_app, 'desktop'), (self.new_platform, 'service'),
                                          (WebBundlePending.objects.get(), 'web-bundle'), (self.web_url, 'web-url')):
            self.post('decline', pending.id, pending_platform)
            self.assertFalse(type(pending).objects.filter(id=pending.id).exists())
        self.assertEqual(['foo'], [app.name for app in App.objects.all()])


class AcceptSafetyTest(SubmissionFixtureMixin, TestCase):
    """Accepting a submission never publishes onto someone else's app, and a failed accept publishes nothing (#155)."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user('admin', 'admin@example.org', 'secret', is_staff=True)
        self.third = User.objects.create_user('third', 'third@example.org', 'secret')

    def admin_post(self, action, pending, pending_platform):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse('pending-apps'), {'action': action, 'pending_id': pending.id,
                                                              'pending_platform': pending_platform})

    def test_second_submission_of_the_same_new_name_is_refused(self):
        # both submit before either is accepted, so both are new apps when submitted
        self.submit_service(self.other, name='Brand New')
        self.submit_bundle(self.third, name='Brand New')
        first, second = ServiceAppPending.objects.get(), WebBundlePending.objects.get()
        self.admin_post('accept', first, 'service')

        response = self.admin_post('accept', second, 'web-bundle')
        self.assertContains(response, 'Brand New already exists and third is not one of its editors', status_code=400)
        app = App.objects.get(name='brandnew')
        self.assertEqual([Platform.SERVICE], app.platforms)
        self.assertEqual(['other'], [u.username for u in app.editors.all()])
        self.assertFalse(WebBundleRelease.objects.filter(app=app).exists())
        self.assertTrue(WebBundlePending.objects.filter(id=second.id).exists())

        self.admin_post('decline', second, 'web-bundle')
        self.assertFalse(WebBundlePending.objects.filter(id=second.id).exists())

    def test_failed_accept_of_a_new_platform_publishes_nothing(self):
        self.submit_bundle(self.editor)
        pending = WebBundlePending.objects.get()
        App.objects.filter(name='foo').update(active=False)
        self.client.raise_request_exception = False
        with patch.object(submit_models, '_copy_bundle_to_storage', side_effect=OSError('disk full')):
            self.assertEqual(500, self.admin_post('accept', pending, 'web-bundle').status_code)

        app = App.objects.get(name='foo')
        self.assertEqual(([Platform.DESKTOP], False), (app.platforms, app.active))
        self.assertFalse(WebBundleRelease.objects.exists())
        self.assertTrue(WebBundlePending.objects.filter(id=pending.id).exists())
        self.admin_post('decline', pending, 'web-bundle')
        self.assertFalse(WebBundlePending.objects.exists())

    def test_failed_accept_of_a_new_app_creates_no_app(self):
        self.submit_bundle(self.other, name='Brand New')
        pending = WebBundlePending.objects.get()
        self.client.raise_request_exception = False
        with patch.object(submit_models, '_copy_bundle_to_storage', side_effect=OSError('disk full')):
            self.assertEqual(500, self.admin_post('accept', pending, 'web-bundle').status_code)

        self.assertFalse(App.objects.filter(name='brandnew').exists())
        self.assertFalse(WebBundleRelease.objects.exists())
        self.assertTrue(WebBundlePending.objects.filter(id=pending.id).exists())

    def pending_bundle_files(self, pending):
        return storages['webbundles'].listdir(pending.bundle_path)[1]

    def test_failed_accept_keeps_the_pending_bundle(self):
        # fails after the release and its public files are written, but before the accept commits
        self.submit_bundle(self.editor)
        pending = WebBundlePending.objects.get()
        self.client.raise_request_exception = False
        with patch.object(WebBundlePending, 'delete', side_effect=OSError('database gone')):
            self.assertEqual(500, self.admin_post('accept', pending, 'web-bundle').status_code)

        self.assertFalse(WebBundleRelease.objects.exists())
        pending = WebBundlePending.objects.get(id=pending.id)
        self.assertTrue(pending.bundle.storage.exists(pending.bundle.name))
        self.assertIn('remoteEntry.js', self.pending_bundle_files(pending))

        # so the admin can accept it again
        self.admin_post('accept', pending, 'web-bundle')
        self.assertTrue(WebBundleRelease.objects.filter(app=self.desktop_app, version='1.0').exists())
        self.assertFalse(WebBundlePending.objects.exists())
        self.assertFalse(pending.bundle.storage.exists(pending.bundle.name))
        self.assertFalse(storages['webbundles'].exists(pending.bundle_path))

    def test_failed_accept_keeps_the_pending_jar(self):
        jar = SimpleUploadedFile('BrandNew-1.0.jar', b'jar', content_type='application/zip')
        pending = views._create_pending(self.other, 'Brand New', '1.0', '3.10', [], jar)
        self.client.raise_request_exception = False
        with patch.object(AppPending, 'delete', side_effect=OSError('database gone')):
            self.assertEqual(500, self.admin_post('accept', pending, 'desktop').status_code)

        self.assertFalse(App.objects.filter(name='brandnew').exists())
        pending = AppPending.objects.get(id=pending.id)
        self.assertTrue(pending.release_file.storage.exists(pending.release_file.name))

    def test_failure_after_the_accept_commits_keeps_it_published(self):
        self.submit_service(self.editor)
        self.submit_bundle(self.editor)
        service, bundle = ServiceAppPending.objects.get(), WebBundlePending.objects.get()
        # TestCase logs a failed robust on_commit callback to django.test; a real commit logs it to django.db
        with patch.object(views, '_send_email_for_accepted', side_effect=RuntimeError('mail server down')), \
                self.assertLogs('django.test', 'ERROR') as logs:
            self.assertRedirects(self.admin_post('accept', service, 'service'), reverse('pending-apps'))
            self.assertRedirects(self.admin_post('accept', bundle, 'web-bundle'), reverse('pending-apps'))

        self.assertEqual(2, sum('mail server down' in line for line in logs.output))
        self.assertEqual([Platform.DESKTOP, Platform.WEB, Platform.SERVICE], App.objects.get(name='foo').platforms)
        self.assertFalse(ServiceAppPending.objects.exists())
        self.assertFalse(WebBundlePending.objects.exists())
        self.assertFalse(bundle.bundle.storage.exists(bundle.bundle.name))

    def test_a_published_web_version_is_not_overwritten(self):
        # the same version submitted twice; both pass the submit-time check, as neither is published yet
        self.submit_bundle(self.editor)
        first = WebBundlePending.objects.get()
        second = WebBundlePending.objects.get(id=first.id)
        second.pk = None
        second.save()
        self.admin_post('accept', first, 'web-bundle')
        release = WebBundleRelease.objects.get(app=self.desktop_app, version='1.0')

        response = self.admin_post('accept', second, 'web-bundle')
        self.assertContains(response, 'Version 1.0 of Foo is already published', status_code=400)
        self.assertEqual(release.created, WebBundleRelease.objects.get(id=release.id).created)
        self.assertTrue(WebBundlePending.objects.filter(id=second.id).exists())
        self.admin_post('decline', second, 'web-bundle')
        self.assertFalse(WebBundlePending.objects.exists())

    def test_a_published_desktop_version_is_not_overwritten(self):
        pending = AppPending.objects.create(submitter=self.editor, fullname='Foo', version='1.0', cy_works_with='3.10')
        response = self.admin_post('accept', pending, 'desktop')
        self.assertContains(response, 'Version 1.0 of Foo is already published', status_code=400)
        self.assertEqual(['3.10'], [r.works_with for r in Release.objects.filter(app=self.desktop_app)])
        self.assertTrue(AppPending.objects.filter(id=pending.id).exists())

    def test_a_deleted_version_can_be_published_again(self):
        Release.objects.filter(app=self.desktop_app, version='1.0').update(active=False)
        pending = AppPending.objects.create(submitter=self.editor, fullname='Foo', version='1.0', cy_works_with='3.11')
        pending.release_file.save('Foo-1.0.jar', ContentFile(b'jar'))
        self.assertRedirects(self.admin_post('accept', pending, 'desktop'), reverse('pending-apps'))
        release = Release.objects.get(app=self.desktop_app, version='1.0')
        self.assertEqual((True, '3.11'), (release.active, release.works_with))
