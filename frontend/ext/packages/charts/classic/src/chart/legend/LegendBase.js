/**
 * The legend base class adapater for classic toolkit.
 */
Ext.define('Ext.chart.legend.LegendBase', {
    extend: 'Ext.view.View',

    config: {
        tpl: [
            '<div class="', Ext.baseCSSPrefix, 'legend-inner">', // for IE8 vertical centering
                '<div class="', Ext.baseCSSPrefix, 'legend-container">',
                    '<tpl for=".">',
                        '<div class="', Ext.baseCSSPrefix, 'legend-item">',
                            '<span ',
                                'class="', Ext.baseCSSPrefix, 'legend-item-marker {[ values.disabled ? Ext.baseCSSPrefix + \'legend-item-inactive\' : \'\' ]}" ',
                                'style="background:{mark};">',
                            '</span>{name}',
                        '</div>',
                    '</tpl>',
                '</div>',
            '</div>'
        ],
        nodeContainerSelector: 'div.' + Ext.baseCSSPrefix + 'legend-inner', // element that contains rows (see AbstractView)
        itemSelector: 'div.' + Ext.baseCSSPrefix + 'legend-item',           // row element (see AbstractView)
        docked: 'bottom'
    },

    setDocked: function (docked) {
        // If we call the method 'updateDocked' instead of 'setDocked', the following error is thrown:
        // "Ext.Component#setDocked" is deprecated. Please use "setDock" instead.
        var me = this,
            panel = me.ownerCt;

        me.docked = me.dock = docked;

        switch (docked) {
            case 'top':
            case 'bottom':
                me.addCls(me.horizontalCls);
                me.removeCls(me.verticalCls);
                break;
            case 'left':
            case 'right':
                me.addCls(me.verticalCls);
                me.removeCls(me.horizontalCls);
                break;
        }

        if (panel) {
            panel.setDock(docked);
        }
    },

    setStore: function (store) {
        this.bindStore(store);
    },

    clearViewEl: function () {
        this.callParent(arguments);
        // The legend-container div is not removed automatically.
        Ext.removeNode(this.getNodeContainer());
    },

    onItemClick: function (record, item, index, e) {
        this.callParent(arguments);
        this.toggleItem(index);
    }
});
