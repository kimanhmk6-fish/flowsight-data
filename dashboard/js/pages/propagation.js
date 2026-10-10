/* FR-04 Propagation Analysis: đồ thị lan truyền có phân loại quan hệ */
(function () {
  const u = FS.ui, COL = ['Incident', 'Máy/Công đoạn', 'Lot', 'Vật tư / Lot con', 'JT/Order', 'Giao hàng'], TC = { 'Incident': '#ef4444', 'Máy/Công đoạn': '#f5a524', 'Lot': '#20b26b', 'Vật tư': '#18b8d9', 'JT/Order': '#2f6bff', 'Giao hàng': '#7c5cff', 'Chưa đủ dữ liệu': '#94a3b8' };
  FS.pages.propagation = { title: 'Phân tích Lan truyền', sub: 'Truy vết lan truyền rủi ro: Sự cố → Máy → Lô → Vật tư → Đơn hàng → Giao hàng', noFilter: true, render(root) {
    const all = FS.tables.incident_truth; let id = FS.q().inc || 'INC-0005', kinds = { 'Trực tiếp': 1, 'Suy luận': 1, 'Chưa xác minh': 1 }, sel = null;
    function draw() {
      const inc = all.find(i => i.incident_id === id), G = FS.engine.graph(inc), cols = {}; G.nodes.forEach(n => (cols[n.col] = cols[n.col] || []).push(n));
      const X = c => 80 + c * 160, Y = (c, i, n) => 58 + i * 62 + (Math.max(...Object.values(cols).map(a => a.length)) - n) * 31, pos = {};
      Object.keys(cols).forEach(c => cols[c].forEach((n, i) => pos[n.id] = [X(+c), Y(+c, i, cols[c].length)]));
      const H = 100 + Math.max(...Object.values(cols).map(a => a.length)) * 62, st = { 'Trực tiếp': ['#2f6bff', ''], 'Suy luận': ['#f5a524', '6 4'], 'Chưa xác minh': ['#94a3b8', '2 4'] };
      const eds = G.edges.filter(e => kinds[e.kind]).map((e, i) => { const [x1, y1] = pos[e.f], [x2, y2] = pos[e.t]; return `<path d="M${x1 + 56},${y1}C${x1 + 100},${y1} ${x2 - 100},${y2} ${x2 - 56},${y2}" fill="none" stroke="${st[e.kind][0]}" stroke-width="2" stroke-dasharray="${st[e.kind][1]}" marker-end="url(#ar${e.kind[0]})" class="ge" data-e="${i}" style="cursor:pointer"><title>${e.kind}: ${e.basis}</title></path>`; }).join('');
      root.innerHTML = `<div class="card"><div class="row"><label>Sự cố<select id="i">${all.map(i => `<option value="${i.incident_id}" ${i.incident_id === id ? 'selected' : ''}>${i.incident_id} · ${i.station_id} · ${FS.lotList(i.affected_lots).length} Lot</option>`).join('')}</select></label>
        ${Object.keys(kinds).map(k => `<label class="row"><input type="checkbox" data-k="${k}" ${kinds[k] ? 'checked' : ''}> <span style="color:${st[k][0]};font-weight:700">${k === 'Trực tiếp' ? '━' : k === 'Suy luận' ? '╌' : '┄'}</span> ${k}</label>`).join('')}</div></div>
      <div class="grid g21 mt"><div class="card"><div class="card-h"><h3>Đồ thị lan truyền</h3><small>Chỉ hiển thị quan hệ có khóa dữ liệu hoặc quy tắc đã công bố</small></div><div class="graph"><svg width="${X(5) + 90}" height="${H}">
        <defs>${Object.entries(st).map(([k, v]) => `<marker id="ar${k[0]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="${v[0]}"/></marker>`).join('')}</defs>
        ${COL.map((c, i) => `<text x="${X(i)}" y="18" text-anchor="middle" class="ax" style="font-size:11px;fill:#8794ad;font-weight:700">${c.toUpperCase()}</text>`).join('')}${eds}
        ${G.nodes.map(n => { const [x, y] = pos[n.id]; return `<g class="gn ${sel === n.id ? 'sel' : ''}" data-n="${n.id}"><rect x="${x - 56}" y="${y - 20}" width="112" height="40" rx="10" fill="#fff" stroke="${TC[n.type]}" stroke-width="2"/><rect x="${x - 56}" y="${y - 20}" width="6" height="40" rx="3" fill="${TC[n.type]}"/><text x="${x + 2}" y="${y - 3}" text-anchor="middle" style="font-size:11.5px;font-weight:700;fill:#0f1b3d">${u.esc(n.label.length > 15 ? n.label.slice(0, 14) + '…' : n.label)}</text><text x="${x + 2}" y="${y + 11}" text-anchor="middle" style="font-size:9.5px;fill:#64748b">${n.type}</text></g>`; }).join('')}</svg></div></div>
        <div class="card" id="side"><h3>Chi tiết nút / liên kết</h3><p class="muted">Chọn một nút hoặc đường nối để xem thuộc tính, nguồn dữ liệu và căn cứ liên kết.</p></div></div>
      <div class="card mt"><div class="card-h"><h3>Danh sách liên kết & căn cứ</h3></div><div id="t"></div></div>`;
      const side = u.$('#side', root), show = h => side.innerHTML = '<h3>Chi tiết</h3>' + h;
      u.$('#i', root).onchange = e => { id = e.target.value; sel = null; draw(); };
      u.$$('[data-k]', root).forEach(c => c.onchange = () => { kinds[c.dataset.k] = c.checked ? 1 : 0; draw(); });
      u.$$('.gn', root).forEach(g => g.onclick = () => { const n = G.nodes.find(x => x.id === g.dataset.n); sel = n.id; u.$$('.gn', root).forEach(x => x.classList.toggle('sel', x === g)); const inE = G.edges.filter(e => e.t === n.id);
        show(u.kv([['Loại', n.type], ['ID', n.id], ...Object.entries(n.attrs).filter(([, v]) => v != null && v !== '').slice(0, 9).map(([k, v]) => [k, u.esc(v)]), ['Căn cứ liên kết', inE.map(e => `${u.prov(e.kind === 'Trực tiếp' ? 'Đã xác nhận' : e.kind === 'Suy luận' ? 'Suy luận' : 'Chưa đủ dữ liệu')} ${u.esc(e.basis)} <small>(${e.src})</small>`).join('<br>') || '—']])); });
      const vis = G.edges.filter(e => kinds[e.kind]); u.$$('.ge', root).forEach(p => p.onclick = () => { const e = vis[+p.dataset.e]; show(u.kv([['Từ', e.f], ['Đến', e.t], ['Loại quan hệ', e.kind], ['Căn cứ', u.esc(e.basis)], ['Nguồn', e.src]])); });
      u.table(u.$('#t', root), { rows: G.edges, export: 'lien_ket_' + id, pageSize: 8, cols: [{ k: 'f', t: 'Từ' }, { k: 't', t: 'Đến' }, { t: 'Quan hệ', r: e => u.badge(e.kind, e.kind === 'Trực tiếp' ? 'blue' : e.kind === 'Suy luận' ? 'amber' : 'gray'), x: e => e.kind }, { k: 'basis', t: 'Căn cứ' }, { k: 'src', t: 'Nguồn' }] });
    }
    draw();
  } };
})();
