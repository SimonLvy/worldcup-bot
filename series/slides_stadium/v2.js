/* ============================================================
   STADIUM — slide 2 (id "v2") · CITY BRAND EMBLEM
   Official host-city logo, centred & large, with the city name and
   its design motif. Graceful empty state when assets are missing.
     m = { post_type:"stadium", city, city_logo, city_motif, ... }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.v2 = (function () {
  // "New York/NJ" -> "NY" · "Atlanta" -> "AT"
  function initials(city) {
    const words = (city || '').split(/[^A-Za-z]+/).filter(Boolean);
    if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
    return 'WC';
  }

  return {
    render(m) {
      const { up, esc } = window.WCF;
      const ini = initials(m.city);

      // The placeholder sits BEHIND the logo (city logos are transparent PNGs).
      // render.js's waitImages() reassigns img.onload/onerror to its own
      // promise resolver, so inline handlers don't fire — slides.css uses
      // :has(img.v2-logo) to hide the placeholder instead.
      const ph = `<div class="ph v2-emblem-ph">
            <span class="v2-mono">${esc(ini)}</span>
            <span class="ph-lbl">brand emblem coming soon</span>
          </div>`;
      const emblem = m.city_logo
        ? `<div class="v2-emblem">
            ${ph}
            <img class="v2-logo" src="${esc(m.city_logo)}" alt="" />
          </div>`
        : `<div class="v2-emblem">${ph}</div>`;

      const motif = m.city_motif
        ? `<p class="v2-motif">${esc(m.city_motif)}</p>`
        : `<p class="v2-motif faint">Host-city identity &mdash; story coming soon.</p>`;

      return `
      <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
      <div class="v2-wrap">
        <div class="v2-eyebrow"><span class="v-dot"></span>HOST CITY IDENTITY</div>
        ${emblem}
        <h1 class="v2-city">${up(m.city || '')}</h1>
        ${motif}
      </div>
      <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
    }
  };
})();
