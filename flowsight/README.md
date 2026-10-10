# FlowSight — Lot-Level Incident Impact & Cause Intelligence

Prototype dashboard for DENSO Factory Hacks 2026 · Team SUPERNOVA

## Overview

FlowSight is a decision-support analytics platform that links production data to:

- Detect anomalies / incidents
- Analyze root cause & evidence
- Estimate impact propagation (Capacity → Production → Inventory → JT/Order → Delivery)
- Prioritize actions based on impact, urgency and data confidence

**It does not replace** MES, SCADA or production control systems.

## Features (Prototype)

| Module | Priority | Description |
|--------|----------|-------------|
| **Command Center** | P0 | KPI overview, impact chain, trend charts, priority actions |
| **Impact Analysis** | P0 | Select incident → calculate lost qty, shortfall, JT risk, assumptions |
| **Lot Genealogy** | P1 | Forward/backward lot tracing with evidence labels |
| **Data Health** | P0 | Completeness, validity, uniqueness, consistency, referential integrity |
| **Import & Mapping** | P0 | CSV upload, column mapping, error preview (inspired by data-cleanup UX) |
| **Validation Lab** | P1 | Predicted vs Actual, R² / MAPE / RMSE, ground-truth comparison |
| **Architecture** | P2 | Data flow diagram & design principles |

## Data Sources

Aligned with [flowsight-data](https://github.com/kimanhmk6-fish/flowsight-data):

- SRC-01 Production/Machine
- SRC-02 IPC Process
- SRC-03 Lot QR Scans
- SRC-04/05 QC
- SRC-06 JT/Order
- SRC-07 Inventory
- SRC-08 Shipping
- SRC-09 Incident
- Ground truth (impact_truth_F01…F12, cause_truth_R01…R08)

## How to run

```bash
# Simple static server
cd flowsight
python3 -m http.server 8080
# Open http://localhost:8080
```

Or open `index.html` directly in a modern browser (Chart.js is loaded from CDN).

## Kết nối 3 tầng với repo flowsight-data

```
Tầng 1 — Data & Engine (repo flowsight-data, nhánh main):
    data/canonical/*.parquet      → 8 bảng canonical
    data/predictions/forward/     → output 12A (F01: 736 sp, JT-0231, shortfall 29)
    data/predictions/backward/    → output 12B (R01: BATCH-HT-B07)
    data/predictions/what_if/     → output 12C (optimal E)

Tầng 2 — Export (cầu nối, chạy trong repo):
    python -m flowsight.engines.export_dashboard
    → sinh data/dashboard_data.json từ predictions mới nhất

Tầng 3 — UI (thư mục này):
    js/app.js fetch('dashboard_data.json') khi khởi động,
    merge số liệu live vào FS_DATA rồi mới render.
    Nếu mở file trực tiếp (không qua server) → dùng data embedded
    trong js/data.js làm fallback (số liệu đã đồng bộ thủ công).
```

Quy trình cập nhật số liệu sau mỗi lần chạy engines:
1. Trong repo: `python -m flowsight.engines.demo` (chạy F01→R01→what-if)
2. Trong repo: `python -m flowsight.engines.export_dashboard`
3. Copy `data/dashboard_data.json` vào thư mục dashboard (cạnh index.html)
4. Mở lại dashboard → số liệu tự cập nhật, không cần sửa code UI.

## Design principles

1. Every KPI has definition, unit, period and data source.
2. Missing data → “Chưa đủ dữ liệu”, never silent zero.
3. Inferred relationships are clearly labeled vs confirmed keys.
4. Assumptions & formulas are visible and expandable.
5. Prototype only — no live machine control.

## Stack

- Pure HTML / CSS / Vanilla JS
- Chart.js 4 for visualizations
- Inter font
- Responsive (desktop + tablet)

## Team

FlowSight | DENSO Factory Hacks 2026 | Team SUPERNOVA | D3
