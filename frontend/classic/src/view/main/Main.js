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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.main.Main', {
  extend: 'Ext.tab.Panel',
  xtype: 'app-main',
  requires: [
    'Ext.plugin.Viewport',
    'Ext.plugin.Responsive',
    'Ext.window.MessageBox',
    'yasmine.view.main.MainController',
    'yasmine.view.main.MainModel'
  ],
  controller: 'main',
  viewModel: 'main',
  ui: 'navigation',
  cls: 'yasmine-app-shell',
  tabBarHeaderPosition: 1,
  titleRotation: 0,
  tabRotation: 0,
  header: {
    layout: {
      align: 'stretchmax'
    },
    title: {
      bind: {
        html: '<div class="yasmine-header-brand"><img class="yasmine-header-logo" src="{logoIconUrl}" alt="Yasmine"><div class="yasmine-header-text"><div>{name}</div><div class="yasmine-header-version">{releaseVersion}</div></div></div>'
      },
      flex: 0
    }
  },
  tabBar: {
    flex: 1,
    layout: {
      align: 'stretch',
      overflowHandler: 'scroller'
    }
  },
  responsiveConfig: {
    'width >= 1280': {
      headerPosition: 'left'
    },
    'width < 1280': {
      headerPosition: 'top'
    },
    'height < 500': {
      headerPosition: 'top'
    }
  },
  defaults: {
    bodyPadding: 8,
    bodyCls: 'yasmine-page-body',
    textAlign: 'left',
    tabConfig: {
      iconAlign: 'left',
      textAlign: 'left'
    }
  },
  activeTab: null,
  listeners: {
    tabchange: 'onTabActivated'
  },
  items: [
    {
      title: 'XMLs',
      iconCls: 'x-fa fa-database',
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
      iconCls: 'x-fa fa-university',
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
      iconCls: 'x-fa fa-cog',
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
      iconCls: 'x-fa fa-info-circle',
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
