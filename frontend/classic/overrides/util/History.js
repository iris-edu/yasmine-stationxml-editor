/* ****************************************************************************
 * 2026-09-18, version 4.1.3-beta: ASGSR, Alexey Emanov
 * Override: Ext.util.History - use replaceState for initial hash
 *
 * When setting the default token on app launch (no hash in URL), use
 * history.replaceState instead of location.hash assignment. This avoids
 * Firefox warning: "A session history item was added by this document without
 * any interaction from the user" (which causes back/forward to be skipped).
 *
 * iOS Safari: replaceState during the first paint can blank the document
 * and also fires pagehide (see overrides.event.publisher.Dom). Keep the
 * original location.hash assignment on iOS.
 * ****************************************************************************/
Ext.define('overrides.util.History', {
    override: 'Ext.util.History',

    setHash: function(hash) {
        var me = this,
            win = me.win,
            currentHash = me.getHash(),
            isIOS = Ext.os && Ext.os.is && Ext.os.is.iOS;

        try {
            if (!isIOS && currentHash === '' && win.history.length === 1 &&
                'replaceState' in win.history) {
                win.history.replaceState(null, '', '#' + hash);
                me.hash = hash;
                me.handleStateChange(hash);
            } else {
                win.location.hash = hash;
                me.currentToken = hash;
            }
        } catch (e) {
            try {
                win.location.hash = hash;
                me.currentToken = hash;
            } catch (ignored) {
                // IE can give Access Denied (esp. in popup windows)
            }
        }
    }
});
