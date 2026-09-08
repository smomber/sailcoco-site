// The full country list, generated verbatim from the product's country table
// (source/countries.json, 143 entries). Flags are real per-country SVGs under
// flags/4x3/ -- never an emoji flag (WEBSITE_SPEC section 5).
(function () {
  'use strict';

  var COUNTRIES = [
    ['AL','Albania'],
    ['DZ','Algeria'],
    ['AO','Angola'],
    ['AG','Antigua and Barbuda'],
    ['AR','Argentina'],
    ['AU','Australia'],
    ['BS','Bahamas'],
    ['BH','Bahrain'],
    ['BD','Bangladesh'],
    ['BB','Barbados'],
    ['BE','Belgium'],
    ['BZ','Belize'],
    ['BJ','Benin'],
    ['BR','Brazil'],
    ['BN','Brunei'],
    ['BG','Bulgaria'],
    ['CV','Cabo Verde'],
    ['KH','Cambodia'],
    ['CM','Cameroon'],
    ['CA','Canada'],
    ['CL','Chile'],
    ['CN','China'],
    ['CO','Colombia'],
    ['KM','Comoros'],
    ['CR','Costa Rica'],
    ['CI','Côte d\'Ivoire'],
    ['HR','Croatia'],
    ['CU','Cuba'],
    ['CY','Cyprus'],
    ['DK','Denmark'],
    ['DJ','Djibouti'],
    ['DM','Dominica'],
    ['DO','Dominican Republic'],
    ['EC','Ecuador'],
    ['EG','Egypt'],
    ['SV','El Salvador'],
    ['GQ','Equatorial Guinea'],
    ['ER','Eritrea'],
    ['EE','Estonia'],
    ['FJ','Fiji'],
    ['FI','Finland'],
    ['FR','France'],
    ['GA','Gabon'],
    ['GM','Gambia'],
    ['GE','Georgia'],
    ['DE','Germany'],
    ['GH','Ghana'],
    ['GR','Greece'],
    ['GD','Grenada'],
    ['GT','Guatemala'],
    ['GN','Guinea'],
    ['GW','Guinea-Bissau'],
    ['GY','Guyana'],
    ['HT','Haiti'],
    ['HN','Honduras'],
    ['IS','Iceland'],
    ['IN','India'],
    ['ID','Indonesia'],
    ['IR','Iran'],
    ['IE','Ireland'],
    ['IL','Israel'],
    ['IT','Italy'],
    ['JM','Jamaica'],
    ['JP','Japan'],
    ['JO','Jordan'],
    ['KE','Kenya'],
    ['KI','Kiribati'],
    ['KW','Kuwait'],
    ['LV','Latvia'],
    ['LB','Lebanon'],
    ['LR','Liberia'],
    ['LY','Libya'],
    ['LT','Lithuania'],
    ['MG','Madagascar'],
    ['MY','Malaysia'],
    ['MV','Maldives'],
    ['MT','Malta'],
    ['MH','Marshall Islands'],
    ['MR','Mauritania'],
    ['MU','Mauritius'],
    ['MX','Mexico'],
    ['FM','Micronesia'],
    ['ME','Montenegro'],
    ['MA','Morocco'],
    ['MZ','Mozambique'],
    ['MM','Myanmar'],
    ['NA','Namibia'],
    ['NR','Nauru'],
    ['NL','Netherlands'],
    ['NZ','New Zealand'],
    ['NI','Nicaragua'],
    ['NG','Nigeria'],
    ['NO','Norway'],
    ['OM','Oman'],
    ['PK','Pakistan'],
    ['PW','Palau'],
    ['PA','Panama'],
    ['PG','Papua New Guinea'],
    ['PE','Peru'],
    ['PH','Philippines'],
    ['PL','Poland'],
    ['PT','Portugal'],
    ['QA','Qatar'],
    ['CG','Republic of the Congo'],
    ['RO','Romania'],
    ['RU','Russia'],
    ['KN','Saint Kitts and Nevis'],
    ['LC','Saint Lucia'],
    ['VC','Saint Vincent and the Grenadines'],
    ['WS','Samoa'],
    ['ST','São Tomé and Príncipe'],
    ['SA','Saudi Arabia'],
    ['SN','Senegal'],
    ['SC','Seychelles'],
    ['SL','Sierra Leone'],
    ['SG','Singapore'],
    ['SI','Slovenia'],
    ['SB','Solomon Islands'],
    ['ZA','South Africa'],
    ['KR','South Korea'],
    ['ES','Spain'],
    ['LK','Sri Lanka'],
    ['SD','Sudan'],
    ['SR','Suriname'],
    ['SE','Sweden'],
    ['TW','Taiwan'],
    ['TZ','Tanzania'],
    ['TH','Thailand'],
    ['TL','Timor-Leste'],
    ['TG','Togo'],
    ['TO','Tonga'],
    ['TT','Trinidad and Tobago'],
    ['TN','Tunisia'],
    ['TR','Türkiye'],
    ['TV','Tuvalu'],
    ['UA','Ukraine'],
    ['AE','United Arab Emirates'],
    ['GB','United Kingdom'],
    ['US','United States'],
    ['UY','Uruguay'],
    ['VU','Vanuatu'],
    ['VE','Venezuela'],
    ['VN','Vietnam']
  ].map(function (c) {
    return { code: c[0], cc: c[0].toLowerCase(), name: c[1] };
  });

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  var CHECK = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="oklch(0.70 0.16 200)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>';

  function tile(c) {
    return '' +
      '<a href="index.html#apps" class="flag-tile">' +
        '<img src="flags/4x3/' + c.cc + '.svg" alt="" width="26" height="20" loading="lazy" decoding="async">' +
        '<span>' + esc(c.name) + '</span>' +
        CHECK +
      '</a>';
  }

  function init() {
    var grid = document.getElementById('country-grid');
    var input = document.getElementById('country-filter');
    var label = document.getElementById('country-count');
    var empty = document.getElementById('country-empty');
    if (!grid) return;

    function render(q) {
      q = (q || '').trim().toLowerCase();
      var shown = q
        ? COUNTRIES.filter(function (c) {
            return c.name.toLowerCase().indexOf(q) !== -1 || c.code.toLowerCase() === q;
          })
        : COUNTRIES;

      grid.innerHTML = shown.map(tile).join('');
      label.textContent = shown.length === COUNTRIES.length
        ? COUNTRIES.length + ' countries'
        : shown.length + ' of ' + COUNTRIES.length;
      empty.hidden = shown.length !== 0;
    }

    input.addEventListener('input', function () { render(input.value); });
    render('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
