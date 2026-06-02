/* ============================================================
   RENDER ENGINE
   - Reads match data from window.__match (injected by Playwright)
     or falls back to fetching match.example.json (live preview).
   - Builds the configured slides into #deck via the module registry.
   - mode=preview  → scaled stage, arrows + dots, one slide visible.
   - mode=capture  → full-size slides stacked, no chrome (for screenshots).
   - window.WC.ready becomes true once everything (incl. images) is settled.
   ============================================================ */
(function () {
  const params = new URLSearchParams(location.search);
  const mode = params.get('mode') || 'preview';
  const deck = document.getElementById('deck');
  const order = (window.WC_CONFIG && window.WC_CONFIG.slides) || Object.keys(window.WCSlides || {});
  const lbl = i => String(i + 1).padStart(2, '0');

  window.WC = { ready: false, data: null, mode: mode };

  function buildSlides(m) {
    deck.innerHTML = '';
    // per-group / per-match background theme
    if (window.WCF && window.WCF.themeFor) deck.style.setProperty('--bg', window.WCF.themeFor(m));
    order.forEach((id, i) => {
      const mod = window.WCSlides[id];
      if (!mod) { console.warn('No slide module for id', id); return; }
      const el = document.createElement('section');
      el.className = 'post';
      el.id = id;
      el.setAttribute('data-screen-label', lbl(i));
      el.innerHTML = mod.render(m);
      deck.appendChild(el);
      if (mod.mount) { try { mod.mount(el, m); } catch (e) { console.error('mount ' + id, e); } }
    });
    window.WC.slideIds = Array.from(deck.querySelectorAll('.post')).map(p => p.id);
  }

  function waitImages() {
    const imgs = Array.from(deck.querySelectorAll('img'));
    return Promise.all(imgs.map(im => im.complete
      ? Promise.resolve()
      : new Promise(res => { im.onload = im.onerror = res; })));
  }

  async function getData() {
    if (window.__match) return window.__match;
    try { const r = await fetch('match.example.json'); return await r.json(); }
    catch (e) { console.error('No match data and example fetch failed', e); return null; }
  }

  /* ---------- PREVIEW: scale + nav ---------- */
  function previewSetup() {
    const posts = Array.from(deck.querySelectorAll('.post'));
    const N = posts.length;
    const prevB = document.getElementById('prev');
    const nextB = document.getElementById('next');
    const cnum = document.getElementById('cnum');
    const dotsEl = document.getElementById('dots');

    function fit() {
      const s = Math.min((innerWidth - 88) / 1080, (innerHeight - 24) / 1350);
      deck.style.transform = `scale(${s})`;
    }
    addEventListener('resize', fit); fit();

    dotsEl.innerHTML = '';
    posts.forEach((_, i) => {
      const d = document.createElement('span');
      d.className = 'dot' + (i === 0 ? ' on' : '');
      d.addEventListener('click', () => go(i));
      dotsEl.appendChild(d);
    });
    const dots = Array.from(dotsEl.children);

    let idx = parseInt(localStorage.getItem('wc26-idx') || '0', 10);
    if (isNaN(idx) || idx < 0 || idx >= N) idx = 0;

    function go(n) {
      idx = (n + N) % N;
      posts.forEach((p, i) => p.classList.toggle('active', i === idx));
      dots.forEach((d, i) => d.classList.toggle('on', i === idx));
      cnum.textContent = lbl(idx) + ' / ' + String(N).padStart(2, '0');
      localStorage.setItem('wc26-idx', String(idx));
    }
    prevB.onclick = () => go(idx - 1);
    nextB.onclick = () => go(idx + 1);
    addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') go(idx - 1);
      if (e.key === 'ArrowRight') go(idx + 1);
    });
    go(idx);
  }

  (async () => {
    const m = await getData();
    window.WC.data = m;
    if (!m) return;
    if (mode === 'capture') document.body.classList.add('capture');
    buildSlides(m);
    if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (e) {} }
    await waitImages();
    if (mode !== 'capture') previewSetup();
    // tiny settle for canvas paint
    await new Promise(r => setTimeout(r, 60));
    window.WC.ready = true;
    document.documentElement.setAttribute('data-wc-ready', '1');
  })();
})();
