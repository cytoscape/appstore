import socket
import ipaddress
import json
import requests
from urllib.parse import urlparse

REQUIRED_METADATA_FIELDS = ('name', 'version', 'author')


class ServiceCheckError(Exception):
    pass


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
    except Exception:
        raise ServiceCheckError('Could not resolve hostname')

    return (
        ip_obj.is_private or
        ip_obj.is_loopback or
        ip_obj.is_link_local or
        ip_obj.is_reserved
    )


def check_reachable(url: str, maxbytes: int = 1024, allow_local: bool=False) -> dict:
    """
    Quick check that the URL is reachable and returns valid service
    metadata. Raises ServiceCheckError on any failure, returns the
    metadata dict on success.

    """
    parsed = urlparse(url) #

    if not parsed.hostname:
        raise ServiceCheckError('URL is required')

    if parsed.scheme not in ('http', 'https'):
        raise ServiceCheckError('Only HTTP/HTTPS allowed')

    if not allow_local and _is_private_ip(parsed.hostname):
        raise ServiceCheckError('Internal IPs are blocked')

    try:
        response = requests.get(url, timeout=10, allow_redirects=False, verify=False)
    except requests.RequestException as e:
        raise ServiceCheckError(f'Could not reach service: {e}')

    if response.status_code != 200:
        response.close()
        raise ServiceCheckError(f'Service returned status {response.status_code}')

    content = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=512):
            if not chunk:
                continue    
            content.extend(chunk)
            if len(content) > maxbytes:
                raise ServiceCheckError('response too large')
    finally:
        response.close()
    try:
        metadata = response.json()
    except ValueError:
        raise ServiceCheckError('Service did not return valid JSON')

    if not isinstance(metadata, dict):
        raise ServiceCheckError('Metadata response must be a JSON object')

    missing = [f for f in REQUIRED_METADATA_FIELDS if not metadata.get(f)]
    if missing:
        raise ServiceCheckError(f"Missing required field(s): {', '.join(missing)}")

    return metadata


def check_metadata(url: str, allow_local: bool = False) -> dict:
    return check_reachable(url, allow_local=allow_local)


def check_service_status(url: str) -> dict:
    status_url = url.rstrip('/') + '/status'

    try:
        response = requests.get(status_url, timeout=10, allow_redirects=False)
        response.raise_for_status()
        status = response.json()
    except requests.RequestException as e:
        raise ServiceCheckError(f'Status check failed: {e}')
    except ValueError:
        raise ServiceCheckError('Invalid status response')

    if not isinstance(status, dict) or 'status' not in status:
        raise ServiceCheckError("Status response missing 'status' field")

    return status