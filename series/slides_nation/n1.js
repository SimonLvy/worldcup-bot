/* ============================================================
   NATION — slide 1 (id "n1") · IDENTITY
   Hero flag, name + nickname, confederation + group + FIFA rank,
   WC appearances + best finish + honours one-liner.
     m = { post_type:"nation", tla, code, name, nickname,
           confederation, group_letter, fifa_rank,
           federation_crest, colors, wc_appearances,
           wc_best_finish, is_first_wc, honours, ... }
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.n1 = (function () {
  function ordinal(n) {
    n = parseInt(n, 10);
    if (!n || isNaN(n)) return '';
    const v = n % 100;
    if (v >= 11 && v <= 13) return n + 'th';
    const last = n % 10;
    return n + (last === 1 ? 'st' : last === 2 ? 'nd' : last === 3 ? 'rd' : 'th');
  }

  return {
    render(m) {
      const { up, esc, flag } = window.WCF;

      const crest = m.federation_crest
        ? `<img class="n1-crest" src="${esc(m.federation_crest)}" alt=""
             onerror="this.style.display='none'" />`
        : '';

      // Hero flag — flagcdn high-res, drop shadow set in CSS.
      const heroFlag = flag(m.code || 'un', 'n1-flag');

      // Eyebrow chips line: CONF · Group X · FIFA #N
      const chips = [];
      if (m.confederation) chips.push(esc(up(m.confederation)));
      if (m.group_letter)  chips.push('Group ' + esc(up(m.group_letter)));
      if (m.fifa_rank)     chips.push('FIFA #' + esc(m.fifa_rank));
      const chipsLine = chips.length
        ? `<div class="n1-chips">${chips.join('<span class="n1-sep">·</span>')}</div>`
        : '';

      // Heritage block — appearance + best finish, OR a centered first-WC badge.
      let heritage;
      if (m.is_first_wc) {
        heritage = `<div class="n1-firstwc">FIRST WORLD CUP APPEARANCE</div>`;
      } else {
        const lines = [];
        if (m.wc_appearances) {
          lines.push(`<div class="n1-line">${esc(ordinal(m.wc_appearances))} World Cup appearance</div>`);
        }
        if (m.wc_best_finish) {
          lines.push(`<div class="n1-line muted">Best: ${esc(m.wc_best_finish)}</div>`);
        }
        // Honours one-liner — JS will trim from the right in mount() if it overflows.
        const honours = Array.isArray(m.honours) ? m.honours.filter(h => h && h.label) : [];
        const honoursHTML = honours.length
          ? `<div class="n1-honours">${honours.map((h, i) =>
              `<span class="n1-honour" data-idx="${i}">${esc(h.label)} <em>× ${esc(h.count)}</em></span>`
            ).join('<span class="n1-honour-sep">·</span>')}</div>`
          : '';
        heritage = lines.join('') + honoursHTML;
      }

      return `
      <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
      ${crest}

      <div class="n1-top">
        <div class="n1-eyebrow"><span class="n-dot"></span>NATION SHOWCASE</div>
      </div>

      <div class="n1-body">
        <div class="n1-flag-wrap">${heroFlag}</div>
        <h1 class="n1-name">${up(m.name || '')}</h1>
        ${m.nickname ? `<div class="n1-nick">${esc(m.nickname)}</div>` : ''}
        ${chipsLine}
        <div class="n1-heritage">${heritage}</div>
      </div>

      <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
    },

    mount(el) {
      // Trim honours from the right until they fit ~980px on one line.
      // Preserve order (WC always first); the trailing separator is auto-hidden.
      const wrap = el.querySelector('.n1-honours');
      if (!wrap) return;
      const max = 980;
      const items = Array.from(wrap.querySelectorAll('.n1-honour'));
      const seps  = Array.from(wrap.querySelectorAll('.n1-honour-sep'));
      // measure on next frame so flag image hasn't shifted layout
      requestAnimationFrame(() => {
        while (wrap.scrollWidth > max && items.length > 1) {
          const drop = items.pop();
          const sep  = seps.pop();
          if (drop) drop.remove();
          if (sep)  sep.remove();
        }
      });
    }
  };
})();
