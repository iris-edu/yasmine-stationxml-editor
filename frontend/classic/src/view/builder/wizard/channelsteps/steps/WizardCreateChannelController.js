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


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.WizardCreateChannelController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.wizard-create-channel-item',
  requires: [
    'Ext.ux.Mediator',
  ],
  init: function () {
    let viewModel = this.getViewModel();
    viewModel.set('totalSteps', this.getView().items.length);
    viewModel.set('isCompleted', false);
    this.updateCompletionStatus();
    this.updateNavigationButtonState();

    let srNumber = viewModel.get('sampleRateNumber');
    Ext.ux.Mediator.on(`wizardCreateChannelController-dataIsChanged-${srNumber}`, this.onDataIsChanged, this);
  },
  isCompleted: function () {
    return this.getViewModel().get('isCompleted');
  },
  isStart: function () {
    return this.getViewModel().get('activeIndex') === 0;
  },
  markComplete: function () {
    this.storeActiveItemData();
    this.getViewModel().set('isCompleted', true);
    this.updateCompletionStatus();
  },
  initComponent: function () {
    this.initActiveItem();
  },
  updateCompletionStatus: function () {
    let viewModel = this.getViewModel();
    let isCompleted = viewModel.get('isCompleted');
    let label = isCompleted
      ? '<i class="fa fa-check" style="color: green"></i>'
      : '<i class="fa fa-ban" style="color: red"></i>';
    viewModel.set('completionStatusLabel', label);
  },
  showNext: function () {
    if (!this.isActiveItemValid()) {
      return;
    }

    if (this.getViewModel().get('hasNextStep')) {
      this.storeActiveItemData();
      this.activateItem(1);
      this.initActiveItem();
      this.getViewModel().set('isCompleted', false);
      this.updateCompletionStatus();
    }
  },
  showPrevious: function () {
    Ext.Msg.confirm(
      'Warning',
      'Are you sure you want to go to the previous step? The data for the current step will be deleted',
      (buttonId) => {
        if (buttonId === 'yes') {
          this.activateItem(-1);
          this.getViewModel().set('isCompleted', false);
          this.updateCompletionStatus();
        }
      });
  },
  onDataIsChanged: function () {
    this.getViewModel().set('isCompleted', false);
    this.updateCompletionStatus();
  },
  activateItem: function (delta) {
    let nextIndex = this.getViewModel().get('activeIndex') + delta;
    let layout = this.getView().getLayout();
    layout.setActiveItem(nextIndex);
    this.getViewModel().set('activeIndex', nextIndex);
    this.updateNavigationButtonState();
  },
  updateNavigationButtonState: function () {
    let viewModel = this.getViewModel();
    viewModel.set('hasNextStep', viewModel.get('activeIndex') + 1 < viewModel.get('totalSteps'));
    viewModel.set('hasPreviousStep', viewModel.get('activeIndex') > 0);
  },
  isActiveItemValid: function () {
    let controller = this.getActiveItemController();
    let isValid = true;
    if (controller && controller.isValid) {
      isValid = controller.isValid();
    }

    if (isValid && !this.getViewModel().get('hasNextStep')) {
      this.markComplete();
    }

    return isValid;
  },
  storeActiveItemData: function () {
    let controller = this.getActiveItemController();
    if (controller && controller.storeStepData) {
      controller.storeStepData();
    }
  },
  initActiveItem: function () {
    let controller = this.getActiveItemController();
    if (controller && controller.initComponent) {
      controller.initComponent();
    }
  },
  getActiveItemController: function () {
    let activeIndex = this.getViewModel().get('activeIndex');
    let currentStep = this.lookupReference(`channel-step-${activeIndex + 1}`);
    return currentStep.getController();
  }
});
