import json
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

def _copy_remote_entry_to_storage(remote_entry, destination: str):
    remote_entry.seek(0)
    web_storage = storages['web_bundles']
    path = f"{destination}remoteEntry.js"
    if web_storage.exists(path):
        web_storage.delete(path)
    web_storage.save(path, ContentFile(remote_entry.read()))