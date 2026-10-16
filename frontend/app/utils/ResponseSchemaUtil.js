/* ****************************************************************************
* 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
*
* StationXML 1.2 Response descriptor cache and tree helpers.
*
* ****************************************************************************/


Ext.define('yasmine.utils.ResponseSchemaUtil', {
  singleton: true,

  descriptor: null,
  loading: false,
  waiters: null,

  constructor: function () {
    this.waiters = [];
    this.callParent(arguments);
  },

  load: function (callback, scope) {
    if (this.descriptor) {
      Ext.callback(callback, scope, [this.descriptor]);
      return;
    }
    this.waiters.push({callback: callback, scope: scope});
    if (this.loading) {
      return;
    }
    this.loading = true;
    Ext.Ajax.request({
      method: 'GET',
      url: '/api/channel/response/schema/',
      scope: this,
      success: function (response) {
        let payload = Ext.decode(response.responseText);
        this.descriptor = payload.data;
        this.finishLoad(this.descriptor);
      },
      failure: function () {
        this.finishLoad(null);
      }
    });
  },

  finishLoad: function (descriptor) {
    this.loading = false;
    let waiters = this.waiters.slice();
    this.waiters.length = 0;
    Ext.Array.each(waiters, function (waiter) {
      Ext.callback(waiter.callback, waiter.scope, [descriptor]);
    });
  },

  getType: function (typeName) {
    return this.descriptor && this.descriptor.types
      ? this.descriptor.types[typeName]
      : null;
  },

  getNamespace: function (name) {
    if (!Ext.isString(name)) {
      return null;
    }
    if (name.charAt(0) === '{') {
      return name.substring(1, name.indexOf('}'));
    }
    return name.indexOf(':') > 0 ? '__prefixed__' : null;
  },

  getLocalName: function (name) {
    if (!Ext.isString(name)) {
      return name;
    }
    if (name.charAt(0) === '{') {
      return name.substring(name.indexOf('}') + 1);
    }
    return name.indexOf(':') > 0 ? name.split(':').pop() : name;
  },

  isForeignName: function (name) {
    let namespace = this.getNamespace(name);
    return !!namespace && (!this.descriptor || namespace !== this.descriptor.namespace);
  },

  displayName: function (name) {
    if (this.isForeignName(name)) {
      return this.getLocalName(name) + ' <span style="color:#777">(foreign namespace)</span>';
    }
    return name;
  },

  childDefinition: function (parentType, childName) {
    let parentDefinition = this.getType(parentType);
    let localName = this.getLocalName(childName);
    if (!parentDefinition) {
      return null;
    }
    return Ext.Array.findBy(parentDefinition.children || [], function (definition) {
      return definition.name === localName;
    }) || null;
  },

  typeForChild: function (parentType, childName) {
    let definition = this.childDefinition(parentType, childName);
    return definition ? definition.type : null;
  },

  definitionForNode: function (node) {
    return node ? this.getType(node.get('schemaType')) : null;
  },

  countChildren: function (node, name) {
    let count = 0;
    Ext.Array.each(node.childNodes || [], function (child) {
      if (this.getLocalName(child.get('key')) === name) {
        count++;
      }
    }, this);
    return count;
  },

  conflictingNodes: function (node, definition) {
    let conflicts = Ext.Array.clone(definition.conflicts || []);
    let parentDefinition = this.definitionForNode(node);
    if (definition.choice && parentDefinition && parentDefinition.choices) {
      Ext.Array.each(parentDefinition.children || [], function (candidate) {
        if (candidate.choice === definition.choice && candidate.name !== definition.name) {
          conflicts.push(candidate.name);
        }
      });
    }
    return Ext.Array.filter(node.childNodes || [], function (child) {
      return Ext.Array.contains(conflicts, this.getLocalName(child.get('key')));
    }, this);
  },

  childOptions: function (node) {
    if (!node || node.get('readOnly') || node.get('foreign')) {
      return [];
    }
    let typeDefinition = this.definitionForNode(node);
    if (!typeDefinition || typeDefinition.kind !== 'complex') {
      return [];
    }
    let options = [];
    Ext.Array.each(typeDefinition.children || [], function (definition) {
      let count = this.countChildren(node, definition.name);
      let unlimited = definition.max === 'unbounded';
      let conflicts = this.conflictingNodes(node, definition);
      let hasChoiceReplacement = conflicts.length > 0;
      if ((unlimited || count < definition.max) && (count === 0 || unlimited)) {
        options.push({
          definition: definition,
          conflicts: conflicts,
          replaces: hasChoiceReplacement
        });
      }
    }, this);
    return options;
  },

  canAddNode: function (node) {
    return this.childOptions(node).length > 0;
  },

  dependentDeleteNodes: function (node) {
    if (!node || !node.parentNode) {
      return [];
    }
    let parentDefinition = this.definitionForNode(node.parentNode);
    let childDefinition = this.childDefinition(node.parentNode.get('schemaType'), node.get('key'));
    if (!parentDefinition || !childDefinition || !childDefinition.choice) {
      return [node];
    }
    let choice = parentDefinition.choices && parentDefinition.choices[childDefinition.choice];
    if (!choice || !choice.allOrNone) {
      return [node];
    }
    return Ext.Array.filter(node.parentNode.childNodes || [], function (candidate) {
      let definition = this.childDefinition(node.parentNode.get('schemaType'), candidate.get('key'));
      return definition && definition.choice === childDefinition.choice;
    }, this);
  },

  canDeleteNode: function (node) {
    if (!node || node.isRoot() || node.get('readOnly') || node.get('foreign') || !node.parentNode) {
      return false;
    }
    let definition = this.childDefinition(node.parentNode.get('schemaType'), node.get('key'));
    if (!definition) {
      return false;
    }
    let count = this.countChildren(node.parentNode, definition.name);
    if ((definition.min || 0) >= count) {
      return false;
    }
    if (definition.requiredUnless) {
      let alternativeExists = Ext.Array.some(definition.requiredUnless, function (name) {
        return this.countChildren(node.parentNode, name) > 0;
      }, this);
      if (!alternativeExists && count <= 1) {
        return false;
      }
    }
    return true;
  },

  insertionTarget: function (parentNode, definition) {
    let target = null;
    let parentDefinition = this.definitionForNode(parentNode) || {};
    Ext.Array.each(parentNode.childNodes || [], function (child) {
      if (target) {
        return;
      }
      let childDefinition = child.get('foreign')
        ? {order: parentDefinition.foreignChildOrder}
        : this.childDefinition(parentNode.get('schemaType'), child.get('key'));
      if (childDefinition && childDefinition.order !== undefined && childDefinition.order > definition.order) {
        target = child;
      }
    }, this);
    return target;
  },

  defaultScalarValue: function (typeName) {
    let definition = this.getType(typeName) || {};
    if (definition.enum && definition.enum.length) {
      return definition.enum[0];
    }
    if (definition.valueType === 'number' || definition.valueType === 'integer') {
      return '0';
    }
    return '';
  },

  defaultAttributes: function (typeName, parentNode) {
    let result = {};
    let definition = this.getType(typeName) || {};
    Ext.Object.each(definition.attributes || {}, function (name, attribute) {
      if (!attribute.required) {
        return;
      }
      if (typeName === 'Stage' && name === 'number' && parentNode) {
        result[name] = String(this.countChildren(parentNode, 'Stage') + 1);
      } else if (attribute.fixed !== undefined) {
        result[name] = attribute.fixed;
      } else {
        result[name] = this.defaultScalarValue(attribute.type);
      }
    }, this);
    return result;
  },

  createLegacyNode: function (name, typeName, parentNode) {
    let definition = this.getType(typeName);
    if (!definition || definition.kind === 'simple') {
      let simpleResult = {};
      simpleResult[name] = this.defaultScalarValue(typeName);
      return simpleResult;
    }

    let value = {};
    let attributes = this.defaultAttributes(typeName, parentNode);
    if (Ext.Object.getSize(attributes)) {
      value.attributes = attributes;
    }
    let children = [];
    Ext.Array.each(definition.children || [], function (childDefinition) {
      let required = childDefinition.min || 0;
      if (childDefinition.requiredUnless && !required) {
        required = 1;
      }
      for (let index = 0; index < required; index++) {
        children.push(this.createLegacyNode(childDefinition.name, childDefinition.type, null));
      }
    }, this);
    if (children.length) {
      value.children = children;
    }
    let result = {};
    result[name] = value;
    return result;
  },

  allowedAttributes: function (node) {
    if (!node || node.get('readOnly') || node.get('foreign')) {
      return [];
    }
    let definition = this.definitionForNode(node);
    let current = node.get(node.get('key')) || {};
    let attributes = current.attributes || {};
    let result = [];
    Ext.Object.each((definition && definition.attributes) || {}, function (name, attributeDefinition) {
      if (!attributes.hasOwnProperty(name)) {
        result.push({name: name, definition: attributeDefinition});
      }
    });
    return result;
  },

  isForeignAttribute: function (name) {
    return this.isForeignName(name) || (Ext.isString(name) && name.indexOf(':') > 0);
  },

  attributeDefinition: function (node, name) {
    let definition = this.definitionForNode(node);
    return definition && definition.attributes ? definition.attributes[name] : null;
  }
});
