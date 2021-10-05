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


class OperatorLookup:
    def create(self, dictionary):
        contacts = []
        contact = dictionary.get('Contact')
        if isinstance(contact, list):
            for contact_item in contact:
                contacts.append(self._create_person(contact_item))
        elif contact is not None:
            contacts.append(self._create_person(contact))

        contacts = list(filter(None, contacts))
        return {
            'agency': Utils.parse_string_list(dictionary.get('Agency'))[0],
            'website': dictionary.get('WebSite'),
            'help': dictionary.get('Help'),
            'contacts': contacts if len(contacts) > 0 else None,
        }

    def _create_person(self, dictionary):
        obj = {
            'names': Utils.parse_string_list(dictionary.get('Name')) if dictionary.get('Name') else None,
            'agencies': Utils.parse_string_list(dictionary.get('Agency')) if dictionary.get('Agency') else None,
            'emails': Utils.parse_string_list(dictionary.get('Email')) if dictionary.get('Email') else None,
            'phones': self._create_phone_numbers(dictionary.get('Phone')) if dictionary.get('Phone') else None
        }
        return obj if any(obj.values()) else None

    def _create_phone_numbers(self, dictionary):
        result = []
        if isinstance(dictionary, list):
            for item in dictionary:
                result.append(self._create_phone_number(item))
        else:
            result.append(self._create_phone_number(dictionary))

        result = list(filter(None, result))
        return result if len(result) > 0 else None

    @staticmethod
    def _create_phone_number(dictionary):
        if not dictionary:
            return

        obj = {
            'country_code': dictionary.get('CountryCode'),
            'area_code': dictionary.get('AreaCode'),
            'phone_number': dictionary.get('PhoneNumber'),
            'description': dictionary.get('Description')
        }
        return obj if any(obj.values()) else None


class Utils:
    @staticmethod
    def parse_string_list(value):
        if isinstance(value, list):
            return value
        if type(value) == str:
            return [value]
