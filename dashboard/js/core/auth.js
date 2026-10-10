/* Đăng nhập / đăng ký / phân quyền theo vai trò (NFR-04). Lưu ý: xác thực phía trình duyệt chỉ phục vụ demo prototype. */
FS.auth = (function () {
  const PERM = { 'Admin': { import: 1, export: 1, config: 1, decide: 1 }, 'Analyst / Data Engineer': { import: 1, export: 1 }, 'Production Planning': { export: 1, decide: 1 }, 'Production / Line Leader': { export: 1, decide: 1 }, 'Maintenance': { decide: 1 }, 'Inventory / Material': { export: 1 }, 'Delivery / Sales': { export: 1 }, 'Quality Control': { export: 1 }, 'Manager / Decision Maker': { export: 1, decide: 1 }, 'Viewer': {} };
  const LBL = { import: 'Nhập dữ liệu', export: 'Xuất dữ liệu', config: 'Cấu hình', decide: 'Ghi nhận quyết định' };
  const DEMO = [['admin@flowsight.demo', 'Quản trị viên', 'Admin', 'Admin@123'], ['analyst@flowsight.demo', 'Trần Thị Phân Tích', 'Analyst / Data Engineer', 'Analyst@123'], ['planner@flowsight.demo', 'Nguyễn Văn A', 'Production Planning', 'Planner@123'], ['viewer@flowsight.demo', 'Khách xem', 'Viewer', 'Viewer@123']];
  const users = () => FS.persist.get('users', []), esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  async function hash(s) { try { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('fs:' + s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); } catch (e) { let h = 2166136261; for (const c of 'fs:' + s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return 'f' + (h >>> 0).toString(16); } }
  const cur = () => { const e = FS.persist.get('session', null); return e ? users().find(x => x.email === e) || null : null; };
  const can = a => { const c = cur(); return !!(c && PERM[c.role] && PERM[c.role][a]); };
  const log = what => { const L = FS.persist.get('audit', []); const c = cur(); L.unshift({ t: new Date().toISOString().slice(0, 19).replace('T', ' '), who: c ? c.email : '—', what }); L.length = Math.min(L.length, 80); FS.persist.set('audit', L); };
  const need = a => { if (can(a)) return true; const c = cur(); FS.ui.toast(`Vai trò "${c ? c.role : '—'}" không có quyền: ${LBL[a]}`, 'warn'); log('Bị từ chối: ' + LBL[a]); return false; };
  async function seed() { if (users().length) return; const U = []; for (const d of DEMO) U.push({ email: d[0], name: d[1], role: d[2], hash: await hash(d[3]), demo: 1 }); FS.persist.set('users', U); }
  function show() {
    document.body.classList.add('locked'); const A = document.getElementById('auth'); let tab = 'in', fails = 0, lockUntil = 0;
    const draw = (msg, ok) => { A.innerHTML = `<div class="auth-l"><div class="brand"><div class="brand-marks"><span class="brand-denso">DENSO</span><span class="brand-x">×</span><img class="brand-img" src="assets/logoflowsight.png" alt="FlowSight"></div><small class="brand-tagline">Hệ thống Phân tích Tác động Sự cố &amp; Nguyên nhân cấp Lô</small></div>
      <div class="auth-copy"><h2>Từ một sự cố máy, nhanh chóng xác định các lô, đơn hàng và chuyến giao hàng bị ảnh hưởng.</h2>
      <p class="tagline">Kết nối dữ liệu sự cố máy với Lot, JT và thông tin giao hàng để hỗ trợ truy xuất tác động.</p>
      <p class="quote">“Từ sự cố đến hành động — dựa trên dữ liệu và trí tuệ.”</p></div>
      <div class="brand-footer"><span class="brand-denso">DENSO</span><span class="brand-x">×</span><span>Control Tower</span><small>v0.4.2 · 2026-10-10</small></div></div>
      <div class="auth-r"><div class="card auth-card"><div class="steps"><span class="${tab === 'in' ? 'on' : ''}" data-t="in" style="cursor:pointer">Đăng nhập</span><span class="${tab === 'up' ? 'on' : ''}" data-t="up" style="cursor:pointer">Đăng ký</span></div>
      ${msg ? `<div class="callout ${ok ? 'ok' : 'err'}">${msg}</div>` : ''}
      ${tab === 'in' ? `<label class="fl">Email<input id="a-e" type="email" autocomplete="username" placeholder="ten@congty.com"></label><label class="fl">Mật khẩu<input id="a-p" type="password" autocomplete="current-password"></label><button class="btn wide" id="a-go">Đăng nhập</button>
        <div class="demo-acc"><small>Tài khoản dùng thử (bấm để điền):</small>${DEMO.map(d => `<button class="btn sm ghost" data-d="${d[0]}|${d[3]}">${d[2]}</button>`).join('')}</div>`
        : `<label class="fl">Họ tên<input id="r-n"></label><label class="fl">Email<input id="r-e" type="email"></label><label class="fl">Vai trò<select id="r-r">${Object.keys(PERM).filter(r => r !== 'Admin').map(r => `<option>${r}</option>`).join('')}</select></label><label class="fl">Mật khẩu (≥ 8 ký tự, có chữ và số)<input id="r-p" type="password" autocomplete="new-password"></label><label class="fl">Nhập lại mật khẩu<input id="r-p2" type="password" autocomplete="new-password"></label><button class="btn wide" id="a-reg">Tạo tài khoản</button>`}
      <small class="muted" style="display:block;margin-top:12px">Bản thử nghiệm dành cho đánh giá ý tưởng cuộc thi DENSO Factory Hacks 2026.</small></div></div>`;
      A.querySelectorAll('[data-t]').forEach(s => s.onclick = () => { tab = s.dataset.t; draw(); });
      A.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { const [e, p] = b.dataset.d.split('|'); A.querySelector('#a-e').value = e; A.querySelector('#a-p').value = p; });
      const q = id => A.querySelector(id), enter = e => { if (e.key === 'Enter') (q('#a-go') || q('#a-reg')).click(); }; A.querySelectorAll('input').forEach(i => i.onkeydown = enter);
      if (q('#a-go')) q('#a-go').onclick = async () => { if (Date.now() < lockUntil) return draw('Thử sai quá nhiều lần. Vui lòng đợi ' + Math.ceil((lockUntil - Date.now()) / 1000) + ' giây.'); const e = q('#a-e').value.trim().toLowerCase(), u = users().find(x => x.email === e);
        if (u && u.hash === await hash(q('#a-p').value)) { FS.persist.set('session', u.email); log('Đăng nhập'); A.innerHTML = ''; FS.auth.onLogin(); } else { fails++; if (fails >= 5) { lockUntil = Date.now() + 30000; fails = 0; } log('Đăng nhập thất bại: ' + e); draw('Email hoặc mật khẩu không đúng.'); } };
      if (q('#a-reg')) q('#a-reg').onclick = async () => { const n = q('#r-n').value.trim(), e = q('#r-e').value.trim().toLowerCase(), p = q('#r-p').value;
        if (!n) return draw('Vui lòng nhập họ tên.'); if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) return draw('Email không hợp lệ.'); if (p.length < 8 || !/[A-Za-z]/.test(p) || !/\d/.test(p)) return draw('Mật khẩu cần ≥ 8 ký tự, gồm chữ và số.'); if (p !== q('#r-p2').value) return draw('Mật khẩu nhập lại không khớp.'); if (users().some(x => x.email === e)) return draw('Email đã được đăng ký.');
        const U = users(); U.push({ email: e, name: n, role: q('#r-r').value, hash: await hash(p) }); FS.persist.set('users', U); log('Đăng ký ' + e); tab = 'in'; draw('Đăng ký thành công. Hãy đăng nhập.', true); };
    }; draw();
  }
  function chip() { const c = cur(); if (!c) return; const el = document.getElementById('usr'); el.innerHTML = `<div class="av">${esc(c.name.split(' ').slice(-2).map(w => w[0]).join('').toUpperCase())}</div><div><b>${esc(c.name)}</b><small>${esc(c.role)}</small></div><button class="icon-btn logout-icon" id="logout-btn" title="Đăng xuất" aria-label="Đăng xuất"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></button>`;
    const lb = el.querySelector('#logout-btn');
    if (lb) { lb.onclick = (e) => { e.stopPropagation(); if (confirm('Đăng xuất khỏi FlowSight?')) { log('Đăng xuất'); FS.persist.set('session', null); location.reload(); } }; }
    el.onclick = () => { const m = FS.ui.modal('Tài khoản', FS.ui.kv([['Họ tên', esc(c.name)], ['Email', esc(c.email)], ['Vai trò', esc(c.role)], ['Quyền', Object.keys(LBL).map(k => PERM[c.role][k] ? FS.ui.badge(LBL[k], 'green', '✔') : FS.ui.badge(LBL[k], 'gray', '✕')).join(' ')]]) + '<div class="row mt"><button class="btn danger" id="lo">Đăng xuất</button></div>'); m.el.querySelector('#lo').onclick = () => { log('Đăng xuất'); FS.persist.set('session', null); location.reload(); }; }; }
  function panel() { return `<div class="grid g2 mt"><div class="card"><h3>Phân quyền theo vai trò</h3><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Vai trò</th>${Object.values(LBL).map(l => `<th>${l}</th>`).join('')}</tr></thead><tbody>${Object.entries(PERM).map(([r, p]) => `<tr><td>${r}</td>${Object.keys(LBL).map(k => `<td>${p[k] ? '✔' : '—'}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div>
    <div class="card"><h3>Nhật ký truy cập</h3>${FS.persist.get('audit', []).slice(0, 10).map(l => `<div class="tl"><div><b>${esc(l.what)}</b><br><small>${l.t} · ${esc(l.who)}</small></div></div>`).join('') || '<small class="muted">Chưa có.</small>'}</div></div>`; }
  async function init(onLogin) {
    FS.auth.onLogin = () => { document.body.classList.remove('locked'); chip(); onLogin(); }; await seed();
    const od = FS.csv.download; FS.csv.download = (n, t, m) => { if (!need('export')) return; log('Xuất ' + n); od(n, t, m); };
    if (cur()) { log('Mở phiên'); FS.auth.onLogin(); } else show();
  }
  return { init, can, need, log, cur, panel, PERM };
})();
