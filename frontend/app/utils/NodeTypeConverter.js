/* ****************************************************************************
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version. *
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details. *
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* 2019/10/07 : version 2.0.0 initial commit
*
* ****************************************************************************/


Ext.define("yasmine.utils.NodeTypeConverter", {
  singleton: true,
  toIcon: function (nodeType) {
    let icons = new Map();
    icons.set(yasmine.NodeTypeEnum.network, "x-fa fa-connectdevelop");
    icons.set(yasmine.NodeTypeEnum.station, "x-fa fa-building-o");
    icons.set(yasmine.NodeTypeEnum.channel, "x-fa fa-rss");

    return icons.has(nodeType) ? icons.get(nodeType) : "x-fa fa-history";
  },
  toString: function (nodeType) {
    let strings = new Map();
    strings.set(yasmine.NodeTypeEnum.network, "Network");
    strings.set(yasmine.NodeTypeEnum.station, "Station");
    strings.set(yasmine.NodeTypeEnum.channel, "Channel");

    return strings.has(nodeType) ? strings.get(nodeType) : yasmine.Globals.NotApplicable;
  },
  getChild: function (parentNodeType) {
    if (parentNodeType === 0) {
      return yasmine.NodeTypeEnum.network
    }
    if (parentNodeType === yasmine.NodeTypeEnum.network) {
      return yasmine.NodeTypeEnum.station
    }
    if (parentNodeType === yasmine.NodeTypeEnum.station) {
      return yasmine.NodeTypeEnum.channel
    }

    return null;
  },
  getParent: function (nodeType) {
    if (nodeType === yasmine.NodeTypeEnum.network) {
      return 0
    }
    if (nodeType === yasmine.NodeTypeEnum.station) {
      return yasmine.NodeTypeEnum.network
    }
    if (nodeType === yasmine.NodeTypeEnum.channel) {
      return yasmine.NodeTypeEnum.station
    }

    return null;
  },
  getChildTitle: function (parentNodeType) {
    return this.toString(this.getChild(parentNodeType));
  },
  getTitle: function (nodeType) {
    return this.toString(nodeType);
  }
});
