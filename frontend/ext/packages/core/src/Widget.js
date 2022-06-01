/**
 * Ext.Widget is a light-weight Component that consists of nothing more than a template
 * Element that can be cloned to quickly and efficiently replicate many instances.
 * Ext.Widget is typically not instantiated directly, because the default template is
 * just a single element with no listeners. Instead Ext.Widget should be extended to
 * create Widgets that have a useful markup structure and event listeners.
 *
 * For example:
 *
 *      Ext.define('MyWidget', {
 *          extend: 'Ext.Widget',
 *
 *          // The element template passed to Ext.Element.create()
 *          element: {
 *              reference: 'element',
 *              listeners: {
 *                  click: 'onClick'
 *              },
 *              children: [{
 *                  reference: 'innerElement',
 *                  listeners: {
 *                      click: 'onInnerClick'
 *                  }
 *              }]
 *          },
 *
 *          constructor: function(config) {
 *              // It is important to remember to call the Widget superclass constructor
 *              // when overriding the constructor in a derived class. This ensures that
 *              // the element is initialized from the template, and that initConfig() is
 *              // is called.
 *              this.callParent([config]);
 *
 *              // After calling the superclass constructor, the Element is available and
 *              // can safely be manipulated. Reference Elements are instances of
 *              // Ext.Element, and are cached on each Widget instance by reference name.
 *              Ext.getBody().appendChild(this.element);
 *          },
 *
 *          onClick: function() {
 *              // listeners use this Widget instance as their scope
 *              console.log('element clicked', this);
 *          },
 *
 *          onInnerClick: function() {
 *              // access the innerElement reference by name
 *              console.log('inner element clicked', this.innerElement);
 *          }
 *      });
 *
 * @since 5.0.0
 */
Ext.define('Ext.Widget', {
    extend: 'Ext.Evented',
    xtype: 'widget',

    alternateClassName: 'Ext.Gadget',

    requires: [
        'Ext.dom.Element'
    ],

    mixins: [
        'Ext.mixin.Inheritable',
        'Ext.mixin.Bindable',
        'Ext.mixin.ComponentDelegation',
        'Ext.mixin.Pluggable'
    ],

    isWidget: true,

    /**
     * @property {Object} element
     * A configuration object for Ext.Element.create() that is used to create the Element
     * template.  Supports all the standard options of a Ext.Element.create() config and
     * adds 2 additional options:
     *
     * 1. `reference` - this option specifies a name for Element references.  These
     * references names become properties of the Widget instance and refer to Ext.Element
     * instances that were created using the template:
     *
     *     element: {
     *         reference: 'element',
     *         children: [{
     *             reference: 'innerElement'
     *         }]
     *     }
     *
     * After construction of a widget the reference elements are accessible as follows:
     *
     *     var foo = new FooWidget(),
     *         innerEl = foo.innerElement; // an Ext.Element that wraps the innerElement
     *
     * The reference attribute is optional, but all Widgets must have a `'element'`
     * reference on some element within the template (usually the outermost one).
     *
     * 2. `listeners` - a standard listeners object as specified by {@link Ext.mixin.Observable}.
     *
     *     element: {
     *         reference: 'element',
     *         listeners: {
     *             click: 'onClick'
     *         },
     *         children: [{
     *             reference: 'innerElement',
     *             listeners: {
     *                 click: 'onInnerClick'
     *             }
     *         }]
     *     }
     *
     * Since listeners cannot be attached without an Ext.Element reference the `reference`
     * property MUST be specified in order to use `listeners`.
     *
     * The Widget instance is used as the scope for all listeners specified in this way,
     * so it is invalid to use the `scope` option in the `listeners` config since it will
     * always be overwritten using `this`.
     * @protected
     */
    element: {
        reference: 'element'
    },

    observableType: 'component',

    cachedConfig: {
        /**
         * @cfg {String/Boolean} [baseCls=true]
         * The base CSS class to apply to this widget's element.
         * Used as the prefix for {@link #ui}-specific class names.
         * When set to `true` the {@link #classCls} will be used as the baseCls
         * @accessor
         * @protected
         */
        baseCls: true,

        /**
         * @cfg {String/String[]} cls The CSS class to add to this widget's element, in
         * addition to the {@link #baseCls}. In many cases, this property will be specified
         * by the derived widget class. See {@link #userCls} for adding additional CSS
         * classes to widget instances (such as items in a {@link Ext.Container}).
         * @accessor
         */
        cls: null,

        /**
         * @cfg {String/Object} style
         * Additional CSS styles that will be rendered into an inline style attribute when
         * the widget is rendered.
         *
         * You can pass either a string syntax:
         *
         *     style: 'background:red'
         *
         * Or by using an object:
         *
         *     style: {
         *         background: 'red'
         *     }
         *
         * When using the object syntax, you can define CSS Properties by using a string:
         *
         *     style: {
         *         'border-left': '1px solid red'
         *     }
         *
         * Although the object syntax is much easier to read, we suggest you to use the
         * string syntax for better performance.
         * @accessor
         */
        style: null,

        /**
         * @cfg {Boolean} border Enables or disables bordering on this component.
         * The following values are accepted:
         *
         * - `null` or `true (default): Do nothing and allow the border to be specified by the theme.
         * - `false`: suppress the default border provided by the theme.
         *
         * Please note that enabling bordering via this config will not add a `border-color`
         * or `border-style` CSS property to the component; you provide the `border-color`
         * and `border-style` via CSS rule or {@link #style} configuration
         * (if not already provide by the theme).
         *
         * ## Using {@link #style}:
         *
         *     Ext.Viewport.add({
         *         centered: true,
         *         width: 100,
         *         height: 100,
         *
         *         style: 'border: 1px solid blue;'
         *         // ...
         *     });
         *
         * ## Using CSS:
         *
         *     Ext.Viewport.add({
         *         centered: true,
         *         width: 100,
         *         height: 100,
         *
         *         cls: 'my-component'
         *         // ...
         *     });
         *
         * And your CSS file:
         *
         *     .my-component {
         *         border: 1px solid red;
         *     }
         *
         * @accessor
         */
        border: null,

        /**
         * @cfg {Object}
         *
         * Emulates the behavior of the CSS
         * {@link https://www.w3.org/TR/pointerevents/#the-touch-action-css-property touch-action}
         * property in a cross-browser compatible manner.
         *
         * Keys in this object are touch action names, and values are `false` to disable
         * a touch action or `true` to enable it.  Accepted keys are:
         *
         * - `panX`
         * - `panY`
         * - `pinchZoom`
         * - `doubleTapZoom`
         *
         * All touch actions are enabled (`true`) by default, so it is usually only necessary
         * to specify which touch actions to disable.  For example, the following disables
         * only horizontal scrolling and pinch-to-zoom on the component's main element:
         *
         *     touchAction: {
         *         panX: false,
         *         pinchZoom: false
         *     }
         *
         * Touch actions can be specified on reference elements using the reference element
         * name, for example:
         *
         *     // disables horizontal scrolling on the main element, and double-tap-zoom
         *     // on the child element named "body"
         *     touchAction: {
         *         panY: false
         *         body: {
         *             doubleTapZoom: false
         *         }
         *     }
         *
         * The primary motivation for setting the touch-action of an element is to prevent
         * the browser's default handling of a gesture such as pinch-to-zoom, or
         * drag-to-scroll, so that the application can implement its own handling of that
         * gesture on the element.  Suppose, for example, a component has a custom drag
         * handler on its element and wishes to prevent horizontal scrolling of its container
         * while it is being dragged:
         *
         *     Ext.create('Ext.Widget', {
         *         touchAction: {
         *             panX: false
         *         },
         *         listeners: {
         *             drag: function(e) {
         *                 // implement drag logic
         *             }
         *         }
         *     });
         */
        touchAction: null
    },

    config: {
        /**
         * @cfg {String/String[]} ui The ui or uis to be used on this Component
         *
         * When a ui is configured, CSS class names are added to the {@link #element}, created
         * by appending the ui name(s) to each {@link #classCls} and/or {@link #baseCls}.
         */
        ui: null,

        /**
         * @cfg {String/String[]} userCls
         * One or more CSS classes to add to the component's primary element. This config
         * is intended solely for use by the component instantiator (the "user"), not by
         * derived classes.
         *
         * For example:
         *
         *      items: [{
         *          xtype: 'button',
         *          userCls: 'my-button'
         *      ...
         *      }]
         */
        userCls: null
    },

    eventedConfig: {
        /**
         * @cfg {Number/String} width
         * The width of this Component; must be a valid CSS length value, e.g: `300`, `100px`, `30%`, etc.
         * By default, if this is not explicitly set, this Component's element will simply have its own natural size.
         * If set to `auto`, it will set the width to `null` meaning it will have its own natural size.
         * @accessor
         * @evented
         */
        width: null,

        /**
         * @cfg {Number/String} height
         * The height of this Component; must be a valid CSS length value, e.g: `300`, `100px`, `30%`, etc.
         * By default, if this is not explicitly set, this Component's element will simply have its own natural size.
         * If set to `auto`, it will set the width to `null` meaning it will have its own natural size.
         * @accessor
         * @evented
         */
        height: null,

        /**
         * @cfg {Boolean} [hidden]
         * Whether or not this Component is hidden (its CSS `display` property is set to `none`).
         *
         * Defaults to `true` for {@link #floated} Components.
         * @accessor
         * @evented
         */
        hidden: null
    },

    /**
     * @property {Array} template
     * An array of child elements to use as the children of the main element in the {@link
        * #element} template.  Only used if "children" are not specified explicitly in the
     * {@link #element} template.
     * @protected
     */
    template: [],

    /**
     * A CSS class to apply to the main element that will be inherited down the class
     * hierarchy.  Subclasses may override this property on their prototype to add their
     * own CSS class in addition to the CSS classes inherited from ancestor classes via
     * the prototype chain.  For example
     *
     *     Ext.define('Foo', {
     *         extend: 'Ext.Widget',
     *         classCls: 'foo'
     *     });
     *
     *     Ext.define('Bar', {
     *         extend: 'Foo',
     *         classCls: 'bar'
     *     });
     *
     *     var bar = new Bar();
     *
     *     console.log(bar.element.className); // outputs 'foo bar'
     *
     * @protected
     * @property
     */
    classCls: null,

    /**
     * When set to `true` during widget class definition, that class will be the "root" for
     * {@link #classCls} inheritance. Derived classes may set this to `true` to avoid
     * inheriting a {@link #classCls} from their superclass.
     * @property
     * @protected
     */
    classClsRoot: true,

    clearPropertiesOnDestroy: 'async',

    /**
     * @property {String} [noBorderCls] The CSS class to add to this component should not have a border.
     * @private
     * @readonly
     */
    noBorderCls: Ext.baseCSSPrefix + 'noborder-trbl',

    constructor: function(config) {
        var me = this,
            controller;

        me.initId(config);
        me.initElement();
        me.mixins.observable.constructor.call(me, config);
        Ext.ComponentManager.register(me);

        controller = me.getController();
        if (controller) {
            controller.init(me);
        }
    },

    afterCachedConfig: function() {
        // This method runs once for the first instance of this Widget type that is
        // created.  It runs after the element config has been processed for the first
        // instance, and after all the cachedConfigs (whose appliers/updaters may modify
        // the element) have been initialized.  At this point we are ready to take the
        // DOM that was generated for the first Element instance, clone it, and cache it
        // on the prototype, so that it can be cloned by future instance to create their
        // elements (see initElement).
        var me = this,
            prototype = me.self.prototype,
            referenceList = me.referenceList,
            renderElement = me.renderElement,
            renderTemplate, element, i, ln, reference, elements;

        // This is where we take the first instance's DOM and clone it as the template
        // for future instances
        prototype.renderTemplate = renderTemplate = document.createDocumentFragment();
        renderTemplate.appendChild(renderElement.clone(true, true));

        elements = renderTemplate.querySelectorAll('[id]');

        for (i = 0, ln = elements.length; i < ln; i++) {
            element = elements[i];
            element.removeAttribute('id');
        }

        // initElement skips removal of reference attributes for the first instance so that
        // the reference attributes will be present in the cached element when it is cloned.
        // Now that we're done cloning and caching the template element, it is safe to
        // remove the reference attributes from this instance's elements
        for (i = 0, ln = referenceList.length; i < ln; i++) {
            reference = referenceList[i];
            me[reference].dom.removeAttribute('reference');
        }
    },

    addCls: function(cls) {
        this.el.addCls(cls);
    },

    applyBaseCls: function(baseCls) {
        var prefix = Ext.baseCSSPrefix,
            xtype = this.xtype;

        if (baseCls === true) {
            baseCls = this.classCls || (prefix + xtype);
        } else if (!baseCls) {
            baseCls = prefix + xtype;
        }

        return baseCls;
    },

    applyCls: function(cls) {
        if (typeof cls == "string") {
            cls = [cls];
        }

        //reset it back to null if there is nothing.
        if (!cls || !cls.length) {
            cls = null;
        }

        return cls;
    },

    applyHidden: function(hidden) {
        return !!hidden;
    },

    applyTouchAction: function(touchAction, oldTouchAction) {
        if (oldTouchAction != null) {
            touchAction = Ext.merge({}, oldTouchAction, touchAction);
        }

        return touchAction;
    },

    applyWidth: function(width) {
        return this.filterLengthValue(width);
    },

    applyHeight: function(height) {
        return this.filterLengthValue(height);
    },

    updateBorder: function(border) {
        // If the border is null it means we should not suppress the border
        border = border || border === null;
        this.el.toggleCls(this.noBorderCls, !border);
    },

    clearListeners: function() {
        var me = this;
        me.mixins.observable.clearListeners.call(me);
        me.mixins.componentDelegation.clearDelegatedListeners.call(me);
    },

    /**
     * Destroys the Widget. This method should not be overridden in custom Widgets,
     * because it sets the flags and does final cleanup that must go last. Instead,
     * override {@link #doDestroy} method to add functionality at destruction time.
     */
    destroy: function() {
        var me = this;

        // isDestroying added for compat reasons
        me.isDestroying = me.destroying = true;

        me.doDestroy();

        // We need to defer clearing listeners until after doDestroy() completes,
        // to let the interested parties fire events until the very end.
        me.clearListeners();

        me.isDestroying = me.destroying = false;

        // ComponentDelegation mixin does not install "after" interceptor on the
        // base class destructor so we need to call it explicitly.
        me.mixins.componentDelegation.destroyComponentDelegation.call(me);

        me.callParent();
    },

    /**
     * Perform the actual destruction sequence. This is the method to override in your
     * subclasses to add steps specific to the destruction of custom Component or Widget.
     *
     * As a rule of thumb, subclasses should destroy their child Components, Elements,
     * and/or other objects before calling parent method. Any object references will be
     * nulled after this method has finished, to prevent the possibility of memory leaks.
     *
     * @since 6.2.0
     */
    doDestroy: function() {
        var me = this,
            referenceList = me.referenceList,
            i, ln, reference;

        // Destroy all element references
        for (i = 0, ln = referenceList.length; i < ln; i++) {
            reference = referenceList[i];
            if (me.hasOwnProperty(reference)) {
                me[reference].destroy();
                me[reference] = null;
            }
        }

        me.destroyBindable();

        Ext.ComponentManager.unregister(me);
    },

    doFireEvent: function(eventName, args, bubbles) {
        var me = this,
            ret = me.mixins.observable.doFireEvent.call(me, eventName, args, bubbles);

        if (ret !== false) {
            ret = me.mixins.componentDelegation.doFireDelegatedEvent.call(me, eventName, args);
        }

        return ret;
    },

    getBubbleTarget: function () {
        return this.getRefOwner();
    },

    /**
     * A template method for modifying the {@link #element} config before it is processed.
     * By default adds the result of `this.getTemplate()` as the `children` array of
     * {@link #element} if `children` were not specified in the original
     * {@link #element} config.  Typically this method should not need to be implemented
     * in subclasses.  Instead the {@link #element} property should be use to configure
     * the element template for a given Widget subclass.
     *
     * This method is called once when the first instance of each Widget subclass is
     * created.  The element config object that is returned is cached and used as the template
     * for all successive instances.  The scope object for this method is the class prototype,
     * not the instance.
     *
     * @return {Object} the element config object
     * @protected
     */
    getElementConfig: function() {
        var me = this,
            el = me.element;

        if (!('children' in el)) {
            el = Ext.apply({
                children: me.getTemplate()
            }, el);
        }

        return el;
    },

    /**
     * Returns the height and width of the Component.
     * @return {Object} The current `height` and `width` of the Component.
     * @return {Number} return.width
     * @return {Number} return.height
     */
    getSize: function() {
        return {
            width: this.getWidth(),
            height: this.getHeight()
        };
    },

    getTemplate: function() {
        return this.template;
    },

    /**
     * @private
     */
    getClassCls: function() {
        var proto = this.self.prototype,
            prototype = proto,
            classes, classCls, i, ln;

        while (prototype) {
            classCls = prototype.classCls;

            if (classCls) {
                if (classCls instanceof Array) {
                    for (i = 0, ln = classCls.length; i < ln; i++) {
                        (classes || (classes = [])).push(classCls[i]);
                    }
                } else {
                    (classes || (classes = [])).push(classCls);
                }
            }

            if (prototype.classClsRoot && prototype.hasOwnProperty('classClsRoot')) {
                break;
            }

            prototype = prototype.superclass;
        }

        if (classes) {
            proto.classClsList = classes;
        }

        return classes;
    },

    hide: function() {
        this.setHidden(true);
    },

    /**
     * Initializes the Element for this Widget instance.  If this is the first time a
     * Widget of this type has been instantiated the {@link #element} config will be
     * processed to create an Element.  This Element is then cached on the prototype (see
     * afterCachedConfig) so that future instances can obtain their element by simply
     * cloning the Element that was cached by the first instance.
     * @protected
     */
    initElement: function() {
        var me = this,
            prototype = me.self.prototype,
            id = me.getId(),
            // The double assignment is intentional to workaround a JIT issue that prevents
            // me.referenceList from being assigned in random scenarios. The issue occurs on 4th gen 
            // iPads and lower, possibly other older iOS devices. See EXTJS-16494.
            referenceList = me.referenceList = me.referenceList = [],
            cleanAttributes = true,
            isFirstInstance = !prototype.hasOwnProperty('renderTemplate'),
            renderTemplate, renderElement, element, referenceNodes, i, ln, referenceNode,
            reference, classCls;

        if (isFirstInstance) {
            // this is the first instantiation of this widget type.  Process the element
            // config from scratch to create our Element.
            cleanAttributes = false;
            renderTemplate = document.createDocumentFragment();
            renderElement = Ext.Element.create(me.processElementConfig.call(prototype), true);
            renderTemplate.appendChild(renderElement);
        } else {
            // we have already created an instance of this Widget type, so the element
            // config has already been processed, and the resulting DOM has been cached on
            // the prototype (see afterCachedConfig).  This means we can obtain our element
            // by simply cloning the cached element.
            renderTemplate = me.renderTemplate.cloneNode(true);
            renderElement = renderTemplate.firstChild;
        }

        referenceNodes = renderTemplate.querySelectorAll('[reference]');

        for (i = 0, ln = referenceNodes.length; i < ln; i++) {
            referenceNode = referenceNodes[i];
            reference = referenceNode.getAttribute('reference');

            if (cleanAttributes) {
                // on first instantiation we do not clean the reference attributes here.
                // This is because this instance's element will be used as the template
                // for future instances, and we need the reference attributes to be
                // present in the template so that future instances can resolve their
                // references.  afterCachedConfig is responsible for removing the
                // reference attributes from the DOM for the first instance after the
                // Element has been cloned and cached as the template.
                referenceNode.removeAttribute('reference');
            }

            if (reference === 'element') {
                //<debug>
                if (element) {
                    // already resolved a reference named element - can't have two
                    Ext.raise("Duplicate 'element' reference detected in '" +
                        me.$className + "' template.");
                }
                //</debug>
                referenceNode.id = id;
                // element reference needs to be established ASAP, so add the reference
                // immediately, not "on-demand"
                element = me.el = me.addElementReference(reference, referenceNode);

                // Poke our id in our magic attribute to enable Component#fromElement
                element.dom.setAttribute('data-componentid', id);

                if (isFirstInstance) {
                    classCls = me.getClassCls();
                    if (classCls) {
                        element.addCls(classCls);
                    }
                }
            } else {
                me.addElementReferenceOnDemand(reference, referenceNode);
            }

            referenceList.push(reference);
        }

        //<debug>
        if (!element) {
            Ext.raise("No 'element' reference found in '" + me.$className +
                "' template.");
        }
        //</debug>

        if (renderElement === element.dom) {
            me.renderElement = element;
        }
        else {
            me.addElementReferenceOnDemand('renderElement', renderElement);
        }
    },

    /**
     * Tests whether this Widget matches a {@link Ext.ComponentQuery ComponentQuery}
     * selector string.
     * @param {String} selector The selector string to test against.
     * @return {Boolean} `true` if this Widget matches the selector.
     */
    is: function(selector) {
        return Ext.ComponentQuery.is(this, selector);
    },

    /**
     * Returns `true` if this Component is currently hidden.
     * @param {Boolean/Ext.Widget} [deep=false] `true` to check if this component
     * is hidden because a parent container is hidden. Alternatively, a reference to the
     * top-most parent at which to stop climbing.
     * @return {Boolean} `true` if currently hidden.
     */
    isHidden: function(deep) {
        var hidden = !!this.getHidden(),
            owner;

        if (!hidden && deep) {
            owner = this.getRefOwner();
            while (owner && owner !== deep) {
                hidden = !!owner.getHidden();
                if (hidden) {
                    break;
                }
                owner = owner.getRefOwner();
            }
        }
        return hidden;
    },

    /**
     * Returns `true` if this Component is currently visible.
     * @param {Boolean} [deep=false] `true` to check if this component
     * is visible and all parents are also visible.
     * @return {Boolean} `true` if currently visible.
     */
    isVisible: function(deep) {
        return !this.isHidden(deep);
    },

    /**
     * Tests whether or not this Component is of a specific xtype. This can test whether this Component is descended
     * from the xtype (default) or whether it is directly of the xtype specified (`shallow = true`).
     * **If using your own subclasses, be aware that a Component must register its own xtype
     * to participate in determination of inherited xtypes.__
     *
     * For a list of all available xtypes, see the {@link Ext.Component} header.
     *
     * Example usage:
     *
     *     var t = new Ext.field.Text();
     *     var isText = t.isXType('textfield'); // true
     *     var isBoxSubclass = t.isXType('field'); // true, descended from Ext.field.Field
     *     var isBoxInstance = t.isXType('field', true); // false, not a direct Ext.field.Field instance
     *
     * @param {String} xtype The xtype to check for this Component.
     * @param {Boolean} shallow (optional) `false` to check whether this Component is descended from the xtype (this is
     * the default), or `true` to check whether this Component is directly of the specified xtype.
     * @return {Boolean} `true` if this component descends from the specified xtype, `false` otherwise.
     */
    isXType: function(xtype, shallow) {
        return shallow ? (Ext.Array.indexOf(this.xtypes, xtype) !== -1) :
            !!this.xtypesMap[xtype];
    },

    /**
     * Gets a named template instance for this class. See {@link Ext.XTemplate#getTpl}.
     * @param {String} name The name of the property that holds the template.
     * @return {Ext.XTemplate} The template, `null` if not found.
     *
     * @since 6.2.0
     */
    lookupTpl: function(name) {
        return Ext.XTemplate.getTpl(this, name);
    },

    removeCls: function(cls) {
        this.el.removeCls(cls);
    },

    /**
     * Toggles the specified CSS class on this element (removes it if it already exists,
     * otherwise adds it).
     * @param {String} className The CSS class to toggle.
     * @param {Boolean} [state] If specified as `true`, causes the class to be added. If
     * specified as `false`, causes the class to be removed.
     */
    toggleCls: function(cls, state) {
        this.element.toggleCls(cls, state);
    },

    resolveListenerScope: function(defaultScope, skipThis) {
        // break the tie between Observable and Inheritable resolveListenerScope
        return this.mixins.inheritable.resolveListenerScope.call(this, defaultScope, skipThis);
    },

    /**
     * Sets the size of the Component.
     * @param {Number} width The new width for the Component.
     * @param {Number} height The new height for the Component.
     */
    setSize: function(width, height) {
        // Allow setSize to be called with a result from getSize.
        if (width && typeof width === 'object') {
            return this.setSize(width.width, width.height);
        }
        if (width !== undefined) {
            this.setWidth(width);
        }
        if (height !== undefined) {
            this.setHeight(height);
        }
    },

    show: function() {
        this.setHidden(false);
    },

    updateBaseCls: function(newBaseCls, oldBaseCls) {
        var me = this,
            element = me.element;

        if (oldBaseCls) {
            element.removeCls(oldBaseCls);
        }

        if (newBaseCls) {
            element.addCls(newBaseCls);
        }

        if (!me.isConfiguring) {
            me.syncUiCls();
        }
    },

    /**
     * @private
     * All cls methods directly report to the {@link #cls} configuration, so anytime it changes, {@link #updateCls} will be called
     */
    updateCls: function (newCls, oldCls) {
        this.element.replaceCls(oldCls, newCls);
    },

    updateHidden: function(hidden) {
        var element = this.renderElement;

        if (element && !element.destroyed) {
            if (hidden) {
                element.hide();
            } else {
                element.show();
            }
        }
    },

    /**
     * @protected
     */
    applyStyle: function(style, oldStyle) {
        // If we're doing something with data binding, say:
        // style: {
        //     backgroundColor: 'rgba({r}, {g}, {b}, 1)'
        // }
        // The inner values will change, but the object won't, so force
        // a copy to be created here if necessary
        if (oldStyle && style === oldStyle && Ext.isObject(oldStyle)) {
            style = Ext.apply({}, style);
        }
        return style;
    },

    /**
     * @protected
     */
    updateStyle: function(style) {
        this.element.applyStyles(style);
    },

    updateTouchAction: function(touchAction) {
        var name, childEl, value, hasRootActions;

        for (name in touchAction) {
            childEl = this[name];
            value = touchAction[name];

            if (childEl && childEl.isElement) {
                childEl.setTouchAction(value);
            } else {
                hasRootActions = true;
            }
        }

        if (hasRootActions) {
            this.el.setTouchAction(touchAction);
        }
    },

    updateUi: function() {
        this.syncUiCls();
    },

    /**
     * @param width
     * @protected
     */
    updateWidth: function(width) {
        this.element.setWidth(width);
    },

    /**
     * @param height
     * @protected
     */
    updateHeight: function(height) {
        this.element.setHeight(height);
    },

    /**
     * Walks up the ownership hierarchy looking for an ancestor Component which matches
     * the passed simple selector.
     *
     * Example:
     *
     *     var owningTabPanel = grid.up('tabpanel');
     *
     * @param {String} selector (optional) The simple selector to test.
     * @param {String/Number/Ext.Component} [limit] This may be a selector upon which to stop the upward scan, or a limit of the number of steps, or Component reference to stop on.
     * @return {Ext.Container} The matching ancestor Container (or `undefined` if no match was found).
     */
    up: function(selector, limit) {
        var result = this.getRefOwner(),
            limitSelector = typeof limit === 'string',
            limitCount = typeof limit === 'number',
            limitComponent = limit && limit.isComponent,
            steps = 0;

        if (selector) {
            for (; result; result = result.getRefOwner()) {
                steps++;
                if (selector.isComponent || selector.isWidget) {
                    if (result === selector) {
                        return result;
                    }
                } else {
                    if (Ext.ComponentQuery.is(result, selector)) {
                        return result;
                    }
                }

                // Stop when we hit the limit selector
                if (limitSelector && result.is(limit)) {
                    return;
                }
                if (limitCount && steps === limit) {
                    return;
                }
                if (limitComponent && result === limit) {
                    return;
                }
            }
        }
        return result;
    },

    updateLayout: Ext.emptyFn, // empty fn for modern/classic compat

    // Temporary workarounds to keep Ext.ComponentManager from throwing errors when dealing
    // Widgets.  TODO: remove these emptyFns when proper focus handling is implmented
    onFocusEnter: Ext.emptyFn,
    onFocusLeave: Ext.emptyFn,
    isAncestor: function() {
        return false;
    },

    //-------------------------------------------------------------------------

    privates: {
        /**
         * Reduces instantiation time for a Widget by lazily instantiating Ext.Element
         * references the first time they are used.  This optimization only works for elements
         * with no listeners specified.
         *
         * @param {String} name The name of the reference
         * @param {HTMLElement} domNode
         * @private
         */
        addElementReferenceOnDemand: function(name, domNode) {
            if (this._elementListeners[name]) {
                // if the element was configured with listeners then we cannot add the
                // reference on demand because we need to make sure the element responds
                // immediately to any events, even if its reference is never accessed
                this.addElementReference(name, domNode);
            } else {
                // no listeners - element reference can be resolved on demand.
                // TODO: measure if this has any significant performance impact.
                Ext.Object.defineProperty(this, name, {
                    get: function() {
                        // remove the property that was defined using defineProperty because
                        // addElementReference will set the property on the instance, - the
                        // getter is not needed after the first access.
                        delete this[name];
                        return this.addElementReference(name, domNode);
                    },
                    configurable: true
                });
            }
        },

        /**
         * Adds an element reference to this Widget instance.
         * @param {String} name The name of the reference
         * @param {HTMLElement} domNode
         * @return {Ext.dom.Element}
         * @private
         */
        addElementReference: function(name, domNode) {
            var me = this,
                referenceEl = me[name] = Ext.get(domNode),
                listeners = me._elementListeners[name],
                eventName, listener;

            referenceEl.skipGarbageCollection = true;
            referenceEl.component = me;

            if (listeners) {
                // TODO: These references will be needed when we use delegation to listen
                // for element events, but for now, we'll just attach the listeners directly
                // referenceEl.reference = name;
                // referenceEl.component = me;
                // referenceEl.listeners = listeners;

                // At this point "listeners" exists on the class prototype.  We need to clone
                // it before poking the scope reference onto it, because it is used as the
                // options object by Observable and so can't be safely shared.
                //
                listeners = Ext.clone(listeners);

                // If the listener is specified as an object it needs to have the scope
                // option added to that object, for example:
                //
                //    {
                //        click: {
                //            fn: 'onClick',
                //            scope: this
                //        }
                //    }
                //
                for (eventName in listeners) {
                    listener = listeners[eventName];
                    if (typeof listener === 'object') {
                        listener.scope = me;
                    }
                }

                // The outermost listeners object always needs the scope option. This covers
                // a listeners object with the following shape:
                //
                //    {
                //        click: 'onClick'
                //        scope: this
                //    }
                //
                listeners.scope = me; // do this *after* the above loop over listeners

                // Hopefully in the future we can stop calling on() here, and just use
                // event delegation to dispatch events to Widgets that have declared their
                // listeners in their template.
                //
                referenceEl.on(listeners);
            }

            return referenceEl;
        },

        detachFromBody: function() {
            // See reattachToBody
            Ext.getDetachedBody().appendChild(this.element);
            this.isDetached = true;
        },

        /**
         * @private
         */
        doAddListener: function(name, fn, scope, options, order, caller, manager) {
            var me = this,
                elementName = options && options.element,
                delegate = options && options.delegate,
                listeners, eventOptions, option;

            if (elementName) {
                //<debug>
                if (Ext.Array.indexOf(me.referenceList, elementName) === -1) {
                    Ext.Logger.error("Adding event listener with an invalid element reference of '" + elementName +
                        "' for this component. Available values are: '" + me.referenceList.join("', '") + "'", me);
                }
                //</debug>

                listeners = {};
                listeners[name] = fn;
                if (scope) {
                    listeners.scope = scope;
                }

                eventOptions = Ext.Element.prototype.$eventOptions;
                for (option in options) {
                    if (eventOptions[option]) {
                        listeners[option] = options[option];
                    }
                }

                me.mon(me[elementName], listeners);
                return;
            } else if (delegate) {
                me.mixins.componentDelegation.addDelegatedListener.call(me, name, fn, scope, options, order, caller, manager);
                return;
            }

            me.callParent([name, fn, scope, options, order, caller, manager]);
        },

        doRemoveListener: function(eventName, fn, scope) {
            var me = this;
            me.mixins.observable.doRemoveListener.call(me, eventName, fn, scope);
            me.mixins.componentDelegation.removeDelegatedListener.call(me, eventName, fn, scope);
        },

        filterLengthValue: function(value) {
            if (value === 'auto' || (!value && value !== 0)) {
                return null;
            }

            return value;
        },

        getFocusEl: function() {
            return this.element;
        },

        /**
         * Called for the first instance of this Widget to create an object that contains the
         * listener configs for all of the element references keyed by reference name. The
         * object is cached on the prototype and has the following shape:
         *
         *     _elementListeners: {
         *         element: {
         *             click: 'onClick',
         *             scope: this
         *         },
         *         fooReference: {
         *             tap: {
         *                 fn: someFunction,
         *                 delay: 100
         *             }
         *         }
         *     }
         *
         * The returned object is prototype chained to the _elementListeners object of its
         * superclass, and each key in the object is prototype chained to object with the
         * corresponding key in the superclass _elementListeners.  This allows element
         * listeners to be inherited and overridden when subclassing widgets.
         *
         * This method is invoked with the prototype object as the scope
         *
         * @private
         */
        initElementListeners: function(elementConfig) {
            var prototype = this,
                superPrototype = prototype.self.superclass,
                superElementListeners = superPrototype._elementListeners,
                reference = elementConfig.reference,
                children = elementConfig.children,
                elementListeners, listeners, superListeners, ln, i;

            if (prototype.hasOwnProperty('_elementListeners')) {
                elementListeners = prototype._elementListeners;
            } else {
                elementListeners = prototype._elementListeners =
                    (superElementListeners ? Ext.Object.chain(superElementListeners) : {});
            }

            if (reference) {
                listeners = elementConfig.listeners;
                if (listeners) {
                    if (superElementListeners) {
                        superListeners = superElementListeners[reference];
                        if (superListeners) {
                            listeners = Ext.Object.chain(superListeners);
                            Ext.apply(listeners, elementConfig.listeners);
                        }
                    }

                    elementListeners[reference] = listeners;
                    // null out the listeners on the elementConfig, since we are going to pass
                    // it to Element.create(), and don't want "listeners" to be treated as an
                    // attribute
                    elementConfig.listeners = null;
                }
            }

            if (children) {
                for (i = 0, ln = children.length; i < ln; i++) {
                    prototype.initElementListeners(children[i]);
                }
            }
        },

        initId: function(config) {
            var me = this,
                defaultConfig = me.config,
                id = (config && config.id) || (defaultConfig && defaultConfig.id);

            if (id) {
                // setId() will normally be inherited from Identifiable, unless "id" is a
                // proper config, in which case it will be generated by the config system.
                me.setId(id);
                me.id = id;
            } else {
                // if no id configured, generate one (Identifiable)
                me.getId();
            }
        },

        /**
         * Recursively processes the element templates for this class and its superclasses,
         * ascending the hierarchy until it reaches a superclass whose element template
         * has already been processed.  This method is invoked using the prototype as the scope.
         *
         * @private
         * @return {Object}
         */
        processElementConfig: function() {
            var prototype = this,
                superPrototype = prototype.self.superclass,
                elementConfig;

            if (prototype.hasOwnProperty('_elementConfig')) {
                elementConfig = prototype._elementConfig;
            } else {
                // cache the elementConfig on the prototype, since we may end up here multiple
                // times if there are multiple subclasses
                elementConfig = prototype._elementConfig = prototype.getElementConfig();

                if (superPrototype.isWidget) {
                    // Before initializing element listeners we must process the element template
                    // for our superclass so that we can chain our listeners to the superclass listeners
                    prototype.processElementConfig.call(superPrototype);
                }

                // initElementListeners needs to be called BEFORE passing the element config
                // along to Ext.Element.create().  This ensures that the listener meta data is
                // saved, and then the listeners objects are removed from the element config
                // so that they do not get added as attributes by create()
                prototype.initElementListeners(elementConfig);
            }

            return elementConfig;
        },

        reattachToBody: function() {
            // See detachFromBody
            this.isDetached = false;
        },

        addUi: function(ui) {
            var me = this,
                currentUI = me.getUi(),
                i, singleUI, len;

            if (ui) {
                ui = ui.split(' ');
                len = ui.length;

                currentUI = (currentUI && currentUI.split(' ')) || [];

                for (i = 0; i < len; i++) {
                    singleUI = ui[i];
                    if (currentUI.indexOf(singleUI) === -1) {
                        currentUI.push(singleUI);
                    }
                }

                me.setUi(currentUI.join(' '));
            }
        },

        removeUi: function(ui) {
            var me = this,
                currentUI = me.getUi(),
                i, singleUI, index, len;

            if (ui) {
                ui = ui.split(' ');
                len = ui.length;

                currentUI = (currentUI && currentUI.split(' ')) || [];

                for (i = 0; i < len; i++) {
                    singleUI = ui[i];
                    index = currentUI.indexOf(singleUI);
                    if (index !== -1) {
                        currentUI.splice(index, 1);
                    }
                }

                me.setUi(currentUI.join(' '));
            }
        },

        syncUiCls: function() {
            var me = this,
                ui = me.getUi(),
                currentUiCls = me.currentUiCls,
                element = me.element,
                baseCls = me.getBaseCls(),
                classClsList = me.classClsList,
                uiCls = [],
                uiSuffix, i, ln, j, jln;

            if (currentUiCls) {
                element.removeCls(currentUiCls);
            }

            if (ui) {
                ui = ui.split(' ');

                for (i = 0, ln = ui.length; i < ln; i++) {
                    uiSuffix = '-' + ui[i];

                    if (baseCls && (baseCls !== me.classCls)) {
                        uiCls.push(baseCls + uiSuffix);
                    }

                    if (classClsList) {
                        for (j = 0, jln = classClsList.length; j < jln; j++) {
                            uiCls.push(classClsList[j] + uiSuffix);
                        }
                    }
                }

                element.addCls(uiCls);

                me.currentUiCls = uiCls;
            }
        },

        updateUserCls: function(newCls, oldCls) {
            this.element.replaceCls(oldCls, newCls);
        }
    }
}, function(Widget) {
    var prototype = Widget.prototype;

    // event options for listeners that use the "element" event options must also include
    // event options from Ext.Element
    (prototype.$elementEventOptions =
        Ext.Object.chain(Ext.Element.prototype.$eventOptions)).element = 1;

    (prototype.$eventOptions = Ext.Object.chain(prototype.$eventOptions)).delegate = 1;
});
