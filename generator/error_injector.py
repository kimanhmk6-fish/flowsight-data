import numpy as np
import pandas as pd
from datetime import timedelta
from config.constants import (
    SEED, CLOCK_OFFSET, DRIFT_PER_DAY_SEC,
    DECIMAL_COMMA_DAYS, SCHEMA_DRIFT_DAY
)

np.random.seed(SEED)

class ErrorInjector:
    def __init__(self):
        self.injected_log = []

    # D01: Clock Offset & Drift cho trạm IPC (M2: -4m, AS2: +6m)
    def apply_clock_offset(self, df: pd.DataFrame, station_col="machine_code", ts_col="ts_raw") -> pd.DataFrame:
        df = df.copy()
        for idx, row in df.iterrows():
            stn = f"STN-{row[station_col]}" if not str(row[station_col]).startswith("STN-") else row[station_col]
            if stn in CLOCK_OFFSET:
                base_offset = CLOCK_OFFSET[stn]
                drift = DRIFT_PER_DAY_SEC.get(stn, 0.0)
                try:
                    ts_dt = pd.to_datetime(row[ts_col])
                    day_idx = (ts_dt.date() - pd.to_datetime("2026-09-29").date()).days
                    day_idx = max(0, day_idx)
                except Exception:
                    day_idx = 0
                total_adj = base_offset + (drift * day_idx)
                adjusted_ts = ts_dt + timedelta(seconds=total_adj)
                df.at[idx, ts_col] = adjusted_ts.strftime("%Y-%m-%dT%H:%M:%S")
        return df

    # D02: Missing Scan (xóa 2% scans ở các trạm chuyển tiếp, ưu tiên case F01, R01)
    def remove_missing_scans(self, df_scans: pd.DataFrame, drop_rate=0.02) -> pd.DataFrame:
        df = df_scans.copy()
        transition_stns = ["HT", "AS1", "AS2", "T1"]
        
        # Mandatory drop: LOT-0005, 0009, 0403, 0404 tại trạm chuyển tiếp (lot F01/R01)
        mandatory_mask = df["qr_code"].str.contains("0005|0009|0403|0404", na=False) & df["station_code"].isin(transition_stns)
        mandatory_indices = df[mandatory_mask].index.tolist()
        
        n_drop_total = int(len(df) * drop_rate)
        n_random = max(0, n_drop_total - len(mandatory_indices))
        
        candidates = df[(~df.index.isin(mandatory_indices)) & (df["station_code"].isin(transition_stns))].index.tolist()
        if len(candidates) > n_random:
            random_indices = list(np.random.choice(candidates, size=n_random, replace=False))
        else:
            random_indices = candidates
            
        drop_all = list(set(mandatory_indices + random_indices))
        df_cleaned = df.drop(index=drop_all).reset_index(drop=True)
        return df_cleaned

    # D03: Duplicate Lot ID (1% trùng nhãn, cụ thể LOT-0404 lấy mã của LOT-0403 cho Case R05)
    def inject_duplicate_lot(self, df_qr: pd.DataFrame) -> pd.DataFrame:
        df = df_qr.copy()
        mask_0403 = df["qr_code"].str.contains("0403", na=False)
        if mask_0403.any():
            qr_0403 = df.loc[mask_0403, "qr_code"].iloc[0]
            mask_0404 = df["qr_code"].str.contains("0404", na=False)
            df.loc[mask_0404, "qr_code"] = qr_0403
        return df

    # D04: Schema Drift Excel (Đổi tên cột ở ngày thứ 9)
    def apply_schema_drift_day9(self, df_qc_day9: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "local_lot_ref": "Mã lô",
            "value_raw": "Giá trị",
            "characteristic": "Đặc tính",
            "measured_date": "Ngày đo",
            "station_code": "Mã trạm",
            "inspector": "Người kiểm tra"
        }
        return df_qc_day9.rename(columns=rename_map)

    # D05: Dấu phẩy thập phân ở 3 ngày (D2, D5, D10)
    def apply_decimal_comma(self, df_qc: pd.DataFrame, day_indices=DECIMAL_COMMA_DAYS) -> pd.DataFrame:
        df = df_qc.copy()
        for idx, row in df.iterrows():
            try:
                dt = pd.to_datetime(row["measured_ts_raw"], format="%d/%m/%Y %H:%M:%S")
                d_idx = (dt.date() - pd.to_datetime("2026-09-29").date()).days
                if d_idx in day_indices:
                    for col in ["value_raw", "lsl", "usl"]:
                        if col in df.columns and pd.notna(df.at[idx, col]):
                            df.at[idx, col] = str(df.at[idx, col]).replace(".", ",")
            except Exception:
                pass
        return df

    # D06: Manual Noise (50% snapshot tồn kho MANUAL bị làm tròn đến hàng chục)
    def round_manual_inventory(self, df_inv: pd.DataFrame) -> pd.DataFrame:
        df = df_inv.copy()
        mask_manual = df["capture_method"] == "MANUAL"
        for idx in df[mask_manual].index:
            try:
                val = float(df.at[idx, "qty_raw"])
                df.at[idx, "qty_raw"] = str(int(round(val / 10.0) * 10))
            except Exception:
                pass
        return df
