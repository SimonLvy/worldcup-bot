/* ============================================================
   REACTION — slide 2 (id "r2") · THE VERDICT
   How the pre-match call aged. Big verdict word + "MY CALL" vs
   "FULL TIME" rows. Green when right, red when cooked, gold on chaos.
     m = { verdict:"nailed|called|upset|missed",
           predicted:{home,away}, actual:{home,away} }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.r2 = {
  render(m) {
    const { esc } = window.WCF;
    const V = {
      nailed: { line: 'NAILED IT',     sub: 'EXACT SCORE CALLED',     cls: 'good' },
      called: { line: 'CALLED IT',     sub: 'RESULT PREDICTED',       cls: 'good' },
      upset:  { line: 'UPSET',         sub: 'NOBODY SAW IT COMING',   cls: 'wild' },
      missed: { line: 'I GOT COOKED',  sub: 'PREDICTION MISSED',      cls: 'bad'  },
    }[m.verdict] || { line: 'FULL TIME', sub: '', cls: '' };

    const p = m.predicted || {}, ac = m.actual || {};
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="r2-wrap">
      <div class="r2-verdict ${V.cls}">${esc(V.line)}</div>
      ${V.sub ? `<div class="r2-sub">${esc(V.sub)}</div>` : ''}
      <div class="r2-rows">
        <div class="r2-row">
          <span class="r2-k">MY CALL</span>
          <span class="r2-v">${p.home}<span class="r2-dash">-</span>${p.away}</span>
        </div>
        <div class="r2-row hot">
          <span class="r2-k">FULL TIME</span>
          <span class="r2-v">${ac.home}<span class="r2-dash">-</span>${ac.away}</span>
        </div>
      </div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
