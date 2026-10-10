/* Sub-tab helper dùng chung cho các trang wrapper */
(function () {
  FS.subtabs = function (root, tabs, defaultKey) {
    // tabs: [{key, label, page}] — page là key trong FS.pages
    const u = FS.ui;
    let cur = defaultKey || tabs[0].key;
    // Đọc sub-tab từ hash: #/incident_intel?tab=impact
    const m = (location.hash.match(/tab=([a-z_]+)/) || [])[1];
    if (m && tabs.some(t => t.key === m)) cur = m;

    function render() {
      const tab = tabs.find(t => t.key === cur);
      const pg = FS.pages[tab.page];
      root.innerHTML = `
        <div class="subtabs">
          ${tabs.map(t => `<button class="subtab ${t.key === cur ? 'on' : ''}" data-tab="${t.key}">${t.label}</button>`).join('')}
        </div>
        <div id="subview" class="subview"></div>`;
      u.$$('.subtab', root).forEach(b => b.onclick = () => {
        cur = b.dataset.tab;
        // Cập nhật hash giữ context
        const base = location.hash.split('?')[0];
        history.replaceState(null, '', base + '?tab=' + cur);
        render();
        if (window.lucide) lucide.createIcons();
      });
      const sv = u.$('#subview', root);
      try {
        // Ẩn filter bar nếu page con yêu cầu
        if (pg.noFilter) u.$('#filters').style.display = 'none';
        else u.$('#filters').style.display = '';
        pg.render(sv);
        if (window.lucide) lucide.createIcons();
      } catch (e) {
        console.error(e);
        sv.innerHTML = `<div class="card"><h3>Lỗi hiển thị</h3><p>${u.esc(e.message)}</p></div>`;
      }
    }
    render();
  };
})();
