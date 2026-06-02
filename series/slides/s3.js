/* SLIDE 3 — STAKES
   Two modes, switched on match.stage:
     • "group"  → group standings table + qualification scenarios
     • anything else (knockout / round_of_16 / quarter_final / …) → full bracket
       with the two match teams shown big in a hero band.
*/
window.WCSlides.s3 = {
  render(m) {
    const knockout = m.stage && m.stage !== 'group';
    return knockout ? this.knockout(m) : this.group(m);
  },

  /* ---------------- GROUP ---------------- */
  group(m) {
    const { flag } = window.WCF;
    const hot = code => (code === m.home.code || code === m.away.code) ? ' class="hot"' : '';
    const gd = n => (n > 0 ? '+' + n : '' + n);
    const rows = (m.standings || []).map(r => `
      <tr${hot(r.code) ? ' class="hot"' : ''}>
        <td class="pos">${r.pos}</td>
        <td class="team"><div class="team-cell">${flag(r.code, 'mini')}<span>${r.name}</span></div></td>
        <td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td>
        <td>${gd(r.gd)}</td><td class="pts">${r.points}</td>
      </tr>`).join('');
    const scen = ((m.stakes && m.stakes.scenarios) || [])
      .map(s => `<li><span class="b"></span><span>${s}</span></li>`).join('');
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>GROUP ${m.group} · STANDINGS</span></div>
      <div class="title">The <em>Table</em></div>
    </div>
    <table class="standings">
      <thead><tr>
        <th></th><th class="team">TEAM</th>
        <th>P</th><th>W</th><th>D</th><th>L</th><th>GD</th><th>PTS</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="panel scen">
      <h4>QUALIFICATION SCENARIOS</h4>
      <ul>${scen}</ul>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  },

  /* ---------------- KNOCKOUT ---------------- */
  knockout(m) {
    const { flag } = window.WCF;
    const k = m.knockout || {};
    const b = k.bracket || {};
    const isHot = t => t && t.code && (t.code === m.home.code || t.code === m.away.code);
    const ab = t => (t && (t.short || (t.name ? t.name.slice(0, 3).toUpperCase() : null))) || 'TBD';

    const slot = t => `<div class="bslot${isHot(t) ? ' hot' : ''}">${t && t.code
      ? flag(t.code, 'mini') : '<span class="tbd"></span>'}<span class="ab">${ab(t)}</span></div>`;
    const match = pair => {
      const p = pair || [null, null];
      const hot = isHot(p[0]) && isHot(p[1]);
      return `<div class="bmatch${hot ? ' hot' : ''}">${slot(p[0])}${slot(p[1])}</div>`;
    };
    const col = arr => `<div class="bcol">${(arr || []).map(match).join('')}</div>`;
    const L = b.left || {}, R = b.right || {};

    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>KNOCKOUT STAGE</span></div>
      <div class="title">The <em>Bracket</em></div>
    </div>
    <div class="ko-round">${(k.round || 'KNOCKOUT').toUpperCase()}</div>
    <div class="ko-hero">
      <div class="kf">${flag(m.home.code)}<div class="kn">${m.home.name}</div></div>
      <div class="kvs">VS</div>
      <div class="kf">${flag(m.away.code)}<div class="kn">${m.away.name}</div></div>
    </div>
    <div class="broundlbls">
      <div class="rl">R16</div><div class="rl">QF</div><div class="rl">SF</div>
      <div class="rl f">FINAL</div>
      <div class="rl">SF</div><div class="rl">QF</div><div class="rl">R16</div>
    </div>
    <div class="bracket">
      <div class="bside left">${col(L.r16)}${col(L.qf)}${col(L.sf)}</div>
      <div class="bfinal">
        <div class="blbl">FINAL</div>
        ${match(b.final)}
        <img src="assets/logo_wc2026.png" alt="" />
      </div>
      <div class="bside right">${col(R.sf)}${col(R.qf)}${col(R.r16)}</div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
