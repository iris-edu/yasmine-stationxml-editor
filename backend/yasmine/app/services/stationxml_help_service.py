# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
"""Read-only access to the generated StationXML 1.2 help catalog."""

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from tornado.web import HTTPError


STATIONXML_HELP_VERSION = '1.2'


def stationxml_help_resource_dir():
    return (
        Path(__file__).resolve().parents[2]
        / 'resources'
        / 'schemas'
        / 'stationxml'
        / STATIONXML_HELP_VERSION
    )


def stationxml_help_catalog_path():
    return stationxml_help_resource_dir() / 'catalog.json'


@lru_cache(maxsize=1)
def _catalog_record():
    path = stationxml_help_catalog_path()
    raw = path.read_bytes()
    catalog = json.loads(raw.decode('utf-8'))
    metadata = catalog.get('metadata') or {}
    if metadata.get('schemaVersion') != STATIONXML_HELP_VERSION:
        raise ValueError('StationXML help catalog version is not 1.2')
    if metadata.get('entryCount') != len(catalog.get('nodes') or {}):
        raise ValueError('StationXML help catalog entry count is inconsistent')
    return catalog, sha256(raw).hexdigest()


def clear_stationxml_help_cache():
    _catalog_record.cache_clear()


class StationXmlHelpService:
    def catalog(self):
        catalog, _ = _catalog_record()
        return catalog

    def catalog_copy(self):
        return deepcopy(self.catalog())

    def etag(self):
        _, digest = _catalog_record()
        return '"%s"' % digest

    def entry(self, path):
        if not path:
            raise HTTPError(400, reason='StationXML schema path is required')
        entry = self.catalog().get('nodes', {}).get(path)
        if entry is None:
            raise HTTPError(
                404,
                reason="StationXML schema path '%s' was not found" % path,
            )
        return entry

    def breadcrumbs(self, path):
        nodes = self.catalog()['nodes']
        result = []
        current = path
        while current:
            entry = nodes.get(current)
            if entry is None:
                break
            result.append({
                'path': current,
                'xmlName': entry['xmlName'],
                'kind': entry['kind'],
            })
            current = entry.get('parentPath')
        result.reverse()
        return result

    def entry_payload(self, path):
        catalog = self.catalog()
        return {
            'metadata': catalog['metadata'],
            'rootPath': catalog['rootPath'],
            'entry': self.entry(path),
            'breadcrumbs': self.breadcrumbs(path),
        }
