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


Ext.define('yasmine.view.xml.builder.menu.Menu', {
  extend: 'Ext.toolbar.Toolbar',
  xtype: 'builder-menu',
  style: 'background-color: rgb(236, 236, 236)',
  items: [
    {
      xtype: 'segmentedbutton',
      allowToggle: false,
      items: [
        {
          text: 'File',
          menu: [
            {text: 'Export as XML', iconCls: 'x-fa fa-upload', handler: 'onExportXmlClick'},
            {text: 'Validate XML', iconCls: 'x-fa fa-cogs', handler: 'onValidateXmlClick'}
          ]
        },
        {
          text: 'Builder Mode',
          iconCls: 'x-fa fa-industry',
          width: 170,
          bind: {
            text: '{xmlModeTitle}',
            iconCls: '{xmlModeIcon}'
          },
          menu: [
            {
              text: 'Builder Mode',
              width: 170,
              iconCls: 'x-fa fa-industry',
              handler: 'buildBuilderModeView',
              hidden: false,
              bind: {
                hidden: '{isBuilderMode}'
              }
            },
            {
              text: 'Comparison Mode',
              width: 170,
              iconCls: 'x-fa fa-clone',
              handler: 'buildComparisonModeView',
              hidden: true,
              bind: {
                hidden: '{!isBuilderMode}'
              }
            }
          ]
        }
      ]
    }
  ]
});
