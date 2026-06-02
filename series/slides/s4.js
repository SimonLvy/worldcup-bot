/* SLIDE 4 — HISTORY & FORM */
window.WCSlides.s4 = {
  render(m) {
    const { flag, fmtYear } = window.WCF;
    const h = m.head_to_head || {}, t = h.total || { home_wins: 0, draws: 0, away_wins: 0 };
    const tot = Math.max(1, t.home_wins + t.draws + t.away_wins);
    const pc = n => (n / tot * 100).toFixed(1) + '%';

    const meeting = row => {
      const parts = String(row.score || '').split('(');
      const main = parts[0].trim();
      const paren = parts[1] ? '(' + parts[1].trim() : '';
      let win;
      if (row.winner === 'draw') win = '<span class="wn">Draw</span>';
      else {
        const tm = row.winner === 'home' ? m.home : m.away;
        win = `${flag(tm.code, 'mini')}<span class="wn">${tm.name}</span>`;
      }
      return `<div class="mt">
        <div class="c">${row.competition}<small>${fmtYear(row.date)}</small></div>
        <div class="sc">${main}${paren ? `<small>${paren}</small>` : ''}</div>
        <div class="c r">${win}</div>
      </div>`;
    };

    const pips = arr => (arr || []).map(r => {
      const k = r.toUpperCase();
      const cls = k === 'W' ? 'w' : k === 'D' ? 'd' : 'l';
      return `<span class="pip ${cls}">${k}</span>`;
    }).join('');

    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>HEAD TO HEAD</span></div>
      <div class="title">History &amp; <em>Form</em></div>
    </div>
    <div class="panel h2h">
      <div class="row">
        <div class="side">${flag(m.home.code, 'mini')}<span class="nm">${m.home.name}</span></div>
        <div class="mid"><div class="lab">ALL-TIME</div><div class="draws">${t.draws} draws</div></div>
        <div class="side r">${flag(m.away.code, 'mini')}<span class="nm">${m.away.name}</span></div>
      </div>
      <div class="row">
        <div class="big" style="text-align:left">${t.home_wins}</div>
        <div></div>
        <div class="big" style="text-align:right">${t.away_wins}</div>
      </div>
      <div class="bar">
        <i class="seg-w" style="width:${pc(t.home_wins)}"></i>
        <i class="seg-d" style="width:${pc(t.draws)}"></i>
        <i class="seg-l" style="width:${pc(t.away_wins)}"></i>
      </div>
    </div>
    <div class="panel recent">
      <h4>LAST ${(h.last3 || []).length} MEETINGS</h4>
      ${(h.last3 || []).map(meeting).join('')}
    </div>
    <div class="form">
      <div class="panel fc"><div class="t">${flag(m.home.code, 'mini')}${m.home.name}<span class="s">LAST 5</span></div>
        <div class="pips">${pips(m.home.last5)}</div></div>
      <div class="panel fc"><div class="t">${flag(m.away.code, 'mini')}${m.away.name}<span class="s">LAST 5</span></div>
        <div class="pips">${pips(m.away.last5)}</div></div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
