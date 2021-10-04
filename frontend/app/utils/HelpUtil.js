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


Ext.define("yasmine.utils.HelpUtil", {
    singleton: true,
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
    }
});


Ext.define('yasmine.help.HTMLEditor',{
	extend: 'Ext.form.field.HtmlEditor',
	alias: 'widget.help_html_editor',
	getToolbarCfg: function(){
        var cfg = this.callParent(arguments);
        if (this.readOnly){
        	cfg['hidden'] = true
        }
        return cfg
    },
    getDocMarkup: function() {
        var me = this,
            h = me.iframeEl.getHeight() - me.iframePad * 2;

        // - IE9+ require a strict doctype otherwise text outside visible area can't be selected.
        // - Opera inserts <P> tags on Return key, so P margins must be removed to avoid double line-height.
        // - On browsers other than IE, the font is not inherited by the IFRAME so it must be specified.
        return Ext.String.format(
               '<!DOCTYPE html>'
               + '<html><head><style type="text/css">'
               + (Ext.isOpera ? 'p{margin:0;}' : '')
               + 'body{border:0;margin:0;padding:{0}px;direction:' + (me.rtl ? 'rtl;' : 'ltr;')
               + (Ext.isIE8 ? Ext.emptyString : 'min-')
               + 'height:{1}px;box-sizing:border-box;-moz-box-sizing:border-box;-webkit-box-sizing:border-box;cursor:text;background-color:white;'
               + (Ext.isIE ? '' : 'font-size:12px;font-family:{2}')
               + '}</style><link rel="stylesheet" type="text/css" href="/static/css/help.css"/></head><body></body></html>'
            , me.iframePad, h, me.defaultFont);
    }    
})

Ext.define('yasmine.help.HelpModel', {
    extend: 'Ext.data.Model',
    fields: ['key', 'content'],
    idProperty: 'id',
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
    modal: false,
    alignOffset: [-10, 0],
    defaultAlign: 'r-r',
    alwaysOnTop: true,
    width: "30%",
    height: "80%",
    maximizable: true,
    border: false,
    layout: 'fit',
    items:[{
    	xtype: 'help_html_editor',
    	readOnly: true,
    	bind: {
    		value: '{record.content}'
    	}
    }] 
})

Ext.on('resize', function() { 
	var main_help = Ext.ComponentQuery.query('main_help');
	if (main_help.length>0){
		main_help[0].close()
	}
});
