/* ============================================================
   REACTION — single slide (id "r1")
   Full-time result hero (the FYP cover, leads with the giant score),
   plus a compact MY CALL vs FINAL strip. No verdict word, no hook line:
   all the personality lives in the caption.
     m = { post_type:"reaction", home:{name,code,tla}, away:{...},
           actual:{home,away}, predicted:{home,away}, stage, group, venue }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.r1 = {
  render(m) {
    const { up, esc, flag } = window.WCF;
    const h = m.home || {}, a = m.away || {};
    const ac = m.actual || {}, pc = m.predicted || {};
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
      <div class="r1-score">${ac.home}<span class="r1-dash">-</span>${ac.away}</div>
      <div class="r1-side">
        ${flag(a.code, 'r-flag')}
        <div class="r1-tla">${esc(a.tla || '')}</div>
      </div>
    </div>

    <div class="r1-names">${esc(h.name || '')} vs ${esc(a.name || '')}</div>
    <div class="r1-meta">${esc(meta)}</div>

    <div class="r1-call">
      <span class="r1-call-k">MY CALL</span>
      <span class="r1-call-v">${pc.home}<span class="r1-dash sm">-</span>${pc.away}</span>
    </div>

    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
