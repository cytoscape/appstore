import socket
import ipaddress
import requests
import json
from urllib.parse import urlparse
import urllib3

REQUIRED_METADATA_FIELDS = ('name', 'version', 'author')
 
ALLOWED_SCHEMES = ('http', 'https')
ALLOWED_PORTS = {80, 443}


class ServiceCheckError(Exception):
    pass

def _resolve_safe_ip(hostname: str) -> str:

    try:
        ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ServiceCheckError('unable to resolve hostname')

    if not ips:
        raise ServiceCheckError('Could not resolve hostname')
    
    for ip in ips:
        ip_str = ip[4][0]

        try:
            ip_obj = addr.ip_address(ip_str)
        except ValueError:
            raise ServiceCheckError('Could not resolve hostname')
        
        if (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local 
            or ip_obj.is_reserved or ip_obj.is_multicast 
            or ip_obj.is_unspecified):
            raise ServiceCheckError('Internal IPs are blocked')
    return infos[0][4][0] #returns first tested ip


def _fetch_pinned(parsed_url, hostname: str, ip: str, maxbytes: int, allow_local: bool = False) -> bytes:
    """
    Fetch `parsed_url` over a connection pinned to `ip`, sending the
    original hostname as the Host header (and TLS SNI, for https) so
    virtual hosting / cert validation still work normally.
    """
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
 
    if port not in ALLOWED_PORTS and not allow_local:
        raise ServiceCheckError('Only ports 80/443 are allowed')
 
    if parsed_url.scheme == 'https':
        pool = urllib3.HTTPSConnectionPool(
            ip,
            port=port,
            assert_hostname=hostname,
            server_hostname=hostname,
            timeout=10,
            retries=False,
        )
    else:
        pool = urllib3.HTTPConnectionPool(
            ip,
            port=port,
            timeout=10,
            retries=False,
        )
 
    path = parsed_url.path or '/'
    if parsed_url.query:
        path += '?' + parsed_url.query
 
    try:
        response = pool.request(
            'GET',
            path,
            headers={'Host': hostname},
            preload_content=False,
            redirect=False,
        )
    except urllib3.exceptions.HTTPError as e:
        raise ServiceCheckError(f'Request failed: {e}')
    finally:
        pool.close()
 
    if response.status != 200:
        raise ServiceCheckError(f'Request failed with status {response.status}')
 
    content = bytearray()
    try:
        for chunk in response.stream(1024):
            content.extend(chunk)
            if len(content) > maxbytes:
                raise ServiceCheckError('Response too large')
    finally:
        response.release_conn()
 
    return bytes(content)

def _validate_url(url: str):
    if not url:
        raise ServiceCheckError('URL is required')

    parsed = urlparse(url)

    if not parsed.hostname:
        raise ServiceCheckError('URL is required')

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ServiceCheckError('Only HTTP/HTTPS allowed')

    ip = _resolve_safe_ip(hostname)

    return parsed, ip

def fetch_json(url: str, maxytes: int=50_000) -> dict:

    parsed, ip = _validate_url(url)

    try:
        content = _fetch_pinned(parsed, parsed.hostname, ip, maxbytes)
    except ServiceCheckError:
        raise
    except Exception as e:
        raise ServiceCheckError(f'Request Failed: {e}')

    try:
        return json.loads(content.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ServiceCheckError('Invalid JSON response')


def check_reachable(url: str) -> None:

    parsed, ip = _validate_url(url)

    _fetch_pinned(parsed, parsed.hostname, ip, maxbytes=50_000)

    metadata = fetch_json(url, maxbytes=maxbytes)
    if not isinstance(metadata, dict):
        raise ServiceCheckError('Response must be a JSON object')

    missing_fields = [f for f in REQUIRED_FIELDS if not metadata.get(f)]
    
    if missing_fields:
        raise ServiceCheckError(f"Missing required field(s): {' ,' .join(missing_field)}")

    return metadata

def check_service_status(url: str, maxbytes: int = 10_000) -> dict:

    status_url = url.rstrip('/') + '/status'
    status = fetch_json(status_url, maxbytes=maxbytes)
 
    if not isinstance(status, dict) or 'status' not in status:
        raise ServiceCheckError("Status response missing 'status' field")
 
    return status
