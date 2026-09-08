// Skipper bundles + the monthly/annual toggle.
// This is the ONLY billing-cycle toggle on the site (WEBSITE_SPEC §4): the four
// consumer tiers are annual-only and carry no toggle.
//
// Figures verified 2026-09-05 against the Stripe catalog + billing code.
(function () {
  'use strict';

  var BUNDLES = [
    {
      name: 'Dayboat',
      blurb: 'Day charters and short coastal hops.',
      berths: 'Crew and passenger berths for a day boat',
      monthly: { retail: '$44.99/mo', intro: '$29.99', note: 'First term · then $44.99/mo' },
      annual: { retail: '$432/yr', intro: '$280', note: 'First year · then $432/yr' }
    },
    {
      name: 'Coastal',
      blurb: 'Season-long coastal programmes with rotating crew.',
      berths: 'Larger berth allocation for rotating crew',
      monthly: { retail: '$79.99/mo', intro: '$51.99', note: 'First term · then $79.99/mo' },
      annual: { retail: '$768/yr', intro: '$499', note: 'First year · then $768/yr' }
    },
    {
      name: 'Bluewater',
      blurb: 'Ocean passages, full manifests, no country ceiling.',
      berths: 'Full manifest for offshore crew and guests',
      monthly: { retail: '$129.99/mo', intro: '$84.99', note: 'First term · then $129.99/mo' },
      annual: { retail: '$1,248/yr', intro: '$811', note: 'First year · then $1,248/yr' }
    }
  ];

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function card(b, cycle) {
    var p = b[cycle];
    return '' +
      '<div class="tier">' +
        '<div>' +
          '<h3>' + esc(b.name) + '</h3>' +
          '<p class="tier-blurb">' + esc(b.blurb) + '</p>' +
        '</div>' +
        '<div>' +
          '<div class="price-row">' +
            '<p class="tier-price" style="font-size:36px;">' + esc(p.intro) + '</p>' +
            '<p class="tier-was" style="font-size:16px;">' + esc(p.retail) + '</p>' +
          '</div>' +
          '<p class="tier-note">' + esc(p.note) + '</p>' +
        '</div>' +
        '<div class="rule"></div>' +
        '<div class="tier-list">' +
          '<p>' + esc(b.berths) + '</p>' +
          '<p>Unlimited countries on the vessel\'s trip</p>' +
          '<p>Manifest, invites and access levels</p>' +
        '</div>' +
        '<a href="#skippers" class="tier-cta tier-cta-outline">Choose ' + esc(b.name) + '</a>' +
      '</div>';
  }

  function init() {
    var grid = document.getElementById('bundle-grid');
    if (!grid) return;

    // The Fleet Skipper card is authored in the HTML and always last.
    var fleet = grid.querySelector('.tier-dashed');
    var monthlyBtn = document.getElementById('cycle-monthly');
    var annualBtn = document.getElementById('cycle-annual');
    var cycle = 'annual';

    function render() {
      var html = BUNDLES.map(function (b) { return card(b, cycle); }).join('');
      grid.innerHTML = html;
      if (fleet) grid.appendChild(fleet);
      monthlyBtn.setAttribute('aria-pressed', String(cycle === 'monthly'));
      annualBtn.setAttribute('aria-pressed', String(cycle === 'annual'));
    }

    monthlyBtn.addEventListener('click', function () { cycle = 'monthly'; render(); });
    annualBtn.addEventListener('click', function () { cycle = 'annual'; render(); });

    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
