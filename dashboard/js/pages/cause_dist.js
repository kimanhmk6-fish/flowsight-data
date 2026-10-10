/* FR-01b Phân bổ nguyên nhân sự cố — trang chuyên sâu (tách từ Command Center) */
(function () {
  const u = FS.ui;
  FS.pages.cause_dist = {
    title: 'Phân bổ nguyên nhân sự cố', sub: 'Phân tích sự cố theo loại nguyên nhân, nhóm lỗi FMEA, máy/công đoạn và mức độ',
    render(root) {
      const incs = FS.engine.incidents(), n = FS.fmt.n;
      const fm = i => (FS.idx.fmea.get(i.fmea_code) || {}).fmea_category || 'Không rõ';
      const fmn = i => (FS.idx.fmea.get(i.fmea_code) || {}).fmea_description || '';
      const group = f => Object.entries(incs.reduce((m, i) => (m[f(i)] = (m[f(i)] || 0) + 1, m), {}))
        .map(([k, v]) => ({ k, v })).sort((a, b) => b.v - a.v);
      const VIEWS = {
        'Loại nguyên nhân': () => group(i => i.root_cause_type || 'Không rõ'),
        'Nhóm lỗi FMEA': () => group(fm),
        'Máy / công đoạn': () => group(i => i.station_id),
        'Mức độ': () => group(i => i.severity_level || 'Không rõ')
      };
      let cv = 'Loại nguyên nhân';
      root.innerHTML = `<div class="grid g4">
        ${u.kpi({ label: 'Tổng sự cố', value: incs.length, unit: 'sự cố', icon: '⚠', color: 'red', def: 'Đếm incident_id duy nhất trong bộ lọc' })}
        ${u.kpi({ label: 'Loại nguyên nhân', value: new Set(incs.map(i => i.root_cause_type)).size, unit: 'loại', icon: '◔', color: 'blue' })}
        ${u.kpi({ label: 'Máy có sự cố', value: new Set(incs.map(i => i.station_id)).size, unit: 'máy', icon: '⚙', color: 'amber' })}
        ${u.kpi({ label: 'RPN cao nhất', value: Math.max(...incs.map(i => i.rpn || 0), 0), unit: '', icon: '▲', color: 'violet', def: 'RPN = Severity × Occurrence × Detection' })}
      </div>
      <div class="grid g21 mt"><div class="card"><div class="card-h"><h3>Phân bổ sự cố</h3></div>
        <div class="seg-tabs">${Object.keys(VIEWS).map(k => `<button data-v="${k}" class="${k === cv ? 'on' : ''}">${k}</button>`).join('')}</div>
        <div id="cd-chart"></div>
        <small class="muted">Bấm tab để đổi cách nhóm; bấm vào bảng bên để xem chi tiết từng sự cố.</small></div>
      <div class="card"><div class="card-h"><h3>Top FMEA theo RPN</h3></div><div id="cd-fmea"></div></div></div>
      <div class="card mt"><div class="card-h"><h3>Chi tiết sự cố</h3><span class="sp" id="cd-count"></span></div><div id="cd-table"></div></div>`;
      const cc = u.$('#cd-chart', root);
      function drawChart() {
        const d = VIEWS[cv]();
        cc.innerHTML = d.length ? u.donut(d, incs.length) : u.empty('Không có sự cố trong bộ lọc');
        u.$$('[data-v]', root).forEach(b => b.onclick = () => { cv = b.dataset.v; u.$$('.seg-tabs button', root).forEach(x => x.classList.toggle('on', x.dataset.v === cv)); drawChart(); drawTable(); });
      }
      function drawTable() {
        const key = { 'Loại nguyên nhân': 'root_cause_type', 'Nhóm lỗi FMEA': null, 'Máy / công đoạn': 'station_id', 'Mức độ': 'severity_level' }[cv];
        const rows = incs.map(i => ({ ...i, _g: key ? i[key] : fm(i) }));
        u.$('#cd-count', root).textContent = `${rows.length} sự cố · nhóm theo ${cv.toLowerCase()}`;
        u.table(u.$('#cd-table', root), {
          cols: [{ k: 'incident_id', t: 'Sự cố' }, { k: 'station_id', t: 'Máy' }, { t: 'Nhóm', r: r => r._g }, { k: 'fmea_code', t: 'FMEA' }, { t: 'Mô tả lỗi', r: r => fmn(r) }, { k: 'rpn', t: 'RPN' }, { k: 'duration_h', t: 'Dừng (h)' }, { t: 'Mức độ', r: r => u.sev(r.severity_level) }],
          rows, pageSize: 10, export: 'phan_bo_nguyen_nhan',
          onRow: r => location.hash = '#/impact?inc=' + r.incident_id
        });
      }
      /* Top FMEA */
      const fmeaAgg = {};
      incs.forEach(i => { const c = i.fmea_code; if (!c) return; fmeaAgg[c] = fmeaAgg[c] || { code: c, n: 0, rpn: 0, desc: '' }; fmeaAgg[c].n++; const f = FS.idx.fmea.get(c) || {}; fmeaAgg[c].rpn = Math.max(fmeaAgg[c].rpn, i.rpn || f.rpn || 0); fmeaAgg[c].desc = f.fmea_description || ''; });
      const top = Object.values(fmeaAgg).sort((a, b) => b.rpn - a.rpn).slice(0, 8);
      u.$('#cd-fmea', root).innerHTML = top.length
        ? top.map(f => `<div class="mrow"><div><b>${f.code}</b><br><small>${u.esc(f.desc)} · ${f.n} sự cố</small></div><div class="bar"><i style="width:${Math.min(100, f.rpn / 1.5)}%;${f.rpn >= 100 ? 'background:#ef4444' : f.rpn >= 50 ? 'background:#f59e0b' : ''}"></i></div><small>RPN ${f.rpn}</small></div>`).join('')
        : u.empty('Chưa đủ dữ liệu FMEA');
      drawChart(); drawTable();
    }
  };
})();
