/**
 * 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
 * Inserts SVG into the interface.
 * Brand slots (header, splash, about) become inline copies of their img src SVGs.
 * Font Awesome glyphs become inline SVG paths from the bundled webfont.
 */
(function (window, document) {
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var logoDocs = {};
  var logoLoading = {};
  var logoWait = {};
  var glyphs = null;
  var glyphLoading = false;
  var classIcons = null;
  var indexedSignature = '';

  function sheetSignature() {
    var total = 0;
    var sheets = document.styleSheets;
    var i;
    for (i = 0; i < sheets.length; i++) {
      try {
        total += sheets[i].cssRules.length;
      } catch (error) {
        total += 0;
      }
    }
    return sheets.length + ':' + total;
  }
  var seq = 0;
  var scheduled = false;

  function injectStyle() {
    var existing = document.getElementById('yasmine-svg-icon-style');
    var parent = document.head || document.documentElement;
    if (existing) {
      if (existing.parentNode !== parent || existing.nextSibling) {
        parent.appendChild(existing);
      }
      return;
    }
    var style = document.createElement('style');
    style.id = 'yasmine-svg-icon-style';
      style.textContent = [
      '.yasmine-fa-svg-host.yasmine-fa-from-before::before{content:none !important;}',
      '.x-tree-arrows .x-tree-expander.yasmine-fa-svg-host.yasmine-fa-from-before::before,.x-tree-arrows .x-grid-tree-node-expanded .x-tree-expander.yasmine-fa-svg-host.yasmine-fa-from-before::before{content:none !important;}',
      '.yasmine-fa-svg-host.yasmine-fa-from-after::after{content:none !important;}',
      '.yasmine-fa-svg{display:block;width:1em;height:1em;fill:currentColor;pointer-events:none;}',
      'i.yasmine-fa-svg-host,a.yasmine-fa-svg-host{display:inline-block;line-height:1;vertical-align:-0.15em;}',
      /* Ext tree elbows/icons are full row-height boxes; FA ::before sat on the
         text line via line-height. Inline SVG must be flex-centered the same way. */
      '.x-tree-elbow-img.yasmine-fa-svg-host,.x-tree-icon.yasmine-fa-svg-host{display:inline-flex;align-items:center;justify-content:center;vertical-align:top;box-sizing:border-box;}',
      '.x-tree-elbow-img.yasmine-fa-svg-host>.yasmine-fa-svg,.x-tree-icon.yasmine-fa-svg-host>.yasmine-fa-svg{flex:0 0 auto;}',
      '.yasmine-header-logo,.yasmine-about-logo,.yasmine-splash-logo{overflow:hidden;display:block;flex:0 0 auto;box-sizing:border-box;}',
      '.yasmine-header-logo{display:block;width:42px;height:42px;border-radius:10px;flex:0 0 auto;box-shadow:0 0 0 1px rgba(255,255,255,0.24),0 4px 12px rgba(4,25,43,0.3);}',
      '.yasmine-vp-xs .yasmine-header-logo,.yasmine-vp-sm .yasmine-header-logo,.yasmine-vp-md .yasmine-header-logo,.yasmine-vp-lg .yasmine-header-logo,.yasmine-compact-height .yasmine-header-logo{width:36px;height:36px;border-radius:8px;}',
      '.yasmine-splash-logo{width:96px;height:96px;border-radius:22px;}',
      '.x-panel-header-navigation,.x-panel-header-navigation-vertical,.x-panel-header-navigation-horizontal{background-color:#123b5d !important;background-image:none !important;}',
      '.x-panel-header-title-navigation{color:#fff;font-size:20px;font-weight:650;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;line-height:24px;margin:6px 12px;background:transparent !important;}',
      '.yasmine-vp-xl .x-panel-header-title-navigation,.yasmine-vp-xxl .x-panel-header-title-navigation,.yasmine-vp-uw .x-panel-header-title-navigation{left:12px !important;}',
      '.yasmine-header-text{line-height:1.15;letter-spacing:0.1px;font-weight:650;color:#fff;}',
      '.yasmine-header-version{font-size:10px;margin-top:2px;padding-left:1px;color:#c9d9e3;font-weight:500;letter-spacing:0.2px;opacity:1;}',
      '.yasmine-header-brand{display:flex;align-items:center;gap:10px;margin:0;padding:0;background:transparent;}',
      '.yasmine-vp-xs .yasmine-header-text,.yasmine-vp-sm .yasmine-header-text,.yasmine-vp-md .yasmine-header-text,.yasmine-vp-lg .yasmine-header-text,.yasmine-compact-height .yasmine-header-text{display:none !important;}',
      '.yasmine-vp-xs .x-panel-header-title-navigation,.yasmine-vp-sm .x-panel-header-title-navigation,.yasmine-vp-md .x-panel-header-title-navigation,.yasmine-vp-lg .x-panel-header-title-navigation,.yasmine-compact-height .x-panel-header-title-navigation{width:auto !important;min-width:0 !important;max-width:48px !important;flex:0 0 auto !important;margin:0 !important;}',
      '.yasmine-vp-md .x-panel-header-navigation,.yasmine-vp-lg .x-panel-header-navigation{padding:2px 4px !important;}',
      '.yasmine-vp-xs .yasmine-header-brand,.yasmine-vp-sm .yasmine-header-brand,.yasmine-vp-md .yasmine-header-brand,.yasmine-vp-lg .yasmine-header-brand,.yasmine-compact-height .yasmine-header-brand{gap:0 !important;height:100%;align-items:center !important;}'
    ].join('');
    (document.head || document.documentElement).appendChild(style);
  }

  function codePointFromContent(content) {
    if (!content || content === 'none' || content === 'normal') {
      return 0;
    }
    var text = content;
    if ((text.charAt(0) === '"' && text.charAt(text.length - 1) === '"') ||
        (text.charAt(0) === "'" && text.charAt(text.length - 1) === "'")) {
      text = text.slice(1, -1);
    }
    if (!text || text === 'none') {
      return 0;
    }
    var cp = text.codePointAt(0);
    if (!cp || cp < 0xf000 || cp > 0xf8ff) {
      return 0;
    }
    if (text.length > (cp > 0xffff ? 2 : 1)) {
      return 0;
    }
    return cp;
  }

  function parseIconSelector(part) {
    var pseudo = /::?after/.test(part) ? 'after' : 'before';
    var cleaned = part.replace(/::?(?:before|after)/g, '').trim();
    if (!cleaned) {
      return null;
    }
    var segments = cleaned.split(/\s+/).filter(Boolean);
    if (!segments.length) {
      return null;
    }
    var targetClasses = (segments[segments.length - 1].match(/\.([A-Za-z0-9_-]+)/g) || []).map(function (token) {
      return token.slice(1);
    }).filter(function (name) {
      return name !== 'x-fa' && name !== 'fa';
    });
    if (!targetClasses.length) {
      return null;
    }
    var target = targetClasses[targetClasses.length - 1];
    var requiredOnEl = targetClasses.slice(0, -1);
    var ancestors = [];
    var s;
    for (s = 0; s < segments.length - 1; s++) {
      var ancestorClasses = (segments[s].match(/\.([A-Za-z0-9_-]+)/g) || []).map(function (token) {
        return token.slice(1);
      }).filter(function (name) {
        return name !== 'x-fa' && name !== 'fa';
      });
      if (ancestorClasses.length) {
        ancestors.push(ancestorClasses);
      }
    }
    return {
      target: target,
      ancestors: ancestors,
      requiredOnEl: requiredOnEl,
      pseudo: pseudo
    };
  }

  function contextKey(ancestors, requiredOnEl) {
    var parts = [];
    var i;
    for (i = 0; i < ancestors.length; i++) {
      parts.push(ancestors[i].join('.'));
    }
    return parts.join('>') + '|' + requiredOnEl.join('.');
  }

  function storeIcon(parsed, cp) {
    var list = classIcons[parsed.target] || (classIcons[parsed.target] = []);
    var key = contextKey(parsed.ancestors, parsed.requiredOnEl);
    var i;
    for (i = 0; i < list.length; i++) {
      if (list[i].key === key) {
        list[i].cp = cp;
        list[i].pseudo = parsed.pseudo;
        return;
      }
    }
    list.push({
      key: key,
      cp: cp,
      pseudo: parsed.pseudo,
      ancestors: parsed.ancestors,
      requiredOnEl: parsed.requiredOnEl
    });
  }

  function walkRules(rules) {
    if (!rules) {
      return;
    }
    var i;
    for (i = 0; i < rules.length; i++) {
      var rule = rules[i];
      if (rule.cssRules) {
        walkRules(rule.cssRules);
      }
      if (!rule.selectorText || !rule.style) {
        continue;
      }
      var cp = codePointFromContent(rule.style.content);
      if (!cp) {
        continue;
      }
      var parts = rule.selectorText.split(',');
      var p;
      for (p = 0; p < parts.length; p++) {
        var parsed = parseIconSelector(parts[p]);
        if (!parsed) {
          continue;
        }
        storeIcon(parsed, cp);
      }
    }
  }

  function indexIcons() {
    classIcons = {};
    var sheets = document.styleSheets;
    var i;
    for (i = 0; i < sheets.length; i++) {
      try {
        walkRules(sheets[i].cssRules);
      } catch (error) {
        // A stylesheet from another origin cannot be indexed.
      }
    }
    indexedSignature = sheetSignature();
  }

  function segmentMatches(node, classes) {
    var i;
    for (i = 0; i < classes.length; i++) {
      if (!node.classList || !node.classList.contains(classes[i])) {
        return false;
      }
    }
    return true;
  }

  function matchesContext(el, entry) {
    var i;
    for (i = 0; i < entry.requiredOnEl.length; i++) {
      if (!el.classList.contains(entry.requiredOnEl[i])) {
        return false;
      }
    }
    var node = el.parentElement;
    for (i = entry.ancestors.length - 1; i >= 0; i--) {
      while (node && !segmentMatches(node, entry.ancestors[i])) {
        node = node.parentElement;
      }
      if (!node) {
        return false;
      }
      node = node.parentElement;
    }
    return true;
  }

  function pickEntry(entries, el) {
    var best = null;
    var bestSpec = -1;
    var i;
    for (i = 0; i < entries.length; i++) {
      var entry = entries[i];
      if (!matchesContext(el, entry)) {
        continue;
      }
      var spec = entry.ancestors.length * 100 + entry.requiredOnEl.length;
      if (spec >= bestSpec) {
        best = entry;
        bestSpec = spec;
      }
    }
    return best;
  }

  function iconFor(el) {
    if (!classIcons || !el.classList) {
      return null;
    }
    // Spinner triggers share the combo trigger class. Their up/down buttons
    // are drawn separately; injecting the caret adds a second down icon.
    if (el.classList.contains('x-form-trigger-spinner')) {
      return null;
    }
    // File browse buttons live in a component trigger that also carries
    // x-form-trigger-default. That class would drop a caret under the path.
    if (el.classList.contains('x-form-trigger-cmp')) {
      return null;
    }
    var faName = '';
    var faLen = 0;
    var bestName = '';
    var bestLen = 0;
    var i;
    for (i = 0; i < el.classList.length; i++) {
      var name = el.classList[i];
      if (!classIcons[name]) {
        continue;
      }
      // Prefer fa-* icon classes over longer Ext structural classes
      // (e.g. x-btn-icon-el-default-small) that can steal the match and
      // draw the wrong glyph (download instead of upload).
      if (name.indexOf('fa-') === 0) {
        if (name.length >= faLen) {
          faName = name;
          faLen = name.length;
        }
        continue;
      }
      // Specialized triggers (clear/search/date/…) share x-form-trigger-default,
      // whose caret-down class name is longer and would otherwise win.
      if (bestName === 'x-form-trigger-default' && name !== 'x-form-trigger-default') {
        bestName = name;
        bestLen = name.length;
        continue;
      }
      if (name === 'x-form-trigger-default' && bestName && bestName !== 'x-form-trigger-default') {
        continue;
      }
      if (name.length >= bestLen) {
        bestName = name;
        bestLen = name.length;
      }
    }
    if (faName) {
      return pickEntry(classIcons[faName], el);
    }
    if (!bestName) {
      return null;
    }
    return pickEntry(classIcons[bestName], el);
  }

  function syncDescendantIcons(root) {
    if (!root || root.nodeType !== 1 || !root.querySelectorAll) {
      return;
    }
    var nodes = root.querySelectorAll(
      '[data-fa-cp], .x-tree-expander, .x-tree-elbow-plus, .x-tree-elbow-end-plus'
    );
    var i;
    for (i = 0; i < nodes.length; i++) {
      syncIcon(nodes[i]);
    }
  }

  function glyphUrl() {
    var sheets = document.styleSheets;
    var i;
    for (i = 0; i < sheets.length; i++) {
      var sheet = sheets[i];
      var rules;
      try {
        rules = sheet.cssRules;
      } catch (error) {
        continue;
      }
      if (!rules) {
        continue;
      }
      var j;
      for (j = 0; j < rules.length; j++) {
        var text = rules[j].cssText || '';
        if (text.indexOf('fontawesome-webfont') === -1) {
          continue;
        }
        var match = text.match(/url\((['"]?)([^'")]*fontawesome-webfont\.[^)'"]+)\1\)/);
        if (!match) {
          continue;
        }
        var raw = match[2].replace(/fontawesome-webfont\.[a-z0-9]+/i, 'fontawesome-webfont.svg').split('#')[0];
        return new URL(raw, sheet.href || window.location.href).href;
      }
    }
    return '';
  }

  function decodeUnicode(value) {
    if (!value) {
      return 0;
    }
    if (value.indexOf('&#x') === 0 || value.indexOf('&#X') === 0) {
      return parseInt(value.slice(3), 16) || 0;
    }
    if (value.indexOf('&#') === 0) {
      return parseInt(value.slice(2), 10) || 0;
    }
    return value.codePointAt(0) || 0;
  }

  function loadGlyphs(done) {
    if (glyphs) {
      done();
      return;
    }
    if (glyphLoading) {
      return;
    }
    var url = glyphUrl();
    if (!url) {
      return;
    }
    glyphLoading = true;
    fetch(url).then(function (response) {
      if (!response.ok) {
        throw new Error('font svg ' + response.status);
      }
      return response.text();
    }).then(function (text) {
      var parsed = new DOMParser().parseFromString(text, 'image/svg+xml');
      var map = {};
      var nodes = parsed.getElementsByTagName('glyph');
      var i;
      for (i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        var d = node.getAttribute('d');
        if (!d) {
          continue;
        }
        var cp = decodeUnicode(node.getAttribute('unicode'));
        if (cp >= 0xf000 && cp <= 0xf8ff) {
          map[cp] = d;
        }
      }
      glyphs = map;
      glyphLoading = false;
      done();
    }).catch(function () {
      glyphLoading = false;
    });
  }

  function makeIcon(d) {
    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'yasmine-fa-svg');
    svg.setAttribute('viewBox', '0 0 1792 1792');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var group = document.createElementNS(SVG_NS, 'g');
    group.setAttribute('transform', 'translate(0 1536) scale(1 -1)');
    var path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', d);
    group.appendChild(path);
    svg.appendChild(group);
    return svg;
  }

  function clearHost(el) {
    var stale = el.querySelector(':scope > .yasmine-fa-svg');
    if (stale) {
      stale.parentNode.removeChild(stale);
    }
    el.classList.remove('yasmine-fa-svg-host', 'yasmine-fa-from-before', 'yasmine-fa-from-after');
    el.removeAttribute('data-fa-cp');
  }

  function syncIcon(el) {
    if (!glyphs || !el || el.namespaceURI === SVG_NS || el.closest('svg')) {
      return;
    }
    // ExtJS menu/split carets put the FA glyph on ::after as a flex item.
    // Replacing that pseudo with an SVG child collapses .x-btn-wrap height
    // and pulls File/Builder labels above Hierarchy/Parameters.
    if (el.classList &&
        (el.classList.contains('x-btn-arrow') || el.classList.contains('x-btn-split'))) {
      if (el.getAttribute('data-fa-cp')) {
        clearHost(el);
      }
      return;
    }
    var icon = iconFor(el);
    var cp = icon && glyphs[icon.cp] ? icon.cp : 0;
    var previous = el.getAttribute('data-fa-cp') || '';
    if (!cp) {
      if (previous) {
        clearHost(el);
      }
      return;
    }
    if (previous === String(cp) && el.querySelector(':scope > .yasmine-fa-svg')) {
      return;
    }
    var existing = el.querySelector(':scope > .yasmine-fa-svg');
    if (existing) {
      existing.parentNode.removeChild(existing);
    }
    el.appendChild(makeIcon(glyphs[cp]));
    el.setAttribute('data-fa-cp', String(cp));
    el.classList.add('yasmine-fa-svg-host');
    el.classList.toggle('yasmine-fa-from-before', !icon || icon.pseudo !== 'after');
    el.classList.toggle('yasmine-fa-from-after', !!(icon && icon.pseudo === 'after'));
  }

  function isLogoImage(el) {
    return el && el.tagName === 'IMG' &&
      /(yasmine-header-logo|yasmine-about-logo|yasmine-splash-logo)/.test(el.className || '') &&
      (el.getAttribute('src') || '').indexOf('.svg') !== -1;
  }

  function prefixLogo(svg, prefix) {
    var nodes = [svg].concat(Array.prototype.slice.call(svg.querySelectorAll('*')));
    var i;
    for (i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      if (node.id) {
        node.id = prefix + node.id;
      }
      var labelled = node.getAttribute('aria-labelledby');
      if (labelled) {
        node.setAttribute('aria-labelledby', labelled.split(/\s+/).map(function (id) {
          return prefix + id;
        }).join(' '));
      }
      var attrs = ['fill', 'stroke', 'filter', 'clip-path', 'mask'];
      var a;
      for (a = 0; a < attrs.length; a++) {
        var value = node.getAttribute(attrs[a]);
        if (value && value.indexOf('url(#') !== -1) {
          node.setAttribute(attrs[a], value.replace(/url\(#/g, 'url(#' + prefix));
        }
      }
    }
    return svg;
  }

  function logoKey(img) {
    return (img.getAttribute('src') || '').split('?')[0];
  }

  function applyLogo(img, doc) {
    if (!img.parentNode || !doc) {
      return;
    }
    var svg = prefixLogo(doc.documentElement.cloneNode(true), 'ym' + (++seq) + '-');
    svg.setAttribute('class', img.className);
    svg.setAttribute('data-src', img.getAttribute('src') || '');
    var box = img.getBoundingClientRect();
    if (box.width > 0 && box.height > 0) {
      svg.setAttribute('width', String(Math.round(box.width)));
      svg.setAttribute('height', String(Math.round(box.height)));
    }
    if (!svg.getAttribute('role')) {
      svg.setAttribute('role', 'img');
    }
    var alt = img.getAttribute('alt');
    if (alt) {
      svg.setAttribute('aria-label', alt);
    }
    img.parentNode.replaceChild(svg, img);
  }

  function inlineLogo(img) {
    if (!isLogoImage(img) || img.getAttribute('data-svg-pending')) {
      return;
    }
    var url = logoKey(img);
    if (!url) {
      return;
    }
    if (logoDocs[url]) {
      applyLogo(img, logoDocs[url]);
      return;
    }
    img.setAttribute('data-svg-pending', '1');
    if (!logoWait[url]) {
      logoWait[url] = [];
    }
    logoWait[url].push(img);
    if (logoLoading[url]) {
      return;
    }
    logoLoading[url] = true;
    fetch(url).then(function (response) {
      if (!response.ok) {
        throw new Error('logo svg ' + response.status);
      }
      return response.text();
    }).then(function (text) {
      var parsed = new DOMParser().parseFromString(text, 'image/svg+xml');
      if (!parsed.documentElement || parsed.documentElement.tagName.toLowerCase() !== 'svg') {
        throw new Error('logo svg parse');
      }
      logoDocs[url] = parsed;
      logoLoading[url] = false;
      var pending = (logoWait[url] || []).splice(0);
      var i;
      for (i = 0; i < pending.length; i++) {
        pending[i].removeAttribute('data-svg-pending');
        applyLogo(pending[i], parsed);
      }
    }).catch(function () {
      logoLoading[url] = false;
      var pending = (logoWait[url] || []).splice(0);
      var i;
      for (i = 0; i < pending.length; i++) {
        pending[i].removeAttribute('data-svg-pending');
      }
    });
  }

  function scan(root) {
    if (!root || root.nodeType !== 1) {
      return;
    }
    if (isLogoImage(root)) {
      inlineLogo(root);
    } else {
      syncIcon(root);
    }
    var nodes = root.getElementsByTagName('*');
    var i;
    for (i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      if (isLogoImage(node)) {
        inlineLogo(node);
      } else {
        syncIcon(node);
      }
    }
  }

  function ensureAssets(done) {
    var signature = sheetSignature();
    var sheetsChanged = !classIcons || indexedSignature !== signature;
    if (sheetsChanged) {
      indexIcons();
    }
    if (!glyphs) {
      loadGlyphs(done);
      return sheetsChanged;
    }
    return sheetsChanged;
  }

  function applyRecords(records) {
    var i;
    for (i = 0; i < records.length; i++) {
      var record = records[i];
      if (record.type === 'attributes' && record.target && record.target.nodeType === 1) {
        if (isLogoImage(record.target)) {
          inlineLogo(record.target);
        } else {
          syncIcon(record.target);
          // Parent class changes (e.g. x-grid-tree-node-expanded) must
          // refresh context-dependent icons such as tree expanders.
          if (record.attributeName === 'class') {
            syncDescendantIcons(record.target);
          }
        }
        continue;
      }
      if (record.type !== 'childList') {
        continue;
      }
      var n;
      for (n = 0; n < record.addedNodes.length; n++) {
        scan(record.addedNodes[n]);
      }
    }
  }

  var pendingRecords = [];

  function flush() {
    scheduled = false;
    if (!document.body) {
      pendingRecords = [];
      return;
    }
    var records = pendingRecords.splice(0);
    var sheetsChanged = ensureAssets(function () {
      scan(document.body);
    });
    if (!records.length || sheetsChanged) {
      scan(document.body);
      return;
    }
    applyRecords(records);
  }

  function schedule(records) {
    if (records) {
      pendingRecords.push.apply(pendingRecords, records);
    }
    if (scheduled) {
      return;
    }
    scheduled = true;
    window.requestAnimationFrame(flush);
    injectStyle();
  }

  function start() {
    injectStyle();
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', start);
      return;
    }
    schedule();
    var observer = new MutationObserver(function (records) {
      schedule(records);
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'src']
    });
  }

  window.yasmineSvgIcons = { start: start };
  start();
}(window, document));
