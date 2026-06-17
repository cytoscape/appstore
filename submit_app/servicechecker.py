# ...existing code...
import logging
import socket
import ipaddress
from urllib.parse import urlparse

import requests
import json

LOGGER = logging.getLogger(__name__)

# minimal required fields in your service metadata
REQUIRED_FIELDS = ['name']

# networks we treat as private/local to avoid SSRF
_PRIVATE_NETWORKS = (
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
)


class ServiceCheckError(Exception):
    """Raised when a service metadata fetch/validation fails."""
    pass


def _host_is_private(hostname: str) -> bool:
    """Resolve hostname and return True if any resolved IP is private/local."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        LOGGER.debug("DNS resolution failed for %s", hostname)
        return True  # treat unresolved hosts as unsafe

    for _, _, _, _, sockaddr in infos:
        ip = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                LOGGER.debug("Host %s resolves to private IP %s", hostname, ip)
                return True
    return False


def fetch_json(url: str, timeout: int = 5, maxbytes: int = 50_000) -> dict:
    """
    Fetch JSON from `url` and return parsed object.
    Raises ServiceCheckError on errors.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ServiceCheckError("Invalid URL")

    hostname = parsed.hostname
    if not hostname:
        raise ServiceCheckError("Invalid URL (no hostname)")

    if _host_is_private(hostname):
        raise ServiceCheckError("Refusing to fetch private or unresolved host")

    headers = {'Accept': 'application/json'}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ServiceCheckError(f"Network error: {exc}")

    # enforce maxbytes
    content = b''
    try:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                if len(content) > maxbytes:
                    raise ServiceCheckError("Response too large")
    finally:
        resp.close()

    try:
        return json.loads(content.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ServiceCheckError("Invalid JSON response") from exc


def check_reachable(url: str) -> dict:
    """
    Fetch and validate service metadata at `url`. Ensures required fields exist.
    Returns metadata dict on success or raises ServiceCheckError.
    """
    metadata = fetch_json(url)
    if not isinstance(metadata, dict):
        raise ServiceCheckError("Response must be a JSON object")

    missing_fields = [f for f in REQUIRED_FIELDS if not metadata.get(f)]
    if missing_fields:
        raise ServiceCheckError("Missing required field(s): %s" % ", ".join(missing_fields))

    # normalize version to string if present
    if 'version' in metadata and metadata['version'] is not None:
        metadata['version'] = str(metadata['version'])

    return metadata


def check_service_status(url: str, maxbytes: int = 10_000) -> dict:
    status_url = url.rstrip('/') + '/status'
    status = fetch_json(status_url, maxbytes=maxbytes)
    if not isinstance(status, dict) or 'status' not in status:
        raise ServiceCheckError("Status response missing 'status' field")
    return status
# ...existing code...