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


Ext.define('yasmine.view.main.MainController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.main',
  routes: {
    'xmls': {action: 'onXml'},
    'xml-builder/:id': {action: 'onXmlBuilder', conditions: {':id': '([0-9]+)'}},
    'settings': {action: 'onSettings'},
    'user-libraries': {action: 'onUserLibrary'},
    'about': {action: 'onAboutInfo'},
    'test': {action: 'onTest'},
    'user-library-builder/:id': {action: 'onUserLibraryBuilder', conditions: {':id': '([0-9]+)'}}
  },
  onXml: function () {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('xmlContainer');
    container.add([Ext.create({xtype: 'xml-list'})]);

    this.activateContainer(container)
    Ext.resumeLayouts(true);
  },
  onXmlBuilder: function (id) {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('xmlContainer');
    let xmlBuilder = Ext.create({xtype: 'xmlBuilder'});
    let xmlViewModel = xmlBuilder.getViewModel();
    xmlViewModel.set('xmlId', id);

    container.add(xmlBuilder);

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onUserLibraryBuilder: function (id) {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('userLibraryContainer');
    let libraryBuilder = Ext.create({xtype: 'userlibrary-builder'});

    libraryBuilder.getController().initModel(id);
    container.add(libraryBuilder);

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onSettings: function () {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('settingsContainer');
    container.add([Ext.create({xtype: 'settings-list'})]);

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onUserLibrary: function () {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('userLibraryContainer');
    container.add(Ext.create({xtype: 'userlibrary-list'}));

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onAboutInfo: function () {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('aboutContainer');
    container.add(Ext.create({xtype: 'about-info'}));

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onTest: function () {
    Ext.suspendLayouts();
    this.cleanAllContainer();

    let container = this.lookupReference('testContainer');
    container.add(Ext.create({xtype: 'test-container'}));

    this.activateContainer(container);
    Ext.resumeLayouts(true);
  },
  onTabActivated: function (panel, tab) {
    if (tab.reference === 'settingsContainer') {
      this.redirectTo('settings');
    } else if (tab.reference === 'xmlContainer') {
      this.redirectTo('xmls');
    } else if (tab.reference === 'useLibraryContainer') {
      this.redirectTo('user-libraries');
    } else if (tab.reference === 'aboutContainer') {
      this.redirectTo('about');
    } else if (tab.reference === 'testContainer') {
      this.redirectTo('test');
    }
  },
  onXmlTabClick: function () {
    this.redirectTo('xmls');
  },
  onSettingsTabClick: function () {
    this.redirectTo('settings');
  },
  onUserLibraryTabClick: function () {
    this.redirectTo('user-libraries');
  },
  onAboutTabClick: function () {
    this.redirectTo('about');
  },
  onTestTabClick: function () {
    this.redirectTo('test');
  },
  cleanAllContainer: function () {
    this.lookupReference('xmlContainer').removeAll(true, true);
    this.lookupReference('settingsContainer').removeAll(true, true);
    this.lookupReference('userLibraryContainer').removeAll(true, true);
    this.lookupReference('aboutContainer').removeAll(true, true);
    // this.lookupReference('testContainer').removeAll(true, true);
  },
  activateContainer: function (container) {
    this.getView().suspendEvents();
    this.getView().setActiveTab(container);
    this.getView().resumeEvents();
  }
});
