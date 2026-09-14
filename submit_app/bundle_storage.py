import json
import zipfile
from apps.models import WebBundleRelease
from django.core.files.storage import storages
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError


def bundle_catalog_entry(release: WebBundleRelease) -> dict:
    return {
        # NOT release.app.name. That is the store's URL slug; this must be the
        # bundle's Module Federation container name or Cytoscape Web refuses to
        # load the app. make_bundle_release always sets cy_app_id, so there is
        # no fallback here on purpose: a slug-shaped id that is wrong looks
        # exactly like a correct one until the install fails.
        'id': release.cy_app_id,
        'name': release.app.fullname,
        'version': release.version,
        'url': release.remote_entry_url,
        'author': release.author,
        'description': release.description,
        'license': release.license,
        'tags': release.tags,
    }

def write_manifest_json(release: WebBundleRelease):
    web_storage = storages['webbundles']
    manifest_data = json.dumps([bundle_catalog_entry(release)])
    path = f"{release.app.name}/{release.version}/manifest.json"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(manifest_data.encode()))
"""
def _copy_remote_entry_to_storage(remote_entry, destination: str):
    remote_entry.seek(0)
    web_storage = storages['webbundles']
    path = f"{destination}remoteEntry.js"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(remote_entry.read()))
    """
def _copy_bundle_to_storage(zip_file, destination: str):
    """Copies every file in the validated bundle zip to storage,
    preserving relative paths (remoteEntry.js, chunks/, assets/, etc.)"""
    web_storage = storages['webbundles']
    zip_file.seek(0)

    with zipfile.ZipFile(zip_file) as zf:
        for member in zf.namelist():
            if member.endswith('/'):
                continue  # skip directory entries
            path = f"{destination}{member}"
            if web_storage.exists(path):
                web_storage.delete(path)
            with zf.open(member) as source:
                web_storage.save(path, ContentFile(source.read()))


def write_pending_manifest_json(pending):
    web_storage = storages['webbundles']
    manifest_data = json.dumps([{
        # WebBundlePending.name is this model's cy_app_id: the upload view
        # sets it from cy-manifest.json, which _extract_cy_manifest requires.
        'id': pending.name,
        'name': pending.fullname,
        'version': pending.version,
        'url': pending.remote_entry_url,
        'author': pending.author,
        'description': pending.description,
        'license': pending.license,
        'tags': pending.tags,
    }]).encode()
    path = f"{pending.bundle_path}manifest.json"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(manifest_data))

def _extract_cy_manifest(zip_file):
    try:
        with zipfile.ZipFile(zip_file) as zf:
            print(zf.namelist())
            names = zf.namelist()
            cy_manifest_name = next((n for n in names if n.endswith('cy-manifest.json')), None)
            if cy_manifest_name is None:
                raise ValidationError(
                    "Bundle is missing cy-manifest.json. Rebuild your app with a "
                    "recent version of create-cytoscape-app to generate this file."
                )
            
            with zf.open(cy_manifest_name) as f:
                try:
                    manifest = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise ValidationError('cy-manifest is present but not a valid json')
                
                required_keys = {'id', 'name', 'version'}
                missing = required_keys - manifest.keys()

                if missing:
                    raise ValidationError(f"cy-manifest.json is missing required field(s): {', '.join(sorted(missing))}")
                
                return manifest


    except zipfile.BadZipFile:
        raise ValidationError('Bundle is not a valid zip file')    