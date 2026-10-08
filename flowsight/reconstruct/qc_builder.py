import pandas as pd
from .config import CANONICAL_DIR

def build_qc_results(
    resolved_qc_auto: pd.DataFrame,
    resolved_qc_sampling: pd.DataFrame,
) -> pd.DataFrame:
    """Tái dựng bảng qc_result từ 2 nguồn QC."""
    print("\n[11C-1g] Building QC results...")
    
    # 1. AUTO (SRC-04)
    if len(resolved_qc_auto) > 0:
        qc_auto = pd.DataFrame({
            "qc_id": resolved_qc_auto.get("qc_id_raw", resolved_qc_auto.get("qc_id")),
            "lot_id": resolved_qc_auto.get("lot_canonical_id"),
            "station_id": resolved_qc_auto.get("station_ref_norm", resolved_qc_auto.get("station_ref_raw")),
            "test_type": "AUTO",
            "characteristic": resolved_qc_auto.get("characteristic_raw", resolved_qc_auto.get("characteristic")),
            "value": pd.to_numeric(
                resolved_qc_auto.get("value_norm", resolved_qc_auto.get("value_raw", resolved_qc_auto.get("value"))), 
                errors="coerce"
            ),
            "lsl": pd.to_numeric(
                resolved_qc_auto.get("lsl_norm", resolved_qc_auto.get("lsl_raw", resolved_qc_auto.get("lsl"))), 
                errors="coerce"
            ),
            "usl": pd.to_numeric(
                resolved_qc_auto.get("usl_norm", resolved_qc_auto.get("usl_raw", resolved_qc_auto.get("usl"))), 
                errors="coerce"
            ),
            "result": resolved_qc_auto.get("result_norm", resolved_qc_auto.get("result_raw", resolved_qc_auto.get("result"))),
            "ng_code": resolved_qc_auto.get("ng_code_raw"),
            "measured_ts": pd.to_datetime(
                resolved_qc_auto.get("ts_aligned", resolved_qc_auto.get("ts_raw")), 
                errors="coerce", 
                dayfirst=True
            ),
            "source": "SRC-04_qc_auto",
        })
    else:
        qc_auto = pd.DataFrame()

    # 2. SAMPLE (SRC-05)
    if len(resolved_qc_sampling) > 0:
        val_col = resolved_qc_sampling.get("value_norm", resolved_qc_sampling.get("value_raw", resolved_qc_sampling.get("value")))
        station_col = resolved_qc_sampling.get("station_ref_norm", resolved_qc_sampling.get("station_ref_raw", resolved_qc_sampling.get("station")))
        char_col = resolved_qc_sampling.get("characteristic_raw", resolved_qc_sampling.get("characteristic"))
        
        qc_sample = pd.DataFrame({
            "qc_id": [f"QC-S-{i:05d}" for i in range(len(resolved_qc_sampling))],
            "lot_id": resolved_qc_sampling.get("lot_canonical_id"),
            "station_id": station_col,
            "test_type": "SAMPLE",
            "characteristic": char_col,
            "value": pd.to_numeric(val_col, errors="coerce"),
            "lsl": None,
            "usl": None,
            "result": None,
            "ng_code": None,
            "measured_ts": pd.to_datetime(
                resolved_qc_sampling.get("ts_aligned", resolved_qc_sampling.get("ts_raw")), 
                errors="coerce", 
                dayfirst=True
            ),
            "source": "SRC-05_qc_sampling",
        })
    else:
        qc_sample = pd.DataFrame()

    qc_all = pd.concat([qc_auto, qc_sample], ignore_index=True)
    qc_all = qc_all.dropna(subset=["lot_id"])
    out_path = CANONICAL_DIR / "qc_result.parquet"
    qc_all.to_parquet(out_path, index=False)
    print(f" ✓ Total: {len(qc_all)} QC records -> {out_path.name}")
    return qc_all