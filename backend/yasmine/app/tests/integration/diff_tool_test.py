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
# ****************************************************************************/


import unittest
import difflib
import os


class DiffTollTest(unittest.TestCase):
    FILES_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

    def test_sensors_keys(self):
        with open(os.path.join(self.FILES_FOLDER, 'station_from_obspy.xml'), 'rt') as f1:
            with open(os.path.join(self.FILES_FOLDER, 'station_from_obspy2.xml'), 'rt') as f2:
                d = difflib.HtmlDiff()
                d._legend = ''
                out_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'result.html')
                result = d.make_file(f1.readlines(), f2.readlines(), context=True)
                with open(out_file, 'w') as f:
                    f.writelines(result)


if __name__ == "__main__":
    unittest.main()
