/* SLIDE 2 — CITY & STADIUM */
window.WCSlides.s2 = {
  render(m) {
    const { flag, photo, fmtNum, fmtDateShort, wxIcon, cToF } = window.WCF;
    const v = m.venue, w = m.weather || {};
    const hasWx = w.temp_c != null;
    // Real forecast when we have it (the normal J-1 case). When Open-Meteo has
    // no data (a fixture previewed >16 days out, or an API failure), show the
    // kickoff time + a neutral note instead of a dash or a fabricated temp.
    const forecastCell = hasWx
      ? `<div class="panel cell wide">
          <div>
            <div class="l">FORECAST · ${fmtDateShort(m.kickoff_local)}</div>
            <div class="wxr">
              <div class="d">${w.summary || ''}${w.wind_kph != null ? ' · wind ' + w.wind_kph + ' kph' : ''}</div>
              ${m.kickoff_local_label ? `<div class="kt">Kickoff · <b>${m.kickoff_local_label}</b> local</div>` : ''}
            </div>
          </div>
          <div class="wx">${wxIcon(w.icon)}<div class="degs"><div class="deg">${w.temp_c}°C</div><div class="degf">${cToF(w.temp_c)}°F</div></div></div>
        </div>`
      : `<div class="panel cell wide">
          <div>
            <div class="l">KICKOFF · ${fmtDateShort(m.kickoff_local)}</div>
            <div class="wxr">
              ${m.kickoff_local_label ? `<div class="d"><b>${m.kickoff_local_label}</b> local time</div>` : ''}
              <div class="kt">Forecast closer to kickoff</div>
            </div>
          </div>
        </div>`;
    const mapInset = v.map_url
      ? `<img class="venue-map" src="${v.map_url}" alt="" />`
      : '';
    return `
    <img class="ghost-mark" src="assets/logo_wc2026.png" alt="" />
    ${mapInset}
    <div class="s-head">
      <div class="eyebrow"><span>THE VENUE</span>
        <span class="mf">${flag(m.home.code, 'mini')}${flag(m.away.code, 'mini')}</span>
      </div>
      <div class="title">${v.stadium}</div>
      <div class="lede">${v.city}, ${v.country} — host venue for this World Cup fixture.</div>
    </div>
    ${photo(v.image_url, 'stadium photo — drop here', 'stadium')}
    <div class="info">
      <div class="panel cell"><div class="l">HOST CITY</div><div class="v">${v.city}<br /><small>${v.country}</small></div></div>
      <div class="panel cell"><div class="l">CAPACITY</div><div class="v">${fmtNum(v.capacity)}<br /><small>seats</small></div></div>
      ${forecastCell}
    </div>
    <div class="footer compact"><img class="wc-logo" src="assets/logo_wc2026.png" alt="" /></div>`;
  }
};
