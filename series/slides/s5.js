/* SLIDE 5 — SQUAD COMPARISON (radar) */
window.WCSlides.s5 = {
  render(m) {
    const { fmtValue } = window.WCF;
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>SQUAD PROFILE</span></div>
      <div class="title">Tale of the <em>Tape</em></div>
    </div>
    <div class="legend">
      <div class="lg"><span class="sw fr"></span>${m.home.name}</div>
      <div class="lg"><span class="sw ar"></span>${m.away.name}</div>
    </div>
    <canvas class="radar" id="radar" width="660" height="660"></canvas>
    <div class="stats">
      <div class="panel sc"><div class="l">AVG AGE</div><div class="row"><span class="v fr">${m.home.avg_age}</span><span class="x">vs</span><span class="v ar">${m.away.avg_age}</span></div></div>
      <div class="panel sc"><div class="l">SQUAD VALUE</div><div class="row"><span class="v fr">${fmtValue(m.home.squad_value_eur_m)}</span><span class="x">vs</span><span class="v ar">${fmtValue(m.away.squad_value_eur_m)}</span></div></div>
      <div class="panel sc"><div class="l">TOP-5 LEAGUE</div><div class="row"><span class="v fr">${m.home.players_top5_leagues}</span><span class="x">vs</span><span class="v ar">${m.away.players_top5_leagues}</span></div></div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  },
  mount(el, m) {
    const AXES = ['Attack', 'Midfield', 'Value', 'Experience', 'Defense'];
    const fr = window.WCF.ratings(m.home);
    const ar = window.WCF.ratings(m.away);
    const cv = el.querySelector('#radar');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    const W = cv.width, cx = W / 2, cy = W / 2 + 4, R = 196, n = AXES.length;
    const ang = i => -Math.PI / 2 + i * (2 * Math.PI / n);
    ctx.clearRect(0, 0, W, W);

    for (let r = 1; r <= 4; r++) {
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = ang(i % n), rr = R * r / 4;
        const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(255,255,255,.10)'; ctx.lineWidth = 1; ctx.stroke();
    }
    for (let i = 0; i < n; i++) {
      const a = ang(i);
      ctx.beginPath(); ctx.moveTo(cx, cy);
      ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
      ctx.strokeStyle = 'rgba(255,255,255,.10)'; ctx.stroke();
    }
    function poly(vals, stroke, fill) {
      ctx.beginPath();
      vals.forEach((v, i) => {
        const a = ang(i), rr = R * v / 100;
        const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = fill; ctx.fill();
      ctx.strokeStyle = stroke; ctx.lineWidth = 4; ctx.stroke();
      vals.forEach((v, i) => {
        const a = ang(i), rr = R * v / 100;
        ctx.beginPath(); ctx.arc(cx + rr * Math.cos(a), cy + rr * Math.sin(a), 6, 0, 7);
        ctx.fillStyle = stroke; ctx.fill();
      });
    }
    poly(ar, '#9ed1ff', 'rgba(158,209,255,.16)');
    poly(fr, '#3a6fe0', 'rgba(58,111,224,.24)');

    ctx.font = '700 24px Archivo, sans-serif';
    ctx.fillStyle = '#cdd9ee'; ctx.textBaseline = 'middle';
    AXES.forEach((tx, i) => {
      const a = ang(i), lr = R + 34;
      const x = cx + lr * Math.cos(a), y = cy + lr * Math.sin(a);
      ctx.textAlign = Math.abs(Math.cos(a)) < 0.3 ? 'center' : (Math.cos(a) > 0 ? 'left' : 'right');
      ctx.fillText(tx, x, y);
    });
  }
};
