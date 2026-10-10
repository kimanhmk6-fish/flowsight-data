/* Lược đồ chuẩn (trường chuẩn, khóa, ràng buộc, đồng nghĩa tên cột) + bộ kiểm tra chất lượng dữ liệu dùng chung */
FS.norm = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase().replace(/[^a-z0-9]/g, '');
FS.SCHEMA = {
  incident_truth: { label: 'Incident', key: ['incident_id'], req: ['incident_id', 'station_id', 'start_time'], dates: ['start_time', 'end_time'], nums: ['duration_h', 'rpn'], fk: [{ f: 'station_id', to: 'dim_station', k: 'station_id' }, { f: 'affected_lots', to: 'canonical_lots', k: 'lot_id', list: 1 }, { f: 'fmea_code', to: 'fmea_registry', k: 'fmea_code' }],
    rules: [{ n: 'duration_h khớp (end − start)', fn: r => r.end_time && r.start_time && r.duration_h != null && Math.abs((FS.T(r.end_time) - FS.T(r.start_time)) / 36e5 - r.duration_h) > .01 ? 'duration_h lệch end − start' : null }, { n: 'end ≥ start', fn: r => FS.T(r.end_time) < FS.T(r.start_time) ? 'end_time trước start_time' : null }] },
  production_truth: { label: 'Production Plan/Result', key: ['event_id'], req: ['event_id', 'lot_id', 'station_id', 'start_time'], dates: ['start_time', 'end_time'], nums: ['qty_in', 'qty_out', 'qty_ng'], fk: [{ f: 'lot_id', to: 'canonical_lots', k: 'lot_id' }, { f: 'station_id', to: 'dim_station', k: 'station_id' }],
    rules: [{ n: 'qty_out ≤ qty_in', fn: r => r.qty_out > r.qty_in ? 'qty_out lớn hơn qty_in' : null }], note: 'lot_id lặp lại hợp lệ (nhiều sự kiện/Lot); khóa là event_id' },
  canonical_lots: { label: 'Lot', key: ['lot_id'], req: ['lot_id', 'product_id'], dates: ['created_ts'], nums: ['qty'], fk: [{ f: 'product_id', to: 'dim_product', k: 'product_id' }] },
  inventory_truth: { label: 'Inventory/WIP', key: ['snapshot_id'], req: ['snapshot_id', 'snapshot_time', 'item_type', 'item_id', 'qty'], dates: ['snapshot_time'], nums: ['qty'], enums: { item_type: ['FG', 'WIP', 'COMPONENT'] }, fk: [] },
  material_lot_truth: { label: 'Material', key: ['mat_lot_id'], req: ['mat_lot_id', 'component_id'], dates: ['received_ts'], nums: ['qty_received'], fk: [] },
  jt_order_truth: { label: 'JT/Order', key: ['jt_id'], req: ['jt_id', 'product_id', 'qty', 'due_ts'], dates: ['due_ts'], nums: ['qty'], fk: [{ f: 'product_id', to: 'dim_product', k: 'product_id' }] },
  qc_truth: { label: 'QC', key: ['qc_id'], req: ['qc_id', 'lot_id', 'characteristic', 'value'], dates: ['measured_time'], nums: ['value', 'lsl', 'usl'], enums: { result: ['OK', 'NG'] }, fk: [{ f: 'lot_id', to: 'canonical_lots', k: 'lot_id' }] },
  shipment_truth: { label: 'Shipping', key: ['shipment_id'], req: ['shipment_id', 'jt_id'], dates: ['truck_time', 'cutoff_time'], nums: ['qty_planned', 'qty_actual'], fk: [{ f: 'jt_id', to: 'jt_order_truth', k: 'jt_id' }] },
  dim_station: { label: 'Production/Machine', key: ['station_id'], req: ['station_id'], dates: [], nums: ['rated_rate_per_h', 'cycle_time_s'], fk: [] }
};
FS.SYN = { lot_id: ['malo', 'lot', 'lotno', 'lotid', 'solo'], value: ['giatri', 'val', 'measurement', 'gtri'], station_id: ['may', 'tram', 'station', 'machine', 'machineid', 'mamay'], start_time: ['batdau', 'start', 'thoigianbatdau', 'begin'], end_time: ['ketthuc', 'end', 'thoigianketthuc'], incident_id: ['masuco', 'incident', 'id'], qty: ['soluong', 'sl', 'quantity'], product_id: ['sanpham', 'product', 'masp'], jt_id: ['jt', 'order', 'donhang', 'madon'], due_ts: ['hangiao', 'due', 'duedate'] };
FS.autoMap = (headers, group) => { const sc = FS.SCHEMA[group], all = [...new Set([...sc.req, ...sc.dates, ...sc.nums, ...sc.key, ...(sc.fk || []).map(f => f.f), ...Object.keys(sc.enums || {}), 'duration_h', 'severity_level'])], m = {}, nh = headers.map(FS.norm);
  all.forEach(f => { const al = [FS.norm(f), ...(FS.SYN[f] || [])]; const i = nh.findIndex(h => al.includes(h)); if (i >= 0) m[f] = headers[i]; }); return m; };
FS.detectGroup = headers => { const nh = headers.map(FS.norm); let best = null, bs = 0; Object.keys(FS.SCHEMA).forEach(g => { const m = FS.autoMap(headers, g), s = Object.keys(m).length / (FS.SCHEMA[g].req.length + 2); if (s > bs) { bs = s; best = g; } }); return bs > .5 ? best : null; };
/* Kiểm tra chất lượng 1 bảng. ref(table)->Set id. Trả {dims, issues, stats} */
FS.quality = function (group, rows, refs) {
  const sc = FS.SCHEMA[group], issues = [], bad = new Set(), n = rows.length || 1; let miss = 0, cells = 0, inval = 0, vcells = 0, fkOk = 0, fkTot = 0, rb = 0;
  const seen = new Map(), add = (i, col, type, msg) => { issues.push({ row: i + 2, col, type, msg }); bad.add(i); };
  const refSet = (t, k) => { const T = refs ? refs(t) : (FS.tables[t] || []); return new Set(T.map(r => r[k])); };
  const fkSets = (sc.fk || []).map(f => refSet(f.to, f.k));
  rows.forEach((r, i) => {
    sc.req.forEach(c => { cells++; if (r[c] == null || r[c] === '') { miss++; add(i, c, 'Completeness', 'Thiếu giá trị bắt buộc'); } });
    sc.dates.forEach(c => { if (r[c] != null && r[c] !== '') { vcells++; if (isNaN(FS.T(r[c]))) { inval++; add(i, c, 'Validity', 'Định dạng ngày giờ không hợp lệ: ' + r[c]); } } });
    sc.nums.forEach(c => { if (r[c] != null && r[c] !== '') { vcells++; if (typeof r[c] !== 'number' || !isFinite(r[c])) { inval++; add(i, c, 'Validity', 'Không phải số: ' + r[c]); } } });
    Object.entries(sc.enums || {}).forEach(([c, v]) => { if (r[c] != null) { vcells++; if (!v.includes(r[c])) { inval++; add(i, c, 'Validity', 'Ngoài miền giá trị: ' + r[c]); } } });
    const k = sc.key.map(c => r[c]).join('|'); if (seen.has(k) && k.replace(/\|/g, '')) add(i, sc.key.join('+'), 'Uniqueness', 'Khóa trùng với dòng ' + (seen.get(k) + 2)); else seen.set(k, i);
    (sc.fk || []).forEach((f, j) => { const vals = f.list ? FS.lotList(r[f.f]) : (r[f.f] != null && r[f.f] !== '' ? [r[f.f]] : []); vals.forEach(v => { fkTot++; if (fkSets[j].has(v)) fkOk++; else add(i, f.f, 'Referential', `Không tìm thấy ${v} trong ${f.to}.${f.k}`); }); });
    (sc.rules || []).forEach(ru => { const m = ru.fn(r); if (m) { rb++; add(i, ru.n, 'Consistency', m); } });
  });
  const ts = sc.dates.length ? rows.map(r => FS.T(r[sc.dates[0]])).filter(x => !isNaN(x)) : [], age = ts.length ? (FS.NOW - Math.max(...ts)) / 864e5 : null;
  const uniq = issues.filter(x => x.type === 'Uniqueness').length;
  return { group, label: sc.label, rows: rows.length, bad: bad.size, good: rows.length - bad.size, issues, note: sc.note,
    dims: { Completeness: cells ? 1 - miss / cells : null, Validity: vcells ? 1 - inval / vcells : null, Uniqueness: 1 - uniq / n, Consistency: 1 - rb / n, 'Referential Integrity': fkTot ? fkOk / fkTot : null, Timeliness: age == null ? null : age }, fk: { ok: fkOk, tot: fkTot } };
};
