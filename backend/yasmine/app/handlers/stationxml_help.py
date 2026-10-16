# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
"""HTTP API for the generated StationXML 1.2 help catalog."""

from yasmine.app.handlers.base import BaseHandler
from yasmine.app.services.stationxml_help_service import StationXmlHelpService


class StationXmlHelpHandler(BaseHandler):
    SUPPORTED_METHODS = ['GET', 'OPTIONS']

    def get(self, *_, **__):
        service = StationXmlHelpService()
        etag = service.etag()
        self.set_header('ETag', etag)
        self.set_header('Cache-Control', 'public, max-age=31536000, immutable')

        if self.request.headers.get('If-None-Match') == etag:
            self.set_status(304)
            self.finish()
            return

        path = self.get_argument('path', None)
        if path:
            self.write(service.entry_payload(path))
        else:
            self.write(service.catalog())
