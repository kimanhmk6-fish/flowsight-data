/* FR-01 Command Center — Kim tự tháp ngược: Cảnh báo → Định hướng hành động */
(function () {
  const u = FS.ui;
  FS.pages.command = {
    title: 'Command Center', sub: 'Cảnh báo và định hướng hành động',
    render(root) {
      const incs = FS.engine.incidents(), R = FS.engine.impactAll(), S = FS.state, n = FS.fmt.n;
      const st = {
        open: incs.filter(i => FS.engine.incStatus(i) === 'Đang mở'),
        prog: incs.filter(i => FS.engine.incStatus(i) === 'Đang xử lý'),
        done: incs.filter(i => FS.engine.incStatus(i) === 'Đã đóng')
      };
      const jtMap = new Map();
      R.forEach(r => r.atRisk.forEach(x => { const o = jtMap.get(x.jt.jt_id); if (!o || x.exposure > o.exposure) jtMap.set(x.jt.jt_id, x); }));
      const jts = [...jtMap.values()].sort((a, b) => b.exposure - a.exposure);
      const lotSet = new Set(incs.flatMap(i => FS.lotList(i.affected_lots)));
      const nets = R.filter(r => r.net != null), short = nets.reduce((s, r) => s + r.net, 0);

      /* Alert feed: top 5 sự cố nghiêm trọng */
      const alerts = incs.slice().sort((a, b) => {
        const w = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
        return (w[a.severity_level] ?? 4) - (w[b.severity_level] ?? 4) || (b.rpn || 0) - (a.rpn || 0);
      }).slice(0, 5);

      /* Action board: top 5 JT nguy cơ cao */
      const topJt = jts.slice(0, 5);

      /* Trend 7 ngày */
      const days = [], f = FS.T(S.from), t = FS.T(S.to);
      for (let d = f; d <= t; d += 864e5) days.push(new Date(d).toISOString().slice(0, 10));
      const icount = days.map(d => incs.filter(i => i.start_time.slice(0, 10) === d).length);

      root.innerHTML = `
      <!-- KPI ROW: 4 chỉ số cốt lõi -->
      <div class="grid g4">
        ${u.kpi({ label: 'Sự cố trong kỳ', value: incs.length, unit: 'sự cố', icon: '⚠', color: 'red', sub: `${st.open.length} mở · ${st.prog.length} xử lý · ${st.done.length} đóng`, def: 'Đếm incident_id duy nhất trong bộ lọc' })}
        ${u.kpi({ label: 'Thiếu hụt ước tính', value: short, unit: 'sp', icon: '◔', color: 'amber', sub: `${nets.length} sự cố có ước tính`, def: 'Σ thiếu hụt ròng từng sự cố' })}
        ${u.kpi({ label: 'JT có nguy cơ', value: jts.length, unit: 'JT', icon: '☰', color: 'violet', sub: `${jts.filter(x => x.risk.t === 'Cao').length} mức cao`, def: 'JT duy nhất có exposure > 0' })}
        ${u.kpi({ label: 'Lot bị ảnh hưởng', value: lotSet.size, unit: 'lot', icon: '▣', color: 'blue', def: 'Lot duy nhất từ affected_lots' })}
      </div>

      <!-- TREND + ALERT FEED -->
      <div class="grid g21 mt">
        <div class="card"><div class="card-h"><h3>Xu hướng sự cố</h3><span class="sp">${u.prov('Pilot')}</span></div>
          <div class="chart-wrapper">${days.length && icount.some(v => v > 0) ? u.line({ labels: days.map(d => d.slice(5)), series: [], bars: { name: 'Số sự cố', vals: icount, color: u.C.red } }) : u.empty('Không có sự cố trong khoảng lọc', 'Thử đổi khoảng ngày hoặc preset 7/30 ngày.')}</div>
        </div>
        <div class="card"><div class="card-h"><h3>Cảnh báo khẩn cấp</h3><span class="sp"><a href="#/incident_intel?tab=incidents">Xem tất cả →</a></span></div>
          ${alerts.map(i => `<div class="act"><div>${u.sev(i.severity_level)}</div><div><b>${i.incident_id} · ${i.station_id}</b><br><small>${FS.fmt.d(i.start_time)} · ${i.duration_h}h · RPN ${i.rpn ?? '—'}</small></div><a class="sp" href="#/incident_intel?tab=impact&inc=${i.incident_id}">Xử lý →</a></div>`).join('') || u.empty('Không có cảnh báo')}
        </div>
      </div>

      <!-- ACTION BOARD: top 5 JT nguy cơ -->
      <div class="card mt"><div class="card-h"><h3>Kiểm soát cổng: JT nguy cơ cao</h3><span class="sp"><a href="#/priority">Ưu tiên xử lý →</a></span></div>
        <div id="cc-jt"></div>
      </div>

      <!-- PHÂN BỔ NGUYÊN NHÂN (widget) -->
      <div class="grid g21 mt">
        <div class="card"><div class="card-h"><h3>Phân bổ nguyên nhân sự cố</h3></div>
          <div id="cc-cause"></div>
          <small class="muted">Theo loại nguyên nhân · <a href="#/incident_intel?tab=rootcause">Phân tích chi tiết →</a></small>
        </div>
        <div class="card"><div class="card-h"><h3>Truy xuất nhanh</h3></div>
          <div class="row" style="gap:8px;flex-wrap:wrap">
            <a class="btn ghost sm" href="#/supply_chain?tab=genealogy">Tra cứu phả hệ Lot</a>
            <a class="btn ghost sm" href="#/supply_chain?tab=materials">Danh mục & vật tư</a>
            <a class="btn ghost sm" href="#/admin?tab=validation">Thẩm định</a>
          </div>
          <p class="muted" style="margin-top:12px">Truy cập nhanh các chức năng truy vết và kiểm chứng.</p>
        </div>
      </div>
      `;

      /* Widget phân bổ nguyên nhân */
      const causeData = Object.entries(incs.reduce((m, i) => (m[i.root_cause_type || 'Không rõ'] = (m[i.root_cause_type || 'Không rõ'] || 0) + 1, m), {}))
        .map(([k, v]) => ({ k, v })).sort((a, b) => b.v - a.v);
      const ccCause = u.$('#cc-cause', root);
      if (ccCause) ccCause.innerHTML = causeData.length ? u.donut(causeData, incs.length) : u.empty('Không có sự cố');

      /* Bảng JT */
      u.table(u.$('#cc-jt', root), {
        cols: [
          { t: 'JT/Order', r: x => `<b>${x.jt.jt_id}</b>`, x: x => x.jt.jt_id },
          { t: 'Sản phẩm', r: x => x.jt.product_id },
          { t: 'Hạn giao', r: x => FS.fmt.d(x.jt.due_ts), x: x => x.jt.due_ts },
          { t: 'Thiếu (sp)', r: x => n(x.exposure), x: x => x.exposure, s: x => x.exposure },
          { t: 'Mức rủi ro', r: x => u.badge(x.risk.t, x.risk.c, x.risk.i), x: x => x.risk.t }
        ],
        rows: topJt, pageSize: 5, search: false,
        onRow: x => location.hash = '#/incident_intel?tab=impact&inc=' + x.inc
      });
    }
  };
})();
