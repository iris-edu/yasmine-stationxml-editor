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
#
# ****************************************************************************/


class XmlNodeEnum(object):
    NETWORK = 1
    STATION = 2
    CHANNEL = 3


class XmlNodeAttrEnum(object):
    IDENTIFIERS = 'identifiers'
    CODE = 'code'
    SOURCE_ID = 'source_id'
    ALT_CODE = 'alternate_code'
    HISTORICAL_CODE = 'historical_code'
    START_DATE = 'start_date'
    DESCRIPTION = 'description'
    LOCATION_CODE = 'location_code'
    END_DATE = 'end_date'
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    DEPTH = 'depth'
    AZIMUTH = 'azimuth'
    DIP = 'dip'
    SAMPLE_RATE = 'sample_rate'
    COMMENTS = 'comments'
    ELEVATION = 'elevation'
    EXTERNAL_REFERENCES = 'external_references'
    RESTRICTED_STATUS = 'restricted_status'
    TERMINATION_DATE = 'termination_date'
    CREATION_DATE = 'creation_date'
    SITE = 'site'
    VAULT = 'vault'
    GEOLOGY = 'geology'
    OPERATORS = 'operators'
    TOTAL_NUMBER_OF_CHANNELS = 'total_number_of_channels'
    SELECTED_NUMBER_OF_CHANNELS = 'selected_number_of_channels'
    TYPES = 'types'
    SAMPLE_RATE_RATIO_NUMBER_SAMPLES = 'sample_rate_ratio_number_samples'
    SAMPLE_RATE_RATIO_NUMBER_SECONDS = 'sample_rate_ratio_number_seconds'
    STORAGE_FORMAT = 'storage_format'
    CLOCK_DRIFT_IN_SECONDS_PER_SAMPLE = 'clock_drift_in_seconds_per_sample'
    CALIBRATION_UNITS = 'calibration_units'
    CALIBRATION_UNITS_DESCRIPTION = 'calibration_units_description'
    SENSOR = 'sensor'
    PRE_AMPLIFIER = 'pre_amplifier'
    DATA_LOGGER = 'data_logger'
    EQUIPMENTS = 'equipments'
    RESPONSE = 'response'


class XmlNodeAttrWindetsEnum(object):
    FLOAT = 'yasmine-float-field'
    INT = 'yasmine-int-field'
    LATITUDE = 'yasmine-latitude-field'
    LONGITUDE = 'yasmine-longitude-field'
    DATE = 'yasmine-date-field'
    SITE = 'yasmine-site-field'
