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
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.Step2View', {
  extend: 'Ext.panel.Panel',
  xtype: 'channel-step-2',
  controller: {
    isValid: function () {
      if (!this.getSelectedValue()) {
        Ext.Msg.alert('Error', 'Please make a choice', Ext.emptyFn);
        return false;
      }

      return true;
    },
    storeStepData: function () {
      let viewModel = this.getViewModel();
      viewModel.get('stepsStoredData').selectedLibrary = this.getSelectedValue();
      viewModel.get('channelInfo').set('libraryType', this.getSelectedValue());
    },
    getSelectedValue: function () {
      let cmp = this.lookup('librarySelectionCmp');
      return cmp.getValue().rb;
    }
  },
  items: [
    {
      xtype: 'radiogroup',
      width: 245,
      reference: 'librarySelectionCmp',
      vertical: true,
      columns: 1,
      items: [
        {xtype: 'component', html: '<b>Select a library to build a response.</b>', cls: 'x-form-check-group-label'},
        {boxLabel: 'NRL', name: 'rb', inputValue: 'nrl'},
        {boxLabel: 'AROL', name: 'rb', inputValue: 'arol'},
        {boxLabel: 'I don\'t need a response', name: 'rb', inputValue: 'none'}
      ]
    }
  ]
});
