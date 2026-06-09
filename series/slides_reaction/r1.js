/* ============================================================
   REACTION — slide 1 (id "r1") · FULL-TIME RESULT
   Flags left/right, giant final score in the middle. The hook slide,
   = the FYP cover, so it leads with the SCORE (scroll-stopping).
     m = { post_type:"reaction", home:{name,code,tla}, away:{...},
           actual:{home,away}, stage, group, venue }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.r1 = {
  render(m) {
    const { up, esc, flag } = window.WCF;
    const h = m.home || {}, a = m.away || {};
    const ah = (m.actual || {}).home, aa = (m.actual || {}).away;
    const stage = m.group ? `GROUP ${up(m.group)}` : up(m.stage || 'WORLD CUP');
    const meta = m.venue ? `${stage} · ${up(m.venue)}` : stage;
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="r-eyebrow"><span class="v-dot"></span>FULL TIME</div>

    <div class="r1-scoreline">
      <div class="r1-side">
        ${flag(h.code, 'r-flag')}
        <div class="r1-tla">${esc(h.tla || '')}</div>
      </div>
      <div class="r1-score">${ah}<span class="r1-dash">-</span>${aa}</div>
      <div class="r1-side">
        ${flag(a.code, 'r-flag')}
        <div class="r1-tla">${esc(a.tla || '')}</div>
      </div>
    </div>

    <div class="r1-names">${esc(h.name || '')} vs ${esc(a.name || '')}</div>
    <div class="r1-meta">${esc(meta)}</div>

    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
