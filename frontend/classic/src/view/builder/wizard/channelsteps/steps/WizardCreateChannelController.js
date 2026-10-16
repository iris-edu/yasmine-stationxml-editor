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
* NRLv2 online support (2026): ASGSR, Alexey Emanov.
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
* 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.wizard.channelsteps.steps.WizardCreateChannelController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.wizard-create-channel-item',
  requires: [
    'Ext.ux.Mediator',
    'yasmine.utils.ResponseRecalculateUtil',
  ],
  init: function () {
    this.callParent(arguments);
    this.mon(Ext.GlobalEvents, 'nrlv2SettingsChanged', function () {
      let vm = this.getViewModel();
      if (vm) vm.set('settingsUpdatedAt', Date.now());
    }, this);
    let viewModel = this.getViewModel();
    viewModel.set('totalSteps', this.getView().items.length);
    viewModel.set('isCompleted', false);
    this.updateCompletionStatus();
    this.updateNavigationButtonState();

    let srNumber = viewModel.get('sampleRateNumber');
    this.mon(Ext.ux.Mediator, `wizardCreateChannelController-dataIsChanged-${srNumber}`, this.onDataIsChanged, this);
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
      ? '<i class="x-fa fa-check yasmine-status-success"></i>'
      : '<i class="x-fa fa-ban yasmine-status-danger"></i>';
    viewModel.set('completionStatusLabel', label);
  },
  showNext: function () {
    if (!this.isActiveItemValid()) {
      return;
    }

    if (this.getViewModel().get('hasNextStep')) {
      this.storeActiveItemData();
      let previousIndex = this.getViewModel().get('activeIndex');
      this.activateItem(1);
      // Only init the newly activated card. If every remaining card is
      // skipped, activateItem is a no-op — re-initing the current card
      // would wipe answers such as Orientation applies.
      if (this.getViewModel().get('activeIndex') !== previousIndex) {
        this.initActiveItem();
        this.getViewModel().set('isCompleted', false);
        this.updateCompletionStatus();
      } else {
        this.updateNavigationButtonState();
      }
    }
  },
  showPrevious: function () {
    Ext.Msg.confirm(
      'Warning',
      'Go back to the previous step? Answers already entered stay available.',
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
  shouldSkipCard: function (index) {
    let card = this.getView().items.getAt(index);
    if (!card) {
      return false;
    }
    if (card.getItemId() === 'wizard-card-type') {
      let library = this.getViewModel().get('selectedLibrary');
      return library !== 'nrl' && library !== 'nrlv2_online';
    }
    // Channel code was already entered; dip and azimuth do not apply.
    if (card.getItemId() === 'wizard-card-5') {
      return !!this.getViewModel().get('hideDipAzimuth');
    }
    return false;
  },
  activateItem: function (delta) {
    let nextIndex = this.getViewModel().get('activeIndex') + delta;
    let view = this.getView();
    let count = view.items.getCount();
    while (nextIndex >= 0 && nextIndex < count && this.shouldSkipCard(nextIndex)) {
      nextIndex += delta;
    }
    if (nextIndex < 0 || nextIndex >= count) {
      return;
    }
    let layout = view.getLayout();
    layout.setActiveItem(nextIndex);
    this.getViewModel().set('activeIndex', nextIndex);
    if (view.updateLayout) {
      view.updateLayout();
    }
    this.updateNavigationButtonState();
    this.updateWizardFooterButtons();
  },
  updateNavigationButtonState: function () {
    let viewModel = this.getViewModel();
    let index = viewModel.get('activeIndex');
    let count = this.getView().items.getCount();
    let hasNext = false;
    for (let i = index + 1; i < count; i++) {
      if (!this.shouldSkipCard(i)) {
        hasNext = true;
        break;
      }
    }
    viewModel.set('hasNextStep', hasNext);
    viewModel.set('hasPreviousStep', index > 0);
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
    this.updateWizardFooterButtons();
  },
  updateWizardFooterButtons: function () {
    let vm = this.getViewModel();
    let card = this.getView().items.getAt(vm.get('activeIndex'));
    let stepsData = vm.get('stepsStoredData') || {};
    if (!card || card.getItemId() !== 'wizard-card-3' || stepsData.selectedLibrary === 'none') {
      Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', []);
      return;
    }
    let step3 = this.lookupReference('channel-step-3');
    let selector = step3 && step3.getController().selector;
    if (!selector || !selector.getViewModel) {
      Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', []);
      return;
    }
    yasmine.utils.ResponseRecalculateUtil.updateWizardActionButtons(selector.getViewModel());
  },
  getActiveItemController: function () {
    let activeIndex = this.getViewModel().get('activeIndex');
    let card = this.getView().items.getAt(activeIndex);
    let stepRef = {
      'wizard-card-1': 'channel-step-1',
      'wizard-card-2': 'channel-step-2',
      'wizard-card-type': 'channel-nrl-response-type',
      'wizard-card-3': 'channel-step-3',
      'wizard-card-4': 'channel-step-4',
      'wizard-card-5': 'channel-step-5'
    }[card.getItemId()];
    let currentStep = this.lookupReference(stepRef);
    return currentStep.getController();
  }
});
