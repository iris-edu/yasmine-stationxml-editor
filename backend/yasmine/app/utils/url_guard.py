# 2026-09-19, version 4.2.0-beta: ASGSR, Alexey Emanov
# URL guards against SSRF (scheme, host, resolved IP).

import ipaddress
import socket
from urllib.parse import urlparse

DOWNLOAD_SCHEMES = ('https',)
NRL_SCHEMES = ('http', 'https')

DEFAULT_ALLOWED_HOSTS = (
    'gitlab.com',
    'service.earthscope.org',
    'service.iris.edu',
    'ds.iris.edu',
    'www.iris.edu',
)


class UrlGuardError(ValueError):
    pass


def _host_allowed(host, allowed_hosts):
    host = (host or '').lower().rstrip('.')
    for allowed in allowed_hosts:
        allowed = allowed.lower()
        if host == allowed or host.endswith('.' + allowed):
            return True
    return False


def _is_blocked_ip(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def _looks_like_decimal_or_raw_ip(host):
    if not host:
        return True
    if host.isdigit():
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _is_loopback_hostname(host):
    host = (host or '').lower().rstrip('.')
    return host in ('localhost', 'ip6-localhost', 'ip6-loopback') or host.endswith('.localhost')


def validate_url(
    url,
    schemes=DOWNLOAD_SCHEMES,
    allowed_hosts=DEFAULT_ALLOWED_HOSTS,
    require_allowlist=True,
    allow_private_hostnames=False,
):
    if not url or not isinstance(url, str):
        raise UrlGuardError('Invalid URL')
    parsed = urlparse(url.strip())
    if parsed.scheme not in schemes:
        raise UrlGuardError('URL scheme is not allowed')
    host = (parsed.hostname or '').lower()
    if not host:
        raise UrlGuardError('URL host is missing')
    if host.isdigit():
        raise UrlGuardError('Decimal IP hosts are not allowed')
    is_raw_ip = _looks_like_decimal_or_raw_ip(host)
    if is_raw_ip and require_allowlist:
        # raw IPs are only acceptable after they pass the private-IP check below
        # and only when they are also on the allowlist (typically they are not).
        if not _host_allowed(host, allowed_hosts):
            raise UrlGuardError('Raw IP hosts are not allowed')
    elif require_allowlist and not _host_allowed(host, allowed_hosts):
        raise UrlGuardError('Host is not allowed')

    # NRL and similar admin-configured services are reached by hostname
    # (e.g. vh07.gsn, host.docker.internal). Those names often resolve to
    # private IPs; that is allowed. Raw IPs and localhost stay blocked.
    if allow_private_hostnames and not is_raw_ip:
        if _is_loopback_hostname(host):
            raise UrlGuardError('Host is not allowed')
        return parsed.geturl()

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80))
    except socket.gaierror as err:
        raise UrlGuardError('Cannot resolve host: %s' % err)
    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise UrlGuardError('Resolved address is not public')
    return parsed.geturl()
