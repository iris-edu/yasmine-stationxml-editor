/* ****************************************************************************
*
* Shared helpers for Recalculate Sensitivity in response selectors / wizard.
*
* ****************************************************************************/

Ext.define('yasmine.utils.ResponseRecalculateUtil', {
  singleton: true,

  applyRecalculateResult: function (vm, result) {
    vm.set('channelResponseText', result.text);
    vm.set('channelResponseImageUrl', result.plot_url);
    vm.set('channelResponseCsvUrl', result.csv_url);
    vm.set('channelResponsePlotMessage', null);
    if (result.data) {
      vm.set('responseTree', result.data);
    }
    this.updateWizardActionButtons(vm);
  },

  updateWizardActionButtons: function (vm) {
    if (!vm || !vm.get('wizardMode')) {
      return;
    }
    let hasText = !!vm.get('channelResponseText');
    let onResponseTab = vm.get('activeSelectorTab') === 2;
    if (!hasText || !onResponseTab) {
      Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', []);
      return;
    }
    let controller = vm.getView().getController();
    Ext.ux.Mediator.fireEvent('wizard-updateActionButtons', [
      this.createWizardRecalculateButton(controller)
    ]);
  },

  createWizardRecalculateButton: function (controller) {
    return Ext.create({
      xtype: 'button',
      text: 'Recalculate Sensitivity',
      iconCls: 'x-fa fa-calculator',
      handler: function () {
        if (controller && typeof controller.recalculateSensitivity === 'function') {
          controller.recalculateSensitivity();
        }
      }
    });
  },

  showRecalculateError: function (message) {
    Ext.MessageBox.show({
      title: 'An error occurred',
      msg: message || 'Cannot recalculate sensitivity.',
      buttons: Ext.MessageBox.OK,
      icon: Ext.MessageBox.ERROR
    });
  }
});
