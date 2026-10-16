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
# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/
from obspy.core.inventory.util import _is_valid_uri

from yasmine.app.enums.xml_error import XmlErrorEnum
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.enums.xml_node import XmlNodeEnum, XmlNodeAttrEnum
from datetime import date, datetime
from yasmine.app.utils.date import parse_naive_datetime, get_utcnow_naive


class ValidateBase(object):
    MESSSAGE_BASE = "Value error"


class ValueRequired(ValidateBase):
    MESSSAGE = "Attribute '%s' required."

    def __init__(self, attr_name, critical=True):
        self.attr_name = attr_name
        self.critical = critical

    def validate(self, value):
        try:
            if self.is_empty(value):
                return ValueRequired.MESSSAGE % self.attr_name
            else:
                return True
        except Exception:
            return self.MESSSAGE_BASE

    def is_empty(self, value):
        if self.is_simple(value):
            return self.is_simple_empty(value)
        elif isinstance(value, list):
            return self.is_array_empty(value)
        elif isinstance(value, dict):
            return self.is_dict_empty(value)
        elif isinstance(value, object):
            return self.is_object_empty(value)
        return False

    def is_simple(self, value):
        if value is None or isinstance(value, str) or isinstance(value, float) or isinstance(value, int) or isinstance(
                value, datetime) or isinstance(value, date):  # nopep8
            return True
        return False

    def is_simple_empty(self, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return True
        else:
            return False

    def is_array_empty(self, values):
        for val in values:
            if not self.is_empty(val):
                return False
        return True

    def is_dict_empty(self, value):
        for _, v in value.items():
            if not self.is_empty(v):
                return False
        return True

    def is_object_empty(self, value):
        return self.is_dict_empty(value.__dict__)


class ValueLength(ValidateBase):
    MESSSAGE_MIN = "Attribute '%s' contains less than %s characters."
    MESSSAGE_MAX = "Attribute '%s' contains more than %s characters."

    def __init__(self, attr_name, min_length, max_length, critical=True):
        self.attr_name = attr_name
        self.min_val = min_length
        self.max_val = max_length
        self.critical = critical

    def validate(self, value):
        if ValueRequired(self.attr_name).validate(value) is True:
            try:
                if len(str(value)) < self.min_val:
                    return ValueLength.MESSSAGE_MIN % (self.attr_name, self.min_val)
                if len(str(value)) > self.max_val:
                    return ValueLength.MESSSAGE_MAX % (self.attr_name, self.max_val)
            except Exception:
                return self.MESSSAGE_BASE
        return True


class ValueWithinRange(ValidateBase):
    MESSSAGE_MIN = "Attribute '%s' is less than %s."
    MESSSAGE_MAX = "Attribute '%s' is greater or equal than %s."
    MESSSAGE_MAX_INCLUSIVE = "Attribute '%s' is greater than %s."

    def __init__(
            self,
            attr_name,
            min_val,
            max_val,
            critical=True,
            max_inclusive=False):
        self.attr_name = attr_name
        self.min_val = min_val
        self.max_val = max_val
        self.critical = critical
        self.max_inclusive = max_inclusive

    def validate(self, value):
        if ValueRequired(self.attr_name).validate(value) is True:
            try:
                if float(value) < self.min_val:
                    return ValueWithinRange.MESSSAGE_MIN % (self.attr_name, self.min_val)
                if (
                        float(value) > self.max_val
                        if self.max_inclusive
                        else float(value) >= self.max_val):
                    message = (
                        ValueWithinRange.MESSSAGE_MAX_INCLUSIVE
                        if self.max_inclusive
                        else ValueWithinRange.MESSSAGE_MAX
                    )
                    return message % (self.attr_name, self.max_val)
            except Exception:
                return self.MESSSAGE_BASE
        return True


class UTCDateRequired(ValidateBase):
    MESSSAGE_MAX = "The '%s' should be equal or before UTC now time."
    WRONG_FORMAT = "Wrong date format"

    def __init__(self, attr_name, critical=True):
        self.attr_name = attr_name
        self.critical = critical

    def validate(self, value):
        if ValueRequired(self.attr_name).validate(value) is True:
            if isinstance(value, str):
                try:
                    value = parse_naive_datetime(value)
                except Exception:
                    return UTCDateRequired.WRONG_FORMAT
            if value > get_utcnow_naive():
                return UTCDateRequired.MESSSAGE_MAX % self.attr_name
        return True


class ValueDipRange(ValidateBase):
    MESSSAGE_MIN = "Attribute '%s' is less than %s."
    MESSSAGE_MAX = "Attribute '%s' is greater than %s."

    def __init__(self, attr_name, min_val, max_val, critical=True):
        self.attr_name = attr_name
        self.min_val = min_val
        self.max_val = max_val
        self.critical = critical

    def validate(self, value):
        if ValueRequired(self.attr_name).validate(value) is True:
            try:
                if value < self.min_val:
                    return ValueWithinRange.MESSSAGE_MIN % (self.attr_name, self.min_val)
                if value > self.max_val:
                    return ValueWithinRange.MESSSAGE_MAX % (self.attr_name, self.max_val)
            except Exception:
                return self.MESSSAGE_BASE
        return True


class ValueUri(ValidateBase):
    MESSSAGE = "Given string seems to not be a valid URI"

    def __init__(self, attr_name, critical=True):
        self.attr_name = attr_name
        self.critical = critical

    def validate(self, value):
        if ValueRequired(self.attr_name).validate(value) is True:
            return True if _is_valid_uri(value) else self.MESSSAGE
        return True


# FDSN / Strict-aligned operational lengths (File → Validate XML warnings).
# Network 1–8 and station 1–5 match Strict; channel codes are exactly 3.
VALIDATION_RULES = {
    XmlNodeEnum.NETWORK: {
        XmlNodeAttrEnum.CODE: [ValueRequired(XmlNodeAttrEnum.CODE, False),
                               ValueLength(XmlNodeAttrEnum.CODE, 1, 8, False)],
        XmlNodeAttrEnum.SOURCE_ID: [ValueUri(XmlNodeAttrEnum.SOURCE_ID, False)],
        XmlNodeAttrEnum.ALT_CODE: [ValueLength(XmlNodeAttrEnum.ALT_CODE, 1, 8, False)],
        XmlNodeAttrEnum.HISTORICAL_CODE: [
            ValueLength(XmlNodeAttrEnum.HISTORICAL_CODE, 1, 8, False)
        ],
    },
    XmlNodeEnum.STATION: {
        XmlNodeAttrEnum.CODE: [ValueRequired(XmlNodeAttrEnum.CODE, False),
                               ValueLength(XmlNodeAttrEnum.CODE, 1, 5, False)],
        XmlNodeAttrEnum.SOURCE_ID: [ValueUri(XmlNodeAttrEnum.SOURCE_ID, False)],
        XmlNodeAttrEnum.ALT_CODE: [ValueLength(XmlNodeAttrEnum.ALT_CODE, 1, 5, False)],
        XmlNodeAttrEnum.HISTORICAL_CODE: [
            ValueLength(XmlNodeAttrEnum.HISTORICAL_CODE, 1, 5, False)
        ],
        XmlNodeAttrEnum.SITE: [ValueRequired(XmlNodeAttrEnum.SITE, True)],
        XmlNodeAttrEnum.LATITUDE: [ValueRequired(XmlNodeAttrEnum.LATITUDE, True),
                                   ValueWithinRange(XmlNodeAttrEnum.LATITUDE, -90, 90, True)],
        XmlNodeAttrEnum.LONGITUDE: [ValueRequired(XmlNodeAttrEnum.LONGITUDE, True),
                                    ValueWithinRange(
                                        XmlNodeAttrEnum.LONGITUDE,
                                        -180,
                                        180,
                                        True,
                                        max_inclusive=True,
                                    )],
        XmlNodeAttrEnum.ELEVATION: [ValueRequired(XmlNodeAttrEnum.ELEVATION, True)],
    },
    XmlNodeEnum.CHANNEL: {
        XmlNodeAttrEnum.CODE: [ValueRequired(XmlNodeAttrEnum.CODE, False),
                               ValueLength(XmlNodeAttrEnum.CODE, 3, 3, False)],
        XmlNodeAttrEnum.SOURCE_ID: [ValueUri(XmlNodeAttrEnum.SOURCE_ID, False)],
        XmlNodeAttrEnum.LOCATION_CODE: [
            ValueLength(XmlNodeAttrEnum.LOCATION_CODE, 0, 2, False)
        ],
        XmlNodeAttrEnum.ALT_CODE: [ValueLength(XmlNodeAttrEnum.ALT_CODE, 0, 3, False)],
        XmlNodeAttrEnum.HISTORICAL_CODE: [
            ValueLength(XmlNodeAttrEnum.HISTORICAL_CODE, 0, 3, False)
        ],
        XmlNodeAttrEnum.LATITUDE: [ValueRequired(XmlNodeAttrEnum.LATITUDE, True),
                                   ValueWithinRange(XmlNodeAttrEnum.LATITUDE, -90, 90, True)],
        XmlNodeAttrEnum.LONGITUDE: [ValueRequired(XmlNodeAttrEnum.LONGITUDE, True),
                                    ValueWithinRange(
                                        XmlNodeAttrEnum.LONGITUDE,
                                        -180,
                                        180,
                                        True,
                                        max_inclusive=True,
                                    )],
        XmlNodeAttrEnum.ELEVATION: [ValueRequired(XmlNodeAttrEnum.ELEVATION, True)],
        XmlNodeAttrEnum.DEPTH: [ValueRequired(XmlNodeAttrEnum.DEPTH, True)],
        XmlNodeAttrEnum.AZIMUTH: [
            ValueWithinRange(XmlNodeAttrEnum.AZIMUTH, 0, 360, True)
        ],
        XmlNodeAttrEnum.DIP: [ValueDipRange(XmlNodeAttrEnum.DIP, -90, 90, True)],
    }
}

# Soft SEED-classic length hints when a code is FDSN-valid but unusual for SEED.
# Applied only for recommendation (non-critical) Validate runs.
SEED_CLASSIC_CODE_LENGTHS = {
    XmlNodeEnum.NETWORK: (XmlNodeAttrEnum.CODE, 1, 2),
    XmlNodeEnum.STATION: (XmlNodeAttrEnum.CODE, 3, 5),
}


class ValidateInventory(HandlerMixin):
    def __init__(
            self,
            inv,
            application=None,
            critical_only=True,
            warnings_only=False,
            *_,
            **__):
        self.inv = inv
        self.critical_only = critical_only
        self.warnings_only = warnings_only
        super(ValidateInventory, self).__init__(application)

    def get_first_start_last_end_dates(self, station_or_channel_list):
        starts = [item.start_date for item in station_or_channel_list if item.start_date is not None]
        ends = [item.end_date for item in station_or_channel_list if item.end_date is not None]
        return (
            min(starts) if starts else None,
            max(ends) if ends else None,
        )

    def validate_level(self, obj, level, prefix):
        level_rules = VALIDATION_RULES.get(level, [])
        errors = []

        for _, rules in level_rules.items():
            for rule in rules:
                should_run = (
                    (self.warnings_only and not rule.critical)
                    or
                    (not self.warnings_only and self.critical_only and rule.critical)
                    or
                    (not self.warnings_only and not self.critical_only)
                )
                if should_run:
                    is_valid = rule.validate(getattr(obj, rule.attr_name))
                    if is_valid is not True and not self._should_ignore_critical(level, rule.attr_name):
                        errors.append("%s: %s" % (prefix, is_valid))
        if not self.critical_only or self.warnings_only:
            seed_hint = self._seed_classic_code_hint(obj, level)
            if seed_hint:
                errors.append("%s: %s" % (prefix, seed_hint))
        return errors

    @staticmethod
    def _seed_classic_code_hint(obj, level):
        """Warn when FDSN-valid codes diverge from classic SEED lengths."""
        spec = SEED_CLASSIC_CODE_LENGTHS.get(level)
        if not spec:
            return None
        attr_name, min_len, max_len = spec
        value = getattr(obj, attr_name, None)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None
        text = str(value)
        fdsn_bounds = {
            XmlNodeEnum.NETWORK: (1, 8),
            XmlNodeEnum.STATION: (1, 5),
        }.get(level)
        if not fdsn_bounds:
            return None
        if ValueLength(attr_name, fdsn_bounds[0], fdsn_bounds[1], False).validate(text) is not True:
            return None
        if min_len <= len(text) <= max_len:
            return None
        return (
            "SEED classic recommends '%s' length %s–%s characters (got %s)."
            % (attr_name, min_len, max_len, len(text))
        )

    @staticmethod
    def _should_ignore_critical(level, attr_name):
        return False

    def validate_network(self, network, prefix):
        errors = self.validate_level(network, XmlNodeEnum.NETWORK, prefix)
        if not self.critical_only:
            nstations = len(network.stations)
            if network.start_date and nstations:
                (earliest_start_date, latest_end_date) = self.get_first_start_last_end_dates(network.stations)
                if earliest_start_date is not None and earliest_start_date < network.start_date:
                    errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_105b))
                if network.end_date is not None:
                    if network.start_date >= network.end_date:
                        errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_105))
                    if latest_end_date is not None and latest_end_date > network.end_date:
                        errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_105c))

            if nstations:
                stations_dict = {}
                # Count occurrence of each station.code
                for station in network.stations:
                    if station.code in stations_dict:
                        stations_dict[station.code] += 1
                    else:
                        stations_dict[station.code] = 1

                # If station.code occurs more than once, make sure epochs don't overlap
                for key in stations_dict.keys():
                    if stations_dict[key] > 1:
                        sorted_list = []
                        for station in network.stations:
                            if station.code == key and station.start_date is not None:
                                sorted_list.append(station)

                        # Sort epochs chronologically by start_date and test consecutive epochs for overlap
                        sorted_list.sort(key=lambda x: x.start_date, reverse=False)
                        for i, station in enumerate(sorted_list):
                            if i > 0:
                                epoch1 = sorted_list[i - 1]
                                epoch2 = station
                                overlap = False
                                # epoch1 start_date <= epoch2 start_date guaranteed from sort
                                if epoch1.start_date == epoch2.start_date:
                                    overlap = True
                                # epoch1 better be closed
                                elif epoch1.end_date is None:
                                    overlap = True
                                # epoch1 close must precede epoch2 start
                                elif epoch1.end_date > epoch2.start_date:
                                    overlap = True
                                if overlap:
                                    errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_152))
        return errors

    def validate_station(self, station, prefix):
        errors = self.validate_level(station, XmlNodeEnum.STATION, prefix)

        if not self.critical_only:
            if station.end_date is not None and station.start_date is not None:
                if station.start_date >= station.end_date:
                    errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_205))

            nchannels = len(station.channels)
            if nchannels:
                for channel in station.channels:
                    if channel.start_date is None:
                        errors.append("Channel %s.%s has empty start_date --> Can't sort/test epochs!" % (
                            channel.location_code, channel.code))
                channel_dict = {}
                # Count occurrence of each channel.code.join(location_code)
                for channel in station.channels:
                    chan_key = "%s.%s" % (channel.location_code, channel.code)
                    if chan_key in channel_dict:
                        channel_dict[chan_key] += 1
                    else:
                        channel_dict[chan_key] = 1
                # If channel key occurs more than once, make sure epochs don't overlap
                for key in channel_dict.keys():
                    if channel_dict[key] > 1:
                        sorted_list = []
                        for channel in station.channels:
                            chan_key = "%s.%s" % (channel.location_code, channel.code)
                            if chan_key == key and channel.start_date is not None:
                                sorted_list.append(channel)

                        # Sort epochs chronologically by start_date and test consecutive epochs for overlap
                        sorted_list.sort(key=lambda x: x.start_date, reverse=False)
                        for i, channel in enumerate(sorted_list):
                            if i > 0:
                                epoch1 = sorted_list[i - 1]
                                epoch2 = channel
                                overlap = False
                                # epoch1 start_date <= epoch2 start_date guaranteed from sort
                                if epoch1.start_date == epoch2.start_date:
                                    overlap = True
                                # epoch1 better be closed
                                elif epoch1.end_date is None:
                                    overlap = True
                                # epoch1 close must precede epoch2 start
                                elif epoch1.end_date > epoch2.start_date:
                                    overlap = True
                                if overlap:
                                    errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_252))
        return errors

    def validate_channel(self, channel, prefix):
        errors = self.validate_level(channel, XmlNodeEnum.CHANNEL, prefix)

        if not self.critical_only:
            if channel.end_date is not None and channel.start_date is not None:
                if channel.start_date >= channel.end_date:
                    errors.append("%s: %s" % (prefix, XmlErrorEnum.ERROR_305))

        return errors

    def check_levele_is_active(self, level, utc_now):
        return level.end_date is None or level.end_date > utc_now

    def run(self):
        errors = []
        utc_now = get_utcnow_naive()
        for network in self.inv.networks:
            if self.check_levele_is_active(network, utc_now):
                network_prefix = network.code if network.code else "undefined"
                errors.extend(self.validate_network(network, network_prefix))
                for station in network.stations:
                    if self.check_levele_is_active(station, utc_now):
                        station_prefix = '%s/%s' % (network_prefix, station.code if station.code else "undefined")
                        errors.extend(self.validate_station(station, station_prefix))
                        for channel in station.channels:
                            if self.check_levele_is_active(channel, utc_now):
                                channel_prefix = '%s/%s' % (
                                    station_prefix, channel.code if channel.code else "undefined")
                                errors.extend(self.validate_channel(channel, channel_prefix))
        return errors
