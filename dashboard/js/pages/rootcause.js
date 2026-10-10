/* FR-08 Root Cause & Evidence */
(function () {
  const u = FS.ui;
  FS.pages.rootcause = { title: 'Nguyên nhân & Bằng chứng', sub: 'Giả thuyết nguyên nhân kèm chuỗi bằng chứng — hỗ trợ kỹ sư đánh giá', noFilter: true, render(root) {
    const all = FS.tables.incident_truth; let id = FS.q().inc || 'INC-0013';
    root.innerHTML = `<div class="card"><label>Sự cố<select id="i">${all.map(i => `<option value="${i.incident_id}" ${i.incident_id === id ? 'selected' : ''}>${i.incident_id} · ${i.station_id} · ${i.root_cause_type}</option>`).join('')}</select></label></div><div id="o"></div>`;
    function run() {
      const inc = all.find(i => i.incident_id === id), F = FS.engine.cause(inc), o = u.$('#o', root);
      o.innerHTML = `<div class="callout warn mt">Phân tích dùng <b>quy tắc nghiệp vụ & thống kê mô tả</b> (chưa dùng ML). Tương quan không được hiểu là nhân quả. Kết quả <b>không</b> tự đóng sự cố hay thay thế đánh giá kỹ sư.</div>
      ${F.length ? `<div class="grid g21"><div class="card"><div class="card-h"><h3>Yếu tố liên quan & bằng chứng</h3></div><div id="t"></div></div><div class="card"><h3>Mốc thời gian</h3><div class="tl"><div><b>${FS.fmt.d(inc.start_time)}</b> Sự cố bắt đầu tại ${inc.station_id}</div><div><b>${FS.fmt.d(inc.end_time)}</b> Kết thúc (${inc.duration_h}h)</div>${FS.lotList(inc.affected_lots).map(l => `<div>Lot liên quan: <a href="#/genealogy?lot=${l}">${l}</a></div>`).join('')}</div><div class="callout info">Timestamp chỉ dùng để sắp xếp; thứ tự nhân quả cần xác nhận khi đồng hồ nguồn chưa đồng bộ.</div></div></div>`
        : `<div class="card mt">${u.empty('Chưa đủ bằng chứng để kết luận', 'Sự cố thiếu Lot liên quan, FMEA hoặc loại nguyên nhân hợp lệ.')}</div>`}`;
      if (F.length) u.table(u.$('#t', o), { rows: F, search: false, cols: [{ k: 'factor', t: 'Yếu tố' }, { k: 'kind', t: 'Nhóm' }, { k: 'ev', t: 'Bằng chứng' }, { t: 'Độ tin cậy', r: f => f.conf == null ? '<span class="muted">—</span>' : `<div class="bar"><i style="width:${f.conf * 100}%"></i></div><small>${Math.round(f.conf * 100)}% (heuristic)</small>`, x: f => f.conf }, { t: 'Trạng thái', r: f => u.prov(f.level), x: f => f.level }, { k: 'src', t: 'Nguồn' }, { k: 'action', t: 'Gợi ý' }] });
    }
    u.$('#i', root).onchange = e => { id = e.target.value; run(); }; run();
  } };
})();
