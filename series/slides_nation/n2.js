/* ============================================================
   NATION — slide 2 (id "n2") · SQUAD & COACH
   Star player + players to watch (text only — no photos), coach
   and squad meta in a two-column row, last five WC finishes in a
   clean tabular two-column list.
     m = { post_type:"nation", star_player, players_to_watch,
           coach, squad_value_eur_m, avg_age,
           wc_history, is_first_wc, nickname, colors, ... }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.n2 = (function () {
  function metaLine(m) {
    const bits = [];
    const sp = m.star_player || {};
    if (sp.club) bits.push(sp.club);
    if (sp.stat) bits.push(sp.stat);
    return bits.join(' \u00b7 ');
  }

  return {
    render(m) {
      const { up, esc, flag, fmtValue, num } = window.WCF;

      const sp = m.star_player || {};
      const watch = Array.isArray(m.players_to_watch) ? m.players_to_watch.filter(Boolean) : [];
      const hasStar = !!sp.name;

      /* ------ STAR PLAYER ------ */
      const starBlock = hasStar ? `
        <div class="n2-block n2-star ${watch.length ? '' : 'expanded'}">
          <div class="n2-eyebrow"><span class="n-dot"></span>STAR PLAYER</div>
          <div class="n2-star-name">${esc(sp.name)}</div>
          ${metaLine(m) ? `<div class="n2-star-meta">${esc(metaLine(m))}</div>` : ''}
        </div>` : '';

      /* ------ PLAYERS TO WATCH ------ */
      const watchBlock = watch.length ? `
        <div class="n2-block n2-watch">
          <div class="n2-eyebrow"><span class="n-dot"></span>PLAYERS TO WATCH</div>
          <div class="n2-watch-list">${watch.map(esc).join('<span class="n2-watch-sep">·</span>')}</div>
        </div>` : '';

      /* ------ COACH + SQUAD row ------ */
      const c = m.coach || null;
      const coachCell = c && c.name ? `
        <div class="n2-cell">
          <div class="n2-eyebrow"><span class="n-dot"></span>COACH</div>
          <div class="n2-cell-v">
            <span>${esc(c.name)}</span>
            ${c.nationality_code ? flag(c.nationality_code, 'mini') : ''}
          </div>
        </div>` : '';

      const squadBits = [];
      if (num(m.squad_value_eur_m)) {
        squadBits.push(`<div class="n2-cell-row"><span class="k">Value</span><span class="v">${esc(fmtValue(m.squad_value_eur_m))}</span></div>`);
      }
      if (num(m.avg_age)) {
        squadBits.push(`<div class="n2-cell-row"><span class="k">Avg age</span><span class="v">${esc(m.avg_age)}</span></div>`);
      }
      const squadCell = squadBits.length ? `
        <div class="n2-cell">
          <div class="n2-eyebrow"><span class="n-dot"></span>SQUAD</div>
          <div class="n2-cell-v stack">${squadBits.join('')}</div>
        </div>` : '';

      const metaRow = (coachCell || squadCell) ? `
        <div class="n2-rule"></div>
        <div class="n2-meta-row">${coachCell}${squadCell}</div>
        <div class="n2-rule"></div>` : '';

      /* ------ LAST 5 WORLD CUPS ------ */
      const hist = Array.isArray(m.wc_history) ? m.wc_history.filter(h => h && h.year) : [];
      let history;
      if (!hist.length && m.is_first_wc) {
        history = `<div class="n2-firstwc">WRITING THEIR FIRST WC STORY</div>`;
      } else if (!hist.length) {
        history = '';
      } else {
        const rows = hist.slice(0, 5).map(h =>
          `<div class="n2-hrow">
             <span class="n2-hy">${esc(h.year)}</span>
             <span class="n2-hf">${esc(h.finish || '\u2014')}</span>
           </div>`).join('');
        history = `
          <div class="n2-eyebrow centered"><span class="n-dot"></span>LAST ${hist.length === 1 ? 'WORLD CUP' : (Math.min(hist.length, 5) + ' WORLD CUPS')}</div>
          <div class="n2-hlist">${rows}</div>`;
      }

      return `
      <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />

      <div class="n2-wrap">
        ${starBlock}
        ${watchBlock}
        ${metaRow}
        <div class="n2-history">${history}</div>
      </div>

      <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
    }
  };
})();
