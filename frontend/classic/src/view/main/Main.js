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


Ext.define('yasmine.view.main.Main', {
  extend: 'Ext.tab.Panel',
  xtype: 'app-main',
  requires: [
    'Ext.plugin.Viewport',
    'Ext.window.MessageBox',
    'yasmine.view.main.MainController',
    'yasmine.view.main.MainModel'
  ],
  controller: 'main',
  viewModel: 'main',
  ui: 'navigation',
  tabBarHeaderPosition: 1,
  titleRotation: 0,
  tabRotation: 0,
  header: {
    layout: {
      align: 'stretchmax'
    },
    title: {
      bind: {
        html: '<div>{name}</div><div style="font-size: 10px;margin-top: -11px;padding-left: 1px;">{releaseVersion}</div>'
      },
      flex: 0
    },
    iconCls: 'fa fa-cubes'
  },
  tabBar: {
    flex: 1,
    layout: {
      align: 'stretch',
      overflowHandler: 'none'
    }
  },
  responsiveConfig: {
    tall: {
      headerPosition: 'top'
    },
    wide: {
      headerPosition: 'left'
    }
  },
  defaults: {
    bodyPadding: 5,
    textAlign: 'left',
    tabConfig: {
      plugins: 'responsive',
      responsiveConfig: {
        wide: {
          iconAlign: 'left',
          textAlign: 'left'
        },
        tall: {
          iconAlign: 'left',
          textAlign: 'left',
          width: 120
        }
      }
    }
  },
  activeTab: null,
  listeners: {
    tabchange: 'onTabActivated'
  },
  items: [
    {
      title: 'XMLs',
      iconCls: 'fa fa-database',
      layout: 'fit',
      reference: 'xmlContainer',
      tabConfig: {
        listeners: {
          click: 'onXmlTabClick'
        }
      }
    },
    {
      title: 'User Library',
      iconCls: 'fa fa-university',
      layout: 'fit',
      reference: 'userLibraryContainer',
      tabConfig: {
        listeners: {
          click: 'onUserLibraryTabClick'
        }
      }
    },
    {
      title: 'Settings',
      iconCls: 'fa-cog',
      layout: 'fit',
      reference: 'settingsContainer',
      tabConfig: {
        listeners: {
          click: 'onSettingsTabClick'
        }
      }
    },
    {
      title: 'About',
      iconCls: 'fa-info-circle',
      layout: 'fit',
      reference: 'aboutContainer',
      tabConfig: {
        listeners: {
          click: 'onAboutTabClick'
        }
      }
    },
    // {
    //   title: 'Test',
    //   layout: 'fit',
    //   reference: 'testContainer',
    //   tabConfig: {
    //     listeners: {
    //       click: 'onTestTabClick'
    //     }
    //   }
    // }
  ]
});
