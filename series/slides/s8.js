/* SLIDE 8 — PREDICTION & ENGAGEMENT
   - If match.prediction = {home_score, away_score, reasoning} is present (e.g. filled
     server-side by your Python Claude call), it is rendered directly — fully automatable.
   - In the live browser preview (no prediction in data) it falls back to window.claude. */
window.WCSlides.s8 = {
  render(m) {
    const o = m.odds || {};
    const min = Math.min(o.home_win, o.draw, o.away_win);
    const fav = val => (val === min ? ' fav' : '');
    const odd = (who, res, val) =>
      `<div class="panel o${fav(val)}"><div class="who">${who}</div><div class="res">${res}</div><div class="val">${val != null ? Number(val).toFixed(2) : '—'}</div></div>`;

    let verdict, reasoning;
    if (m.prediction) {
      verdict = `${m.home.name} <span class="score">${m.prediction.home_score} – ${m.prediction.away_score}</span> ${m.away.name}`;
      reasoning = m.prediction.reasoning || '';
    } else {
      const sc = (min === o.draw) ? '1 – 1' : (min === o.home_win) ? '2 – 1' : '1 – 2';
      verdict = `${m.home.name} <span class="score">${sc}</span> ${m.away.name}`;
      reasoning = 'Generating an AI read of this fixture…';
    }

    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="s-head">
      <div class="eyebrow"><span>THE CALL</span></div>
      <div class="title">Prediction</div>
    </div>
    <div class="odds">
      ${odd(m.home.name, 'HOME · 1', o.home_win)}
      ${odd('Draw', 'X', o.draw)}
      ${odd(m.away.name, 'AWAY · 2', o.away_win)}
    </div>
    <div class="odds-src">ODDS · ${o.source || 'BOOKMAKER'}</div>
    <div class="panel pred">
      <div class="hd">
        <svg class="spark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v6m0 8v6M2 12h6m8 0h6M5 5l4 4m6 6l4 4m0-14l-4 4m-6 6l-4 4"/></svg>
        AI MATCH READ
      </div>
      <div class="verdict">${verdict}</div>
      <div class="why" id="ai-why">${reasoning}</div>
    </div>
    <div class="cta">
      <div class="q">Your call?</div>
      <div class="pick"><div class="b">1</div><div class="b">X</div><div class="b">2</div></div>
      <div class="sub">Drop your score in the comments 👇</div>
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  },
  mount(el, m) {
    if (m.prediction) return;                       // data-driven: nothing to do
    const why = el.querySelector('#ai-why');
    if (!why) return;
    if (!(window.claude && window.claude.complete)) {
      why.textContent = `${m.home.name} hold the edge on paper — see the odds above.`;
      return;
    }
    const prompt = `You are a sharp, concise football pundit. ${m.competition}, Group ${m.group} Match ${m.match_number_in_group}: ${m.home.name} vs ${m.away.name} at ${m.venue.stadium}.
${m.home.name} ${m.home.group_points} pts, ${m.away.name} ${m.away.group_points} pts. Give one punchy sentence (max 28 words, present tense, no emoji) on who edges it and why. Sentence only.`;
    why.style.opacity = '.55';
    window.claude.complete(prompt).then(out => {
      const c = (out || '').trim().replace(/^["']|["']$/g, '');
      if (c.length > 12) why.textContent = c;
      why.style.opacity = '1';
    }).catch(() => {
      why.textContent = `${m.home.name} hold the edge on paper — see the odds above.`;
      why.style.opacity = '1';
    });
  }
};
