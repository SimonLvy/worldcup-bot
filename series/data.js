/* ============================================================
   WORLD CUP 2026 SERIES — data helpers (window.WCF)
   Pure formatting + asset helpers shared by every slide module.
   Slide modules register into window.WCSlides.
   ============================================================ */
window.WCSlides = window.WCSlides || {};

window.WCF = (function () {
  const WD  = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  const MO  = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];
  const MO3 = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  const num = v => (typeof v === 'number' ? v : parseFloat(v) || 0);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const up = s => (s || '').toString().toUpperCase();
  const esc = s => (s == null ? '' : String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'));

  /* ---------- dates (timezone-safe: reads the calendar date in the string) ---------- */
  function ymd(iso) { return (iso || '').slice(0, 10).split('-').map(Number); }
  function weekday(iso) {
    const [y, m, d] = ymd(iso);
    return WD[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
  }
  function fmtDate(iso) {
    const [y, m, d] = ymd(iso);
    return `${weekday(iso)} · ${MO[m - 1]} ${d}, ${y}`;
  }
  function fmtDateShort(iso) {
    const [, m, d] = ymd(iso);
    return `${MO3[m - 1]} ${d}`;
  }
  function fmtYear(iso) { return ymd(iso)[0]; }

  /* ---------- numbers ---------- */
  const fmtNum = n => num(n).toLocaleString('en-US');
  function fmtValue(millionsEur) {
    const v = num(millionsEur);
    if (v >= 1000) return '€' + (v / 1000).toFixed(2).replace(/\.?0+$/, '') + 'B';
    return '€' + Math.round(v) + 'M';
  }

  /* ---------- assets ---------- */
  // Real flags via flagcdn (ISO 3166-1 alpha-2, lowercase). object-fit:cover in CSS.
  function flag(code, cls) {
    const c = (code || 'un').toLowerCase();
    const res = (cls || '').indexOf('mini') >= 0 ? 'w160' : 'w640';
    return `<img class="flag ${cls || ''}" src="https://flagcdn.com/${res}/${c}.png" alt="" />`;
  }
  // Photo slot: shows the URL if provided, else a labelled placeholder the user can fill.
  function photo(url, label, cls) {
    if (url) {
      return `<div class="ph ${cls || ''}" style="background-image:url('${esc(url)}');background-size:cover;background-position:center;"></div>`;
    }
    return `<div class="ph ${cls || ''}"><span class="ph-lbl">${esc(label || 'photo')}</span></div>`;
  }

  /* ---------- weather icon (clean line icons, not emoji) ---------- */
  function wxIcon(icon) {
    const k = (icon || 'sun').toLowerCase();
    const sun = `<svg class="wx-ico sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.3M12 19.1v2.3M2.6 12h2.3M19.1 12h2.3M5.1 5.1l1.6 1.6M17.3 17.3l1.6 1.6M18.9 5.1l-1.6 1.6M6.7 17.3l-1.6 1.6"/></svg>`;
    const cloud = `<svg class="wx-ico cloud" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.2 18.5h9.4a3.7 3.7 0 0 0 .3-7.38 5.2 5.2 0 0 0-9.97-1.3A4.1 4.1 0 0 0 7.2 18.5Z"/></svg>`;
    const rain = `<svg class="wx-ico rain" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.2 15.5h9.4a3.7 3.7 0 0 0 .3-7.38 5.2 5.2 0 0 0-9.97-1.3A4.1 4.1 0 0 0 7.2 15.5Z"/><path d="M9 18.4l-.9 2.1M12.4 18.4l-.9 2.1M15.8 18.4l-.9 2.1"/></svg>`;
    const partly = `<svg class="wx-ico partly" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8.5" cy="7.6" r="2.9"/><path d="M8.5 2.7v1.4M3.6 7.6H5M12 7.6h1.4M5 4.1l1 1M11 4.1l-1 1"/><path d="M9.3 18.8h7.4a3.2 3.2 0 0 0 .3-6.4 4.5 4.5 0 0 0-8.5-1.05A3.5 3.5 0 0 0 9.3 18.8Z" stroke="#c7d4e8"/></svg>`;
    if (k.indexOf('rain') >= 0 || k.indexOf('shower') >= 0 || k.indexOf('drizzle') >= 0) return rain;
    if (k.indexOf('part') >= 0) return partly;
    if (k.indexOf('cloud') >= 0 || k.indexOf('overcast') >= 0) return cloud;
    return sun;
  }

  /* ---------- temperature ---------- */
  const cToF = c => Math.round(c * 9 / 5 + 32);

  /* ---------- radar ratings ----------
     Uses team.ratings = {attack,midfield,value,experience,defense} (0–100) if present.
     Otherwise derives plausible proxies from fifa_rank / squad value / avg age so the
     chart is never flat. Order returned matches the radar axes. */
  function ratings(team) {
    if (team && team.ratings) {
      const r = team.ratings;
      return [r.attack, r.midfield, r.value, r.experience, r.defense].map(v => clamp(num(v), 0, 100));
    }
    const base  = clamp(100 - (num(team.fifa_rank) || 12) * 1.8, 62, 96);
    const value = clamp(58 + ((num(team.squad_value_eur_m) || 500) / 1100) * 40, 60, 98);
    const exp   = clamp(48 + ((num(team.avg_age) || 27) - 23) * 6, 55, 96);
    return [base + 4, base, value, exp, base - 3].map(v => clamp(Math.round(v), 0, 100));
  }

  /* ---------- background theme (per group / per knockout match) ----------
     12 dark jewel tones — one per group (A–L). Gold accent stays readable on all.
     Group matches share their group's colour; knockout matches alternate by a
     deterministic hash of match_id, so consecutive ties differ. */
  const THEMES = [
    ['#17345f', '#0e2346', '#08152a'], // A · navy
    ['#115450', '#0a3331', '#05201e'], // B · teal
    ['#29285f', '#181642', '#0c0b26'], // C · indigo
    ['#14492f', '#0c2e20', '#061b12'], // D · emerald
    ['#3a2566', '#241546', '#130c28'], // E · violet
    ['#1c3d86', '#112a5e', '#081634'], // F · royal blue
    ['#2b3d52', '#1a2937', '#0d1820'], // G · slate
    ['#4a2657', '#2d1739', '#180c20'], // H · plum
    ['#0d4a5e', '#082f3c', '#041d26'], // I · deep cyan
    ['#54243f', '#341628', '#1c0c17'], // J · wine
    ['#244a24', '#152e15', '#0a1a0a'], // K · forest
    ['#1f3a55', '#132636', '#08151f']  // L · steel blue
  ];
  function hashStr(s) {
    let h = 0;
    for (let i = 0; i < (s || '').length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    return Math.abs(h);
  }
  function themeFor(m) {
    let idx;
    if (m.post_type === 'stadium') idx = hashStr(m.stadium || m.city || '') % THEMES.length;
    else if (m.stage && m.stage !== 'group') idx = hashStr(m.match_id || m.knockout && m.knockout.round || '') % THEMES.length;
    else idx = ((m.group ? m.group.toUpperCase().charCodeAt(0) - 65 : 0) % THEMES.length + THEMES.length) % THEMES.length;
    const t = THEMES[idx] || THEMES[0];
    return `radial-gradient(125% 85% at 50% -12%, ${t[0]} 0%, ${t[1]} 42%, ${t[2]} 100%)`;
  }

  return { num, clamp, up, esc, weekday, fmtDate, fmtDateShort, fmtYear, fmtNum, fmtValue, flag, photo, wxIcon, cToF, ratings, themeFor };
})();
