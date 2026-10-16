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
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.xml.builder.parameter.items.channelresponse.treeeditor.tree.TreeController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.channel-response-tree',
  id: 'channel-response-tree-controller',
  listen: {
    controller: {
      '#channel-response-attribute-editor-controller': {
        onAttributeUpdated: 'onAttributeUpdated',
        onAttributeDeleted: 'onAttributeDeleted'
      },
      '#channel-response-value-editor-controller': {
        onNodenameUpdated: 'onNodeNameUpdated',
        onNodevalueUpdated: 'onNodeValueUpdated'
      }
    }
  },
  onExpandAll: function () {
    this.getView().getStore().getRoot().expandChildren(true);
  },
  onCollapseAll: function () {
    let rootNode = this.getView().getStore().getRoot();
    this.getView().setSelection(rootNode);
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
    this.getView().getStore().getRoot().collapseChildren(true);
  },
  onAddMenuBeforeShow: function (menu) {
    let selectedNode = this.getSelectedRecord();
    let options = yasmine.utils.ResponseSchemaUtil.childOptions(selectedNode);
    menu.removeAll();
    if (!options.length) {
      menu.add({text: 'No schema children available', disabled: true});
      return;
    }
    Ext.Array.each(options, function (option) {
      menu.add({
        text: Ext.htmlEncode(option.definition.name) + (option.replaces ? ' (replace current choice)' : ''),
        iconCls: option.replaces ? 'x-fa fa-exchange' : 'x-fa fa-code',
        handler: function () {
          this.onAddNewNodeClick(option);
        },
        scope: this
      });
    }, this);
  },
  onAddNewNodeClick: function (option) {
    let selectedNode = this.getSelectedRecord();
    if (!selectedNode || !option) {
      return;
    }
    if (option.conflicts && option.conflicts.length) {
      let names = Ext.Array.map(option.conflicts, function (node) {
        return node.get('key');
      }).join(', ');
      Ext.MessageBox.confirm(
        'Replace response choice',
        `Adding '${option.definition.name}' replaces: ${Ext.htmlEncode(names)}. Continue?`,
        function (button) {
          if (button === 'yes') {
            this.addSchemaOption(selectedNode, option);
          }
        },
        this
      );
      return;
    }
    this.addSchemaOption(selectedNode, option);
  },
  addSchemaOption: function (selectedNode, option) {
    Ext.Array.each(option.conflicts || [], function (node) {
      node.remove();
      node.destroy();
    });

    let parentDefinition = yasmine.utils.ResponseSchemaUtil.definitionForNode(selectedNode);
    let choice = option.definition.choice && parentDefinition && parentDefinition.choices
      ? parentDefinition.choices[option.definition.choice]
      : null;
    let definitions = [option.definition];
    if (choice && choice.allOrNone) {
      definitions = Ext.Array.filter(parentDefinition.children || [], function (definition) {
        return definition.choice === option.definition.choice &&
          yasmine.utils.ResponseSchemaUtil.countChildren(selectedNode, definition.name) === 0;
      });
    }

    let addedNode = null;
    Ext.Array.each(definitions, function (definition) {
      addedNode = this.addDefinition(selectedNode, definition) || addedNode;
    }, this);
    this.ensureRequiredChildren(selectedNode);
    selectedNode.expand();
    this.getView().setSelection(addedNode || selectedNode);
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
  },
  addDefinition: function (parentNode, definition) {
    let rawNode = yasmine.utils.ResponseSchemaUtil.createLegacyNode(
      definition.name,
      definition.type,
      parentNode
    );
    let editor = this.getView().up('channel-response-tree-editor');
    editor.getController().convertResponseTreeStore(rawNode, parentNode.get('schemaType'));
    let newNode = parentNode.createNode(rawNode);
    let target = yasmine.utils.ResponseSchemaUtil.insertionTarget(parentNode, definition);
    if (target) {
      parentNode.insertBefore(newNode, target);
    } else {
      parentNode.appendChild(newNode);
    }
    return newNode;
  },
  ensureRequiredChildren: function (parentNode) {
    let parentDefinition = yasmine.utils.ResponseSchemaUtil.definitionForNode(parentNode);
    Ext.Array.each((parentDefinition && parentDefinition.children) || [], function (definition) {
      let required = definition.min || 0;
      if (definition.requiredUnless) {
        let alternativeExists = Ext.Array.some(definition.requiredUnless, function (name) {
          return yasmine.utils.ResponseSchemaUtil.countChildren(parentNode, name) > 0;
        });
        if (!alternativeExists) {
          required = Math.max(required, 1);
        }
      }
      while (yasmine.utils.ResponseSchemaUtil.countChildren(parentNode, definition.name) < required) {
        this.addDefinition(parentNode, definition);
      }
    }, this);
  },
  onDeleteClick: function () {
    let node = this.getViewModel().get('selectedResponseNode');
    if (!yasmine.utils.ResponseSchemaUtil.canDeleteNode(node)) {
      return;
    }
    let nodeName = node.data.key;
    Ext.MessageBox.confirm(`Delete '${nodeName}' node`, `Are you sure you want to delete '${nodeName}'?`, function (btn) {
      if (btn === 'yes') {
        this.deleteNode();
      }
    }, this);
  },
  onAttributeUpdated: function (attributes) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let newAttr = {};
    attributes.forEach(x => {
      newAttr[x.name] = x.value;
    });

    if (!nodeData[nodeData.key]) {
      nodeData[nodeData.key] = {};
    }

    if (nodeData[nodeData.key]['attributes']) {
      nodeData[nodeData.key]['attributes'] = newAttr;
      return;
    }

    if (yasmine.utils.XmlNodeUtil.isPlainValue(selectedNode)) {
      let value = nodeData[nodeData.key];
      nodeData[nodeData.key] = {
        children: [value],
        attributes: newAttr
      };
      return;
    }

    nodeData[nodeData.key]['attributes'] = newAttr;
  },
  onAttributeDeleted: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let nodeValue = nodeData[nodeData.key];
    let attr = nodeValue && nodeValue['attributes'];
    if (attr) {
      delete attr[record.get('name')];
    }
  },
  onNodeValueUpdated: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let nodeName = `<span>${nodeData.key}</span>`;
    let encodedValue = Ext.htmlEncode(String(record.get('value') || ''));
    selectedNode.set('text', record.get('value') ? `${nodeName}:&nbsp;<b>${encodedValue}</b>` : nodeName);

    if (yasmine.utils.XmlNodeUtil.isPlainValue(selectedNode)) {
      nodeData[nodeData.key] = record.get('value');
    } else if (yasmine.utils.XmlNodeUtil.isArrayValue(selectedNode)) {
      nodeData[nodeData.key].children[0] = record.get('value');
    } else if (Ext.isObject(nodeData[nodeData.key])) {
      nodeData[nodeData.key].children = record.get('value') === ''
        ? []
        : [record.get('value')];
    }

    this.fireEvent('responseNodeSelected', selectedNode);
  },
  onNodeNameUpdated: function (record) {
    let selectedNode = this.getSelectedRecord();
    let nodeData = selectedNode.data;
    let oldName = record.previousValues.name;
    let newName = record.get('name');
    if (nodeData.hasOwnProperty(oldName)) {
      nodeData[newName] = nodeData[oldName];
      nodeData.key = newName;
      delete nodeData[oldName];
      selectedNode.set('text', yasmine.utils.XmlNodeUtil.getNodeTitle(selectedNode));
    }
  },
  deleteNode: function () {
    let node = this.getSelectedRecord();
    let parentNode = node.parentNode;
    let nodes = yasmine.utils.ResponseSchemaUtil.dependentDeleteNodes(node);
    Ext.Array.each(nodes, function (item) {
      item.remove();
      item.destroy();
    });

    this.getView().setSelection(parentNode);
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
  },
  getSelectedRecord: function () {
    return this.getView().getSelection()[0];
  },
  onResponseNodeSelect: function () {
    this.fireEvent('responseNodeSelected', this.getSelectedRecord());
  }
});
