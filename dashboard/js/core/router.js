/* Điều hướng, thanh bộ lọc toàn cục, khởi động */
FS.pages = {};
FS.NAV = [
  ['command', 'Trung tâm Điều hành', 'layout-dashboard'],
  ['incident_intel', 'Quản lý Sự cố', 'alert-triangle'],
  ['supply_chain', 'Vật tư & Truy xuất', 'package'],
  ['priority', 'Ưu tiên & Hành động', 'star'],
  ['admin', 'Quản trị & Dữ liệu', 'settings'],
];
FS.go = function () {
  if (!FS.auth.cur()) return;
  const key = (location.hash.slice(2) || 'command').split('?')[0], pg = FS.pages[key] || FS.pages.command, root = FS.ui.$('#view');
  FS.ui.$$('.nav a').forEach(a => a.classList.toggle('on', a.dataset.k === key));
  FS.ui.$('#title').textContent = pg.title; FS.ui.$('#subtitle').textContent = pg.sub;
  FS.ui.$('#filters').style.display = pg.noFilter ? 'none' : '';
  root.classList.remove('in'); root.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';
  requestAnimationFrame(() => setTimeout(() => { try { root.innerHTML = ''; pg.render(root); FS.ui.countUp(root); } catch (e) { console.error(e); root.innerHTML = `<div class="card"><h3>Lỗi hiển thị</h3><p>${FS.ui.esc(e.message)}</p><button class="btn" onclick="FS.go()">Thử lại</button></div>`; } root.classList.add('in'); }, 40));
};
FS.drill = (title, cols, rows, exportName) => { const m = FS.ui.modal(title, '<div id="drill"></div>', true); FS.ui.table(FS.ui.$('#drill', m.el), { cols, rows, export: exportName || 'drill', pageSize: 8 }); };
FS.boot = function () {
  const u = FS.ui; u.$('#nav').innerHTML = FS.NAV.map(n => n[0] === '__d' ? `<div class="nav-sep">${n[1]}</div>` : `<a href="#/${n[0]}" data-k="${n[0]}"><i data-lucide="${n[2]}"></i>${n[1]}</a>`).join('');
  if (window.lucide) lucide.createIcons();
  FS.loadBundle();
  const st = FS.tables.dim_station.filter(s => s.station_id !== 'x');
  u.$('#f-station').innerHTML = '<option value="">Tất cả máy/công đoạn</option>' + st.map(s => `<option value="${s.station_id}">${s.station_id} · ${u.esc(s.station_name)}</option>`).join('');
  ['from', 'to', 'station', 'status', 'q'].forEach(k => { const el = u.$('#f-' + k); el.value = FS.state[k]; el.addEventListener(k === 'q' ? 'input' : 'change', e => { FS.state[k] = e.target.value; clearTimeout(FS._d); FS._d = setTimeout(FS.go, 200); }); });
  u.$$('.date-presets .chip').forEach(c => c.onclick = () => {
    const days = +c.dataset.range, to = new Date(FS.NOW), from = new Date(FS.NOW - (days - 1) * 864e5);
    const fmt = d => d.toISOString().slice(0, 10);
    FS.state.from = fmt(from); FS.state.to = fmt(to);
    u.$('#f-from').value = FS.state.from; u.$('#f-to').value = FS.state.to;
    u.$$('.date-presets .chip').forEach(x => x.classList.toggle('on', x === c));
    FS.go();
  });
  u.$('#f-reset').onclick = () => { Object.assign(FS.state, { from: '2026-09-29', to: '2026-10-10', station: '', status: '', q: '' }); ['from', 'to', 'station', 'status', 'q'].forEach(k => u.$('#f-' + k).value = FS.state[k]); FS.go(); };
  u.$('#menu').onclick = () => { if (window.innerWidth <= 860) document.body.classList.toggle('nav-open'); else document.body.classList.toggle('side-collapsed'); };
  window.addEventListener('hashchange', () => { document.body.classList.remove('nav-open'); FS.go(); });
  u.$('#gs').onkeydown = e => { if (e.key !== 'Enter') return; const v = e.target.value.trim().toUpperCase(); if (!v) return; e.target.value = '';
    if (/^(LOT|BATCH|MAT)/.test(v)) location.hash = '#/genealogy?lot=' + v; else if (/^INC/.test(v)) location.hash = '#/impact?inc=' + v;
    else if (/^JT/.test(v)) { const r = FS.engine.impactAll().find(r => r.jts.some(x => x.jt.jt_id === v)) || { inc: { incident_id: 'INC-0001' } }; location.hash = '#/impact?inc=' + r.inc.incident_id; }
    else { FS.state.q = v; u.$('#f-q').value = v; location.hash = '#/incidents'; FS.go(); } };
  u.$('#bell').onclick = () => { const L = FS.tables.incident_truth.filter(i => ['CRITICAL', 'HIGH'].includes(i.severity_level)).slice(-6).reverse(); u.modal('Cảnh báo sự cố nghiêm trọng', L.map(i => `<div class="act"><div>${u.sev(i.severity_level)}</div><div><b>${i.incident_id} · ${i.station_id}</b><br><small>${FS.fmt.d(i.start_time)} · ${i.duration_h}h · ${i.fmea_code}</small></div><a class="sp" href="#/impact?inc=${i.incident_id}" onclick="document.querySelector('.modal-bg').remove()">Phân tích →</a></div>`).join('')); };
  FS.auth.init(() => FS.go());
};
window.addEventListener('DOMContentLoaded', () => { try { FS.boot(); } catch (e) { document.body.innerHTML = '<pre style="padding:24px">' + e.message + '</pre>'; } });
