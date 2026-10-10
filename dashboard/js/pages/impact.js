/* FR-03 Impact Analysis */
FS.q = () => Object.fromEntries(new URLSearchParams((location.hash.split('?')[1] || '')));
(function () {
  const u = FS.ui;
  FS.pages.impact = { title: 'Impact Analysis', sub: 'Chọn sự cố, kiểm tra thông số, tính sản lượng mất, thiếu hụt ròng và JT/Order bị ảnh hưởng', noFilter: true, render(root) {
    const all = FS.tables.incident_truth, q = FS.q(); let id = q.inc || all[0].incident_id, dur = q.dur != null ? +q.dur : null;
    const C = FS.config;
    function draw() {
      const inc = all.find(i => i.incident_id === id), R = FS.engine.impact(inc, dur != null ? { durH: dur } : {}), what = dur != null && dur !== inc.duration_h;
      root.innerHTML = `<div class="card"><div class="row"><label>Sự cố<select id="i">${all.map(i => `<option value="${i.incident_id}" ${i.incident_id === id ? 'selected' : ''}>${i.incident_id} · ${i.station_id} · ${i.duration_h}h · ${i.test_case_link}</option>`).join('')}</select></label>
        <label>Thời gian dừng (h) — what-if<input type="number" id="d" step=".5" min="0" value="${R.durH}" style="width:110px"></label>
        <label>Lịch SX (giờ bắt đầu–kết thúc)<span class="row"><input type="number" id="s1" value="${C.schedStart}" style="width:62px" min="0" max="23"><input type="number" id="s2" value="${C.schedEnd}" style="width:62px" min="1" max="24"></span></label>
        <label>% FG khả dụng<input type="number" id="fg" value="${C.fgUsablePct}" style="width:80px" min="0" max="100"></label>
        <label class="row"><input type="checkbox" id="rc" ${C.useRecovery ? 'checked' : ''}> Dùng công suất bù</label>
        <button class="btn" id="go">Tính lại</button>${what ? `<button class="btn ghost" id="rs">Về giá trị gốc (${inc.duration_h}h)</button>` : ''}<span class="sp">${u.prov(R.status)} ${what ? u.badge('What-if', 'violet', '✎') : ''}</span></div></div>
      <div class="grid g4 mt">${u.kpi({ label: 'Giờ SX bị mất', value: R.lostH, unit: 'h', icon: '⏱', color: 'blue', def: 'Thời gian dừng giao với lịch sản xuất' })}${u.kpi({ label: 'Sản lượng mất lý thuyết', value: R.lostQty, unit: 'sp', icon: '▤', color: 'amber', nodata: R.lostQty == null, def: 'giờ mất × công suất' })}${u.kpi({ label: 'Thiếu hụt ròng', value: R.net, unit: 'sp', icon: '◔', color: 'red', nodata: R.net == null, sub: R.status, def: 'Sau tồn kho khả dụng & công suất bù' })}${u.kpi({ label: 'JT/Order có nguy cơ', value: R.atRisk.length, unit: '/ ' + R.jts.length, icon: '☰', color: 'violet', def: 'exposure > 0' })}</div>
      <div class="grid g2 mt"><div class="card"><div class="card-h"><h3>Kế hoạch – tồn kho – dự báo</h3><span class="sp">${u.badge('Dự báo', 'amber', '≈')}</span></div>${u.bars([{ k: 'Mất lý thuyết', v: R.lostQty || 0, c: u.C.red }, { k: 'FG khả dụng', v: R.fgUsable, c: u.C.green }, { k: 'Thiếu sau tồn', v: R.deficit || 0, c: u.C.amber }, { k: 'Bù / ngày', v: R.perDay, c: u.C.cyan }, { k: 'Thiếu ròng', v: R.net || 0, c: u.C.violet }], ' sp')}
        <div class="callout info">Số liệu <b>thực tế</b>: thời gian dừng, tồn kho snapshot. <b>Giả định</b>: lịch SX, %FG khả dụng, công suất bù. <b>Dự báo</b>: sản lượng mất, thiếu hụt, JT nguy cơ.</div></div>
        <div class="card"><div class="card-h"><h3>Chuỗi ảnh hưởng</h3></div><div class="chain">${[['⚙', 'Sự cố', inc.station_id, 'c-red'], ['▤', 'Mất SL', FS.fmt.n(R.lostQty), 'c-amber'], ['▣', 'FG/WIP', FS.fmt.n(R.fgUsable), 'c-green'], ['☰', 'JT', R.atRisk.length, 'c-blue'], ['▷', 'Giao hàng', R.shipRisk.length, 'c-violet']].map((s, i, a) => `<div class="step"><div class="ic ${s[3]}">${s[0]}</div><b>${s[2]}</b><small>${s[1]}</small></div>${i < a.length - 1 ? '<span class="ar">→</span>' : ''}`).join('')}</div>
        <small class="muted">WIP không cộng với FG để tránh đếm trùng cùng một lượng sản phẩm.</small></div></div>
      <div class="card mt"><div class="card-h"><h3>JT/Order bị ảnh hưởng</h3><small>Bấm dòng để xem căn cứ liên kết</small></div><div id="t"></div></div>
      <details class="fx mt" open><summary>Giả định & công thức (tái lập được)</summary><table class="tbl mt"><tbody>${R.steps.map(s => `<tr><td><b>${s[0]}</b></td><td>${s[1]}</td><td class="muted">${s[2]}</td></tr>`).join('')}</tbody></table>
        <ul>${R.assume.map(a => `<li>${a}</li>`).join('')}<li>Ngưỡng rủi ro: ${C.thresholdOn ? `Cao ≥ ${C.thHigh}% · TB ≥ ${C.thMid}% (ngưỡng dung sai quy định (Tolerance Threshold))` : 'Chưa cấu hình ngưỡng'}</li><li>Không khẳng định giao trễ khi chưa đối chiếu lịch giao & phương án phục hồi.</li></ul></details>`;
      u.$('#i', root).onchange = e => { id = e.target.value; dur = null; draw(); };
      u.$('#go', root).onclick = () => { dur = +u.$('#d', root).value; C.schedStart = +u.$('#s1', root).value; C.schedEnd = +u.$('#s2', root).value; C.fgUsablePct = +u.$('#fg', root).value; C.useRecovery = u.$('#rc', root).checked; if (FS.auth.can('config')) FS.saveConfig('Thay đổi tham số từ Impact Analysis'); u.toast('Đã tính lại các chỉ số phụ thuộc'); draw(); };
      const rs = u.$('#rs', root); if (rs) rs.onclick = () => { dur = null; draw(); };
      u.table(u.$('#t', root), { rows: R.jts, export: 'jt_bi_anh_huong_' + id, pageSize: 8, empty: 'Không xác định được JT liên quan — Chưa đủ dữ liệu liên kết', cols: [
        { t: 'JT/Order', r: x => x.jt.jt_id, x: x => x.jt.jt_id }, { t: 'SP', r: x => x.jt.product_id, x: x => x.jt.product_id }, { t: 'SL', r: x => x.jt.qty, x: x => x.jt.qty }, { t: 'Hạn giao', r: x => FS.fmt.d(x.jt.due_ts), x: x => x.jt.due_ts },
        { t: 'Slack (h)', r: x => FS.fmt.n(x.slackH), x: x => x.slackH, s: x => x.slackH }, { t: 'Đã phân bổ', r: x => x.alloc || '—', x: x => x.alloc }, { t: 'Thiếu ước tính', r: x => FS.fmt.n(x.exposure), x: x => x.exposure, s: x => x.exposure },
        { t: 'Liên kết', r: x => u.prov(x.link), x: x => x.link }, { t: 'Rủi ro', r: x => u.badge(x.risk.t, x.risk.c, x.risk.i), x: x => x.risk.t }, { t: 'Giao hàng', r: x => x.ship.map(s => s.status).join(', ') || 'Chưa có lịch giao', x: x => x.ship.map(s => s.status).join(',') }],
        onRow: x => u.modal('Căn cứ ' + x.jt.jt_id, u.kv([['Liên kết', u.prov(x.link)], ['Căn cứ', x.basis], ['Khách hàng', x.jt.customer], ['Ưu tiên', x.jt.priority], ['Line', x.jt.line_id], ['Giao hàng', x.ship.map(s => `${s.shipment_id}: ${s.qty_actual}/${s.qty_planned} ${s.status}`).join('<br>') || 'Chưa có dữ liệu lịch giao → không kết luận trễ']])) });
    }
    draw();
  } };
})();
