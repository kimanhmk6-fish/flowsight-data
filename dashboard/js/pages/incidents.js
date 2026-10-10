/* FR-02 Incident Monitoring */
(function () {
  const u = FS.ui;
  function detail(i) {
    const fm = FS.idx.fmea.get(i.fmea_code), a = FS.T(i.start_time), b = FS.T(i.end_time), calc = (b - a) / 36e5, flags = [];
    if (i.duration_h != null && Math.abs(calc - i.duration_h) > .01) flags.push('duration_h lệch với (end − start): ' + FS.fmt.n(calc) + 'h');
    if (!i.start_time || !i.station_id) flags.push('Thiếu thời điểm hoặc khóa máy');
    const dup = FS.tables.incident_truth.filter(x => x.station_id === i.station_id && x.start_time === i.start_time && x.incident_id !== i.incident_id); if (dup.length) flags.push('Nhiều bản ghi cùng máy/thời điểm: ' + dup.map(d => d.incident_id).join(', ') + ' → cần đối soát');
    const st = FS.engine.incStatus(i), m = u.modal('Chi tiết ' + i.incident_id, `${u.kv([['Máy / Line', `${i.station_id} · ${(FS.idx.station.get(i.station_id) || {}).station_name || '—'} · line ${(FS.idx.station.get(i.station_id) || {}).line_id || '—'}`], ['Bắt đầu', FS.fmt.d(i.start_time)], ['Kết thúc', st === 'Đang mở' && b > FS.NOW ? 'Đang mở' : FS.fmt.d(i.end_time)], ['Thời gian dừng', `${i.duration_h} h — tính từ ${i.start_time} → ${i.end_time}`], ['Mức độ', u.sev(i.severity_level)], ['Loại nguyên nhân', i.root_cause_type], ['FMEA', fm ? `${fm.fmea_code} · ${fm.fmea_description} (RPN ${fm.rpn})` : (i.fmea_code + ' — không có trong registry')], ['Lot liên quan', FS.lotList(i.affected_lots).join(', ') || 'Chưa đủ dữ liệu liên kết'], ['Nguồn', 'incident_truth.csv · ' + u.prov('Pilot')]])}
      ${flags.length ? `<div class="callout warn"><b>Cần đối soát:</b><ul>${flags.map(f => `<li>${f}</li>`).join('')}</ul></div>` : '<div class="callout ok">Bản ghi hợp lệ: đủ khóa và mốc thời gian, thời lượng khớp.</div>'}
      <div class="row"><label>Cập nhật trạng thái xử lý <select id="ss">${['Đang mở', 'Đang xử lý', 'Đã đóng'].map(s => `<option ${s === st ? 'selected' : ''}>${s}</option>`).join('')}</select></label><button class="btn sm" id="sv">Lưu</button><a class="btn sm ghost" href="#/impact?inc=${i.incident_id}" style="text-decoration:none">Phân tích tác động →</a><a class="btn sm ghost" href="#/propagation?inc=${i.incident_id}" style="text-decoration:none">Lan truyền →</a></div>`);
    u.$('#sv', m.el).onclick = () => { if (!FS.auth.need('decide')) return; FS.wf.inc[i.incident_id] = u.$('#ss', m.el).value; FS.wf.hist.unshift({ t: new Date().toISOString().slice(0, 19), what: i.incident_id + ' → ' + u.$('#ss', m.el).value }); FS.saveWf(); m.close(); u.toast('Đã cập nhật trạng thái'); FS.go(); };
  }
  FS.pages.incidents = { title: 'Incident Monitoring', sub: 'Danh sách, chi tiết và truy vết mốc thời gian sự cố', render(root) {
    const incs = FS.engine.incidents(), open = incs.filter(i => FS.engine.incStatus(i) !== 'Đã đóng');
    root.innerHTML = `<div class="grid g4">${u.kpi({ label: 'Tổng sự cố', value: incs.length, icon: '⚠', color: 'red' })}${u.kpi({ label: 'Chưa đóng', value: open.length, icon: '◐', color: 'amber' })}${u.kpi({ label: 'Tổng giờ dừng', value: incs.reduce((s, i) => s + (i.duration_h || 0), 0), unit: 'h', icon: '⏱', color: 'blue', def: 'Σ duration_h trong bộ lọc' })}${u.kpi({ label: 'Thiếu Lot liên quan', value: incs.filter(i => !i.affected_lots).length, icon: '?', color: 'violet', sub: 'Không tạo liên kết suy đoán', def: 'Sự cố không có affected_lots' })}</div>
    <div class="card mt"><div class="card-h"><h3>Danh sách sự cố</h3><small>Bấm dòng để xem chi tiết & cập nhật trạng thái</small></div><div id="t"></div></div>
    <div class="card mt"><div class="card-h"><h3>Lịch sử thay đổi trạng thái</h3></div>${FS.wf.hist.slice(0, 8).map(h => `<div class="tl"><div><b>${h.what}</b> <small>${h.t}</small></div></div>`).join('') || '<small class="muted">Chưa có thay đổi.</small>'}</div>`;
    u.table(u.$('#t', root), { rows: incs, export: 'danh_sach_su_co', onRow: detail, cols: [...FS.pages.command.incCols, { k: 'fmea_code', t: 'FMEA' }, { k: 'root_cause_type', t: 'Nguyên nhân' }, { t: 'Lot', r: r => FS.lotList(r.affected_lots).length || '<span class="muted">—</span>', x: r => FS.lotList(r.affected_lots).length }] });
  } };
})();
