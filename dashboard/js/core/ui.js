/* Thành phần giao diện dùng chung: KPI, bảng (tìm/sắp xếp/phân trang/xuất), modal, toast, biểu đồ SVG */
FS.ui = (function () {
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const badge = (t, c = 'gray', i = '') => `<span class="badge b-${c}">${i ? `<i>${i}</i>` : ''}${esc(t)}</span>`;
  const prov = p => ({ 'Đã xác nhận': badge('Đã xác nhận', 'green', '✔'), 'Suy luận': badge('Suy luận', 'amber', '≈'), 'Chưa đủ dữ liệu': badge('Chưa đủ dữ liệu', 'gray', '?'), 'Mâu thuẫn': badge('Mâu thuẫn', 'red', '≠'), 'Pilot': badge('Pilot Testing', 'blue', '◇'), 'Giả thuyết': badge('Giả thuyết', 'amber', '≈'), 'Ước tính một phần': badge('Ước tính một phần', 'amber', '≈'), 'Đủ dữ liệu': badge('Đủ dữ liệu', 'green', '✔') }[p] || badge(p));
  const sev = s => ({ CRITICAL: badge('Nghiêm trọng', 'red', '▲'), HIGH: badge('Cao', 'red', '▲'), MEDIUM: badge('Trung bình', 'amber', '●'), LOW: badge('Thấp', 'green', '▼'), UNKNOWN: badge('Không rõ', 'gray', '?') }[s] || badge(s));
  const stat = s => badge(s, { 'Đang mở': 'red', 'Đang xử lý': 'amber', 'Đã đóng': 'green' }[s] || 'gray', { 'Đang mở': '●', 'Đang xử lý': '◐', 'Đã đóng': '✔' }[s] || '');
  function toast(msg, type = 'ok') { const t = document.createElement('div'); t.className = 'toast t-' + type; t.textContent = msg; $('#toasts').appendChild(t); setTimeout(() => t.classList.add('out'), 2600); setTimeout(() => t.remove(), 3100); }
  function modal(title, html, wide) { const m = document.createElement('div'); m.className = 'modal-bg'; m.innerHTML = `<div class="modal ${wide ? 'wide' : ''}" role="dialog" aria-label="${esc(title)}"><div class="modal-h"><h3>${esc(title)}</h3><button class="icon-btn" aria-label="Đóng">✕</button></div><div class="modal-b">${html}</div></div>`;
    const close = () => { m.classList.add('out'); setTimeout(() => m.remove(), 180); }; m.onclick = e => { if (e.target === m) close(); }; $('.icon-btn', m).onclick = close; document.body.appendChild(m); return { el: m, close }; }
  function kpi(o) { return `<div class="card kpi ${o.click ? 'click' : ''}" ${o.click ? `data-kpi="${o.click}" tabindex="0"` : ''} title="${esc(o.def || '')}">
    <div class="kpi-ic c-${o.color || 'blue'}">${o.icon || '◆'}</div><div class="kpi-b"><div class="kpi-l">${esc(o.label)}</div>
    <div class="kpi-v">${o.nodata ? '<span class="nodata">Chưa đủ dữ liệu</span>' : `<span data-count="${o.value}">${FS.fmt.n(o.value)}</span><small>${esc(o.unit || '')}</small>`}</div>
    <div class="kpi-s">${o.sub || ''}</div><div class="kpi-d">${esc(o.def || '')}</div></div></div>`; }
  function countUp(root) { $$('[data-count]', root).forEach(el => { const v = +el.dataset.count; if (!isFinite(v) || Math.abs(v) > 1e7) return; const t0 = performance.now(); (function f(t) { const k = Math.min(1, (t - t0) / 700), e = 1 - Math.pow(1 - k, 3); el.textContent = FS.fmt.n(v * e); if (k < 1) requestAnimationFrame(f); else el.textContent = FS.fmt.n(v); })(t0); }); }
  /* Bảng: cols [{k,t,r(row)->html,s(row)->sortvalue,x(row)->text export}] */
  function table(el, o) {
    let q = '', sk = null, sd = 1, pg = 0; const ps = o.pageSize || 10;
    function draw() {
      let rows = o.rows.filter(r => !q || o.cols.some(c => String(c.x ? c.x(r) : r[c.k] ?? '').toLowerCase().includes(q)));
      if (sk != null) { const c = o.cols[sk], g = r => c.s ? c.s(r) : r[c.k]; rows = rows.slice().sort((a, b) => (g(a) > g(b) ? 1 : g(a) < g(b) ? -1 : 0) * sd); }
      const pages = Math.max(1, Math.ceil(rows.length / ps)); pg = Math.min(pg, pages - 1);
      el.innerHTML = `<div class="tbl-bar">${o.search === false ? '' : `<input class="search" placeholder="Tìm trong bảng…" value="${esc(q)}" aria-label="Tìm trong bảng">`}<span class="muted">${rows.length} bản ghi</span>${o.export ? `<button class="btn sm ghost" data-ex>⭳ Xuất CSV</button>` : ''}</div>
      <div class="tbl-wrap"><table class="tbl"><thead><tr>${o.cols.map((c, i) => `<th data-i="${i}" class="${sk === i ? 'sorted' : ''}">${c.t}${sk === i ? (sd > 0 ? ' ▲' : ' ▼') : ''}</th>`).join('')}</tr></thead>
      <tbody>${rows.length ? rows.slice(pg * ps, pg * ps + ps).map((r, i) => `<tr data-r="${pg * ps + i}" class="${o.onRow ? 'click' : ''}">${o.cols.map(c => `<td>${c.r ? c.r(r) : esc(r[c.k] ?? '—')}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${o.cols.length}" class="empty">${o.empty || 'Không có bản ghi trong phạm vi bộ lọc'}</td></tr>`}</tbody></table></div>
      ${pages > 1 ? `<div class="pager"><button class="btn sm ghost" data-p="-1" ${pg ? '' : 'disabled'}>‹</button><span>Trang ${pg + 1}/${pages}</span><button class="btn sm ghost" data-p="1" ${pg < pages - 1 ? '' : 'disabled'}>›</button></div>` : ''}`;
      const s = $('.search', el); if (s) { s.oninput = e => { q = e.target.value.toLowerCase(); pg = 0; const p = e.target.selectionStart; draw(); const n = $('.search', el); n.focus(); n.setSelectionRange(p, p); }; }
      $$('th', el).forEach(th => th.onclick = () => { const i = +th.dataset.i; sd = sk === i ? -sd : 1; sk = i; draw(); });
      $$('[data-p]', el).forEach(b => b.onclick = () => { pg += +b.dataset.p; draw(); });
      if (o.onRow) $$('tr[data-r]', el).forEach(tr => tr.onclick = () => o.onRow(rows[+tr.dataset.r]));
      const ex = $('[data-ex]', el); if (ex) ex.onclick = () => FS.csv.download(o.export + '.csv', FS.csv.stringify(rows.map(r => Object.fromEntries(o.cols.map(c => [c.t.replace(/<[^>]+>/g, ''), c.x ? c.x(r) : r[c.k]])))));
    }
    draw(); return { redraw: draw };
  }
  const C = { blue: '#2f6bff', cyan: '#18b8d9', green: '#20b26b', amber: '#f5a524', red: '#ef4444', violet: '#7c5cff', gray: '#94a3b8' }, PAL = [C.blue, C.cyan, C.green, C.amber, C.red, C.violet, C.gray];
  function line(o) { // o: {labels, series:[{name,vals,color,dash}], bars:{vals,color,name}, h}
    const W = 640, H = o.h || 240, p = { l: 44, r: 12, t: 14, b: 28 }, n = o.labels.length, all = o.series.flatMap(s => s.vals).concat(o.bars ? o.bars.vals : []); const mx = Math.max(1, ...all) * 1.12;
    const x = i => p.l + (n < 2 ? 0 : i * (W - p.l - p.r) / (n - 1)), y = v => p.t + (H - p.t - p.b) * (1 - v / mx); let g = '';
    for (let k = 0; k <= 4; k++) { const v = mx * k / 4; g += `<line x1="${p.l}" x2="${W - p.r}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${p.l - 6}" y="${y(v) + 4}" class="ax" text-anchor="end">${FS.fmt.n(v)}</text>`; }
    o.labels.forEach((l, i) => { if (n <= 12 || i % Math.ceil(n / 12) === 0) g += `<text x="${x(i)}" y="${H - 8}" class="ax" text-anchor="middle">${l}</text>`; });
    if (o.bars) { const bw = Math.min(18, (W - p.l - p.r) / n / 2); o.bars.vals.forEach((v, i) => { if (v) g += `<rect x="${x(i) - bw / 2}" width="${bw}" y="${y(v)}" height="${y(0) - y(v)}" fill="${o.bars.color}" rx="3" opacity=".85"><title>${o.bars.name}: ${v}</title></rect>`; }); }
    o.series.forEach((s, si) => { const d = s.vals.map((v, i) => `${i ? 'L' : 'M'}${x(i)},${y(v)}`).join(''); if (s.area) g += `<path d="${d}L${x(n - 1)},${y(0)}L${x(0)},${y(0)}Z" fill="${s.color}" opacity=".08"/>`;
      g += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2.4" ${s.dash ? 'stroke-dasharray="6 4"' : ''} class="draw"/>` + s.vals.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="3.2" fill="#fff" stroke="${s.color}" stroke-width="2"><title>${s.name} ${o.labels[i]}: ${FS.fmt.n(v)}</title></circle>`).join(''); });
    const lg = o.series.concat(o.bars ? [{ name: o.bars.name, color: o.bars.color }] : []).map(s => `<span><i style="background:${s.color}"></i>${s.name}</span>`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="${esc(o.title || 'Biểu đồ')}">${g}</svg><div class="legend">${lg}</div>`;
  }
  function donut(items, center) { const tot = items.reduce((s, i) => s + i.v, 0) || 1; let a = -Math.PI / 2, r = 70, ir = 46, d = '';
    items.forEach((it, i) => { const b = a + it.v / tot * Math.PI * 2 - (items.length > 1 ? .02 : 0), big = b - a > Math.PI ? 1 : 0, c = PAL[i % PAL.length];
      if (items.length === 1) d += `<circle cx="90" cy="90" r="${(r + ir) / 2}" fill="none" stroke="${c}" stroke-width="${r - ir}"/>`; else d += `<path d="M${90 + r * Math.cos(a)},${90 + r * Math.sin(a)}A${r},${r} 0 ${big} 1 ${90 + r * Math.cos(b)},${90 + r * Math.sin(b)}L${90 + ir * Math.cos(b)},${90 + ir * Math.sin(b)}A${ir},${ir} 0 ${big} 0 ${90 + ir * Math.cos(a)},${90 + ir * Math.sin(a)}Z" fill="${c}" class="seg"><title>${it.k}: ${it.v}</title></path>`; a += it.v / tot * Math.PI * 2; });
    return `<div class="donut"><svg viewBox="0 0 180 180">${d}<text x="90" y="86" text-anchor="middle" class="dn">${center ?? tot}</text><text x="90" y="104" text-anchor="middle" class="ax">Tổng</text></svg><ul>${items.map((it, i) => `<li><i style="background:${PAL[i % PAL.length]}"></i>${esc(it.k)}<b>${Math.round(it.v / tot * 100)}%</b></li>`).join('')}</ul></div>`; }
  function bars(items, unit = '') { const mx = Math.max(1, ...items.map(i => i.v)); return `<div class="hbars">${items.map(i => `<div class="hb"><span>${esc(i.k)}</span><div><b style="width:${i.v / mx * 100}%;background:${i.c || C.blue}"></b></div><em>${FS.fmt.n(i.v)}${unit}</em></div>`).join('')}</div>`; }
  const kv = (rows) => `<dl class="kv">${rows.map(r => `<dt>${esc(r[0])}</dt><dd>${r[1] ?? '—'}</dd>`).join('')}</dl>`;
  const empty = (t, s) => `<div class="empty-state"><div>○</div><b>${t}</b><p>${s || ''}</p></div>`;
  return { esc, $, $$, badge, prov, sev, stat, toast, modal, kpi, countUp, table, line, donut, bars, kv, empty, C };
})();
