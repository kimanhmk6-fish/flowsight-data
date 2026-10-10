/* FlowSight — Sample data derived from flowsight-data GitHub repo structure */

const FS_DATA = {
  incidents: [
    { id: 'INC-0001', station: 'STN-M2', stationName: 'Máy ép thủy lực M2', start: '2026-09-29T08:00:00', end: '2026-09-29T16:00:00', duration: 8.0, fmea: 'FMEA-M2-001', rpn: 96, severity: 'HIGH', rootCause: 'MACHINE', lots: ['LOT-0005','LOT-0009'], case: 'F01', desc: 'M2 - Dừng máy 8h' },
    { id: 'INC-0003', station: 'STN-M2', stationName: 'Máy ép thủy lực M2', start: '2026-10-01T08:00:00', end: '2026-10-01T20:00:00', duration: 12.0, fmea: 'FMEA-M2-001', rpn: 128, severity: 'CRITICAL', rootCause: 'MACHINE', lots: ['LOT-0231','LOT-0235'], case: 'F03', desc: 'M2 - Dừng máy 12h CRITICAL' },
    { id: 'INC-0005', station: 'STN-HT', stationName: 'Lò nhiệt luyện HT', start: '2026-10-03T08:00:00', end: '2026-10-03T16:00:00', duration: 8.0, fmea: 'FMEA-HT-001', rpn: 135, severity: 'CRITICAL', rootCause: 'PROCESS', lots: ['LOT-0401','LOT-0402','LOT-0403','LOT-0404','LOT-0405'], case: 'F05', desc: 'HT - Lỗi nhiệt luyện' },
    { id: 'INC-0008', station: 'STN-M2', stationName: 'Máy ép thủy lực M2', start: '2026-10-05T16:00:00', end: '2026-10-06T00:00:00', duration: 8.0, fmea: 'FMEA-M2-001', rpn: 96, severity: 'HIGH', rootCause: 'MACHINE', lots: ['LOT-0232'], case: 'F08', desc: 'M2 - Dừng máy ca đêm' },
    { id: 'INC-0013', station: 'STN-HT', stationName: 'Lò nhiệt luyện HT', start: '2026-09-30T16:00:00', end: '2026-09-30T16:30:00', duration: 0.5, fmea: 'FMEA-HT-001', rpn: 135, severity: 'HIGH', rootCause: 'BATCH', lots: ['LOT-0403','LOT-0404'], case: 'R01', desc: 'HT - Mẻ lò B07 gây NG lực ép (p=0.0001, lift=82.2)' },
  ],

  openIncidents: [
    { id: 'INC-0001', title: 'M2 - Dừng máy 8h', meta: '14:20 · Line 1 · P1', severity: 'high', label: 'Cao' },
    { id: 'INC-L005', title: 'Lò L005 - NG cuối line', meta: '10:15 · Line 2 · P2', severity: 'medium', label: 'Trung bình' },
    { id: 'INC-DATA', title: 'Lệch giờ dữ liệu', meta: '08:30 · Line 1', severity: 'low', label: 'Thấp' },
  ],

  jtRisks: [
    { rank: 1, jt: 'JT-0231', product: 'P1', shortfall: 29, pLate: 100 },
    { rank: 2, jt: 'JT-0005', product: 'P1', shortfall: 2350, pLate: 100 },
    { rank: 3, jt: 'JT-0001', product: 'P1', shortfall: 2350, pLate: 100 },
    { rank: 4, jt: 'JT-0009', product: 'P1', shortfall: 557, pLate: 100 },
    { rank: 5, jt: 'JT-0013', product: 'P1', shortfall: 557, pLate: 100 },
  ],

  shipments: [
    { rank: 1, order: 'SHP-1002-1 (JT-0231)', date: '01/10', status: 'Thiếu 100/1300', type: 'warning' },
    { rank: 2, order: 'SHP-1001-1 (JT-0001)', date: '01/10', status: 'Đúng hạn 600/600', type: 'success' },
    { rank: 3, order: 'SHP-1010-1 (JT-0235)', date: '10/10', status: 'Đúng hạn 600/600', type: 'success' },
  ],

  actions: [
    { num: 1, title: 'E: Resequencing + OT2 cho JT-0231', desc: 'Giảm P(trễ): 100% → 1.0%, chi phí 3.7M VND', severity: 'Cao' },
    { num: 2, title: 'Khoanh vùng BATCH-HT-B07 (5 lots)', desc: 'LOT-0401..0405: kiểm tra lực ép, cách ly LOT-0403/0404', severity: 'Cao' },
    { num: 3, title: 'Theo dõi JT-0231 (giao 01/10)', desc: 'Thiếu 29 sp sau khi bù; xác nhận với khách hàng', severity: 'Trung bình' },
  ],

  impactCases: {
    'INC-0001': {
      duration: '8.0h',
      lost: 736,
      shortfall: 29,
      pLate: '100%',
      jt: 'JT-0231',
      lots: 'LOT-0005, LOT-0009',
      action: 'resequencing + OT2',
      station: 'STN-M2 · Máy ép thủy lực',
      rate: 92,
      fmea: 'FMEA-M2-001',
      affectedJT: [
        { jt: 'JT-0231', product: 'PROD-P1', qty: 1300, due: '2026-10-01', shortfall: 29, pLate: 1.0, action: 'resequencing + OT2', status: 'HIGH RISK' },
      ]
    },
    'INC-0003': {
      duration: '12.0h',
      lost: 1200,
      shortfall: 350,
      pLate: '99.8%',
      jt: 'JT-0231, JT-0235',
      lots: 'LOT-0231, LOT-0235',
      action: 'OT + external capacity',
      station: 'STN-M2 · Máy ép thủy lực',
      rate: 100,
      fmea: 'FMEA-M2-001',
      affectedJT: [
        { jt: 'JT-0231', product: 'PROD-P1', qty: 1300, due: '2026-10-02', shortfall: 200, pLate: 0.998, action: 'OT + external', status: 'CRITICAL' },
        { jt: 'JT-0235', product: 'PROD-P2', qty: 600, due: '2026-10-03', shortfall: 150, pLate: 0.92, action: 'resequence', status: 'HIGH RISK' },
      ]
    },
    'INC-0005': {
      duration: '8.0h',
      lost: 160,
      shortfall: 160,
      pLate: '85%',
      jt: 'Multiple',
      lots: 'LOT-0401…LOT-0405',
      action: 'Batch rework + HT recovery',
      station: 'STN-HT · Lò nhiệt luyện',
      rate: 20,
      fmea: 'FMEA-HT-001',
      affectedJT: [
        { jt: 'JT-0401', product: 'PROD-P3', qty: 900, due: '2026-10-04', shortfall: 160, pLate: 0.85, action: 'Batch rework', status: 'HIGH RISK' },
      ]
    },
    'INC-0008': {
      duration: '8.0h',
      lost: 800,
      shortfall: 80,
      pLate: '72%',
      jt: 'JT-0232',
      lots: 'LOT-0232',
      action: 'OT2',
      station: 'STN-M2 · Máy ép thủy lực',
      rate: 100,
      fmea: 'FMEA-M2-001',
      affectedJT: [
        { jt: 'JT-0232', product: 'PROD-P1', qty: 900, due: '2026-10-06', shortfall: 80, pLate: 0.72, action: 'OT2', status: 'MEDIUM' },
      ]
    }
  },

  dqSources: [
    { src: 'SRC-01', name: 'Production/Machine', file: 'output_perf', rows: 411, valid: 411, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-02', name: 'IPC Process', file: 'ipc_events', rows: 3088, valid: 3088, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-03', name: 'Lot QR Scans', file: 'lot_qr_scans', rows: 3027, valid: 3027, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-04', name: 'QC Auto', file: 'qc_auto', rows: 411, valid: 411, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-05', name: 'QC Manual', file: 'qc_manual', rows: 822, valid: 822, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-06', name: 'JT/Order', file: 'jt_orders', rows: 47, valid: 47, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-07', name: 'Inventory', file: 'inventory_snap', rows: 140, valid: 140, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-08', name: 'Shipping', file: 'shipping_plan', rows: 3, valid: 3, errors: 0, warnings: 0, status: 'Hợp lệ' },
    { src: 'SRC-09', name: 'Incident', file: 'incidents', rows: 20, valid: 20, errors: 0, warnings: 0, status: 'Hợp lệ' },
  ],

  stations: {
    'STN-M2': { name: 'Máy ép thủy lực M2', line: 'A', rate: 92, bottleneck: true },
    'STN-M1': { name: 'Máy phay CNC M1', line: 'A', rate: 128.57, bottleneck: false },
    'STN-HT': { name: 'Lò nhiệt luyện HT', line: 'SHARED', rate: 20, bottleneck: false },
    'STN-AS2': { name: 'Lắp ráp thủ công AS2', line: 'B', rate: 65.45, bottleneck: false },
  },

  trend: {
    labels: ['01/10','02/10','03/10','04/10','05/10','06/10','07/10'],
    actual: [1200, 1350, 1100, 1400, 1250, 1600, 1450],
    plan: [1500, 1500, 1500, 1500, 1500, 1500, 1500],
    incidents: [1, 0, 2, 0, 1, 1, 0]
  }
};
