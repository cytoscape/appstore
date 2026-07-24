import json
import zipfile
from apps.models import WebBundleRelease
from django.core.files.storage import storages
from django.core.files.base import ContentFile


def bundle_catalog_entry(release: WebBundleRelease) -> dict:
    return {
        'id': release.app.name,
        'name': release.app.fullname,
        'version': release.version,
        'url': release.remote_entry_url,
        'author': release.author,
        'description': release.description,
        'license': release.license,
        'tags': release.tags,
    }

def write_manifest_json(release: WebBundleRelease):
    web_storage = storages['web_bundles']
    manifest_data = json.dumps([bundle_catalog_entry(release)])
    path = f"{release.app.name}/{release.version}/manifest.json"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(manifest_data.encode()))
"""
def _copy_remote_entry_to_storage(remote_entry, destination: str):
    remote_entry.seek(0)
    web_storage = storages['web_bundles']
    path = f"{destination}remoteEntry.js"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(remote_entry.read()))
    """
def _copy_bundle_to_storage(zip_file, destination: str):
    """Copies every file in the validated bundle zip to storage,
    preserving relative paths (remoteEntry.js, chunks/, assets/, etc.)"""
    web_storage = storages['web_bundles']
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