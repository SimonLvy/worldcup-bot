/* ============================================================
   STADIUM — slide 3 (id "v3") · SCHEDULE + MAP
   Medium venue map up top, then the venue's fixtures as clean rows:
       BRA [flag]   VS   [flag] MAR        with a stage tag rail.
   Real flags for known sides (ISO alpha-2 code); a neutral chip for
   TBD knockout slots. No fixtures -> a tidy "Schedule TBD" card.
     m = { post_type:"stadium", stadium, map_url,
           matches:[{stage, teams:[{tla,code,name,short}, ...]}] }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.v3 = (function () {
  const isCode = c => /^[a-z]{2}$/i.test((c || '').trim());

  function stageLabel(s) {
    const k = (s || '').toString().toLowerCase().replace(/[^a-z0-9]/g, '');
    if (k.includes('final') && !k.includes('semi') && !k.includes('quarter')) return 'FINAL';
    if (k.includes('third') || k.includes('bronze')) return '3RD';
    if (k.includes('semi') || k === 'sf') return 'SEMI';
    if (k.includes('quarter') || k === 'qf') return 'QF';
    if (k.includes('16') || k === 'r16') return 'R16';
    if (k.includes('32') || k === 'r32') return 'R32';
    if (k.includes('group') || k === 'g') return 'GROUP';
    return s ? String(s).toUpperCase().slice(0, 5) : 'TBD';
  }

  function teamHTML(t, side) {
    const { up, esc, flag } = window.WCF;
    t = t || {};
    const code = (t.code || '').trim();
    const tla = up(t.short || t.tla || t.name || 'TBD');
    if (isCode(code)) {
      const fl = flag(code, 'mini');
      return side === 'l'
        ? `<div class="v3-team l"><span class="tla">${esc(tla)}</span>${fl}</div>`
        : `<div class="v3-team r">${fl}<span class="tla">${esc(tla)}</span></div>`;
    }
    return `<div class="v3-team ${side}"><span class="v3-tbd">${esc(tla)}</span></div>`;
  }

  return {
    render(m) {
      const { up, esc } = window.WCF;
      const matches = Array.isArray(m.matches) ? m.matches : [];

      // map: placeholder sits BEHIND the (transparent) map PNG. render.js's
      // waitImages() reassigns img.onload/onerror to its own resolver, so inline
      // handlers don't fire — slides.css uses :has(img.v3-map) to hide the
      // placeholder instead.
      const map = m.map_url
        ? `<div class="v3-map-wrap">
             <div class="ph v3-map-ph"><span class="ph-lbl">venue map</span></div>
             <img class="v3-map" src="${esc(m.map_url)}" alt="" />
           </div>`
        : `<div class="v3-map-wrap"><div class="ph v3-map-ph"><span class="ph-lbl">venue map</span></div></div>`;

      let body;
      if (!matches.length) {
        body = `<div class="v3-empty">
            <div class="v3-empty-k">SCHEDULE TBD</div>
            <div class="v3-empty-s">Fixtures for this venue are still to be confirmed.</div>
          </div>`;
      } else {
        const dense = matches.length > 5 ? ' dense' : '';
        const rows = matches.map(mt => {
          const teams = Array.isArray(mt.teams) ? mt.teams : [];
          const lab = stageLabel(mt.stage);
          const stCls = lab === 'FINAL' ? 'gold' : 'ghost';
          return `<div class="v3-match">
              <span class="v3-stage ${stCls}">${esc(lab)}</span>
              ${teamHTML(teams[0], 'l')}
              <span class="v3-vs">VS</span>
              ${teamHTML(teams[1], 'r')}
            </div>`;
        }).join('');
        body = `<div class="v3-list${dense}">${rows}</div>`;
      }

      return `
      <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
      <div class="v3-head">
        <div class="v3-eyebrow"><span class="v-dot"></span>MATCH SCHEDULE</div>
        <div class="v3-title">${up(m.stadium || '')}</div>
      </div>
      ${map}
      ${body}
      <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
    }
  };
})();
