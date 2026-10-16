# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from yasmine.app.models import XmlModel
from yasmine.app.utils.facade import HandlerMixin
from tornado.web import HTTPError
from yasmine.app.utils.date import get_utcnow_naive
from yasmine.app.utils.imp_exp import ConvertToInventory
from yasmine.app.utils.stationxml_codec import serialize_inventory_12
from yasmine.app.utils.stationxml_strict_validation import validate_inventory_strict
from yasmine.app.utils.stationxml_validation import (
    validate_inventory_recommendations,
    validate_stationxml_12,
)


class XmlService(HandlerMixin):
    def update_timestamp(self, xml_id):
        self.db.query(XmlModel) \
            .filter(XmlModel.id == xml_id) \
            .update({'updated_at': get_utcnow_naive()})

    def validate(self, xml_id):
        return self._validation_report(xml_id, strict=False)

    def validate_strict(self, xml_id, progress=None):
        """Strict warnings for one file. Schema checks stay on Validate XML."""
        return self._validation_report(xml_id, strict=True, progress=progress)

    def _validation_report(self, xml_id, strict, progress=None):
        def report(percent):
            if progress is None:
                return
            try:
                progress(percent)
            except Exception:
                pass

        report(1)
        try:
            converter = ConvertToInventory(xml_id, self)
            if strict and progress is not None:
                def build_progress(done, total):
                    if total:
                        report(3 + int(37 * done / total))
                converter.progress = build_progress
            inv = converter.run()
        except Exception as e:
            raise HTTPError(reason="Unable to build XML: '%s'" % str(e))

        report(42)
        errors = []
        if not strict:
            try:
                stationxml = serialize_inventory_12(
                    inv,
                    converter.sidecar_tree(),
                    validate=False,
                )
            except Exception as e:
                issues = [{
                    'severity': 'error',
                    'code': 'STATIONXML_SERIALIZE',
                    'path': '/',
                    'message': str(e),
                }]
                return {'errors': issues, 'warnings': [], 'issues': issues}

            errors = validate_stationxml_12(stationxml)
            del stationxml
        report(48)
        try:
            warnings = validate_inventory_recommendations(inv, application=self.application)
        except Exception as exc:
            warnings = [{
                'severity': 'warning',
                'code': 'YASMINE_RECOMMENDATION_CHECK',
                'path': '/',
                'message': 'Additional recommendation checks could not be completed: %s' % exc,
            }]
        if strict:
            warnings = list(warnings) + self._strict_warnings(inv, progress)
        report(99)

        return {
            'errors': errors,
            'warnings': warnings,
            'issues': errors + warnings,
        }

    def _strict_warnings(self, inventory, progress=None):
        def channel_progress(done, total):
            if not total:
                if progress is not None:
                    progress(99)
                return
            if progress is not None:
                progress(48 + int(51 * done / total))

        try:
            return validate_inventory_strict(inventory, progress=channel_progress)
        except Exception as exc:
            return [{
                'severity': 'warning',
                'category': 'response',
                'code': 'strict.scan_failed',
                'path': '/',
                'message': 'Strict checks could not be completed: %s' % exc,
            }]
