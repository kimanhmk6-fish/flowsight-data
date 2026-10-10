/* Engine: công thức tách khỏi giao diện (NFR-08). Mỗi hàm trả kèm 'steps' để giải thích (NFR-03). */
FS.engine = (function () {
  const H = 3600000, D = 86400000;
  function schedOverlapH(a, b) { // giờ nằm trong ca sản xuất theo lịch [schedStart, schedEnd) mỗi ngày
    const { schedStart: s, schedEnd: e } = FS.config; let tot = 0;
    for (let d = new Date(a); d.setHours(0, 0, 0, 0) <= b; d.setDate(d.getDate() + 1)) {
      const ws = new Date(d).setHours(s, 0, 0, 0), we = new Date(d).setHours(e, 0, 0, 0);
      tot += Math.max(0, Math.min(b, we) - Math.max(a, ws));
    }
    return tot / H;
  }
  const incStatus = i => FS.wf.inc[i.incident_id] || (FS.T(i.end_time) > FS.NOW ? 'Đang mở' : 'Đã đóng');
  function incidents() {
    const S = FS.state, from = FS.T(S.from + 'T00:00:00'), to = FS.T(S.to + 'T23:59:59');
    return FS.tables.incident_truth.filter(i => { const t = FS.T(i.start_time);
      return t >= from && t <= to && (!S.station || i.station_id === S.station) && (!S.status || incStatus(i) === S.status) &&
        (!S.q || JSON.stringify(i).toLowerCase().includes(S.q.toLowerCase())); });
  }
  function latestFG(product, beforeMs) {
    const rows = (FS.idx.invByItem.get(product) || []).filter(r => r.item_type === 'FG' && FS.T(r.snapshot_time) <= beforeMs).sort((a, b) => FS.T(b.snapshot_time) - FS.T(a.snapshot_time));
    return rows[0] || null;
  }
  /* Phân tích tác động 1 sự cố. ov: {durH} để what-if. */
  function impact(inc, ov = {}) {
    const C = FS.config, st = FS.idx.station.get(inc.station_id) || {}, steps = [], assume = [];
    const a = FS.T(inc.start_time), durH = ov.durH != null ? ov.durH : (inc.duration_h != null ? inc.duration_h : (FS.T(inc.end_time) - a) / H);
    const b = a + durH * H;
    let rate = st.rated_rate_per_h, rateSrc = 'dim_station.rated_rate_per_h';
    if (!rate && st.cycle_time_s) { rate = 3600 / st.cycle_time_s; rateSrc = '3600 / cycle_time_s (suy ra)'; assume.push('Công suất suy ra từ cycle time vì thiếu rated_rate_per_h'); }
    const lostH = schedOverlapH(a, b), lostQty = rate ? lostH * rate : null;
    steps.push(['Thời gian dừng', durH + ' h', 'duration_h / (end − start)'], ['Thời gian sản xuất bị mất', FS.fmt.n(lostH) + ' h', `giao với ca ${C.schedStart}:00–${C.schedEnd}:00`], ['Công suất tham chiếu', rate ? FS.fmt.n(rate) + ' sp/h' : 'Chưa đủ dữ liệu', rateSrc], ['Sản lượng mất lý thuyết', lostQty == null ? 'Chưa đủ dữ liệu' : FS.fmt.n(lostQty) + ' sp', 'giờ mất × công suất']);
    // JT liên quan: xác nhận (khóa allocation) + suy luận (cùng line, hạn trong cửa sổ 72h)
    const lots = FS.lotList(inc.affected_lots), conf = new Map();
    lots.forEach(l => (FS.idx.allocByLot.get(l) || []).forEach(al => conf.set(al.jt_id, `Khóa jt_allocation: ${l} → ${al.jt_id}`)));
    const jts = [];
    conf.forEach((basis, id) => FS.idx.jt.get(id) && jts.push({ jt: FS.idx.jt.get(id), link: 'Đã xác nhận', basis }));
    FS.tables.jt_order_truth.forEach(j => { if (conf.has(j.jt_id) || j.status !== 'OPEN') return;
      const due = FS.T(j.due_ts); if ((st.line_id === 'SHARED' || j.line_id === st.line_id) && due >= a && due <= b + 72 * H)
        jts.push({ jt: j, link: 'Suy luận', basis: `Cùng line ${j.line_id}, hạn giao trong 72h sau sự cố (quy tắc R-LINK-01)` }); });
    const prods = [...new Set(jts.map(x => x.jt.product_id))];
    let fg = 0, fgMissing = 0; prods.forEach(p => { const s = latestFG(p, a); s ? fg += s.qty : fgMissing++; });
    const fgUsable = fg * C.fgUsablePct / 100; if (prods.length) assume.push(`Tồn FG khả dụng = ${C.fgUsablePct}% tồn snapshot gần nhất (giả định, chưa xét QC-hold/vị trí)`);
    const deficit = lostQty == null ? null : Math.max(0, lostQty - fgUsable);
    const perDay = C.useRecovery && rate ? (st.spare_capacity_h_per_day || 0) * rate : 0;
    steps.push(['Tồn FG khả dụng', FS.fmt.n(fgUsable) + ' sp', 'Σ snapshot FG gần nhất trước sự cố × %khả dụng (không cộng WIP)'], ['Thiếu hụt sau tồn kho', deficit == null ? 'Chưa đủ dữ liệu' : FS.fmt.n(deficit) + ' sp', 'sản lượng mất − FG khả dụng'], ['Công suất bù / ngày', FS.fmt.n(perDay) + ' sp', 'spare_capacity_h_per_day × công suất']);
    jts.forEach(x => { const j = x.jt, due = FS.T(j.due_ts); x.slackH = (due - b) / H;
      x.exposure = deficit == null ? null : Math.min(j.qty, Math.max(0, deficit - perDay * Math.max(0, (due - b) / D)));
      x.ratio = x.exposure == null ? null : x.exposure / j.qty; x.alloc = (FS.idx.allocByJt.get(j.jt_id) || []).reduce((s, r) => s + r.qty_allocated, 0);
      x.ship = FS.idx.shipByJt.get(j.jt_id) || []; x.risk = riskLabel(x.ratio); });
    jts.sort((p, q) => (q.exposure || 0) - (p.exposure || 0) || p.slackH - q.slackH);
    const atRisk = jts.filter(x => x.exposure > 0), net = deficit == null ? null : (jts.length ? Math.max(0, ...jts.map(x => x.exposure || 0)) : deficit);
    const status = rate == null ? 'Chưa đủ dữ liệu' : (!jts.length || fgMissing) ? 'Ước tính một phần' : 'Đủ dữ liệu';
    steps.push(['Thiếu hụt ròng', net == null ? 'Chưa đủ dữ liệu' : FS.fmt.n(net) + ' sp', 'max exposure JT (không cộng trùng cùng một thiếu hụt)'], ['JT/Order có nguy cơ', atRisk.length + ' / ' + jts.length, 'exposure > 0 sau khi trừ công suất bù đến hạn giao']);
    return { inc, st, durH, lostH, lostQty, rate, fg, fgUsable, deficit, perDay, jts, atRisk, net, status, steps, assume, lots,
      shipRisk: atRisk.flatMap(x => x.ship.filter(s => s.status !== 'DEPARTED' || s.qty_actual < s.qty_planned)).filter((s, i, arr) => arr.findIndex(z => z.shipment_id === s.shipment_id) === i) };
  }
  function riskLabel(ratio) {
    if (ratio == null) return { t: 'Chưa đủ dữ liệu', c: 'gray', i: '?' };
    if (!FS.config.thresholdOn) return { t: 'Chưa cấu hình ngưỡng', c: 'gray', i: '–' };
    const p = ratio * 100; return p >= FS.config.thHigh ? { t: 'Cao', c: 'red', i: '▲' } : p >= FS.config.thMid ? { t: 'Trung bình', c: 'amber', i: '●' } : { t: 'Thấp', c: 'green', i: '▼' };
  }
  const cache = new Map();
  function impactAll() { const key = JSON.stringify([FS.state, FS.config, FS.tables.incident_truth.length]); if (cache.has(key)) return cache.get(key); const r = incidents().map(i => impact(i)); cache.clear(); cache.set(key, r); return r; }
  /* Đồ thị lan truyền: Incident → Station → Lot → (Material/Genealogy) → JT → Shipment */
  function graph(inc) {
    const N = new Map(), E = []; const node = (id, type, label, col, attrs = {}) => { if (!N.has(id)) N.set(id, { id, type, label, col, attrs }); return N.get(id); };
    const edge = (f, t, kind, basis, src) => E.push({ f, t, kind, basis, src });
    node(inc.incident_id, 'Incident', inc.incident_id, 0, { ...inc }); const st = FS.idx.station.get(inc.station_id);
    node(inc.station_id, 'Máy/Công đoạn', inc.station_id, 1, { ...st }); edge(inc.incident_id, inc.station_id, 'Trực tiếp', 'incident.station_id = station_id', 'incident_truth');
    const lots = FS.lotList(inc.affected_lots);
    lots.forEach(l => { const L = FS.idx.lot.get(l); node(l, 'Lot', l, 2, { ...(L || {}) }); edge(inc.station_id, l, L ? 'Trực tiếp' : 'Chưa xác minh', L ? 'incident.affected_lots' : 'Lot không tồn tại trong canonical_lots', 'incident_truth');
      (FS.idx.consByLot.get(l) || []).forEach(c => { node(c.mat_lot_id, 'Vật tư', c.mat_lot_id, 3, { ...(FS.idx.matlot.get(c.mat_lot_id) || {}) }); edge(l, c.mat_lot_id, 'Trực tiếp', `Tiêu thụ ${c.qty_consumed} ${c.component_id}`, 'material_consumption_truth'); });
      (FS.idx.childOf.get(l) || []).forEach(g => { node(g.child_lot_id, 'Lot', g.child_lot_id, 3, {}); edge(l, g.child_lot_id, 'Trực tiếp', g.edge_type, 'genealogy_truth'); });
      (FS.idx.allocByLot.get(l) || []).forEach(al => { const j = FS.idx.jt.get(al.jt_id); node(al.jt_id, 'JT/Order', al.jt_id, 4, { ...(j || {}) }); edge(l, al.jt_id, 'Trực tiếp', `Phân bổ ${al.qty_allocated}`, 'jt_allocation_truth'); }); });
    const R = impact(inc); R.jts.filter(x => x.link === 'Suy luận').slice(0, 6).forEach(x => { node(x.jt.jt_id, 'JT/Order', x.jt.jt_id, 4, { ...x.jt }); edge(inc.station_id, x.jt.jt_id, 'Suy luận', x.basis, 'quy tắc R-LINK-01'); });
    [...N.values()].filter(n => n.type === 'JT/Order').forEach(n => (FS.idx.shipByJt.get(n.id) || []).forEach(s => { node(s.shipment_id, 'Giao hàng', s.shipment_id, 5, { ...s }); edge(n.id, s.shipment_id, 'Trực tiếp', 'shipment.jt_id', 'shipment_truth'); }));
    if (!lots.length) { node('NOLINK', 'Chưa đủ dữ liệu', 'Chưa đủ dữ liệu liên kết', 2, { note: 'Sự cố không có affected_lots; không tạo quan hệ chỉ vì gần nhau về thời gian.' }); edge(inc.station_id, 'NOLINK', 'Chưa xác minh', 'Thiếu khóa Lot', 'incident_truth'); }
    return { nodes: [...N.values()], edges: E };
  }
  /* Bằng chứng nguyên nhân (FR-08): quy tắc + thống kê mô tả, không ML */
  function cause(inc) {
    const F = [], lots = FS.lotList(inc.affected_lots), fm = FS.idx.fmea.get(inc.fmea_code);
    if (fm) F.push({ factor: `${fm.fmea_category}: ${fm.fmea_description}`, kind: 'Cơ cấu lỗi (FMEA)', ev: `RPN ${fm.rpn} (S${fm.severity}·O${fm.occurrence}·D${fm.detection}) tại ${fm.station_id}`, src: 'fmea_registry', level: 'Giả thuyết', conf: null, action: fm.recommended_action });
    const mats = new Map(); lots.forEach(l => (FS.idx.consByLot.get(l) || []).forEach(c => { (mats.get(c.mat_lot_id) || mats.set(c.mat_lot_id, new Set()).get(c.mat_lot_id)).add(l); }));
    mats.forEach((s, m) => { const share = lots.length ? s.size / lots.length : 0; const tot = (FS.idx.consByMat.get(m) || []).length;
      if (lots.length > 1 && share === 1) F.push({ factor: 'Lô vật tư chung: ' + m, kind: 'Vật tư', ev: `${s.size}/${lots.length} Lot bị ảnh hưởng cùng dùng lô này (tổng ${tot} Lot dùng)`, src: 'material_consumption_truth', level: 'Giả thuyết', conf: Math.round(share * 100) / 100 * (inc.root_cause_type === 'MATERIAL' ? 1 : .6), action: 'Cô lập lô và kiểm tra IQC' }); });
    const anom = []; lots.forEach(l => (FS.idx.prodByLot.get(l) || []).forEach(e => e.is_physical_anomaly && anom.push(e)));
    if (anom.length) F.push({ factor: 'Bất thường vật lý: ' + [...new Set(anom.map(a => a.anomaly_type))].join(', '), kind: 'Quá trình', ev: `${anom.length} sự kiện bất thường trên các Lot liên quan`, src: 'production_truth', level: 'Giả thuyết', conf: null, action: '—' });
    let ng = 0, n = 0; lots.forEach(l => (FS.idx.qcByLot.get(l) || []).forEach(q => { n++; q.result === 'NG' && ng++; }));
    if (n) F.push({ factor: 'Kết quả QC của Lot liên quan', kind: 'Chất lượng', ev: `${ng} NG / ${n} phép đo`, src: 'qc_truth', level: ng ? 'Giả thuyết' : 'Đã xác nhận', conf: null, action: '—' });
    if (inc.root_cause_type && !['UNKNOWN'].includes(inc.root_cause_type)) F.unshift({ factor: 'Loại nguyên nhân ghi nhận: ' + inc.root_cause_type, kind: 'Ghi nhận nguồn', ev: 'Trường root_cause_type của incident_truth', src: 'incident_truth', level: 'Đã xác nhận', conf: null, action: '—' });
    return F.length > 1 || (F[0] && F[0].level === 'Đã xác nhận') ? F : [];
  }
  return { schedOverlapH, incidents, incStatus, impact, impactAll, graph, cause, riskLabel, latestFG };
})();
