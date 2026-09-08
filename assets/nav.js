// Header navigation: mega menu + mobile panel.
// Menu state is a single value (null | 'product' | 'resources' | 'mobile'),
// per WEBSITE_SPEC §2 — never two independent booleans.
(function () {
  'use strict';

  function init() {
    var header = document.querySelector('[data-nav]');
    if (!header) return;

    var panels = {};
    Array.prototype.forEach.call(header.querySelectorAll('[data-panel]'), function (el) {
      panels[el.getAttribute('data-panel')] = el;
    });
    var triggers = header.querySelectorAll('[data-opens]');
    var state = null;

    function apply() {
      Object.keys(panels).forEach(function (key) {
        panels[key].hidden = key !== state;
      });
      Array.prototype.forEach.call(triggers, function (btn) {
        var opens = btn.getAttribute('data-opens');
        if (btn.tagName === 'BUTTON') {
          btn.setAttribute('aria-expanded', String(opens === state));
        }
      });
    }

    function set(next) {
      if (state === next) return;
      state = next;
      apply();
    }

    Array.prototype.forEach.call(triggers, function (btn) {
      var opens = btn.getAttribute('data-opens');

      // Mega menus open on hover and on click; the mobile panel only toggles.
      if (opens === 'mobile') {
        btn.addEventListener('click', function () {
          set(state === 'mobile' ? null : 'mobile');
        });
        return;
      }

      btn.addEventListener('mouseenter', function () { set(opens); });
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        set(state === opens ? null : opens);
      });
      btn.addEventListener('focus', function () { set(opens); });
    });

    // Hovering a plain nav link closes an open mega panel.
    Array.prototype.forEach.call(header.querySelectorAll('[data-closes]'), function (el) {
      el.addEventListener('mouseenter', function () {
        if (state !== 'mobile') set(null);
      });
      el.addEventListener('click', function () { set(null); });
    });

    // Closes on mouse-leave of the whole header.
    header.addEventListener('mouseleave', function () {
      if (state !== 'mobile') set(null);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') set(null);
    });

    document.addEventListener('click', function (e) {
      if (!header.contains(e.target)) set(null);
    });

    // The nav collapses at 1040px; drop any open menu when crossing the line.
    var narrow = window.matchMedia('(max-width: 1039px)');
    var wasNarrow = narrow.matches;
    window.addEventListener('resize', function () {
      if (narrow.matches !== wasNarrow) {
        wasNarrow = narrow.matches;
        set(null);
      }
    });

    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
