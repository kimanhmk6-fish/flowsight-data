# FlowSight Pipeline Contract — 11A→11E

## Input (immutable)
- data/raw/SRC-01_output/output_perf_LineA_20260929.csv     (utf-8-sig, sep=,)
- data/raw/SRC-02_ipc/ipc_M2_20260929.csv                   (utf-8, sep=,)
- data/raw/SRC-03_qr/lot_scans.csv                          (utf-8, sep=,)
- data/raw/SRC-04_qc_auto/qc_autotest_LineA_20260929.csv    (utf-8, sep=,)
- data/raw/SRC-05_qc_sampling/qc_sampling_W39.xlsx          (2 sheet: Data, Day_9)
- data/raw/SRC-06_jt/plan_jt_orders.csv                     (utf-8, sep=;)
- data/raw/SRC-07_inventory/inventory_snapshot.csv          (utf-8, sep=,)
- data/raw/SRC-08_shipping/shipping_plan.csv                (utf-8, sep=,)
- data/raw/SRC-09_incident/andon_scans.csv                  (utf-8, sep=,)
- data/ground_truth/entity_mapping_truth.csv                (dùng cho 11B resolve)
- data/master/*.csv                                         (dùng cho 11E fact)

## Output
| Tầng | Folder | Nội dung |
|---|---|---|
| Bronze (11A) | data/staged/*.parquet | Cột chuẩn + lot_ref_norm |
| Silver (11B-D) | data/curated/*.parquet | + canonical_lot_id, ts_aligned, dq_flag |
| Gold (11E) | data/mart/fact_production.parquet | Sự kiện join |
| Gold (11E) | data/mart/kpi_by_station.parquet | KPI theo trạm |
| Audit | data/audit/ingestion_log.json | Log 9 nguồn |

## Cột metadata bắt buộc
- _raw_row_id, _source_file, _ingested_at

## Nguyên tắc
- KHÔNG sửa data/raw/
- KHÔNG commit data/staged, curated, mart, audit
- Time alignment: anchor-based (median+MAD), fallback hard-code
- Entity resolution: exact match → suffix fallback


