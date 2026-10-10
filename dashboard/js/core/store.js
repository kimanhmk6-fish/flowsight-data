/* Kho dữ liệu, trạng thái toàn cục, cấu hình, workflow (lưu localStorage nếu có) */
FS.NOW = Date.parse('2026-10-10T12:00:00');
FS.T = s => (s ? Date.parse(s) : NaN);
FS.fmt = { n: v => v == null || isNaN(v) ? '—' : Math.abs(v) >= 100 ? Math.round(v).toLocaleString('vi-VN') : (Math.round(v * 10) / 10).toLocaleString('vi-VN'),
  d: s => s ? s.replace('T', ' ').slice(0, 16) : '—', day: s => s ? s.slice(0, 10) : '—' };
FS.persist = {
  get(k, d) { try { const v = localStorage.getItem('fs_' + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('fs_' + k, JSON.stringify(v)); } catch (e) { /* bộ nhớ trình duyệt có thể bị chặn */ } }
};
FS.config = Object.assign({ version: 'cfg-1.0.0', schedStart: 6, schedEnd: 22, fgUsablePct: 60, useRecovery: true, thresholdOn: true, thHigh: 30, thMid: 10,
  wShort: 35, wSlack: 30, wLink: 15, wBreadth: 10, wConf: 10, useWeights: false, changelog: [] }, FS.persist.get('config', {}));
FS.saveConfig = (note) => { FS.config.changelog.unshift({ t: new Date().toISOString().slice(0, 19), note }); FS.config.changelog.length = Math.min(FS.config.changelog.length, 30); FS.persist.set('config', FS.config); };
FS.wf = Object.assign({ inc: {}, act: {}, hist: [], imports: [] }, FS.persist.get('wf', {}));
FS.saveWf = () => FS.persist.set('wf', FS.wf);
FS.state = { from: '2026-09-29', to: '2026-10-10', station: '', status: '', q: '' };
FS.tables = {}; FS.json = {}; FS.idx = {};
FS.TABLE_ORIGIN = {}; // tên bảng -> 'Pilot' | 'Đã nhập (người dùng)'

FS.loadBundle = function () {
  const B = window.FS_BUNDLE; if (!B) throw new Error('Thiếu data/bundle.js — chạy tools/build_bundle.py');
  Object.keys(B.csv).forEach(n => { FS.tables[n] = FS.csv.toObjects(FS.csv.parse(B.csv[n])); FS.TABLE_ORIGIN[n] = 'Pilot'; });
  FS.json = B.json; FS.reindex();
};
FS.reindex = function () {
  const T = FS.tables, by = (rows, k) => { const m = new Map(); (rows || []).forEach(r => { const a = m.get(r[k]); a ? a.push(r) : m.set(r[k], [r]); }); return m; };
  const one = (rows, k) => new Map((rows || []).map(r => [r[k], r]));
  FS.idx = {
    station: one(T.dim_station, 'station_id'), product: one(T.dim_product, 'product_id'), lot: one(T.canonical_lots, 'lot_id'),
    jt: one(T.jt_order_truth, 'jt_id'), fmea: one(T.fmea_registry, 'fmea_code'), matlot: one(T.material_lot_truth, 'mat_lot_id'),
    prodByLot: by(T.production_truth, 'lot_id'), consByLot: by(T.material_consumption_truth, 'lot_id'), consByMat: by(T.material_consumption_truth, 'mat_lot_id'),
    allocByJt: by(T.jt_allocation_truth, 'jt_id'), allocByLot: by(T.jt_allocation_truth, 'lot_id'), shipByJt: by(T.shipment_truth, 'jt_id'),
    childOf: by(T.genealogy_truth, 'parent_lot_id'), parentOf: by(T.genealogy_truth, 'child_lot_id'), qcByLot: by(T.qc_truth, 'lot_id'), invByItem: by(T.inventory_truth, 'item_id')
  };
};
FS.lotList = s => (s ? String(s).split(',').map(x => x.trim()).filter(Boolean) : []);
