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


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ChannelResponseTreeEditorModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.channel-response-tree-editor',
  data: {
    selectedResponseNode: null,
    newNodeName: null
  },
  formulas: {
    titleAddNew: function (get) {
      let parentNode = get('selectedResponseNode') ? get('selectedResponseNode').get('key') : 'Response';
      let newNode = get('newNodeName') ? `<b>${get('newNodeName')}</b>` : 'a new';

      return `Add ${newNode} node into <b>${parentNode}</b> node`;
    },
    // canAddNewNode: function (get) {
    //   console.log('sss');
    //   let selectedNode = get('selectedResponseNode');
    //   if (!selectedNode || selectedNode.isRoot()) {
    //     return true;
    //   }
    //
    //   return !yasmine.utils.XmlNodeUtil.getValue(selectedNode);
    // },
    canDelete: function (get) {
      return !!(get('selectedResponseNode') && get('selectedResponseNode').data.key);
    },
    deleteNodeTitle: function (get) {
      let selectedNode = get('selectedResponseNode');
      if (selectedNode && selectedNode.data.key) {
        return selectedNode.data.key;
      }

      return null;
    }
  }
});

