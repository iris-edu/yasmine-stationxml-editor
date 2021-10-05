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


from yasmine.app.enums.xml_node import XmlNodeEnum
from yasmine.app.enums.configs import NetworkCfgEnum, StationCfgEnum,\
    ChannelCfgEnum


class ConfigDict(object):

    def __init__(self, config_list):
        self.configs = self.map_config(config_list)

    def get(self, group, var=None):
        group_confg = self.configs.get(group)
        if var is not None:
            if group_confg:
                return group_confg.get(var)
            else:
                return None
        else:
            return group_confg

    def map_config(self, configs):
        config_dict = {}
        for c in configs:
            if c.group not in config_dict:
                config_dict[c.group] = {}
            config_dict[c.group][c.name] = c.value_obj
        return config_dict

    def get_cfg_by_node_id(self, node_id):
        if node_id == XmlNodeEnum.NETWORK:
            return self.get(*NetworkCfgEnum.CODE), self.get(*NetworkCfgEnum.NUM_STATIONS), XmlNodeEnum.STATION, self.get(*NetworkCfgEnum.REQUIRED_FIELDS)
        elif node_id == XmlNodeEnum.STATION:
            return self.get(*StationCfgEnum.CODE), self.get(*StationCfgEnum.NUM_CHANNELS), XmlNodeEnum.CHANNEL, self.get(*StationCfgEnum.REQUIRED_FIELDS)
        elif node_id == XmlNodeEnum.CHANNEL:
            return self.get(*ChannelCfgEnum.CODE), 0, None, self.get(*ChannelCfgEnum.REQUIRED_FIELDS)
