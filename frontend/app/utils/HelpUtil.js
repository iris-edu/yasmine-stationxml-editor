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
* 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define("yasmine.utils.HelpUtil", {
    singleton: true,
    requires: [
        'yasmine.view.help.stationxml.StationXmlHelp'
    ],
    helpMe: function (helpId, helpTitle = 'Help panel') {
        var title = `Help: '${helpTitle}'`;
    	yasmine.help.HelpModel.load(helpId, {
			success: function(record, operation){
				var main_help = Ext.ComponentQuery.query('main_help');
				if (main_help.length>0){
					main_help[0].getViewModel().set('record', record)
					main_help[0].setTitle(title)
				}else{
			   		Ext.create('yasmine.help.Help',{
			   			title: title,
			   			viewModel:{
			   				type: 'main_help',
			   				data:{
			   					record: record
			   				}
			   			}
			   		}).show()
				}
			}
		})
    },
    stationXmlHelpMe: function (context, helpTitle = 'Schema help') {
        var windows = Ext.ComponentQuery.query('stationxml-help');
        var helpWindow = windows.length ? windows[0] : Ext.create({
            xtype: 'stationxml-help'
        });
        helpWindow.showContext(context, helpTitle);
    }
});


Ext.define('yasmine.help.HelpModel', {
    extend: 'Ext.data.Model',
    fields: ['key', 'content'],
    idProperty: 'key',
    proxy: {
        type: 'rest',
        url : '/api/help/',
        writer:{
        	type: 'json'
        }
    }
});

Ext.define('yasmine.help.HelpViewModel', {
    extend: 'Ext.app.ViewModel',
    alias: 'viewmodel.main_help'
})

Ext.define('yasmine.help.HelpController', {
    extend: 'Ext.app.ViewController',
    alias: 'controller.main_help'    
})

Ext.define('yasmine.help.Help', {
    extend: 'Ext.window.Window',
    alias: 'widget.main_help',
    viewModel: 'main_help',
    controller: 'main_help',
    cls: 'yasmine-window yasmine-context-help',
    modal: false,
    alignOffset: [-10, 0],
    defaultAlign: 'r-r',
    alwaysOnTop: true,
    width: 480,
    maxWidth: 480,
    height: "80%",
    maximizable: true,
    border: false,
    layout: 'fit',
    listeners: {
        show: function () {
            yasmine.utils.ResponsiveUtil.fitHelpWindow(this);
        }
    },
    items:[{
    	xtype: 'panel',
    	scrollable: true,
    	bodyPadding: 12,
        bodyCls: 'x-selectable yasmine-help-content',
    	bind: {
    		html: '{record.content}'
    	},
    	listeners: {
    		afterrender: function (panel) {
    			if (panel.body && panel.body.selectable) {
    				panel.body.selectable();
    			}
    		}
    	}
    }] 
})

Ext.on('resize', function() { 
	var main_help = Ext.ComponentQuery.query('main_help');
	if (main_help.length>0){
		yasmine.utils.ResponsiveUtil.fitHelpWindow(main_help[0]);
	}
    var stationxmlHelp = Ext.ComponentQuery.query('stationxml-help');
    if (stationxmlHelp.length > 0 && stationxmlHelp[0].isVisible()) {
        yasmine.utils.ResponsiveUtil.fitStationXmlHelpWindow(stationxmlHelp[0]);
    }
});
