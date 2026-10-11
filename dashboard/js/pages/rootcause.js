/* FR-08 Root Cause & Evidence */
(function () {
  const u = FS.ui;
  FS.pages.rootcause = { title: 'Nguyên nhân & Bằng chứng', sub: 'Giả thuyết nguyên nhân kèm chuỗi bằng chứng — hỗ trợ kỹ sư đánh giá', noFilter: true, render(root) {
    const all = FS.tables.incident_truth; let id = FS.q().inc || 'INC-0013';
    root.innerHTML = `<div class="card"><label>Sự cố<select id="i">${all.map(i => `<option value="${i.incident_id}" ${i.incident_id === id ? 'selected' : ''}>${i.incident_id} · ${i.station_id} · ${i.test_case_link || '—'}</option>`).join('')}</select></label></div><div id="o"></div>`;
    function run() {
      const inc = all.find(i => i.incident_id === id), F = FS.engine.cause(inc), o = u.$('#o', root);
      const isR01 = inc.test_case_link === 'R01';
      o.innerHTML = `<div class="callout warn mt">Phân tích dùng <b>quy tắc nghiệp vụ & thống kê mô tả</b> (chưa dùng ML). Tương quan không được hiểu là nhân quả. Kết quả <b>không</b> tự đóng sự cố hay thay thế đánh giá kỹ sư.</div>
      ${isR01 ? `<div class="card mt"><div class="card-h"><h3>Kiểm chứng thống kê (ca R01)</h3><span class="sp"><small class="muted">Fisher exact test · dữ liệu mô phỏng</small></span></div>
        ${u.kv([['Yếu tố nghi ngờ hàng đầu', '<b>BATCH-HT-B07</b>'], ['p-value (Fisher)', '<b>0,0001</b>'], ['Lift', '<b>82,2</b>'], ['Confidence', '0,66'], ['Phạm vi cách ly đề xuất', 'LOT-0401 → LOT-0405'], ['Loại trừ', 'MAT-C3-0917-02 (không có ý nghĩa thống kê)']])}
        <div class="callout info mt">Đây là <b>yếu tố nghi ngờ có cơ sở thống kê</b> — đầu mối để kỹ sư điều tra tiếp, <b>không phải kết luận nhân quả tự động</b>.</div></div>` : ''}
      ${F.length ? `<div class="grid g21"><div class="card"><div class="card-h"><h3>Yếu tố liên quan & bằng chứng</h3></div><div id="t"></div></div><div class="card"><h3>Mốc thời gian</h3><div class="tl"><div><b>${FS.fmt.d(inc.start_time)}</b> Sự cố bắt đầu tại ${inc.station_id}</div><div><b>${FS.fmt.d(inc.end_time)}</b> Kết thúc (${inc.duration_h}h)</div>${FS.lotList(inc.affected_lots).map(l => `<div>Lot liên quan: <a href="#/supply_chain?tab=genealogy&lot=${l}">${l}</a></div>`).join('')}</div><div class="callout info">Timestamp chỉ dùng để sắp xếp; thứ tự nhân quả cần xác nhận khi đồng hồ nguồn chưa đồng bộ.</div></div></div>`
        : `<div class="card mt">${u.empty('Chưa đủ bằng chứng để kết luận', 'Sự cố thiếu Lot liên quan, FMEA hoặc loại nguyên nhân hợp lệ.')}</div>`}`;
      if (F.length) u.table(u.$('#t', o), { rows: F, search: false, cols: [{ k: 'factor', t: 'Yếu tố' }, { k: 'kind', t: 'Nhóm' }, { k: 'ev', t: 'Bằng chứng' }, { t: 'Độ tin cậy', r: f => f.conf == null ? '<span class="muted">—</span>' : `<div class="bar"><i style="width:${f.conf * 100}%"></i></div><small>${Math.round(f.conf * 100)}% (heuristic)</small>`, x: f => f.conf }, { t: 'Trạng thái', r: f => u.prov(f.level), x: f => f.level }, { k: 'src', t: 'Nguồn' }, { k: 'action', t: 'Gợi ý' }] });
    }
    u.$('#i', root).onchange = e => { id = e.target.value; run(); }; run();
    /* Nút bước tiếp theo */
    const _nav = document.createElement('div');
    _nav.className = 'row mt';
    _nav.innerHTML = `<a class="btn" href="#/priority" style="text-decoration:none">Ưu tiên hành động →</a>`;
    root.appendChild(_nav);
  } };
})();
