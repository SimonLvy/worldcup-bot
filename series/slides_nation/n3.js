/* ============================================================
   NATION — slide 3 (id "n3") · GROUP FIXTURES + OUTLOOK
   Three matchday rows (J1/J2/J3) with date · UTC · flags · venue,
   then a predictor verdict block (quali % first, predicted round
   second, optional flavor line). Predictor numbers stay gold —
   the per-nation accent rules the rest of the carousel.
     m = { post_type:"nation", group_letter, tla, code, name, nickname,
           fixtures:[{kickoff_utc, opponent_tla, opponent_code,
                      opponent_name, venue, matchday}],
           quali_pct, predicted_round, caption_hook, ... }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.n3 = (function () {
  const MO3 = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  function parseUtc(iso) {
    // returns { dd, mon, hhmm } from "2026-06-16T19:00:00Z" (timezone-safe)
    if (!iso) return null;
    const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
    if (!m) return null;
    return { dd: parseInt(m[3], 10), mon: MO3[parseInt(m[2], 10) - 1], hhmm: m[4] + ':' + m[5] };
  }

  function venueShort(v) {
    if (!v) return '';
    // strip trailing "Stadium" / "Field" only when the prefix already reads as one
    return v.replace(/\s+Stadium$/i, '').replace(/\s+Field$/i, ' Field');
  }

  function fixtureRow(m, fx, i) {
    const { esc, flag, up } = window.WCF;
    const t = parseUtc(fx.kickoff_utc);
    const md = fx.matchday || (i + 1);
    const ourTLA = up(m.tla || '');
    const oppTLA = up(fx.opponent_tla || '');
    const ourCode = (m.code || '').toLowerCase();
    const oppCode = (fx.opponent_code || '').toLowerCase();

    const chip = `
      <div class="n3-chip">
        <span class="n3-md">J${esc(md)}</span>
        ${t ? `<span class="n3-dot">·</span>
               <span class="n3-date">${t.dd} ${t.mon}</span>
               <span class="n3-dot">·</span>
               <span class="n3-time">${t.hhmm}<small> UTC</small></span>` : ''}
      </div>`;

    const usSide  = `<div class="n3-team us">
        <span class="tla">${esc(ourTLA)}</span>
        ${ourCode ? flag(ourCode, 'mini') : ''}
      </div>`;
    const oppSide = `<div class="n3-team opp">
        ${oppCode ? flag(oppCode, 'mini') : ''}
        <span class="tla">${esc(oppTLA || 'TBD')}</span>
      </div>`;

    const venueLine = fx.venue
      ? `<div class="n3-venue" title="${esc(fx.venue)}">${esc(venueShort(fx.venue))}</div>`
      : '';

    return `
      <div class="n3-match">
        ${chip}
        <div class="n3-vs-row">
          ${usSide}
          <span class="n3-vs">VS</span>
          ${oppSide}
        </div>
        ${venueLine}
      </div>`;
  }

  return {
    render(m) {
      const { up, esc, num } = window.WCF;
      const fixtures = Array.isArray(m.fixtures) ? m.fixtures.slice(0, 3) : [];

      const fixturesHTML = fixtures.length
        ? `<div class="n3-list">${fixtures.map((f, i) => fixtureRow(m, f, i)).join('')}</div>`
        : `<div class="n3-empty"><div class="n3-empty-k">FIXTURES TBD</div></div>`;

      const groupTitle = m.group_letter
        ? `GROUP ${esc(up(m.group_letter))} FIXTURES`
        : 'GROUP FIXTURES';

      /* ---- PREDICTOR ---- */
      const qPct = num(m.quali_pct);
      const round = m.predicted_round ? up(m.predicted_round) : '';
      const nickname = m.nickname || m.name || 'them';
      const hook = m.caption_hook
        ? esc(m.caption_hook)
        : (round
            ? `The bot sees ${esc(nickname)} going to the ${esc(up(round))}.`
            : `The bot's outlook is brewing.`);

      const qualiRow = m.quali_pct != null
        ? `<div class="n3-prow">
             <span class="n3-plabel">Chance to escape Group ${esc(up(m.group_letter || ''))}</span>
             <span class="n3-pval">${qPct}<small>%</small></span>
           </div>` : '';
      const roundRow = round
        ? `<div class="n3-prow">
             <span class="n3-plabel">Pre-tournament prediction</span>
             <span class="n3-pval round">${esc(round)}</span>
           </div>` : '';

      return `
      <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />

      <div class="n3-head">
        <div class="n3-eyebrow"><span class="n-dot"></span>GROUP STAGE</div>
        <div class="n3-title">${esc(groupTitle)}</div>
      </div>

      ${fixturesHTML}

      <div class="n3-rule"></div>

      <div class="n3-predict">
        <div class="n3-peyebrow"><span class="g-dot"></span>PREDICTOR VERDICT</div>
        ${qualiRow}
        ${roundRow}
        <div class="n3-flavor">${hook}</div>
        <div class="n3-cta">Do you back the call?</div>
      </div>

      <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
    }
  };
})();
