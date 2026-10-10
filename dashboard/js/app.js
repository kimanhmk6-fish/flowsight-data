/* FlowSight — Main Application Logic */

(function () {
  'use strict';

  // ---------- Tầng kết nối: load số liệu thật từ repo flowsight-data ----------
  // File dashboard_data.json do `python -m flowsight.engines.export_dashboard`
  // sinh ra từ predictions. Nếu không có (mở file trực tiếp), dùng data
  // embedded trong data.js làm fallback.
  async function loadLiveData() {
    try {
      const res = await fetch('dashboard_data.json');
      if (!res.ok) return;
      const live = await res.json();
      // Merge F01
      if (live.f01) {
        const f = live.f01;
        const ic = FS_DATA.impactCases['INC-0001'];
        if (ic) {
          ic.lost = f.qty_lost;
          ic.shortfall = f.shortfall;
          ic.pLate = f.p_late + '%';
          ic.jt = f.jt_late;
          ic.action = f.action;
          ic.affectedJT[0].shortfall = f.shortfall;
          ic.affectedJT[0].pLate = f.p_late / 100;
          ic.affectedJT[0].jt = f.jt_late;
        }
        // what-if options -> actions list
        if (f.what_if && f.what_if.length) {
          const opt = f.what_if.find(o => o.recommended);
          if (opt) {
            FS_DATA.actions[0] = {
              num: 1,
              title: opt.id + ': ' + opt.name + ' cho ' + f.jt_late,
              desc: 'Giảm P(trễ) xuống ' + opt.p_late + '%, chi phí ' +
                    Math.round(opt.cost).toLocaleString('vi-VN') + ' VND',
              severity: 'Cao'
            };
          }
        }
      }
      // Merge R01
      if (live.r01) {
        const r = live.r01;
        const inc = FS_DATA.incidents.find(i => i.case === 'R01');
        if (inc) inc.desc = 'HT - ' + r.top_cause + ' gây NG (p=' +
                            r.p_value + ', lift=' + r.lift + ')';
      }
      console.log('[FlowSight] Đã nạp số liệu live từ dashboard_data.json');
    } catch (e) {
      console.log('[FlowSight] Dùng data embedded (không tìm thấy dashboard_data.json)');
    }
  }

  // ---------- Navigation ----------
  const views = document.querySelectorAll('.view');
  const navItems = document.querySelectorAll('.nav-item');
  const breadcrumb = document.getElementById('breadcrumb');
  const sidebar = document.getElementById('sidebar');

  const viewTitles = {
    dashboard: 'Command Center',
    impact: 'Impact Analysis',
    genealogy: 'Lot Genealogy',
    datahealth: 'Data Health',
    validation: 'Validation Lab',
    architecture: 'Architecture & Docs',
    import: 'Import Data',
    mapping: 'Data Mapping',
    settings: 'Settings'
  };

  function switchView(name) {
    views.forEach(v => v.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));
    const target = document.getElementById('view-' + name);
    if (target) target.classList.add('active');
    const nav = document.querySelector(`[data-view="${name}"]`);
    if (nav) nav.classList.add('active');
    if (breadcrumb) breadcrumb.textContent = viewTitles[name] || name;
    // Re-init charts when switching
    if (name === 'dashboard') initDashboardCharts();
    if (name === 'validation') initValChart();
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const view = item.dataset.view;
      if (view) switchView(view);
      if (window.innerWidth <= 900) sidebar.classList.remove('open');
    });
  });

  document.getElementById('toggleSidebar')?.addEventListener('click', () => {
    if (window.innerWidth <= 900) {
      sidebar.classList.toggle('open');
    } else {
      sidebar.classList.toggle('collapsed');
    }
  });

  // ---------- Dashboard population ----------
  function renderIncidents() {
    const list = document.getElementById('incidentList');
    if (!list) return;
    list.innerHTML = FS_DATA.openIncidents.map(inc => `
      <div class="incident-item">
        <div class="inc-severity ${inc.severity}"></div>
        <div>
          <div class="inc-title">${inc.title}</div>
          <div class="inc-meta">${inc.meta}</div>
        </div>
        <span class="inc-badge ${inc.severity}">${inc.label}</span>
      </div>
    `).join('');
  }

  function renderJTRisks() {
    const tbody = document.getElementById('jtRiskTable');
    if (!tbody) return;
    tbody.innerHTML = FS_DATA.jtRisks.map(r => `
      <tr>
        <td>${r.rank}</td>
        <td><strong>${r.jt}</strong></td>
        <td>${r.product}</td>
        <td>${r.shortfall}</td>
        <td>
          <div style="display:flex;align-items:center;gap:6px">
            <div class="bar" style="width:60px;height:6px"><div style="width:${r.pLate}%;background:${r.pLate>70?'#EF4444':r.pLate>40?'#F59E0B':'#10B981'}"></div></div>
            <strong>${r.pLate}%</strong>
          </div>
        </td>
      </tr>
    `).join('');
  }

  function renderShipments() {
    const tbody = document.getElementById('shipTable');
    if (!tbody) return;
    tbody.innerHTML = FS_DATA.shipments.map(s => `
      <tr>
        <td>${s.rank}</td>
        <td><strong>${s.order}</strong></td>
        <td>${s.date}</td>
        <td><span class="badge ${s.type === 'danger' ? 'danger' : s.type === 'warning' ? 'warning' : 'success'}">${s.status}</span></td>
      </tr>
    `).join('');
  }

  function renderActions() {
    const list = document.getElementById('actionList');
    if (!list) return;
    list.innerHTML = FS_DATA.actions.map(a => `
      <div class="action-item">
        <div class="action-num">${a.num}</div>
        <div class="action-body">
          <div class="action-title">${a.title}</div>
          <div class="action-desc">${a.desc}</div>
        </div>
        <span class="badge ${a.severity === 'Cao' ? 'danger' : a.severity === 'Trung bình' ? 'warning' : 'info'}">${a.severity}</span>
      </div>
    `).join('');
  }

  // ---------- Charts ----------
  let causeChart, trendChart, valChart;

  function initDashboardCharts() {
    // Cause donut
    const causeCtx = document.getElementById('causeChart');
    if (causeCtx) {
      if (causeChart) causeChart.destroy();
      causeChart = new Chart(causeCtx, {
        type: 'doughnut',
        data: {
          labels: ['Máy móc', 'Vật tư', 'Lỗi QC', 'Ca / Nhân sự', 'Khác'],
          datasets: [{
            data: [45, 20, 15, 10, 10],
            backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
            borderWidth: 0,
            cutout: '70%'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { display: false }, tooltip: { enabled: true } }
        }
      });
    }

    // Trend line
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
      if (trendChart) trendChart.destroy();
      trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: FS_DATA.trend.labels,
          datasets: [
            {
              label: 'Sản lượng thực tế',
              data: FS_DATA.trend.actual,
              borderColor: '#3B82F6',
              backgroundColor: 'rgba(59,130,246,.08)',
              fill: true,
              tension: 0.3,
              pointRadius: 4,
              pointBackgroundColor: '#3B82F6'
            },
            {
              label: 'Sản lượng kế hoạch',
              data: FS_DATA.trend.plan,
              borderColor: '#94A3B8',
              borderDash: [6, 4],
              fill: false,
              tension: 0,
              pointRadius: 0
            },
            {
              label: 'Sự cố máy',
              data: FS_DATA.trend.incidents.map(v => v * 200),
              borderColor: '#EF4444',
              backgroundColor: '#EF4444',
              type: 'bar',
              barThickness: 12,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 2000, grid: { color: '#F1F5F9' }, ticks: { font: { size: 11 } } },
            y1: { display: false, max: 600 },
            x: { grid: { display: false }, ticks: { font: { size: 11 } } }
          }
        }
      });
    }
  }

  function initValChart() {
    const ctx = document.getElementById('valChart');
    if (!ctx) return;
    if (valChart) valChart.destroy();
    valChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12'],
        datasets: [
          {
            label: 'Predicted',
            data: [110, 130, 105, 140, 120, 145, 155, 280, 220, 240, 180, 165],
            borderColor: '#1E40AF',
            backgroundColor: 'rgba(30,64,175,.1)',
            fill: false,
            tension: 0.3,
            pointRadius: 3
          },
          {
            label: 'Actual',
            data: [120, 115, 110, 135, 145, 150, 160, 250, 260, 230, 190, 175],
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59,130,246,.1)',
            fill: false,
            tension: 0.3,
            pointRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', align: 'end', labels: { boxWidth: 12, usePointStyle: true } }
        },
        scales: {
          y: { beginAtZero: true, max: 300, grid: { color: '#F1F5F9' }, ticks: { callback: v => v + 'K' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // ---------- Impact Analysis ----------
  function runImpact() {
    const sel = document.getElementById('incidentSelect');
    const id = sel?.value || 'INC-0001';
    const data = FS_DATA.impactCases[id];
    if (!data) return;

    document.getElementById('impDuration').textContent = data.duration;
    document.getElementById('impLost').textContent = data.lost.toLocaleString();
    document.getElementById('impShortfall').textContent = data.shortfall.toLocaleString();
    document.getElementById('impPlate').textContent = data.pLate;

    const tbody = document.getElementById('impactJTTable');
    if (tbody) {
      tbody.innerHTML = data.affectedJT.map(j => `
        <tr>
          <td><strong>${j.jt}</strong></td>
          <td>${j.product}</td>
          <td>${j.qty}</td>
          <td>${j.due}</td>
          <td><strong>${j.shortfall}</strong></td>
          <td><strong style="color:${j.pLate > 0.8 ? '#DC2626' : j.pLate > 0.4 ? '#D97706' : '#059669'}">${(j.pLate * 100).toFixed(1)}%</strong></td>
          <td>${j.action}</td>
          <td><span class="badge ${j.status.includes('CRITICAL') || j.status.includes('HIGH') ? 'danger' : 'warning'}">${j.status}</span></td>
        </tr>
      `).join('');
    }

    // Update prop flow briefly
    const flow = document.getElementById('propFlow');
    if (flow) {
      flow.querySelector('.prop-node:first-child .prop-id').textContent = id;
      flow.querySelector('.prop-node:first-child .prop-detail').textContent = `${data.station.split('·')[0].trim()} · ${data.duration} · ${data.fmea}`;
    }
  }

  document.getElementById('runImpact')?.addEventListener('click', runImpact);
  document.getElementById('incidentSelect')?.addEventListener('change', runImpact);

  // ---------- Data Health table ----------
  function renderDQ() {
    const tbody = document.getElementById('dqTable');
    if (!tbody) return;
    tbody.innerHTML = FS_DATA.dqSources.map(s => {
      const statusClass = s.status === 'Hợp lệ' ? 'success' : 'warning';
      return `
        <tr>
          <td><strong>${s.src}</strong></td>
          <td>${s.name}</td>
          <td class="muted">${s.file}</td>
          <td>${s.rows.toLocaleString()}</td>
          <td class="text-success">${s.valid.toLocaleString()}</td>
          <td class="${s.errors ? 'text-danger' : ''}">${s.errors}</td>
          <td class="${s.warnings ? 'text-warning' : ''}">${s.warnings}</td>
          <td><span class="badge ${statusClass}">${s.status}</span></td>
          <td><button class="link-btn">Xem →</button></td>
        </tr>
      `;
    }).join('');
  }

  // ---------- Lot search ----------
  document.getElementById('searchLot')?.addEventListener('click', () => {
    const lotId = document.getElementById('lotSearch')?.value.trim() || 'LOT-0147';
    const info = document.getElementById('lotInfo');
    if (info) {
      info.querySelector('.info-row:first-child strong').textContent = lotId;
    }
  });

  // ---------- Dropzone ----------
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', e => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      const files = e.dataTransfer?.files;
      if (files?.length) {
        dropzone.querySelector('p').textContent = `Đã chọn: ${files[0].name}`;
      }
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files?.length) {
        dropzone.querySelector('p').textContent = `Đã chọn: ${fileInput.files[0].name}`;
      }
    });
  }

  // ---------- Global search ----------
  document.getElementById('globalSearch')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim().toUpperCase();
      if (q.startsWith('LOT')) {
        switchView('genealogy');
        const inp = document.getElementById('lotSearch');
        if (inp) inp.value = q;
      } else if (q.startsWith('INC') || q.startsWith('JT')) {
        switchView('impact');
      } else if (q.startsWith('STN')) {
        switchView('dashboard');
      }
    }
  });

  // ---------- Init ----------
  function init() {
    // Nạp số liệu live từ repo trước, rồi mới render (fallback: data embedded)
    loadLiveData().then(() => {
      renderIncidents();
      renderJTRisks();
      renderShipments();
      renderActions();
      renderDQ();
      runImpact();
      initDashboardCharts();
    });

    // Ensure charts resize properly
    window.addEventListener('resize', () => {
      causeChart?.resize();
      trendChart?.resize();
      valChart?.resize();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
