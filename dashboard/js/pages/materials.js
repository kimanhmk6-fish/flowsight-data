/* FR-01c Danh mục & vật tư — trang chuyên sâu (tách từ Command Center) */
(function () {
  const u = FS.ui;
  FS.pages.materials = {
    title: 'Danh mục & vật tư', sub: 'Tiêu thụ vật tư, tồn kho so với tồn an toàn, danh mục sản phẩm và lô vật tư',
    render(root) {
      const S = FS.state, n = FS.fmt.n, f0 = FS.T(S.from + 'T00:00:00'), t0 = FS.T(S.to + 'T23:59:59');
      const cons = FS.tables.material_consumption_truth.filter(c => { const t = FS.T(c.consumption_time); return t >= f0 && t <= t0; });
      const byComp = {}; cons.forEach(c => byComp[c.component_id] = (byComp[c.component_id] || 0) + (c.qty_consumed || 0));
      const comps = FS.tables.dim_component || [], nm = id => (comps.find(c => c.component_id === id) || {}).component_name || id;
      const stock = id => { const r = (FS.idx.invByItem.get(id) || []).filter(x => x.item_type === 'COMPONENT').sort((a, b) => FS.T(b.snapshot_time) - FS.T(a.snapshot_time))[0]; return r ? r.qty : null; };
      const lowList = comps.filter(c => { const s = stock(c.component_id); return s != null && s < c.safety_stock_qty; });
      const totalCons = Object.values(byComp).reduce((a, b) => a + b, 0);
      root.innerHTML = `<div class="grid g4">
        ${u.kpi({ label: 'Vật tư tiêu thụ', value: totalCons, unit: 'sp', icon: '▣', color: 'blue', def: 'Σ qty_consumed theo component trong kỳ' })}
        ${u.kpi({ label: 'Loại vật tư', value: comps.length, unit: 'loại', icon: '☰', color: 'violet' })}
        ${u.kpi({ label: 'Dưới tồn an toàn', value: lowList.length, unit: 'loại', icon: '▲', color: 'red', def: 'Tồn snapshot mới nhất < safety_stock_qty' })}
        ${u.kpi({ label: 'Lô vật tư đã nhận', value: (FS.tables.material_lot_truth || []).length, unit: 'lô', icon: '⭳', color: 'green' })}
      </div>
      <div class="grid g21 mt">
        <div class="card"><div class="card-h"><h3>Tiêu thụ vật tư trong kỳ</h3><span class="sp">${u.prov('Pilot')}</span></div>
          ${Object.keys(byComp).length ? u.donut(Object.entries(byComp).map(([k, v]) => ({ k: nm(k), v })).sort((a, b) => b.v - a.v), n(totalCons)) : u.empty('Chưa đủ dữ liệu tiêu thụ')}
          <div id="m-cons-tbl" class="mt"></div></div>
        <div class="card"><div class="card-h"><h3>Tồn kho so với tồn an toàn</h3></div><div id="m-stock"></div></div>
      </div>
      <div class="grid g2 mt">
        <div class="card"><div class="card-h"><h3>Lô vật tư nhận & truy xuất</h3></div><div id="m-lots"></div></div>
        <div class="card"><div class="card-h"><h3>Danh mục sản phẩm</h3></div><div id="m-prod"></div></div>
      </div>`;
      /* Bảng tiêu thụ chi tiết */
      u.table(u.$('#m-cons-tbl', root), {
        cols: [{ t: 'Vật tư', r: r => `<b>${r.id}</b><br><small>${u.esc(nm(r.id))}</small>` }, { t: 'Tiêu thụ', r: r => n(r.v), x: r => r.v, s: r => r.v }, { t: 'Tỷ trọng', r: r => (r.v / totalCons * 100).toFixed(1) + '%' }],
        rows: Object.entries(byComp).map(([id, v]) => ({ id, v })).sort((a, b) => b.v - a.v),
        pageSize: 6, search: false, export: 'tieu_thu_vat_tu'
      });
      /* Tồn kho */
      u.$('#m-stock', root).innerHTML = comps.map(c => {
        const s = stock(c.component_id), low = s != null && s < c.safety_stock_qty;
        return `<div class="mrow"><div><b>${c.component_id}</b><br><small>${u.esc(c.component_name)} · ${c.supplier_code} · LT ${c.lead_time_days}d</small></div>
          <div class="bar"><i style="width:${s == null ? 0 : Math.min(100, s / (c.safety_stock_qty * 1.5) * 100)}%;${low ? 'background:#ef4444' : ''}"></i></div>
          <small>${s == null ? 'Chưa có snapshot' : n(s) + ' / an toàn ' + n(c.safety_stock_qty)} ${s == null ? u.badge('Chưa đủ dữ liệu', 'gray', '?') : low ? u.badge('Dưới tồn an toàn', 'red', '▲') : u.badge('Đủ', 'green', '✔')}</small></div>`;
      }).join('') || u.empty('Chưa có danh mục vật tư');
      /* Lô vật tư */
      const mlots = FS.tables.material_lot_truth || [];
      u.table(u.$('#m-lots', root), {
        cols: [{ k: 'mat_lot_id', t: 'Lô vật tư' }, { k: 'component_id', t: 'Vật tư' }, { k: 'qty_received', t: 'SL nhận' }, { k: 'supplier_code', t: 'NCC' }, { t: 'Ngày nhận', r: r => FS.fmt.d(r.received_time || r.receipt_time) }],
        rows: mlots, pageSize: 8, export: 'lo_vat_tu',
        onRow: r => location.hash = '#/genealogy?lot=' + r.mat_lot_id
      });
      /* Danh mục sản phẩm */
      const prods = FS.tables.dim_product || [];
      u.$('#m-prod', root).innerHTML = prods.length
        ? `<div class="grid g2">${prods.map(p => `<div class="card"><b>${p.product_id}</b> <small>${u.esc(p.product_family || '')}</small><br><small class="muted">Mục tiêu/ngày: <b>${n(p.target_daily_qty)}</b> sp</small><br><a href="#/genealogy">Truy vết Lot →</a></div>`).join('')}</div>`
        : u.empty('Chưa có danh mục sản phẩm');
    }
  };
})();
