/* FR-12 Kiến trúc & Cấu hình + bộ ca kiểm thử (NFR-08) */
(function () {
  const u = FS.ui;
  const RULES = [['R-LINK-01', 'Liên kết suy luận JT↔sự cố: cùng line, hạn giao trong 72h sau sự cố'], ['R-IMP-01', 'Giờ mất = giao (dừng, lịch SX)'], ['R-IMP-02', 'Mất SL = giờ mất × công suất tham chiếu'], ['R-IMP-03', 'FG khả dụng = snapshot FG gần nhất × %khả dụng; không cộng WIP'], ['R-IMP-04', 'Exposure JT = deficit − công suất bù × thời gian đến hạn'], ['R-QUA-01', 'Khóa trùng đánh giá theo cấp dữ liệu'], ['R-CAU-01', 'Lô vật tư chung của mọi Lot bị ảnh hưởng → giả thuyết vật tư']];
  const tests = () => {
    const I = FS.tables.incident_truth, T = [], t = (n, f) => { try { const r = f(); T.push([n, r === true, r === true ? '' : String(r)]); } catch (e) { T.push([n, false, e.message]); } };
    t('TC-01 Dữ liệu đầy đủ → có thiếu hụt ròng hữu hạn', () => { const r = FS.engine.impact(I[0]); return isFinite(r.net) && r.status !== 'Chưa đủ dữ liệu' || r.net; });
    t('TC-02 Thiếu dữ liệu (máy không có công suất) → "Chưa đủ dữ liệu"', () => { const r = FS.engine.impact({ incident_id: 'X', station_id: 'NOPE', start_time: '2026-10-01T08:00:00', end_time: '2026-10-01T16:00:00', duration_h: 8 }); return r.status === 'Chưa đủ dữ liệu' && r.lostQty == null && r.net == null; });
    t('TC-03 Khóa trùng bị phát hiện', () => FS.quality('incident_truth', [I[0], I[0]]).issues.some(i => i.type === 'Uniqueness'));
    t('TC-04 Quan hệ không tìm thấy (Lot không tồn tại)', () => FS.quality('incident_truth', [{ ...I[0], incident_id: 'T', affected_lots: 'LOT-9999' }]).issues.some(i => i.type === 'Referential'));
    t('TC-05 Chỉ tính giờ trong lịch SX (INC-0008: 16:00→00:00 = 6h)', () => { const r = FS.engine.impact(I.find(i => i.incident_id === 'INC-0008')); return FS.config.schedEnd !== 22 || Math.abs(r.lostH - 6) < .01 || 'lostH=' + r.lostH; });
    t('TC-06 Tái lập: cùng đầu vào → cùng kết quả', () => JSON.stringify(FS.engine.impact(I[0]).steps) === JSON.stringify(FS.engine.impact(I[0]).steps));
    t('TC-07 Không đếm trùng JT trong một sự cố', () => { const r = FS.engine.impact(I[0]); return new Set(r.jts.map(x => x.jt.jt_id)).size === r.jts.length; });
    t('TC-08 Lot ID lặp trong bảng sự kiện không bị coi là khóa trùng', () => FS.quality('production_truth', FS.tables.production_truth.slice(0, 200)).issues.every(i => i.type !== 'Uniqueness'));
    t('TC-09 Sự cố không có Lot → nhánh "Chưa đủ dữ liệu liên kết"', () => FS.engine.graph(I.find(i => !i.affected_lots)).nodes.some(n => n.type === 'Chưa đủ dữ liệu'));
    return T;
  };
  FS.pages.architecture = { title: 'Kiến trúc & Cấu hình', sub: 'Sơ đồ lớp dữ liệu, tham số tính toán, quy tắc nghiệp vụ và ca kiểm thử', noFilter: true, render(root) {
    const C = FS.config, N = FS.tables;
    root.innerHTML = `<div class="card"><div class="card-h"><h3>Sơ đồ kiến trúc</h3><span class="sp">${u.badge('Cấu hình ' + C.version, 'blue')}</span></div><div class="arch">
      <div class="lay"><h4>1 · Nguồn dữ liệu</h4>${['dim_station / routing / bom', 'production_truth', 'canonical_lots · genealogy', 'inventory · material', 'jt_order · allocation', 'qc_truth · incident', 'shipment_truth'].map(x => `<div class="it">${x}</div>`).join('')}</div>
      <div class="lay"><h4>2 · Chuẩn hóa & Kiểm tra</h4><div class="it">CSV parser (UTF-8)</div><div class="it">Auto-mapping tên cột</div><div class="it">Data Quality (6 chiều)</div><div class="it">Entity mapping (1.640 khóa nguồn)</div></div>
      <div class="lay"><h4>3 · Mô hình quan hệ</h4><div class="it">Incident → Station → Lot</div><div class="it">Lot → Material · Genealogy</div><div class="it">Lot → JT → Shipment</div><div class="it">Nhãn: xác nhận / suy luận</div></div>
      <div class="lay"><h4>4 · Phân tích & Giao diện</h4><div class="it">engine.js: Impact · Graph · Cause</div><div class="it">Dashboard · Báo cáo · Validation</div><div class="it">Mở rộng: API / kho dữ liệu</div></div></div>
      <p class="muted">Dữ liệu hiện có: ${Object.keys(N).map(k => `${k} (${N[k].length})`).join(' · ')}</p></div>
    <div class="card mt"><div class="card-h"><h3>Tham số tính toán</h3><span class="sp"><button class="btn" id="sv">Lưu cấu hình</button></span></div><div class="cfg">
      ${[['schedStart', 'Giờ bắt đầu ca SX'], ['schedEnd', 'Giờ kết thúc ca SX'], ['fgUsablePct', '% tồn FG khả dụng'], ['thHigh', 'Ngưỡng rủi ro Cao (%)'], ['thMid', 'Ngưỡng Trung bình (%)'], ['wShort', 'Trọng số: thiếu hụt'], ['wSlack', 'Trọng số: slack'], ['wLink', 'Trọng số: liên kết'], ['wBreadth', 'Trọng số: lan truyền'], ['wConf', 'Trọng số: tin cậy dữ liệu']].map(([k, l]) => `<label>${l}<input type="number" data-c="${k}" value="${C[k]}"></label>`).join('')}
      <label class="row"><input type="checkbox" id="th" ${C.thresholdOn ? 'checked' : ''}> Áp dụng ngưỡng dung sai quy định (Tolerance Threshold)</label><label class="row"><input type="checkbox" id="ur" ${C.useRecovery ? 'checked' : ''}> Dùng công suất bù</label></div>
      <h4 class="mt">Lịch sử thay đổi</h4>${C.changelog.slice(0, 6).map(c => `<div class="tl"><div>${c.t} · ${u.esc(c.note)}</div></div>`).join('') || '<small class="muted">Chưa có thay đổi.</small>'}<p class="muted" style="font-size:12px">Cấu hình lưu trong trình duyệt (localStorage) — không phải kho bảo mật; triển khai thật cần xác thực, phân quyền và nhật ký truy cập.</p></div>
    <div class="grid g2 mt"><div class="card"><h3>Quy tắc nghiệp vụ</h3><div id="rl"></div></div><div class="card"><div class="card-h"><h3>Ca kiểm thử</h3><span class="sp"><button class="btn" id="rt">▶ Chạy kiểm thử</button></span></div><div id="tr"><small class="muted">Bấm để chạy 9 ca: đủ dữ liệu, thiếu dữ liệu, khóa trùng, quan hệ không tìm thấy…</small></div></div></div>
    <div class="card mt"><h3>Phi chức năng — đáp ứng trong prototype</h3>${u.kv([['Hiệu năng', 'Đo thời gian render từng trang (xem console); lọc/đổi tab xử lý tại chỗ trên ~' + N.production_truth.length + ' dòng'], ['Explainability', 'Mọi KPI có định nghĩa; mọi liên kết có căn cứ; công thức mở rộng trong Impact'], ['Bảo mật', 'Dữ liệu xử lý hoàn toàn cục bộ trong trình duyệt, không gửi lên dịch vụ ngoài; chưa có xác thực (cần xác nhận)'], ['UX', 'Nền sáng, trạng thái loading/empty/error, trạng thái có icon (không chỉ màu), desktop & tablet'], ['Mở rộng', 'Schema, quy tắc, engine, giao diện tách tệp; thêm bảng bằng FS.SCHEMA']])}</div>`;
    root.insertAdjacentHTML('beforeend', FS.auth.panel());
    u.table(u.$('#rl', root), { rows: RULES.map(r => ({ id: r[0], d: r[1] })), cols: [{ k: 'id', t: 'Mã' }, { k: 'd', t: 'Mô tả' }], search: false, pageSize: 10 });
    u.$('#sv', root).onclick = () => { if (!FS.auth.need('config')) return; u.$$('[data-c]', root).forEach(i => C[i.dataset.c] = +i.value); C.thresholdOn = u.$('#th', root).checked; C.useRecovery = u.$('#ur', root).checked; FS.saveConfig('Cập nhật tham số từ trang Cấu hình'); u.toast('Đã lưu cấu hình'); FS.go(); };
    u.$('#rt', root).onclick = () => { const r = tests(); u.$('#tr', root).innerHTML = r.map(x => `<div class="act"><div>${x[1] ? u.badge('PASS', 'green', '✔') : u.badge('FAIL', 'red', '✕')}</div><div>${x[0]}${x[2] ? `<br><small>${u.esc(x[2])}</small>` : ''}</div></div>`).join('') + `<b>${r.filter(x => x[1]).length}/${r.length} đạt</b>`; };
  } };
})();
