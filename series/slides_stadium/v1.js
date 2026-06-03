/* ============================================================
   STADIUM — slide 1 (id "v1") · HERO
   Full-bleed stadium photo, name in Anton, gold capacity badge.
   Reads the post dict (m) the engine exposes from window.__post:
     m = { post_type:"stadium", stadium, city, country, capacity,
           image_url, ... }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.v1 = {
  render(m) {
    const { up, esc, fmtNum, num } = window.WCF;

    const cap = num(m.capacity);
    const badge = cap ? `${fmtNum(cap)} SEATS` : 'HOST VENUE';

    // Photo sits on top of a labelled placeholder; onerror reveals it.
    const photo = m.image_url
      ? `<img class="v1-img" src="${esc(m.image_url)}" alt=""
            onerror="this.style.display='none'" />`
      : '';

    return `
    <div class="v1-photo">
      <div class="ph v1-photo-ph"><span class="ph-lbl">stadium photo &mdash; ${esc(m.stadium || 'host venue')}</span></div>
      ${photo}
    </div>
    <div class="v1-scrim"></div>
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />

    <div class="v1-top">
      <div class="v1-eyebrow"><span class="v-dot"></span>HOST VENUE</div>
    </div>

    <div class="v1-body">
      <div class="v1-badge">${esc(badge)}</div>
      <h1 class="v1-name">${up(m.stadium || '')}</h1>
      <div class="v1-loc">${esc(m.city || '')}${m.country ? ', ' + esc(m.country) : ''}</div>
    </div>

    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
