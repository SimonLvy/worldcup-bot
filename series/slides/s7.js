/* SLIDE 7 — STATS THAT HIT */
window.WCSlides.s7 = {
  render(m) {
    const stat = s => `<div class="panel stat"><div class="n">${s.value}</div><div class="tx">${s.label}</div></div>`;
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>BY THE NUMBERS</span></div>
      <div class="title">Stats That <em>Hit</em></div>
    </div>
    <div class="big3">
      ${(m.fun_stats || []).slice(0, 3).map(stat).join('')}
    </div>
    <div class="didyou">
      <div class="k">DID YOU KNOW?</div>
      <div class="t">${m.did_you_know || ''}</div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
