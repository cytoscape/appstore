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

from unittest.mock import MagicMock
from django.test import TestCase

from django.conf import settings

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.http import HttpRequest
from django.contrib.auth.models import User
from apps.models import App
from apps.models import Release
from submit_app.models import AppPending
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
        response = self.client.post('/submit_app/confirm/12345',
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
        response = self.client.post('/submit_app/confirm/' + str(pending.id)
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
        response = self.client.post('/submit_app/confirm/' + str(pending.id),
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
        response = self.client.post('/submit_app/confirm/' + str(pending.id),
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
        response = self.client.post('/submit_app/confirm/' + str(pending.id),
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
        response = self.client.post('/submit_app/confirm/' + str(pending.id),
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

            response = self.client.post('/submit_app/submit_api/' +
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

        response = self.client.post('/submit_app/submit_api/' +
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

        response = self.client.post('/submit_app/submit_api/' +
                                    str(pending.id),
                                    {'submit': 'true',
                                     'pom_xml': testpomfile,
                                     'javadocs_jar': javadocfile},
                                    follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(b'Submit an API' in response.content)
        self.assertTrue(b'pom.xml is not valid; '
                        b'it must have' in response.content)


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
