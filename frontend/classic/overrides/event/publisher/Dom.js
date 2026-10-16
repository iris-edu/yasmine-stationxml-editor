/* ****************************************************************************
 * 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
 * Override: Dom event publisher
 *
 * 1. Use passive: false for wheel events - fixes Chrome "[Intervention] Unable
 *    to preventDefault inside passive event listener" when ExtJS calls
 *    stopEvent/preventDefault on mousewheel.
 *
 * 2. Use pagehide instead of unload - the unload event is deprecated and will
 *    be removed. pagehide is the recommended replacement. Only destroy when
 *    persisted is false (page is actually being unloaded, not cached in bfcache).
 * ****************************************************************************/
Ext.define('overrides.event.publisher.Dom', {
    override: 'Ext.event.publisher.Dom',

    // Events that need passive: false for preventDefault to work (Chrome)
    passiveFalseEvents: {
        wheel: 1,
        mousewheel: 1,
        DOMMouseScroll: 1
    },

    // Use pagehide instead of deprecated unload (same semantics when !e.persisted)
    unloadToPagehide: {
        unload: 1
    },

    addDelegatedListener: function(eventName) {
        var me = this,
            target = me.target,
            capture = !!me.captureEvents[eventName],
            options;

        me.delegatedListeners[eventName] = 1;

        if (me.passiveFalseEvents[eventName]) {
            options = { capture: capture, passive: false };
            target.addEventListener(eventName, me.onDelegatedEvent, options);
        } else {
            target.addEventListener(eventName, me.onDelegatedEvent, capture);
        }
    },

    removeDelegatedListener: function(eventName) {
        var me = this,
            target = me.target,
            capture = !!me.captureEvents[eventName],
            options;

        delete me.delegatedListeners[eventName];

        if (me.passiveFalseEvents[eventName]) {
            options = { capture: capture, passive: false };
            target.removeEventListener(eventName, me.onDelegatedEvent, options);
        } else {
            target.removeEventListener(eventName, me.onDelegatedEvent, capture);
        }
    },

    addDirectListener: function(eventName, element, capture) {
        var me = this,
            dom = element.dom,
            handler = capture ? me.onDirectCaptureEvent : me.onDirectEvent,
            options, wrapper, key;

        if (me.unloadToPagehide[eventName] && !(Ext.os && Ext.os.is && Ext.os.is.iOS)) {
            wrapper = function(e) {
                if (!e.persisted) {
                    handler.call(me, e);
                }
            };
            key = (element.id || dom.id || (dom === window ? 'win' : 'el')) + '-' + eventName + '-' + capture;
            me._pagehideWrappers = me._pagehideWrappers || {};
            me._pagehideWrappers[key] = wrapper;
            dom.addEventListener('pagehide', wrapper, capture);
        } else if (me.passiveFalseEvents[eventName]) {
            options = { capture: capture, passive: false };
            dom.addEventListener(eventName, handler, options);
        } else {
            dom.addEventListener(eventName, handler, capture);
        }
    },

    removeDirectListener: function(eventName, element, capture) {
        var me = this,
            dom = element.dom,
            handler = capture ? me.onDirectCaptureEvent : me.onDirectEvent,
            options, wrapper, key;

        if (me.unloadToPagehide[eventName] && !(Ext.os && Ext.os.is && Ext.os.is.iOS)) {
            key = (element.id || dom.id || (dom === window ? 'win' : 'el')) + '-' + eventName + '-' + capture;
            wrapper = me._pagehideWrappers && me._pagehideWrappers[key];
            if (wrapper) {
                dom.removeEventListener('pagehide', wrapper, capture);
                delete me._pagehideWrappers[key];
            }
        } else if (me.passiveFalseEvents[eventName]) {
            options = { capture: capture, passive: false };
            dom.removeEventListener(eventName, handler, options);
        } else {
            dom.removeEventListener(eventName, handler, capture);
        }
    },

    onReady: function() {
        var me = this,
            domEvents = me.handledDomEvents,
            ln, i;

        if (domEvents) {
            for (i = 0, ln = domEvents.length; i < ln; i++) {
                me.addDelegatedListener(domEvents[i]);
            }
        }

        // Chrome/Firefox: pagehide replaces deprecated unload (skip bfcache).
        // iOS Safari fires pagehide during history.replaceState / hash updates
        // on first load; destroying the publisher then leaves a blank screen.
        if (Ext.os && Ext.os.is && Ext.os.is.iOS) {
            window.addEventListener('unload', function() {
                me.destroy();
            });
        } else {
            window.addEventListener('pagehide', function(e) {
                if (!e.persisted) {
                    me.destroy();
                }
            });
        }
    }
});
