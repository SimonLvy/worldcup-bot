/* SLIDE 1 — MATCH ANNOUNCEMENT (hero) */
window.WCSlides.s1 = {
  render(m) {
    const { flag, up, fmtDate } = window.WCF;
    const stage = m.stage === 'knockout'
      ? (m.knockout && m.knockout.round ? m.knockout.round.toUpperCase() : 'KNOCKOUT STAGE')
      : `GROUP ${m.group} · MATCH ${m.match_number_in_group}`;
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    <div class="pad">
      <div class="kick">${stage}</div>
      <div class="date">${fmtDate(m.kickoff_local)}</div>
      <div class="mid">
        <div class="flags">
          ${flag(m.home.code)}
          <div class="vs">VS</div>
          ${flag(m.away.code)}
        </div>
        <div class="names">
          <div class="name">${up(m.home.name)}</div>
          <div class="name">${up(m.away.name)}</div>
        </div>
        <div class="meta">
          <div class="lbl">KICKOFF · STADIUM</div>
          <div class="big"><b>${m.kickoff_utc_label || m.kickoff_local_label}</b>&nbsp;&nbsp;<b>·</b>&nbsp;&nbsp;${m.venue.stadium}</div>
          <div class="sub">${m.venue.city}, ${m.venue.country}</div>
        </div>
      </div>
    </div>
    <div class="footer">
      <img class="wc-logo" src="assets/logo_wc2026.png" alt="" />
      <div class="rule"></div>
      <div class="cap">MATCHDAY</div>
    </div>`;
  }
};
