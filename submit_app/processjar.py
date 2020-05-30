from zipfile import ZipFile, BadZipfile
from .mfparse import max_of_lower_cytoscape_pkg_versions, parse_app_dependencies
from apps.models import App, Release, VersionRE
from django.utils.encoding import smart_text
from util.view_util import get_object_or_none

_MANIFEST_FILE_NAME = 'META-INF/MANIFEST.MF'
_MAX_MANIFEST_FILE_SIZE_B = 1024 * 1024


def process_jar(jar_file, expect_app_name):

    try:
        archive = ZipFile(jar_file.temporary_file_path())
    except BadZipfile as IOError:
        raise ValueError('is not a valid zip file')

    manifest_file = archive.read(_MANIFEST_FILE_NAME)
    manifest = ParseManifest(manifest_file)
    archive.close()

    is_osgi_bundle = True if manifest.main_section[b'Bundle-SymbolicName'] else False
    parser_func = _parse_osgi_bundle # if is_osgi_bundle else _parse_simple_app
    app_name, app_ver, app_works_with, app_dependencies, has_export_pkg = parser_func(manifest)

    app_name = smart_text(app_name, errors='replace')
    if expect_app_name and (not app_name == expect_app_name):
        raise ValueError('has app name as <tt>%s</tt> but must be <tt>%s</tt>' % (app_name, expect_app_name))
    app_ver = smart_text(app_ver, errors='replace')
    app_works_with = smart_text(app_works_with, errors='replace')

    try:
        app_dependencies = list(_app_dependencies_to_releases(app_dependencies))
    except ValueError as e:
        (msg, ) = e.args
        raise ValueError('has a problem with its manifest for entry <tt>Cytoscape-App-Dependencies</tt>: ' + msg)

    return app_name, app_ver, app_works_with, app_dependencies, has_export_pkg


class Manifest(object):

    def __init__(self, main_section, sections):
        self.main_section = main_section
        self.sections = sections


def ParseManifest(manifest_string):
    manifest_string = b'\n'.join(manifest_string.splitlines()).rstrip(b'\n')
    section_strings = manifest_string.split(b'\n\n')
    parsed_sections = [_ParseManifestSection(s) for s in section_strings]
    main_section = parsed_sections[0]
    try:
        sections = dict((entry[b'Name'], entry) for entry in parsed_sections[1:])
    except KeyError:
        raise InvalidJarError('Manifest entry has no Name attribute: %s' % entry)
    return Manifest(main_section, sections)


def _ParseManifestSection(section):
    section = section.replace(b'\n ', b'')
    try:
        return dict(line.split(b': ', 1) for line in section.split(b'\n'))
    except ValueError:
        raise InvalidJarError('Invalid manifest %r' % section)


def _app_dependencies_to_releases(app_dependencies):
    for dependency in app_dependencies:
        app_name, app_version = dependency

        app = get_object_or_none(App, active = True, fullname = app_name)
        if not app:
            raise ValueError('dependency on "%s": no such app exists' % app_name)

        release = get_object_or_none(Release, app = app, version = app_version, active = True)
        if not release:
            raise ValueError('dependency on "%s" with version "%s": no such release exists' % (app_name, app_version))

        yield release


def _get_manifest_file(zip_archive):
    try:
        manifest_info = zip_archive.getinfo(_MANIFEST_FILE_NAME)
    except KeyError:
        raise ValueError('does not have a manifest file located in <tt>%s</tt>' % _MANIFEST_FILE_NAME)

    if manifest_info.file_size > _MAX_MANIFEST_FILE_SIZE_B:
        raise ValueError('has a manifest file that\'s too large; it can be at most %d bytes but is %d bytes' % (_MAX_MANIFEST_FILE_SIZE_B, manifest_info.file_size))

    try:
        manifest_file = zip_archive.open(_MANIFEST_FILE_NAME , 'r')
        return manifest_file
    except IOError:
        raise ValueError('does not have an accessible manifest file located in <tt>%s</tt>' % _MANIFEST_FILE_NAME)


def _last(d, k):
    v = d.get(k)
    return v[-1] if v else None


def _get_name_and_version(manifest, name_attr, version_attr):
    app_name = manifest.main_section[name_attr]
    app_name = app_name.decode('utf-8')
    #_last(manifest, name_attr)
    if not app_name:
        raise ValueError('does not have <tt>%s</tt> in its manifest' % name_attr)

    app_version = manifest.main_section[version_attr]
    app_version = app_version.decode('utf-8')
    #_last(manifest, version_attr)
    if not app_version:
        raise ValueError('does not have <tt>%s</tt> in its manifest' % version_attr)
    #if not VersionRE.match(str(app_version)):
        #raise ValueError('<tt>%s</tt> does not follow this format: <i>major</i>[.<i>minor</i>][.<i>patch</i>][.<i>tag</i>]' % version_attr)

    return (app_name, app_version)


def _parse_simple_app(manifest):
    app_name, app_version = _get_name_and_version(manifest, 'Cytoscape-App-Name', 'Cytoscape-App-Version')

    app_works_with = manifest.main_section[b'Cytoscape-API-Compatibility']
    #_last(manifest, 'Cytoscape-API-Compatibility')
    if not app_works_with:
        raise ValueError('does not have <tt>Cytoscape-API-Compatibility</tt> in its manifest')

    app_dependencies = list() # simple apps can't have dependencies
    has_export_pkg = False # simple apps can't export packages

    return (app_name, app_version, app_works_with, app_dependencies, has_export_pkg)


def _ver_tuple_to_str(tup):
    return tup[0] + ('.' + tup[1] if tup[1] else '') + ('.' + tup[2] if tup[2] else '') + ('.' + tup[3] if tup[3] else '')


def _parse_osgi_bundle(manifest):
    app_name, app_version = _get_name_and_version(manifest, b'Bundle-Name', b'Bundle-Version')
    import_packages = manifest.main_section[b'Import-Package']

    import_packages = import_packages.decode("utf-8")
    if not import_packages:
        raise ValueError('does not import any packages--<tt>Import-Package</tt> is not in its manifest')

    max_cy_ver = max_of_lower_cytoscape_pkg_versions(import_packages)
    if max_cy_ver:
        app_works_with = _ver_tuple_to_str(max_cy_ver)
    else:
        raise ValueError('does not import Cytoscape packages in <tt>Import-Package</tt>')
    try:
        app_dependencies_str = di
        app_dependencies_str = app_dependencies_str.decode('utf-8')
    except:
        app_dependencies_str = None
    if app_dependencies_str:
        try:
            app_dependencies = list(parse_app_dependencies(app_dependencies_str))
        except ValueError as e:
            (msg, ) = e.args
            raise ValueError('has a problem with the <tt>Cytoscape-App-Dependencies</tt> entry: ' + msg)
    else:
        app_dependencies = list()
    try:
        has_export_pkg_str = manifest.main_section[b'Export-Package']
        has_export_pkg_str = has_export_pkg_str.decode('utf-8')
    except:
        has_export_pkg_str = None
    has_export_pkg = True if has_export_pkg_str else False

    return (app_name, app_version, app_works_with, app_dependencies, has_export_pkg)
