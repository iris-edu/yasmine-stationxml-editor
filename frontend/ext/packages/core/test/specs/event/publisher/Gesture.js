describe("Ext.event.publisher.Gesture", function() {
    var helper = Ext.testHelper,
        targetEl;

    beforeEach(function() {
        targetEl = Ext.getBody().createChild({
            id: 'target'
        });
    });

    afterEach(function() {
        if (targetEl) {
            targetEl.destroy();
            targetEl = null;
        }
    });

    describe("removing the target el before a gesture is complete", function() {
        var GC = Ext.dom.GarbageCollector,
            interval = GC.interval;

        beforeEach(function() {
            spyOn(targetEl, 'clearListeners');
            GC.interval = 60;
            GC.pause();
            GC.resume();
        });

        afterEach(function() {
            GC.interval = interval;
            GC.pause();
            GC.resume();
        });

        function removeTarget() {
            document.body.removeChild(targetEl.dom);
        }

        function expectCollected(collected) {
            if (collected) {
                expect('target' in Ext.cache).toBe(false);
                expect(targetEl.clearListeners).toHaveBeenCalled();
            } else {
                expect('target' in Ext.cache).toBe(true);
                expect(targetEl.clearListeners).not.toHaveBeenCalled();
            }
        }

        (Ext.toolkit === 'classic' ? it : xit)("should not garbage collect the target element until the current gesture is complete", function() {
            runs(function() {
                helper.touchStart(targetEl, { id: 1, x: 10, y: 10 });
                helper.touchMove(targetEl, { id: 1, x: 15, y: 15 });
                removeTarget();
            });

            waits(90);

            runs(function() {
                expectCollected(false);
                helper.touchEnd(Ext.supports.TouchEvents ? targetEl : document.body, { id: 1, x: 15, y: 15 });
            });

            waits(90);

            runs(function() {
                expectCollected(true);
            })
        });
    });

    describe("order of recognizers", function() {
        it("should invoke the recognizers in priority order when an event is fired", function() {
            var gesture = Ext.event.gesture,
                Drag = gesture.Drag.instance,
                Tap = gesture.Tap.instance,
                DoubleTap = gesture.DoubleTap.instance,
                LongPress = gesture.LongPress.instance,
                EdgeSwipe = gesture.EdgeSwipe.instance,
                Swipe = gesture.Swipe.instance,
                Pinch = gesture.Pinch.instance,
                Rotate = gesture.Rotate.instance,
                result = [];

            Drag.onStart = Tap.onStart = DoubleTap.onStart = LongPress.onStart = Swipe.onStart =
                Pinch.onStart = Rotate.onStart = EdgeSwipe.onStart = function() {
                    result.push([this.$className, this.priority]);
                };

            Ext.testHelper.touchStart(document.body, {id: 1, x: 100, y: 100});

            expect(result[0]).toEqual(['Ext.event.gesture.Drag', 100]);
            expect(result[1]).toEqual(['Ext.event.gesture.Tap', 200]);
            expect(result[2]).toEqual(['Ext.event.gesture.DoubleTap', 300]);
            expect(result[3]).toEqual(['Ext.event.gesture.LongPress', 400]);
            expect(result[4]).toEqual(['Ext.event.gesture.EdgeSwipe', 500]);
            expect(result[5]).toEqual(['Ext.event.gesture.Swipe', 600]);
            expect(result[6]).toEqual(['Ext.event.gesture.Pinch', 700]);
            expect(result[7]).toEqual(['Ext.event.gesture.Rotate', 800]);

            delete Drag.onStart;
            delete Tap.onStart;
            delete DoubleTap.onStart;
            delete LongPress.onStart;
            delete EdgeSwipe.onStart;
            delete Swipe.onStart;
            delete Pinch.onStart;
            delete Rotate.onStart;
        });
    });
    
    // window.onerror method of catching exceptions in synthetic event handlers
    // doesn't work in IE8 for some reason :(
    (Ext.isIE8m ? xdescribe : describe)("exceptions in recognizers", function() {
        var gesture = Ext.event.publisher.Gesture.instance;

        beforeEach(function() {
            targetEl.on('tap', function() {
                throw new Error("This error is caught but will show in console IE");
            });
        });
        
        it("should allow the exception to propagate", function() {
            expect(function() {
                helper.touchStart(targetEl, { id: 1, x: 1, y: 1 });
                helper.touchEnd(targetEl, { id: 1, x: 1, y: 1 });
            }).toThrow('This error is caught but will show in console IE');
        });
        
        it("should finish gesture an exception is thrown in recognizer", function() {
            expect(function() {
                helper.touchStart(targetEl, { id: 1, x: 1, y: 1 });
                helper.touchEnd(targetEl, { id: 1, x: 1, y: 1 });
            }).toThrow('This error is caught but will show in console IE');
            
            expect(gesture.isStarted).toBe(false);
        });
    });

    describe("bubbling", function() {
        var childEl;

        beforeEach(function() {
            childEl = targetEl.createChild({
                id: 'child'
            });
        });

        afterEach(function() {
            childEl.destroy();
        });

        it("should bubble in the correct order", function() {
            var out = [],
                handler = function(e) {
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragend: handler,
                    touchend: handler,
                    drag: handler,
                    touchmove: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 20, y: 35});
            helper.touchMove(childEl, {id: 1, x: 30, y: 45});
            helper.touchEnd(childEl, {id: 1, x: 30, y: 45});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',

                'target-touchmove',
                'target-dragstart',
                'target-drag',

                'child-touchmove',
                'child-drag',

                'target-touchmove',
                'target-drag',

                'child-touchend',
                'child-dragend',

                'target-touchend',
                'target-dragend'
            ]);
        });

        it("should stop propagation of the dom event", function() {
            var out = [],
                handler = function(e) {
                    if (e.type === 'touchmove') {
                        e.stopPropagation();
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',
                'child-swipestart',

                'target-dragstart',
                'target-drag',
                'target-swipestart',

                'child-touchmove',
                'child-drag',

                'target-drag',

                'child-touchend',
                'child-dragend',
                'child-swipe',

                'target-touchend',
                'target-dragend',
                'target-swipe'
            ]);
        });

        it("should stop propagation of a gesture event", function() {
            var out = [],
                handler = function(e) {
                    if (e.type === 'drag') {
                        e.stopPropagation();
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',
                'child-swipestart',

                'target-touchmove',
                'target-dragstart',
                'target-swipestart',

                'child-touchmove',
                'child-drag',

                'target-touchmove',

                'child-touchend',
                'child-dragend',
                'child-swipe',

                'target-touchend',
                'target-dragend',
                'target-swipe'
            ]);
        });
    });

    describe("claimGesture", function() {
        var childEl;

        beforeEach(function() {
            childEl = targetEl.createChild({
                id: 'child'
            });
        });

        afterEach(function() {
            childEl.destroy();
        });

        it("should fire multiple gestures in tandem when no gesture is claimed", function() {
            var out = [],
                handler = function(e) {
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',
                'child-swipestart',

                'target-touchmove',
                'target-dragstart',
                'target-drag',
                'target-swipestart',

                'child-touchmove',
                'child-drag',

                'target-touchmove',
                'target-drag',

                'child-touchend',
                'child-dragend',
                'child-swipe',

                'target-touchend',
                'target-dragend',
                'target-swipe'
            ]);
        });

        it("should cancel swipe events when drag is claimed", function() {
            var out = [],
                claimed = false,
                handler = function(e) {
                    if (!claimed && e.type === 'drag') {
                        e.claimGesture();
                        claimed = true;
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',

                'child-swipecancel',
                'target-swipecancel',

                'target-touchmove',
                'target-dragstart',
                'target-drag',

                'child-touchmove',
                'child-drag',

                'target-touchmove',
                'target-drag',

                'child-touchend',
                'child-dragend',

                'target-touchend',
                'target-dragend'
            ]);
        });

        it("should cancel drag events when swipe is claimed", function() {
            var out = [],
                claimed = false,
                handler = function(e) {
                    if (!claimed && e.type === 'swipestart') {
                        e.claimGesture();
                        claimed = true;
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            // swipe comes after drag in priority ranking.
            // therefore we expect drag events to fire prior to the swipestart listener
            // that claims the event
            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',
                'child-swipestart',

                'child-dragcancel',
                'target-dragcancel',

                'target-touchmove',
                'target-swipestart',

                'child-touchmove',

                'target-touchmove',

                'child-touchend',
                'child-swipe',

                'target-touchend',
                'target-swipe'
            ]);
        });

        it("should not fire gesture events when touchstart is claimed", function() {
            var out = [],
                claimed = false,
                handler = function(e) {
                    if (!claimed && e.type === 'touchstart') {
                        e.claimGesture();
                        claimed = true;
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});
            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            // swipe comes after drag in priority ranking.
            // therefore we expect drag events to fire prior to the swipestart listener
            // that claims the event
            expect(out).toEqual([
                'child-touchstart',
                'target-touchstart',

                'child-touchmove',
                'target-touchmove',

                'child-touchmove',
                'target-touchmove',

                'child-touchend',
                'target-touchend'
            ]);
        });

        it("should cancel gesture events when touchmove is claimed", function() {
            var out = [],
                claimed = false,
                claimNext = false,
                handler = function(e) {
                    if (claimNext && !claimed && e.type === 'touchmove') {
                        e.claimGesture();
                        claimed = true;
                    }
                    out.push(e.currentTarget.id + '-' + e.type);
                },
                listeners = {
                    dragcancel: handler,
                    swipecancel: handler,
                    dragend: handler,
                    touchend: handler,
                    swipe: handler,
                    drag: handler,
                    touchmove: handler,
                    swipestart: handler,
                    dragstart: handler,
                    touchstart: handler
                };

            targetEl.on(listeners);
            childEl.on(listeners);

            helper.touchStart(childEl, {id: 1, x: 10, y: 15});
            helper.touchMove(childEl, {id: 1, x: 50, y: 15});

            claimNext = true;

            helper.touchMove(childEl, {id: 1, x: 200, y: 15});
            helper.touchEnd(childEl, {id: 1, x: 200, y: 15});

            expect(out).toEqual([
                'child-touchstart',

                'target-touchstart',

                'child-touchmove',
                'child-dragstart',
                'child-drag',
                'child-swipestart',

                'target-touchmove',
                'target-dragstart',
                'target-drag',
                'target-swipestart',

                'child-touchmove',

                'child-dragcancel',
                'target-dragcancel',
                'child-swipecancel',
                'target-swipecancel',

                'target-touchmove',

                'child-touchend',

                'target-touchend'
            ]);
        });
    });
});
