/* ****************************************************************************
 * 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
 * Override: Ext.dom.Element viewport size
 *
 * Ext.plugin.Viewport sizes the Classic app to documentElement.clientHeight.
 * On iOS Safari that value is often 0 on first layout (empty body, 100%
 * height chain, visual viewport not ready), so the UI paints at 0x0.
 * Prefer window.innerHeight / visualViewport when client size is unusable.
 * ****************************************************************************/
Ext.define('overrides.dom.Element', {
    override: 'Ext.dom.Element'
}, function (Element) {
    var originalGetViewportWidth = Element.getViewportWidth;
    var originalGetViewportHeight = Element.getViewportHeight;

    function readViewportSize(axis) {
        var visual = window.visualViewport;
        var inner = axis === 'width' ? window.innerWidth : window.innerHeight;
        var visualSize = visual && (axis === 'width' ? visual.width : visual.height);
        var size = visualSize || inner;
        if (size > 0) {
            return Math.round(size);
        }
        return 0;
    }

    Element.getViewportWidth = function () {
        var width = readViewportSize('width');
        if (width > 0) {
            return width;
        }
        width = originalGetViewportWidth.call(Element);
        return width > 0 ? width : 1;
    };

    Element.getViewportHeight = function () {
        var height = readViewportSize('height');
        if (height > 0) {
            return height;
        }
        height = originalGetViewportHeight.call(Element);
        return height > 0 ? height : 1;
    };
});
