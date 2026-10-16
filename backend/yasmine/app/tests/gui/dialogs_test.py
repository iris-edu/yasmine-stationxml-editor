# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
# GUI smoke: import, wizard, parameter editor, and help dialogs.

import unittest

from yasmine.app.tests.common import check_web_app_is_down, skip_unless_gui
from yasmine.app.tests.common.wgui import SeletiounTestMixin


@skip_unless_gui
@unittest.skipIf(check_web_app_is_down(), "Application is down")
class DialogsGuiTest(SeletiounTestMixin):

    def test_required_dialog_classes_exist(self):
        self.open_page('#xmls')
        ready = self.driver.execute_script("""
            return !!(
                Ext.ClassManager.getByAlias('widget.xml-import') &&
                Ext.ClassManager.getByAlias('widget.wizard-create') &&
                Ext.ClassManager.getByAlias('widget.parameter-editor') &&
                Ext.ClassManager.getByAlias('widget.main_help') &&
                Ext.ClassManager.getByAlias('widget.stationxml-help') &&
                Ext.ClassManager.getByAlias('widget.yasmine-data-availability-field') &&
                Ext.ClassManager.getByAlias('widget.measurement-metadata-window')
            );
        """)
        self.assertTrue(ready, 'required Ext dialog classes are missing')

    def test_xml_import_dialog_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script("Ext.create({xtype: 'xml-import'}).show();")
        self.wait_js(
            "Ext.ComponentQuery.query('xml-import').length>0",
            'xml-import dialog missing',
        )

    def test_help_window_opens(self):
        self.open_page('#about')
        self.driver.execute_script(
            "Ext.create({xtype: 'main_help'}).show();"
        )
        self.wait_js(
            "Ext.ComponentQuery.query('main_help').length>0",
            'help window missing',
        )

    def test_stationxml_help_window_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script(
            "Ext.create({xtype: 'stationxml-help'}).show();"
        )
        self.wait_js(
            "Ext.ComponentQuery.query('stationxml-help').length>0",
            'stationxml-help window missing',
        )

    def test_data_availability_editor_creates(self):
        self.open_page('#xmls')
        created = self.driver.execute_script("""
            var editor = Ext.create({xtype: 'yasmine-data-availability-field'});
            return !!(editor && editor.getXType &&
                editor.getXType() === 'yasmine-data-availability-field');
        """)
        self.assertTrue(created, 'data availability editor missing')

    def test_measurement_metadata_window_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script(
            "Ext.create({xtype: 'measurement-metadata-window'}).show();"
        )
        self.wait_js(
            "Ext.ComponentQuery.query('measurement-metadata-window').length>0",
            'measurement metadata window missing',
        )

    def test_measurement_metadata_buttons_fit(self):
        self.open_page('#xmls')
        self.resize_viewport(375, 812)
        opened = self.driver.execute_script("""
            return (function () {
                try {
                    Ext.ComponentQuery.query('measurement-metadata-window').forEach(
                        function (win) {
                            if (win.destroy) { win.destroy(); }
                        }
                    );
                    Ext.create({xtype: 'measurement-metadata-window'}).show();
                    return {ok: true};
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error)
                    };
                }
            })();
        """)
        self.assertTrue(opened.get('ok'), opened)
        self.wait_js(
            "Ext.ComponentQuery.query('measurement-metadata-window').length>0",
            'measurement metadata window missing',
        )
        geometry = self.driver.execute_script("""
            var win = Ext.ComponentQuery.query('measurement-metadata-window')[0];
            var clearBtn = win && win.down('button[text=Clear Metadata]');
            var saveBtn = win && win.down('button[text=Save]');
            var cancelBtn = win && win.down('button[text=Cancel]');
            var winBox = win && win.getBox();
            function fits(box, host) {
                if (!box || !host) { return false; }
                return box.x >= host.x - 2 &&
                    box.y >= host.y - 2 &&
                    box.x + box.width <= host.x + host.width + 2 &&
                    box.y + box.height <= host.y + host.height + 2;
            }
            function info(btn) {
                if (!btn) { return null; }
                var box = btn.getBox();
                return {
                    visible: btn.isVisible(true),
                    fits: !!(winBox && fits(box, winBox)),
                    w: box.width,
                    h: box.height,
                    y: box.y
                };
            }
            return {
                winHeight: winBox && winBox.height,
                clear: info(clearBtn),
                save: info(saveBtn),
                cancel: info(cancelBtn)
            };
        """)
        self.save_screenshot('measurement-metadata-buttons')
        for name in ('clear', 'save', 'cancel'):
            button = geometry.get(name) or {}
            self.assertTrue(
                button.get('visible'),
                '%s button missing: %s' % (name, geometry),
            )
            self.assertTrue(
                button.get('fits'),
                '%s button does not fit: %s' % (name, geometry),
            )
            self.assertGreater(
                button.get('h') or 0,
                20,
                '%s button is clipped: %s' % (name, geometry),
            )

    def test_xml_edit_dialog_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script("Ext.create({xtype: 'xml-edit'}).show();")
        self.wait_js(
            "Ext.ComponentQuery.query('xml-edit').length>0",
            'xml-edit dialog missing',
        )

    def test_xml_edit_header_tools_are_touch_sized_and_aligned(self):
        self.open_page('#xmls')
        self.resize_viewport(375, 812)
        geometry = self.driver.execute_script("""
            var win = Ext.create({xtype: 'xml-edit'});
            win.show();
            yasmine.utils.ResponsiveUtil.syncHeaderTools();

            return win.header.query('tool').map(function (tool) {
                var outer = tool.el.dom.getBoundingClientRect();
                var inner = tool.toolEl.dom.getBoundingClientRect();
                var innerCenterX = inner.left + inner.width / 2;
                var innerCenterY = inner.top + inner.height / 2;
                var target = document.elementFromPoint(innerCenterX, innerCenterY);
                return {
                    type: tool.type,
                    width: outer.width,
                    height: outer.height,
                    iconWidth: inner.width,
                    iconHeight: inner.height,
                    iconFontSize: parseFloat(
                        window.getComputedStyle(tool.toolEl.dom).fontSize
                    ),
                    centerDeltaX: Math.abs(
                        outer.left + outer.width / 2 - innerCenterX
                    ),
                    centerDeltaY: Math.abs(
                        outer.top + outer.height / 2 - innerCenterY
                    ),
                    iconInsideHitTarget: tool.el.dom.contains(target)
                };
            });
        """)
        self.save_screenshot('xml-edit-touch-header-tools')
        self.assertEqual(
            [tool.get('type') for tool in geometry],
            ['help', 'close'],
            geometry,
        )
        for tool in geometry:
            self.assertGreaterEqual(tool.get('width') or 0, 44, tool)
            self.assertGreaterEqual(tool.get('height') or 0, 44, tool)
            self.assertGreaterEqual(tool.get('iconWidth') or 0, 28, tool)
            self.assertGreaterEqual(tool.get('iconHeight') or 0, 28, tool)
            self.assertGreaterEqual(tool.get('iconFontSize') or 0, 26, tool)
            self.assertLessEqual(tool.get('centerDeltaX') or 0, 1, tool)
            self.assertLessEqual(tool.get('centerDeltaY') or 0, 1, tool)
            self.assertTrue(tool.get('iconInsideHitTarget'), tool)

    def test_wizard_dialog_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script("Ext.create({xtype: 'wizard-create'}).show();")
        self.wait_js(
            "Ext.ComponentQuery.query('wizard-create').length>0",
            'wizard dialog missing',
        )

    def test_wizard_final_step_has_visible_content(self):
        self.open_page('#xmls')
        geometry = self.driver.execute_script("""
            return (function () {
                Ext.ComponentQuery.query('wizard-create').forEach(function (win) {
                    if (win.destroy) { win.destroy(); }
                });
                var win = Ext.create({xtype: 'wizard-create'});
                var vm = win.getViewModel();
                vm.set('networkCode', 'XX');
                vm.set('stationCode', 'YYYY');
                vm.set('channelStoredData', {channelInfos: []});
                vm.set('currentIndex', 3);
                win.show();
                win.getLayout().setActiveItem(3);
                win.setTitle(vm.get('currentTitle'));
                var step = win.down('wizard-final-step');
                var controller = step && step.getController();
                if (controller && controller.initComponent) {
                    controller.initComponent();
                }
                var inner = step && step.child();
                var checkbox = step && step.down('checkboxfield');
                var combo = step && step.down('combobox');
                var nameField = step && step.down('[reference=newlibraryname]');
                var text = (step && step.el && step.el.dom.innerText) || '';
                function boxOf(cmp) {
                    if (!cmp || !cmp.getBox) { return null; }
                    var box = cmp.getBox();
                    return {
                        visible: !!(cmp.isVisible && cmp.isVisible(true)),
                        w: box.width,
                        h: box.height
                    };
                }
                return {
                    title: win.getTitle && win.getTitle(),
                    step: boxOf(step),
                    inner: boxOf(inner),
                    checkbox: boxOf(checkbox),
                    combo: boxOf(combo),
                    nameField: boxOf(nameField),
                    text: text.replace(/\\s+/g, ' ').trim()
                };
            })();
        """)
        self.save_screenshot('wizard-final-step')
        self.assertTrue(
            (geometry.get('inner') or {}).get('visible'),
            'final step inner container hidden: %s' % geometry,
        )
        self.assertGreater(
            (geometry.get('inner') or {}).get('w') or 0,
            200,
            'final step inner container has no width: %s' % geometry,
        )
        self.assertTrue(
            (geometry.get('checkbox') or {}).get('visible'),
            'final step checkbox hidden: %s' % geometry,
        )
        self.assertGreater(
            (geometry.get('checkbox') or {}).get('w') or 0,
            100,
            'final step checkbox has no width: %s' % geometry,
        )
        text = geometry.get('text') or ''
        self.assertIn('User Library', text, geometry)
        self.assertIn('Use an existing library', text, geometry)
        self.assertIn('Create a new library', text, geometry)
        combo_visible = (geometry.get('combo') or {}).get('visible')
        name_visible = (geometry.get('nameField') or {}).get('visible')
        self.assertTrue(
            combo_visible or name_visible,
            'final step library choice hidden: %s' % geometry,
        )
        title = geometry.get('title') or ''
        self.assertNotIn('Networkwork', title, geometry)
        self.assertIn('FINAL STEP', title.upper(), geometry)

    def test_wizard_channel_step_has_visible_content(self):
        self.open_page('#xmls')
        self.driver.execute_script("""
            Ext.ComponentQuery.query('wizard-create').forEach(function (win) {
                if (win.destroy) { win.destroy(); }
            });
            var win = Ext.create({xtype: 'wizard-create'});
            var vm = win.getViewModel();
            vm.set('currentIndex', 2);
            vm.set('stationStoredData', {activeSampleRate: 1, attributes: []});
            win.show();
            win.getLayout().setActiveItem(2);
            var step = win.down('wizard-create-channel');
            if (step && step.getController()) {
                step.getController().initComponent(null, null);
            }
        """)
        self.wait_js(
            "!!Ext.ComponentQuery.query('channel-step-1')[0]",
            'channel step 1 missing',
        )
        geometry = self.driver.execute_script("""
            var step = Ext.ComponentQuery.query('channel-step-1')[0];
            var box = step && step.getBox ? step.getBox() : null;
            var win = Ext.ComponentQuery.query('wizard-create')[0];
            return {
                visible: !!(step && step.isVisible && step.isVisible(true)),
                w: box && box.width,
                h: box && box.height,
                title: win && win.getTitle && win.getTitle()
            };
        """)
        self.save_screenshot('wizard-channel-step')
        self.assertTrue(geometry.get('visible'), 'channel step hidden: %s' % geometry)
        self.assertGreater(geometry.get('w') or 0, 200, geometry)
        self.assertGreater(geometry.get('h') or 0, 80, geometry)
        title = geometry.get('title') or ''
        self.assertNotIn('Networkwork', title, geometry)
        self.assertIn('CHANNEL', title.upper(), geometry)

    def test_parameter_editor_dialog_opens(self):
        self.open_page('#xmls')
        self.driver.execute_script("Ext.create({xtype: 'parameter-editor'}).show();")
        self.wait_js(
            "Ext.ComponentQuery.query('parameter-editor').length>0",
            'parameter-editor dialog missing',
        )

    def test_comments_editor_header_stays_compact(self):
        self.open_page('#xmls')
        opened = self.driver.execute_script("""
            return (function () {
                try {
                    Ext.ComponentQuery.query('parameter-editor').forEach(function (win) {
                        if (win.destroy) { win.destroy(); }
                    });
                    var record = Ext.create('yasmine.model.Parameter');
                    record.set('name', 'comments');
                    record.set('class', 'yasmine-comments-field');
                    record.set('value', []);
                    var win = Ext.create({xtype: 'parameter-editor'});
                    win.getViewModel().set('record', record);
                    win.getViewModel().set('nodeType', yasmine.NodeTypeEnum.station);
                    win.getController().createFrom();
                    win.show();
                    return {ok: true};
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error)
                    };
                }
            })();
        """)
        self.assertTrue(opened.get('ok'), opened)
        self.wait_js(
            "Ext.ComponentQuery.query('yasmine-comments-field grid').length>0",
            'comments grid missing',
        )
        geometry = self.driver.execute_script("""
            var field = Ext.ComponentQuery.query('yasmine-comments-field')[0];
            var grid = field && field.down('grid');
            var header = grid && grid.headerCt;
            var authors = grid && grid.getColumnManager &&
                grid.getColumnManager().getColumns().filter(function (col) {
                    return col.dataIndex === 'authors';
                })[0];
            return {
                headerHeight: header && header.getHeight ? header.getHeight() : null,
                authorsHeight: authors && authors.getHeight ? authors.getHeight() : null,
                authorsFlex: authors && authors.flex,
                gridHeight: grid && grid.getHeight ? grid.getHeight() : null
            };
        """)
        self.save_screenshot('comments-editor-header')
        self.assertLess(
            geometry.get('headerHeight') or 0,
            80,
            'comments grid header is oversized: %s' % geometry,
        )
        self.assertNotEqual(
            geometry.get('authorsHeight'),
            400,
            'Authors column still has a 400px header: %s' % geometry,
        )

    def test_comment_stationxml_id_is_not_store_identity(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                var field;
                try {
                    var parameter = Ext.create('yasmine.model.Parameter');
                    parameter.set('value', [
                        {id: null, value: 'without id 1'},
                        {id: null, value: 'without id 2'},
                        {id: 7, value: 'duplicate id 1'},
                        {id: 7, value: 'duplicate id 2'}
                    ]);
                    field = Ext.create({xtype: 'yasmine-comments-field'});
                    field.getViewModel().set('record', parameter);
                    field.getController().initData();

                    var store = field.getViewModel().getStore('commentStore');
                    var records = store.getRange();
                    var domainIdsBefore = records.map(function (record) {
                        return record.get('id');
                    });
                    var extIds = records.map(function (record) {
                        return record.getId();
                    });
                    var editedRecord = records[2];
                    var editedRecordId = editedRecord.getId();

                    editedRecord.set('id', 8);
                    var identityStable = editedRecord.getId() === editedRecordId;
                    var lookupStable = store.getById(editedRecordId) === editedRecord;
                    var countAfterEdit = store.getCount();

                    records[0].drop();
                    field.getController().fillRecord();
                    var persisted = parameter.get('value');

                    return {
                        ok: true,
                        countBefore: records.length,
                        domainIdsBefore: domainIdsBefore,
                        extIdsUnique: new Set(extIds).size === extIds.length,
                        identityStable: identityStable,
                        lookupStable: lookupStable,
                        countAfterEdit: countAfterEdit,
                        countAfterDrop: store.getCount(),
                        persistedIds: persisted.map(function (comment) {
                            return comment.id;
                        }),
                        persistedValues: persisted.map(function (comment) {
                            return comment.value;
                        })
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error)
                    };
                } finally {
                    Ext.destroy(field);
                }
            })();
        """)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(result.get('countBefore'), 4, result)
        self.assertEqual(result.get('domainIdsBefore'), [None, None, 7, 7], result)
        self.assertTrue(result.get('extIdsUnique'), result)
        self.assertTrue(result.get('identityStable'), result)
        self.assertTrue(result.get('lookupStable'), result)
        self.assertEqual(result.get('countAfterEdit'), 4, result)
        self.assertEqual(result.get('countAfterDrop'), 3, result)
        self.assertEqual(result.get('persistedIds'), [None, 8, 7], result)
        self.assertEqual(
            result.get('persistedValues'),
            ['without id 2', 'duplicate id 1', 'duplicate id 2'],
            result,
        )

    def test_collection_models_use_independent_store_identity(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                var records = [];
                var stores = [];
                try {
                    var transientModels = [
                        'yasmine.view.xml.builder.parameter.items.comments.Comment',
                        'yasmine.view.xml.builder.parameter.items.operators.Operator',
                        'yasmine.view.xml.builder.parameter.items.externalreferences.ExternalReference',
                        'yasmine.view.xml.builder.parameter.items.dataavailability.DataAvailabilitySpan',
                        'yasmine.view.xml.builder.parameter.items.channelequipment.CalibrationDate',
                        'yasmine.view.xml.builder.parameter.components.person.Person',
                        'yasmine.view.xml.builder.parameter.components.person.AgencyHelper',
                        'yasmine.view.xml.builder.parameter.components.person.Name',
                        'yasmine.view.xml.builder.parameter.components.person.Agency',
                        'yasmine.view.xml.builder.parameter.components.person.Email',
                        'yasmine.view.xml.builder.parameter.components.person.Phone',
                        'yasmine.view.xml.builder.parameter.items.identifiers.Identifier',
                        'yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate',
                        'yasmine.view.xml.builder.parameter.items.equipments.Equipment',
                        'XmlAttribute',
                        'XmlValue',
                        'yasmine.view.xml.builder.children.control.Date',
                        'yasmine.view.xml.builder.parameter.items.texthelp.Help',
                        'yasmine.view.xml.builder.parameter.items.channeltypes.ChannelType',
                        'yasmine.view.xml.builder.parameter.items.restrictedstatus.RestrictedStatus'
                    ];
                    var transientChecks = transientModels.map(function (name) {
                        var Model = Ext.ClassManager.get(name);
                        if (!Model) {
                            throw new Error('Model is not loaded: ' + name);
                        }
                        var first = new Model();
                        var second = new Model();
                        var store = Ext.create('Ext.data.Store', {model: Model});
                        records.push(first, second);
                        stores.push(store);
                        store.add([first, second]);
                        var idField = first.getField('_extRecordId');
                        return {
                            name: name,
                            idProperty: first.idProperty,
                            firstId: first.getId(),
                            secondId: second.getId(),
                            persistent: idField && idField.persist,
                            duplicateCount: store.getCount(),
                            firstLookupStable: store.getById(first.getId()) === first,
                            secondLookupStable: store.getById(second.getId()) === second
                        };
                    });

                    var serverModels = [
                        'yasmine.model.Parameter',
                        'yasmine.model.UserLibrary',
                        'yasmine.model.Xml'
                    ];
                    var serverChecks = serverModels.map(function (name) {
                        var Model = Ext.ClassManager.get(name);
                        if (!Model) {
                            throw new Error('Model is not loaded: ' + name);
                        }
                        var server = new Model({id: 42});
                        var first = new Model();
                        var second = new Model();
                        var store = Ext.create('Ext.data.Store', {model: Model});
                        records.push(server, first, second);
                        stores.push(store);
                        store.add([server, first, second]);
                        return {
                            name: name,
                            count: store.getCount(),
                            serverId: server.getId(),
                            firstId: first.getId(),
                            secondId: second.getId()
                        };
                    });

                    var Help = Ext.ClassManager.get('yasmine.help.HelpModel');
                    if (!Help) {
                        throw new Error('yasmine.help.HelpModel is not loaded');
                    }
                    var help = new Help({key: 'Network.Station'});
                    records.push(help);

                    var Xml = Ext.ClassManager.get('yasmine.model.Xml');
                    var xmlIdField = Xml && Xml.getField('id');
                    return {
                        ok: true,
                        transientChecks: transientChecks,
                        serverChecks: serverChecks,
                        helpIdProperty: help.idProperty,
                        helpId: help.getId(),
                        xmlIdPersistent: xmlIdField && xmlIdField.persist
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error),
                        stack: error && error.stack
                    };
                } finally {
                    Ext.destroy(stores);
                    Ext.destroy(records);
                }
            })();
        """)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(len(result.get('transientChecks') or []), 20, result)
        for check in result.get('transientChecks') or []:
            self.assertEqual(check.get('idProperty'), '_extRecordId', check)
            self.assertLess(check.get('firstId'), 0, check)
            self.assertLess(check.get('secondId'), 0, check)
            self.assertNotEqual(check.get('firstId'), check.get('secondId'), check)
            self.assertFalse(check.get('persistent'), check)
            self.assertEqual(check.get('duplicateCount'), 2, check)
            self.assertTrue(check.get('firstLookupStable'), check)
            self.assertTrue(check.get('secondLookupStable'), check)
        for check in result.get('serverChecks') or []:
            self.assertEqual(check.get('count'), 3, check)
            self.assertEqual(check.get('serverId'), 42, check)
            self.assertLess(check.get('firstId'), 0, check)
            self.assertLess(check.get('secondId'), 0, check)
            self.assertNotEqual(check.get('firstId'), check.get('secondId'), check)
        self.assertEqual(result.get('helpIdProperty'), 'key', result)
        self.assertEqual(result.get('helpId'), 'Network.Station', result)
        self.assertFalse(result.get('xmlIdPersistent'), result)

    def test_equipment_duplicate_calibration_dates_are_row_scoped(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                var controller;
                var store;
                try {
                    var Equipment = Ext.ClassManager.get(
                        'yasmine.view.xml.builder.parameter.items.equipments.Equipment'
                    );
                    var CalibrationDate = Ext.ClassManager.get(
                        'yasmine.view.xml.builder.parameter.items.equipments.CalibrationDate'
                    );
                    var Controller = Ext.ClassManager.get(
                        'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditorController'
                    );
                    if (!Equipment || !CalibrationDate || !Controller) {
                        throw new Error('Equipment editor classes are not loaded');
                    }
                    var duplicate = new Date('2024-01-02T03:04:05Z');
                    var replacement = new Date('2025-02-03T04:05:06Z');
                    var equipment = new Equipment({
                        calibrationDates: [duplicate, duplicate]
                    });
                    store = Ext.create('Ext.data.Store', {
                        model: CalibrationDate,
                        data: [{value: duplicate}, {value: duplicate}]
                    });
                    var viewModel = {
                        get: function (name) {
                            return name === 'selectedEquipment' ? equipment : null;
                        },
                        getStore: function (name) {
                            return name === 'calibrationDateStore' ? store : null;
                        }
                    };
                    controller = new Controller();
                    controller.getViewModel = function () {
                        return viewModel;
                    };

                    store.getAt(0).set('value', replacement);
                    controller.onCalibrationDateEdited();
                    var afterEdit = equipment.get('calibrationDates').map(function (value) {
                        return value.toISOString();
                    });

                    controller.onDeleteCalibrationDateClick(null, 0);
                    var afterDelete = equipment.get('calibrationDates').map(function (value) {
                        return value.toISOString();
                    });

                    return {
                        ok: true,
                        rowIdsUnique: store.getCount() === 1,
                        afterEdit: afterEdit,
                        afterDelete: afterDelete
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error),
                        stack: error && error.stack
                    };
                } finally {
                    Ext.destroy(controller, store);
                }
            })();
        """)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(
            result.get('afterEdit'),
            ['2025-02-03T04:05:06.000Z', '2024-01-02T03:04:05.000Z'],
            result,
        )
        self.assertEqual(
            result.get('afterDelete'),
            ['2024-01-02T03:04:05.000Z'],
            result,
        )

    def test_comment_form_person_toolbar_fits(self):
        self.open_page('#xmls')
        opened = self.driver.execute_script("""
            return (function () {
                try {
                    Ext.ComponentQuery.query('comments-editor-form').forEach(function (win) {
                        if (win.destroy) { win.destroy(); }
                    });
                    var win = Ext.create({xtype: 'comments-editor-form'});
                    win.show();
                    return {ok: true};
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error)
                    };
                }
            })();
        """)
        self.assertTrue(opened.get('ok'), opened)
        self.wait_js(
            "Ext.ComponentQuery.query('comments-editor-form person-list').length>0",
            'comment form person-list missing',
        )
        geometry = self.driver.execute_script("""
            var win = Ext.ComponentQuery.query('comments-editor-form')[0];
            var grid = win && win.down('person-list');
            var tbar = grid && grid.getDockedItems('toolbar[dock=top]')[0];
            var buttons = tbar ? tbar.query('button') : [];
            var collectionLabel = tbar ? tbar.down('label') : null;
            var saveBtn = win && win.down('button[text=Save]');
            var cancelBtn = win && win.down('button[text=Cancel]');
            var winBox = win && win.getBox();
            var gridBox = grid && grid.getBox();
            var tbarBox = tbar && tbar.getBox();
            function fits(box, host) {
                if (!box || !host) { return false; }
                return box.x >= host.x - 2 &&
                    box.y >= host.y - 2 &&
                    box.x + box.width <= host.x + host.width + 2 &&
                    box.y + box.height <= host.y + host.height + 2;
            }
            return {
                winWidth: winBox && winBox.width,
                winHeight: winBox && winBox.height,
                gridWidth: gridBox && gridBox.width,
                tbarWidth: tbarBox && tbarBox.width,
                buttonCount: buttons.length,
                collectionLabel: collectionLabel && collectionLabel.el ?
                    collectionLabel.el.dom.innerText.trim() : null,
                buttonTooltips: buttons.map(function (btn) {
                    return (btn.el &&
                        btn.el.dom.getAttribute('data-qtip')) ||
                        btn.tooltip ||
                        (btn.initialConfig && btn.initialConfig.tooltip) ||
                        (btn.getTooltip ? btn.getTooltip() : null);
                }),
                buttonsFit: buttons.every(function (btn) {
                    return btn.isVisible(true) && fits(btn.getBox(), tbarBox || gridBox);
                }),
                buttonBoxes: buttons.map(function (btn) {
                    var box = btn.getBox();
                    return {
                        w: box.width,
                        h: box.height,
                        x: box.x,
                        y: box.y,
                        visible: btn.isVisible(true)
                    };
                }),
                saveVisible: !!(saveBtn && saveBtn.isVisible(true)),
                saveFits: !!(saveBtn && winBox && fits(saveBtn.getBox(), winBox)),
                cancelVisible: !!(cancelBtn && cancelBtn.isVisible(true)),
                cancelFits: !!(cancelBtn && winBox && fits(cancelBtn.getBox(), winBox))
            };
        """)
        self.save_screenshot('comment-form-person-toolbar')
        self.assertGreaterEqual(geometry.get('buttonCount') or 0, 3, geometry)
        self.assertEqual(geometry.get('collectionLabel'), 'Authors', geometry)
        self.assertEqual(
            geometry.get('buttonTooltips'),
            ['Add Author', 'Delete Author', 'Edit Author'],
            geometry,
        )
        self.assertTrue(
            geometry.get('buttonsFit'),
            'PERSONS toolbar buttons overflow: %s' % geometry,
        )
        self.assertTrue(geometry.get('saveVisible'), 'Save button missing: %s' % geometry)
        self.assertTrue(geometry.get('cancelVisible'), 'Cancel button missing: %s' % geometry)
        self.assertTrue(geometry.get('saveFits'), 'Save button does not fit: %s' % geometry)
        self.assertTrue(geometry.get('cancelFits'), 'Cancel button does not fit: %s' % geometry)
        self.assertGreater(
            geometry.get('gridWidth') or 0,
            (geometry.get('winWidth') or 0) * 0.7,
            'PERSONS grid is not stretching to dialog width: %s' % geometry,
        )

    def test_collection_editor_titles_match_item_context(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                var contacts;
                var contactEditor;
                var operatorEditor;
                var equipmentEditor;
                try {
                    Ext.syncRequire([
                        'yasmine.view.xml.builder.parameter.components.person.PersonList',
                        'yasmine.view.xml.builder.parameter.components.person.PersonEdit',
                        'yasmine.view.xml.builder.parameter.items.operators.OperatorsEditorForm',
                        'yasmine.view.xml.builder.parameter.items.equipments.EquipmentsEditor'
                    ]);
                    contacts = Ext.create({
                        xtype: 'person-list',
                        renderTo: Ext.getBody()
                    });
                    contacts.getViewModel().set('stationXmlPersonPath', 'Contact');
                    contacts.getViewModel().notify();
                    contacts.getController().syncPersonChrome();
                    var toolbar = contacts.getDockedItems('toolbar[dock=top]')[0];
                    var label = toolbar && toolbar.down('label');
                    var buttons = toolbar ? toolbar.query('button') : [];

                    contactEditor = Ext.create({xtype: 'person-edit'});
                    contactEditor.getViewModel().set('stationXmlPersonPath', 'Contact');
                    contactEditor.getViewModel().notify();
                    contactEditor.show();
                    operatorEditor = Ext.create({xtype: 'operators-editor-form'});
                    equipmentEditor = Ext.create({
                        xtype: 'yasmine-equipments-field',
                        renderTo: Ext.getBody()
                    });
                    var equipmentGrid = equipmentEditor.down('grid');
                    var equipmentToolbar = equipmentGrid &&
                        equipmentGrid.getDockedItems('toolbar[dock=top]')[0];
                    var equipmentTitle = equipmentToolbar &&
                        equipmentToolbar.items.getAt(0);

                    return {
                        ok: true,
                        collectionLabel: label && label.el ?
                            label.el.dom.innerText.trim() : null,
                        buttonTooltips: buttons.map(function (button) {
                            return (button.el &&
                                button.el.dom.getAttribute('data-qtip')) ||
                                button.tooltip ||
                                (button.initialConfig &&
                                    button.initialConfig.tooltip) ||
                                (button.getTooltip ?
                                    button.getTooltip() : null);
                        }),
                        contactTitle: contactEditor.getTitle(),
                        operatorTitle: operatorEditor.getTitle(),
                        equipmentTitle: equipmentTitle && equipmentTitle.el ?
                            equipmentTitle.el.dom.innerHTML : null
                    };
                } catch (error) {
                    return {
                        ok: false,
                        error: String((error && error.message) || error)
                    };
                } finally {
                    Ext.destroy(
                        contacts,
                        contactEditor,
                        operatorEditor,
                        equipmentEditor
                    );
                }
            })();
        """)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(result.get('collectionLabel'), 'Contacts', result)
        self.assertEqual(
            result.get('buttonTooltips'),
            ['Add Contact', 'Delete Contact', 'Edit Contact'],
            result,
        )
        self.assertEqual(result.get('contactTitle'), 'Contact', result)
        self.assertEqual(result.get('operatorTitle'), 'Operator', result)
        self.assertEqual(
            result.get('equipmentTitle'),
            '<b>Equipment</b>',
            result,
        )

    def test_parameter_labels_use_spaced_xml_names(self):
        self.open_page('#xmls')
        labels = self.driver.execute_script("""
            var Context = yasmine.utils.StationXmlHelpContext;
            return {
                startDate: Context.labelForParameter('start_date'),
                clockDrift: Context.labelForParameter(
                    'clock_drift_in_seconds_per_sample'
                ),
                samples: Context.labelForParameter(
                    'sample_rate_ratio_number_samples'
                ),
                sourceId: Context.labelForParameter('source_id'),
                comments: Context.labelForParameter('comments'),
                identifiers: Context.labelForParameter('identifiers'),
                operators: Context.labelForParameter('operators'),
                externalReferences: Context.labelForParameter(
                    'external_references'
                ),
                types: Context.labelForParameter('types'),
                equipments: Context.labelForParameter('equipments')
            };
        """)
        self.assertEqual(labels.get('startDate'), 'Start Date', labels)
        self.assertEqual(labels.get('clockDrift'), 'Clock Drift', labels)
        self.assertEqual(
            labels.get('samples'),
            'Sample Rate Ratio / Number Samples',
            labels,
        )
        self.assertEqual(labels.get('sourceId'), 'Source ID', labels)
        self.assertEqual(labels.get('comments'), 'Comments', labels)
        self.assertEqual(labels.get('identifiers'), 'Identifiers', labels)
        self.assertEqual(labels.get('operators'), 'Operators', labels)
        self.assertEqual(
            labels.get('externalReferences'),
            'External References',
            labels,
        )
        self.assertEqual(labels.get('types'), 'Types', labels)
        self.assertEqual(labels.get('equipments'), 'Equipment', labels)

    def test_stationxml_double_fields_keep_small_fractions(self):
        self.open_page('#xmls')
        result = self.driver.execute_script("""
            return (function () {
                try {
                    Ext.syncRequire([
                        'yasmine.view.xml.builder.parameter.items.float.StationXmlDoubleField',
                        'yasmine.view.xml.builder.parameter.items.float.FloatEditor',
                        'yasmine.view.xml.builder.parameter.items.longitude.LongitudeEditor',
                        'yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.ValueEditor'
                    ]);

                    function roundTrip(xtype, typed) {
                        var field = Ext.create({
                            xtype: xtype,
                            renderTo: Ext.getBody(),
                            validator: function () {
                                return true;
                            }
                        });
                        field.setRawValue(typed);
                        field.setValue(field.rawToValue(field.getRawValue()));
                        var result = {
                            ok: field.getValue() === Number(typed),
                            precision: field.decimalPrecision
                        };
                        field.destroy();
                        return result;
                    }

                    var floatSmall = roundTrip('yasmine-float-field', '0.001');
                    var floatSlow = roundTrip('yasmine-float-field', '0.000023148');
                    var longDouble = roundTrip(
                        'yasmine-stationxml-double-field',
                        '-180.12345678901234'
                    );
                    var longitudeField = Ext.create({
                        xtype: 'yasmine-longitude-field'
                    });
                    var longitudeMaxLengthOk = longitudeField.maxLength > 20;
                    longitudeField.destroy();

                    var grid = Ext.create({
                        xtype: 'channel-response-value-editor',
                        renderTo: Ext.getBody()
                    });
                    var record = Ext.create('XmlValue', {
                        name: 'Value',
                        value: '',
                        canHaveValue: true,
                        definition: {valueType: 'number'},
                        readOnly: false
                    });
                    var columns = grid.getColumns();
                    var valueCol = null;
                    for (var i = 0; i < columns.length; i++) {
                        if (columns[i].dataIndex === 'value') {
                            valueCol = columns[i];
                            break;
                        }
                    }
                    var editor = valueCol.getEditor(record);
                    var responseField = editor.field;
                    responseField.setRawValue('0.001');
                    responseField.setValue(
                        responseField.rawToValue(responseField.getRawValue())
                    );
                    var responseOk = responseField.getValue() === 0.001;
                    var responseXtype = responseField.getXType();
                    grid.destroy();

                    return {
                        floatSmallOk: floatSmall.ok,
                        floatPrecision: floatSmall.precision,
                        floatSlowOk: floatSlow.ok,
                        longitudeOk: longDouble.ok,
                        longitudeMaxLengthOk: longitudeMaxLengthOk,
                        responseOk: responseOk,
                        responseXtype: responseXtype
                    };
                } catch (e) {
                    return {error: String(e && e.message ? e.message : e)};
                }
            })();
        """)
        self.assertNotIn('error', result or {}, result)
        self.assertTrue(result.get('floatSmallOk'), result)
        self.assertEqual(result.get('floatPrecision'), 16, result)
        self.assertTrue(result.get('floatSlowOk'), result)
        self.assertTrue(result.get('longitudeOk'), result)
        self.assertTrue(result.get('longitudeMaxLengthOk'), result)
        self.assertTrue(result.get('responseOk'), result)
        self.assertEqual(
            result.get('responseXtype'),
            'yasmine-stationxml-double-field',
            result,
        )
