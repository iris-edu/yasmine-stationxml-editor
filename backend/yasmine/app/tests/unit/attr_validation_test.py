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


import unittest

from yasmine.app.utils.inv_valid import ValueRequired, ValueLength,\
    ValueWithinRange


class AttrValidationTests(unittest.TestCase):
    def test_required_attr(self):

        self.assertIsNot(ValueRequired('attr1').validate(None), True, 'Values is valid.')
        self.assertIsNot(ValueRequired('attr1').validate(''), True, 'Values is valid.')
        self.assertIsNot(ValueRequired('attr1').validate({}), True, 'Values is valid.')
        self.assertIsNot(ValueRequired('attr1').validate([]), True, 'Values is valid.')
        self.assertIsNot(ValueRequired('attr1').validate([[{'aa': ''}]]), True, 'Values is invalid.')
        self.assertIsNot(ValueRequired('attr1').validate([[{'aa': None}]]), True, 'Values is invalid.')
        self.assertIsNot(ValueRequired('attr1').validate([[{}]]), True, 'Values is invalid.')

        self.assertTrue(ValueRequired('attr1').validate([[{'aa': 'ss'}]]), 'Values is valid.')
        self.assertTrue(ValueRequired('attr1').validate('test'), 'Values is invalid.')
        self.assertTrue(ValueRequired('attr1').validate(0), 'Values is invalid.')
        self.assertTrue(ValueRequired('attr1').validate(0.0), 'Values is invalid.')
        self.assertTrue(ValueRequired('attr1').validate(1), 'Values is invalid.')
        self.assertTrue(ValueRequired('attr1').validate(1.1), 'Values is invalid.')

    def test_length_attr(self):
        self.assertIsNot(ValueLength('attr1', 3, 5).validate(12), True, 'Values is valid.')
        self.assertIsNot(ValueLength('attr1', 3, 5).validate(122345), True, 'Values is valid.')
        self.assertIsNot(ValueLength('attr1', 3, 5).validate(123.123), True, 'Values is valid.')
        self.assertIsNot(ValueLength('attr1', 3, 5).validate('12'), True, 'Values is valid.')
        self.assertIsNot(ValueLength('attr1', 3, 5).validate('123456'), True, 'Values is valid.')
        self.assertTrue(ValueLength('attr1', 3, 5).validate('123'), 'Values is invalid.')
        self.assertTrue(ValueLength('attr1', 3, 5).validate('12345'), 'Values is invalid.')
        self.assertTrue(ValueLength('attr1', 3, 5).validate(123), 'Values is invalid.')
        self.assertTrue(ValueLength('attr1', 3, 5).validate(123.1), 'Values is invalid.')

    def test_range_attr(self):
        self.assertIsNot(ValueWithinRange('attr1', -90, 90).validate(-91), True, 'Values is valid.')
        self.assertIsNot(ValueWithinRange('attr1', -90, 90).validate(90), True, 'Values is valid.')
        self.assertTrue(ValueWithinRange('attr1', -90, 90).validate(-90), 'Values is invalid.')
        self.assertTrue(ValueWithinRange('attr1', -90, 90).validate(50), 'Values is invalid.')
        self.assertTrue(ValueWithinRange('attr1', -90, 90).validate(89), 'Values is invalid.')
