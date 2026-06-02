/* ============================================================
   COUNTDOWN — single hero slide (id "c1")
   Reads the post dict (m) the engine exposes from window.__post.

   m = {
     post_id, post_type:"countdown",
     days_to_kickoff:9, days_label:"9 DAYS TO GO",
     kickoff_date:"2026-06-11", kickoff_date_label:"JUNE 11, 2026",
     bg_color_top:"#2D1B4E", bg_color_bottom:"#5A1B7A"
   }

   The big number is the hero (~50%+ of the height). Background gradient is
   per-day (top → bottom). J-0 (kickoff day) gets the premium glow treatment.
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCSlides.c1 = {
  render(m) {
    const { up, esc } = window.WCF;
    const d = window.WCF.num(m.days_to_kickoff);
    const isKick = d === 0;

    // label suffix derived from the count (singular / plural / kickoff)
    const label = isKick ? 'KICKOFF DAY' : (d === 1 ? 'DAY TO GO' : 'DAYS TO GO');
    const dateLabel = up(m.kickoff_date_label || '');

    const top = m.bg_color_top || '#17345f';
    const bot = m.bg_color_bottom || '#08152a';

    // hero: word "TODAY" on kickoff day, otherwise the number
    const heroCls = isKick ? 'cd-num word' : ('cd-num' + (d >= 10 ? ' two' : ''));
    const hero = isKick ? 'TODAY' : String(d);

    return `
    <div class="cd-bg" style="background:linear-gradient(180deg, ${esc(top)} 0%, ${esc(bot)} 100%);"></div>
    <div class="cd-bg cd-bg-fx"></div>
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />

    <div class="cd-wrap${isKick ? ' kick' : ''}" data-cd-d="${d}">
      <div class="cd-eyebrow"><span class="cd-dot"></span>COUNTDOWN${isKick ? ' · IT\u2019S HERE' : ''}</div>
      <div class="cd-hero">
        <div class="${heroCls}">${hero}</div>
      </div>
      <div class="cd-foot">
        <div class="cd-label">${label}</div>
        <div class="cd-date">KICKOFF&nbsp;·&nbsp;${dateLabel}</div>
        <div class="cd-brand">
          <img class="wc-logo" src="assets/logo_wc2026.png" alt="" />
          <div class="cd-cap">WORLD CUP 2026</div>
        </div>
      </div>
    </div>`;
  },

  /* Preview-only day switcher — lets you flip through the palette during review.
     Mutates this slide's DOM in place; never runs in capture mode, so the
     Python pipeline output is unaffected. */
  mount(el, m) {
    if (window.WC && window.WC.mode === 'capture') return;
    if (document.body.classList.contains('capture')) return;

    // Representative palette: J-11 → J-0 (Python supplies the real colours per post).
    const PAL = [
      { d: 11, top: '#16335c', bot: '#081428' }, // navy
      { d: 10, top: '#26285c', bot: '#0c0b26' }, // indigo
      { d: 9,  top: '#2D1B4E', bot: '#5A1B7A' }, // violet
      { d: 8,  top: '#14492f', bot: '#061b12' }, // green
      { d: 7,  top: '#1c3d86', bot: '#081634' }, // royal blue
      { d: 6,  top: '#7a3a12', bot: '#2e1405' }, // orange
      { d: 5,  top: '#6e1a52', bot: '#2a0a1f' }, // magenta
      { d: 4,  top: '#0d4a5e', bot: '#041d26' }, // teal
      { d: 3,  top: '#7a1c1f', bot: '#2c0a0b' }, // red
      { d: 2,  top: '#5a3a1a', bot: '#231405' }, // bronze
      { d: 1,  top: '#2b2f36', bot: '#0d1014' }, // charcoal
      { d: 0,  top: '#000000', bot: '#241a05' }  // kickoff: black → trophy gold
    ];

    const apply = (p) => {
      const isKick = p.d === 0;
      const label = isKick ? 'KICKOFF DAY' : (p.d === 1 ? 'DAY TO GO' : 'DAYS TO GO');
      el.querySelector('.cd-bg:not(.cd-bg-fx)').style.background =
        `linear-gradient(180deg, ${p.top} 0%, ${p.bot} 100%)`;
      const wrap = el.querySelector('.cd-wrap');
      wrap.classList.toggle('kick', isKick);
      el.querySelector('.cd-eyebrow').innerHTML =
        '<span class="cd-dot"></span>COUNTDOWN' + (isKick ? ' · IT\u2019S HERE' : '');
      const hero = el.querySelector('.cd-num');
      hero.className = isKick ? 'cd-num word' : ('cd-num' + (p.d >= 10 ? ' two' : ''));
      hero.textContent = isKick ? 'TODAY' : String(p.d);
      el.querySelector('.cd-label').textContent = label;
    };

    const bar = document.createElement('div');
    bar.className = 'cd-switch';
    bar.title = 'Preview only — flip through the daily palette';
    PAL.forEach((p) => {
      const b = document.createElement('button');
      b.textContent = p.d === 0 ? '0' : 'J-' + p.d;
      b.dataset.d = p.d;
      if (window.WCF.num(m.days_to_kickoff) === p.d) b.classList.add('on');
      b.addEventListener('click', () => {
        bar.querySelectorAll('button').forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        apply(p);
      });
      bar.appendChild(b);
    });
    document.body.appendChild(bar);
  }
};
