/* FR-05 Lot Genealogy */
(function () {
  const u = FS.ui;
  function trace(lot) {
    const I = FS.idx, rel = [], seen = new Set();
    (function up(l, d) { if (seen.has('u' + l) || d > 4) return; seen.add('u' + l); (I.parentOf.get(l) || []).forEach(e => { rel.push({ dir: 'Truy ngược', type: 'Lot cha (' + e.edge_type + ')', id: e.parent_lot_id, qty: e.qty, time: e.true_time, src: 'genealogy_truth', lvl: 'Đã xác nhận' }); up(e.parent_lot_id, d + 1); }); })(lot, 0);
    (function down(l, d) { if (seen.has('d' + l) || d > 4) return; seen.add('d' + l); (I.childOf.get(l) || []).forEach(e => { rel.push({ dir: 'Truy xuôi', type: 'Lot con (' + e.edge_type + ')', id: e.child_lot_id, qty: e.qty, time: e.true_time, src: 'genealogy_truth', lvl: 'Đã xác nhận' }); down(e.child_lot_id, d + 1); }); })(lot, 0);
    const lots = [lot, ...rel.map(r => r.id)].filter(l => I.lot.has(l) || l === lot);
    [...new Set([lot, ...rel.map(r => r.id)])].forEach(l => {
      (I.consByLot.get(l) || []).forEach(c => { const m = I.matlot.get(c.mat_lot_id) || {}; rel.push({ dir: 'Truy ngược', type: `Vật tư ${c.component_id}${l !== lot ? ' (của ' + l + ')' : ''}`, id: c.mat_lot_id, qty: c.qty_consumed, time: c.consumption_time, src: 'material_consumption_truth', lvl: 'Đã xác nhận', note: m.supplier_code }); });
      (I.allocByLot.get(l) || []).forEach(a => { rel.push({ dir: 'Truy xuôi', type: 'JT/Order' + (l !== lot ? ' (qua ' + l + ')' : ''), id: a.jt_id, qty: a.qty_allocated, time: a.allocation_time, src: 'jt_allocation_truth', lvl: 'Đã xác nhận' }); (I.shipByJt.get(a.jt_id) || []).forEach(s => rel.push({ dir: 'Truy xuôi', type: 'Chuyến giao', id: s.shipment_id, qty: s.qty_actual, time: s.truck_time, src: 'shipment_truth', lvl: 'Suy luận', note: 'Nối qua JT; dữ liệu chỉ ở mức JT, không tới từng Lot' })); });
    });
    return rel;
  }
  FS.pages.genealogy = { title: 'Lot Genealogy', sub: 'Truy ngược / truy xuôi Lot với máy, công đoạn, vật tư, JT/Order và mốc thời gian', noFilter: true, render(root) {
    const ex = FS.tables.genealogy_truth[7].parent_lot_id; let lot = FS.q().lot || 'LOT-0403';
    root.innerHTML = `<div class="card"><div class="row"><label>Lot ID<input id="l" list="ll" value="${lot}" style="width:200px"></label><datalist id="ll">${FS.tables.canonical_lots.map(l => `<option value="${l.lot_id}">`).join('')}</datalist><button class="btn" id="s">Truy vết</button><small class="muted">Gợi ý: LOT-0403, LOT-0404 (lô vật tư MAT-C3-0917-02), LOT-0147, LOT-2207</small></div></div><div id="out"></div>`;
    function run() {
      lot = u.$('#l', root).value.trim(); const L = FS.idx.lot.get(lot), out = u.$('#out', root);
      if (!L && !FS.idx.parentOf.has(lot) && !FS.idx.childOf.has(lot)) { out.innerHTML = '<div class="card mt">' + u.empty('Không tìm thấy Lot ' + u.esc(lot), 'Kiểm tra lại Lot ID. Quan hệ không tìm thấy sẽ không bị suy đoán.') + '</div>'; return; }
      const ev = (FS.idx.prodByLot.get(lot) || []).slice().sort((a, b) => FS.T(a.start_time) - FS.T(b.start_time)), qc = FS.idx.qcByLot.get(lot) || [], rel = trace(lot);
      out.innerHTML = `<div class="grid g3 mt"><div class="card"><h3>Thông tin Lot</h3>${L ? u.kv([['Lot', lot], ['Sản phẩm', L.product_id], ['SL', L.qty], ['Line', L.line_id], ['Ca', L.shift], ['Tạo lúc', FS.fmt.d(L.created_ts)], ['Loại cha', L.parent_kind + (L.parent_batch ? ' · ' + L.parent_batch : '')], ['Trạng thái', L.status]]) : u.kv([['Lot', lot], ['Ghi chú', 'Có trong cạnh genealogy nhưng không có trong canonical_lots']])}<div class="callout info">Mức truy vết: <b>Lot/Batch</b> — không phải từng sản phẩm riêng lẻ.</div></div>
        <div class="card" style="grid-column:span 2"><div class="card-h"><h3>Quan hệ truy vết</h3><span class="sp"><button class="btn sm ghost" id="ex">⭳ Xuất danh sách</button></span></div><div id="rt"></div></div></div>
      <div class="grid g2 mt"><div class="card"><div class="card-h"><h3>Dòng thời gian công đoạn</h3></div><div class="tl">${ev.map(e => `<div><b>${e.station_id}</b> ${e.event_type} · ${FS.fmt.d(e.start_time)} <small>(${e.shift}, in ${e.qty_in} / out ${e.qty_out}${e.qty_ng ? ' / NG ' + e.qty_ng : ''})</small>${e.is_physical_anomaly ? ' ' + u.badge('Bất thường ' + (e.anomaly_type || ''), 'red', '▲') : ''}</div>`).join('') || '<small class="muted">Chưa đủ dữ liệu sự kiện</small>'}</div></div>
        <div class="card"><div class="card-h"><h3>Kết quả QC</h3></div><div id="qt"></div></div></div>`;
      u.table(u.$('#rt', root), { rows: rel, pageSize: 8, cols: [{ k: 'dir', t: 'Hướng', r: r => u.badge(r.dir, r.dir === 'Truy ngược' ? 'violet' : 'blue') }, { k: 'type', t: 'Đối tượng' }, { k: 'id', t: 'ID', r: r => r.id.startsWith('LOT') ? `<a href="#/genealogy?lot=${r.id}" data-lot="${r.id}">${r.id}</a>` : r.id }, { k: 'qty', t: 'SL' }, { t: 'Thời điểm', r: r => FS.fmt.d(r.time), x: r => r.time }, { t: 'Mức xác nhận', r: r => u.prov(r.lvl), x: r => r.lvl }, { k: 'src', t: 'Nguồn' }], empty: 'Chưa đủ dữ liệu quan hệ cho Lot này' });
      u.table(u.$('#qt', root), { rows: qc, pageSize: 6, search: false, cols: [{ k: 'station_id', t: 'Trạm' }, { k: 'characteristic', t: 'Đặc tính' }, { t: 'Giá trị', r: q => `${q.value} <small>[${q.lsl}–${q.usl}]</small>`, x: q => q.value }, { t: 'KQ', r: q => u.badge(q.result, q.result === 'OK' ? 'green' : 'red', q.result === 'OK' ? '✔' : '✕'), x: q => q.result }], empty: 'Không có dữ liệu QC' });
      u.$('#ex', root).onclick = () => FS.csv.download('truy_vet_' + lot + '.csv', FS.csv.stringify(rel.map(r => ({ lot_goc: lot, huong: r.dir, doi_tuong: r.type, id: r.id, so_luong: r.qty, thoi_diem: r.time, muc_xac_nhan: r.lvl, nguon: r.src, ghi_chu: r.note || '' }))));
      u.$$('[data-lot]', root).forEach(a => a.onclick = e => { e.preventDefault(); u.$('#l', root).value = a.dataset.lot; run(); });
    }
    u.$('#s', root).onclick = run; u.$('#l', root).onkeydown = e => { if (e.key === 'Enter') run(); }; run();
  } };
})();
