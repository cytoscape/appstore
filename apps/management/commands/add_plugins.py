import sys
from xml.dom.minidom import parse
from urllib import urlopen
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.models import App, Author, AuthorOrder
from CyAppStore.util.id_util import fullname_to_name
from CyAppStore.apps.views import _parse_iso_date

PLUGINS_XML_URL = 'http://cytoscape.org/plugins/plugins.xml'

def dom_to_std_obj(dom_obj):
    result = dict()
    
    result['description'] = dom_obj.getElementsByTagName('description')[0].childNodes[0].nodeValue
    result['version'] = dom_obj.getElementsByTagName('pluginVersion')[0].childNodes[0].nodeValue
    result['release-date'] = dom_obj.getElementsByTagName('release_date')[0].childNodes[0].nodeValue
    
    authors_dom = dom_obj.getElementsByTagName('authorlist')
    if authors_dom and authors_dom[0].hasChildNodes():
        authors = list()
        for author_dom in authors_dom[0].childNodes:
            name_dom = author_dom.getElementsByTagName('name')
            if name_dom and name_dom[0].hasChildNodes():
                name = name_dom[0].childNodes[0].nodeValue
            else:
                continue

            institutions_dom = author_dom.getElementsByTagName('institution')
            if institutions_dom and institutions_dom[0].hasChildNodes():
                institution = institutions_dom[0].childNodes[0].nodeValue
                authors.append((name, institution))
            else:
                authors.append((name, None))
        result['authors'] = authors
    
    cy_versions = list()
    cy_versions_dom = dom_obj.getElementsByTagName('cytoscapeVersions')[0]
    for cy_version_dom in cy_versions_dom.childNodes:
        cy_versions.append(cy_version_dom.childNodes[0].nodeValue)
    result['cy-versions'] = cy_versions
    
    result['download'] = dom_obj.getElementsByTagName('url')[0].childNodes[0].nodeValue
    
    return result

def gather_plugins_by_name_and_version(plugins):
    result = defaultdict(dict)
    for plugin in plugins:
        names = plugin.getElementsByTagName('name')
        if not len(names): continue
        name = names[0].childNodes[0].nodeValue
        version = plugin.getElementsByTagName('pluginVersion')[0].childNodes[0].nodeValue
        result[name][version] = dom_to_std_obj(plugin)
    return result

def extract_latest_version(plugins):
    result = dict()
    for name in plugins:
        versions = plugins[name]
        latest_version = max(versions)
        latest_plugin = versions[latest_version]
        result[name] = latest_plugin
    return result

class Command(BaseCommand):
    def handle(self, *args, **options):
        input_file = urlopen(PLUGINS_XML_URL)
        #input_file = open('plugins.xml', 'r')
        dom_root = parse(input_file)
        input_file.close()
        
        plugins = dom_root.getElementsByTagName('plugin')
        plugins_by_name_and_version = gather_plugins_by_name_and_version(plugins)
        plugins_by_name = extract_latest_version(plugins_by_name_and_version)

        for arg in args:
            if not arg in plugins_by_name:
                print '"%s" not found in plugins.xml' % arg
                return
    
        for fullname in args:
            plugin = plugins_by_name[fullname]
            plugin_name = fullname_to_name(fullname)
            
            print '%s:' % plugin_name,
            sys.stdout.flush()
            app, _ = App.objects.get_or_create(name = plugin_name)
            if not app.fullname: app.fullname = fullname

            if not app.details and plugin['description']:
                app.details = plugin['description']

            if not app.authors.count() and 'authors' in plugin:
                author_order = 0
                for name, institution in plugin['authors']:
                    author, _ = Author.objects.get_or_create(name = name, institution = institution)
                    author_order = AuthorOrder.objects.create(app = app, author = author, author_order = author_order)

            app.cy_2x_plugin_download = plugin['download']
            app.cy_2x_plugin_version = plugin['version']
            app.cy_2x_plugin_release_date = _parse_iso_date(plugin['release-date'])
            app.cy_2x_versions = ', '.join(plugin['cy-versions'])
            app.save()

            print 'done.'
            sys.stdout.flush()