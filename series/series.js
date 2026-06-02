/* ============================================================
   WORLD CUP 2026 SERIES — viewer + radar + AI prediction
   ============================================================ */
(function () {
  const deck   = document.getElementById('deck');
  const posts  = Array.from(document.querySelectorAll('.post'));
  const prevB  = document.getElementById('prev');
  const nextB  = document.getElementById('next');
  const cnum   = document.getElementById('cnum');
  const dotsEl = document.getElementById('dots');
  const N = posts.length;
  let radarDrawn = false, predicted = false;
  const pad2 = n => String(n + 1).padStart(2, '0');

  /* ---------- scaling ---------- */
  function fit() {
    const m = 88; // room for side arrows
    const s = Math.min((innerWidth - m) / 1080, (innerHeight - 24) / 1350);
    deck.style.transform = `scale(${s})`;
  }
  addEventListener('resize', fit); fit();

  /* ---------- dots ---------- */
  posts.forEach((_, i) => {
    const d = document.createElement('span');
    d.className = 'dot' + (i === 0 ? ' on' : '');
    d.addEventListener('click', () => go(i));
    dotsEl.appendChild(d);
  });
  const dots = Array.from(dotsEl.children);

  /* ---------- navigation ---------- */
  let idx = parseInt(localStorage.getItem('wc26-idx') || '0', 10);
  if (isNaN(idx) || idx < 0 || idx >= N) idx = 0;

  function go(n) {
    idx = (n + N) % N;
    posts.forEach((p, i) => p.classList.toggle('active', i === idx));
    dots.forEach((d, i) => d.classList.toggle('on', i === idx));
    cnum.textContent = pad2(idx) + ' / ' + String(N).padStart(2, '0');
    localStorage.setItem('wc26-idx', String(idx));
    if (idx === 4) drawRadar();
    if (idx === 7) runPrediction();
  }
  prevB.addEventListener('click', () => go(idx - 1));
  nextB.addEventListener('click', () => go(idx + 1));
  addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') go(idx - 1);
    if (e.key === 'ArrowRight') go(idx + 1);
  });
  go(idx);

  /* ============================================================
     RADAR CHART (slide 5)
     ============================================================ */
  // radial order: Attack(top) → Midfield → Value → Experience → Defense
  const AXES = ['Attack', 'Midfield', 'Value', 'Experience', 'Defense'];
  const FR   = [92, 85, 95, 78, 88];
  const AR   = [88, 90, 82, 92, 80];

  function drawRadar() {
    const cv = document.getElementById('radar');
    if (!cv || radarDrawn) return;
    radarDrawn = true;
    const ctx = cv.getContext('2d');
    const W = cv.width, cx = W / 2, cy = W / 2 + 4, R = 196;
    const n = AXES.length;
    const ang = i => -Math.PI / 2 + i * (2 * Math.PI / n);
    ctx.clearRect(0, 0, W, W);

    // grid rings
    for (let r = 1; r <= 4; r++) {
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = ang(i % n), rr = R * r / 4;
        const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(255,255,255,.10)';
      ctx.lineWidth = 1; ctx.stroke();
    }
    // spokes
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
        const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
        ctx.beginPath(); ctx.arc(x, y, 6, 0, 7); ctx.fillStyle = stroke; ctx.fill();
      });
    }
    poly(AR, '#9ed1ff', 'rgba(158,209,255,.16)');
    poly(FR, '#3a6fe0', 'rgba(58,111,224,.24)');

    // labels
    ctx.font = '700 24px Archivo, sans-serif';
    ctx.fillStyle = '#cdd9ee';
    AXES.forEach((t, i) => {
      const a = ang(i), lr = R + 34;
      let x = cx + lr * Math.cos(a), y = cy + lr * Math.sin(a);
      ctx.textBaseline = 'middle';
      ctx.textAlign = Math.abs(Math.cos(a)) < 0.3 ? 'center' : (Math.cos(a) > 0 ? 'left' : 'right');
      ctx.fillText(t, x, y);
    });
  }

  /* ============================================================
     AI PREDICTION (slide 8) — graceful fallback if unavailable
     ============================================================ */
  async function runPrediction() {
    if (predicted) return;
    predicted = true;
    const whyEl = document.getElementById('ai-why');
    if (!whyEl || !(window.claude && window.claude.complete)) return; // keep static fallback
    const original = whyEl.textContent;
    whyEl.style.opacity = '.55';
    whyEl.textContent = 'Reading the match…';
    const prompt = `You are a sharp, concise football pundit. Group B, Match 3 of the 2026 World Cup: France vs Argentina at SoFi Stadium.
Context: France 3 pts (must win), Argentina 4 pts (a draw tops the group). They last met in the 2022 final (3-3, Argentina won on penalties).
Give a one-sentence, punchy match read (max 28 words, no emoji, present tense) explaining who edges it and why. Reply with the sentence only.`;
    try {
      const out = await window.claude.complete(prompt);
      const clean = (out || '').trim().replace(/^["']|["']$/g, '');
      whyEl.textContent = clean.length > 12 ? clean : original;
    } catch (e) {
      whyEl.textContent = original;
    }
    whyEl.style.opacity = '1';
  }

  drawRadar(); // ensure the chart paints even before navigation
})();
