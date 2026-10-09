# FlowSight — Data Pipeline & Intelligence Engines

Hệ thống dữ liệu và engine truy vết cho bài toán DENSO Factory Hacks 2026 (đề D3).

## Kiến trúc pipeline

```
generator/                 → dữ liệu mô phỏng + ground truth (nguồn chuẩn, seed=42)
  factory_sim.py           → mô phỏng nhà máy 14 ngày
  ground_truth_builder.py  → 12 bảng truth + đáp án 24 case (F01–F12, R01–R08, D01–D04)
  export_raw.py            → xuất 9 nguồn RAW (data/raw/SRC-*)
  error_injector.py        → chèn lỗi D01–D10 vào RAW
  validator.py             → kiểm chứng 41 rules (schema, volume, FK, genealogy, JT, F01...)
flowsight/ingest/          → 11A: đọc RAW → staged (chuẩn hóa ID, timestamp, đơn vị)
flowsight/align/           → 11B: time alignment (anchor-based)
flowsight/resolve/         → 11B: entity resolution (exact → suffix → temporal)
flowsight/reconstruct/     → 11C: dựng bảng canonical (data/canonical/*.parquet) + graph
flowsight/engines/         → 12: Forward (12A), Backward (12B), Action Simulator (12C)
```

## Thứ tự chạy tái sinh toàn bộ

```bash
pip install -r requirements.txt

# 1. Sinh ground truth (nguồn chuẩn)
python -m generator.ground_truth_builder

# 2. Xuất 9 nguồn RAW (kèm lỗi D01–D10)
python -m generator.export_raw

# 3. Kiểm chứng dữ liệu (41 rules)
python -m generator.validator

# 4. Ingestion → Staged
python -m flowsight.ingest.runner

# 5. Time Alignment + Entity Resolution
python -m flowsight.orchestrator.step_11b

# 6. Reconstruction → Canonical + Graph
python -m flowsight.orchestrator.step_11c

# 7. Engines
python -m flowsight.engines.runner_12a   # Forward Impact Cascade (F01–F12)
python -m flowsight.engines.runner_12b   # Backward Cause Ranking (R01–R08)
python -m flowsight.engines.runner_12c   # Action Simulator / What-if
python -m flowsight.engines.runner_12e   # Validation: F1/MAPE/Brier/Top-3 + báo cáo gộp
```

## Output chính

- `data/ground_truth/` — đáp án kiểm chứng (không sửa thủ công, tái sinh từ generator)
- `data/canonical/*.parquet` — 8 bảng canonical engine đọc
- `data/predictions/` — output từng case của engine
- `reports/` — `forward_engine_report.json`, `backward_engine_report.json`,
  `action_engine_report.json`, `validation_24cases.json`, `benchmark_report.csv`

## Quy ước

- Canonical ID dùng dấu gạch ngang `-` (VD: `LOT-0147`, `JT-0231`, `BATCH-HT-B07`).
- Mọi thay đổi nghiệp vụ (JT, tồn kho, allocation, đáp án case) sửa trong
  `generator/` rồi chạy lại pipeline — không sửa file output thủ công.
- Trạng thái demo các case xem trong `reports/*_engine_report.json`
  (so sánh `top_cause`/`jts_late` thực tế với `expected_*`).

## Demo trực tiếp (1 lệnh)
```bash
python -m flowsight.engines.demo            # chạy mới F01 → R01 → what-if
python -m flowsight.engines.demo --cached   # đọc predictions đã lưu
```

## Case demo cốt lõi (đã kiểm chứng)

- **F01**: incident M2 dừng 8h (D0) → JT-0231 trễ, shortfall 29 sp, đề xuất `resequencing + OT2`.
- **R01**: lot NG LOT-0403 → top-1 `BATCH-HT-B07` (Fisher p=0.0001, lift=82.2),
  khoanh vùng LOT-0401..0405.
