"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import zipfile
import io
import tempfile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import TemporaryUploadedFile

from submit_app import processjar


TEST_VALID_MANIFEST_ONE = b'Manifest-Version: 1.0\r\nBnd-LastModified: 1592239529972\r\nBuild-Jdk: 11.0.4\r\nBuilt-By: churas\r\nBundle-Activator: org.cytoscape.app.communitydetection.CyActivator\r\nBundle-ClassPath: .,httpclient-4.5.9.jar,httpcore-4.4.11.jar,commons-l\r\n ogging-1.2.jar,commons-codec-1.11.jar,httpmime-4.5.9.jar,gson-2.8.5.j\r\n ar,communitydetection-rest-model-0.8.1.jar,swagger-annotations-2.0.0.\r\n jar,logback-classic-1.2.3.jar,logback-core-1.2.3.jar,slf4j-api-1.7.25\r\n .jar,jackson-databind-2.10.1.jar,jackson-annotations-2.10.1.jar,jacks\r\n on-core-2.10.1.jar,jackson-jaxrs-base-2.10.1.jar,ndex-object-model-2.\r\n 5.0-20200508.163437-2.jar\r\nBundle-ManifestVersion: 2\r\nBundle-Name: CyCommunityDetectionTest\r\nBundle-SymbolicName: org.cytoscape.app.communitydetection\r\nBundle-Version: 1.11.0\r\nCreated-By: Apache Maven Bundle Plugin\r\nEmbed-Dependency: *;scope=!provided|test;groupId=!org.cytoscape\r\nEmbed-Transitive: true\r\nEmbedded-Artifacts: httpclient-4.5.9.jar;g="org.apache.httpcomponents"\r\n ;a="httpclient";v="4.5.9",httpcore-4.4.11.jar;g="org.apache.httpcompo\r\n nents";a="httpcore";v="4.4.11",commons-logging-1.2.jar;g="commons-log\r\n ging";a="commons-logging";v="1.2",commons-codec-1.11.jar;g="commons-c\r\n odec";a="commons-codec";v="1.11",httpmime-4.5.9.jar;g="org.apache.htt\r\n pcomponents";a="httpmime";v="4.5.9",gson-2.8.5.jar;g="com.google.code\r\n .gson";a="gson";v="2.8.5",communitydetection-rest-model-0.8.1.jar;g="\r\n org.ndexbio.communitydetection.rest.model";a="communitydetection-rest\r\n -model";v="0.8.1",swagger-annotations-2.0.0.jar;g="io.swagger.core.v3\r\n ";a="swagger-annotations";v="2.0.0",logback-classic-1.2.3.jar;g="ch.q\r\n os.logback";a="logback-classic";v="1.2.3",logback-core-1.2.3.jar;g="c\r\n h.qos.logback";a="logback-core";v="1.2.3",slf4j-api-1.7.25.jar;g="org\r\n .slf4j";a="slf4j-api";v="1.7.25",jackson-databind-2.10.1.jar;g="com.f\r\n asterxml.jackson.core";a="jackson-databind";v="2.10.1",jackson-annota\r\n tions-2.10.1.jar;g="com.fasterxml.jackson.core";a="jackson-annotation\r\n s";v="2.10.1",jackson-core-2.10.1.jar;g="com.fasterxml.jackson.core";\r\n a="jackson-core";v="2.10.1",jackson-jaxrs-base-2.10.1.jar;g="com.fast\r\n erxml.jackson.jaxrs";a="jackson-jaxrs-base";v="2.10.1",ndex-object-mo\r\n del-2.5.0-20200508.163437-2.jar;g="org.ndexbio";a="ndex-object-model"\r\n ;v="2.5.0-SNAPSHOT"\r\nExport-Package: org.cytoscape.app.communitydetection.subnetwork;uses:=\r\n "javax.swing,org.cytoscape.app.communitydetection.util,org.cytoscape.\r\n application.swing,org.cytoscape.model,org.cytoscape.model.subnetwork,\r\n org.cytoscape.session,org.cytoscape.task,org.cytoscape.view.layout,or\r\n g.cytoscape.view.model,org.cytoscape.view.vizmap,org.cytoscape.work";\r\n version="1.11.0",org.cytoscape.app.communitydetection.hierarchy;uses:\r\n ="javax.swing,org.cytoscape.app.communitydetection.cx2,org.cytoscape.\r\n app.communitydetection.edgelist,org.cytoscape.app.communitydetection.\r\n event,org.cytoscape.app.communitydetection.rest,org.cytoscape.app.com\r\n munitydetection.util,org.cytoscape.application.swing,org.cytoscape.mo\r\n del,org.cytoscape.model.subnetwork,org.cytoscape.session,org.cytoscap\r\n e.task,org.cytoscape.task.read,org.cytoscape.view.layout,org.cytoscap\r\n e.view.model,org.cytoscape.view.vizmap,org.cytoscape.work";version="1\r\n .11.0",org.cytoscape.app.communitydetection.util;uses:="javax.swing,o\r\n rg.cytoscape.model";version="1.11.0",org.cytoscape.app.communitydetec\r\n tion.cx2;version="1.11.0",org.cytoscape.app.communitydetection;uses:=\r\n "javax.swing,org.cytoscape.app.communitydetection.event,org.cytoscape\r\n .app.communitydetection.hierarchy,org.cytoscape.app.communitydetectio\r\n n.util,org.cytoscape.application.swing,org.cytoscape.model,org.cytosc\r\n ape.property,org.cytoscape.service.util,org.cytoscape.task,org.cytosc\r\n ape.work,org.osgi.framework";version="1.11.0",org.cytoscape.app.commu\r\n nitydetection.iquery;uses:="org.cytoscape.app.communitydetection.util\r\n ,org.cytoscape.application.swing,org.cytoscape.model,org.cytoscape.ta\r\n sk,org.cytoscape.view.model,org.cytoscape.work";version="1.11.0",org.\r\n cytoscape.app.communitydetection.termmap;uses:="org.cytoscape.app.com\r\n munitydetection.hierarchy,org.cytoscape.application.swing,org.cytosca\r\n pe.model,org.cytoscape.task,org.cytoscape.view.model,org.cytoscape.wo\r\n rk";version="1.11.0",org.cytoscape.app.communitydetection.edgelist;us\r\n es:="org.cytoscape.io.write,org.cytoscape.model,org.cytoscape.work";v\r\n ersion="1.11.0",org.cytoscape.app.communitydetection.event;version="1\r\n .11.0",org.cytoscape.app.communitydetection.rest;uses:="org.cytoscape\r\n .work";version="1.11.0"\r\nImport-Package: groovy.lang;resolution:=optional,javax.crypto;resoluti\r\n on:=optional,javax.crypto.spec;resolution:=optional,javax.mail;resolu\r\n tion:=optional,javax.mail.internet;resolution:=optional,javax.managem\r\n ent;resolution:=optional,javax.naming;resolution:=optional,javax.nami\r\n ng.directory;resolution:=optional,javax.naming.ldap;resolution:=optio\r\n nal,javax.net;resolution:=optional,javax.net.ssl;resolution:=optional\r\n ,javax.security.auth.x500;resolution:=optional,javax.servlet;resoluti\r\n on:=optional,javax.servlet.http;resolution:=optional,javax.sql;resolu\r\n tion:=optional,javax.swing;resolution:=optional,javax.swing.border;re\r\n solution:=optional,javax.swing.event;resolution:=optional,javax.ws.rs\r\n .core;resolution:=optional,javax.ws.rs.ext;resolution:=optional,javax\r\n .xml.datatype;resolution:=optional,javax.xml.namespace;resolution:=op\r\n tional,javax.xml.parsers;resolution:=optional,javax.xml.stream;resolu\r\n tion:=optional,javax.xml.stream.events;resolution:=optional,org.apach\r\n e.avalon.framework.logger;resolution:=optional;version="[4.3,5)",org.\r\n apache.log;resolution:=optional,org.apache.log4j;resolution:=optional\r\n ;version="[1.2,2)",org.codehaus.commons.compiler;resolution:=optional\r\n ,org.codehaus.groovy.control;resolution:=optional,org.codehaus.groovy\r\n .control.customizers;resolution:=optional,org.codehaus.groovy.reflect\r\n ion;resolution:=optional,org.codehaus.groovy.runtime;resolution:=opti\r\n onal,org.codehaus.groovy.runtime.callsite;resolution:=optional,org.co\r\n dehaus.groovy.runtime.typehandling;resolution:=optional,org.codehaus.\r\n groovy.runtime.wrappers;resolution:=optional,org.codehaus.groovy.tran\r\n sform;resolution:=optional,org.codehaus.janino;resolution:=optional,o\r\n rg.cytoscape.app.communitydetection.event;resolution:=optional,org.cy\r\n toscape.application.swing;resolution:=optional;version="[3.7,4)",org.\r\n cytoscape.io.write;resolution:=optional;version="[3.7,4)",org.cytosca\r\n pe.model;resolution:=optional;version="[3.7,4)",org.cytoscape.model.s\r\n ubnetwork;resolution:=optional;version="[3.7,4)",org.cytoscape.proper\r\n ty;resolution:=optional;version="[3.7,4)",org.cytoscape.service.util;\r\n resolution:=optional;version="[3.7,4)",org.cytoscape.session;resoluti\r\n on:=optional;version="[3.7,4)",org.cytoscape.task;resolution:=optiona\r\n l;version="[3.7,4)",org.cytoscape.task.read;resolution:=optional;vers\r\n ion="[3.7,4)",org.cytoscape.view.layout;resolution:=optional;version=\r\n "[3.7,4)",org.cytoscape.view.model;resolution:=optional;version="[3.7\r\n ,4)",org.cytoscape.view.vizmap;resolution:=optional;version="[3.7,4)"\r\n ,org.cytoscape.work;resolution:=optional;version="[3.7,4)",org.ietf.j\r\n gss;resolution:=optional,org.osgi.framework;resolution:=optional;vers\r\n ion="[1.8,2)",org.w3c.dom;resolution:=optional,org.w3c.dom.bootstrap;\r\n resolution:=optional,org.w3c.dom.ls;resolution:=optional,org.xml.sax;\r\n resolution:=optional,org.xml.sax.helpers;resolution:=optional,sun.mis\r\n c;resolution:=optional,sun.reflect;resolution:=optional\r\nRequire-Capability: osgi.ee;filter:="(&(osgi.ee=JavaSE)(version=1.8))"\r\nTool: Bnd-4.2.0.201903051501\r\n\r\n'


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