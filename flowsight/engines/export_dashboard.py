"""
export_dashboard.py — Xuất dữ liệu cho dashboard 12D (giao diện HTML).

Đọc predictions của engines (12A/12B/12C) và sinh file JSON mà dashboard
tĩnh (flowsight-dashboard) load qua fetch. Đây là "cầu nối" giữa tầng
data/engine (repo flowsight-data) và tầng UI (dashboard).

Kiến trúc 3 tầng:
    Tầng 1 — Data/Engine (repo này):
        data/canonical/*.parquet  → dữ liệu chuẩn
        data/predictions/         → output 12A/12B/12C
    Tầng 2 — Export (script này):
        đọc predictions → dashboard_data.json
    Tầng 3 — UI (flowsight-dashboard/):
        js/data.js fetch dashboard_data.json (fallback: data embedded)

Chạy:
    python -m flowsight.engines.export_dashboard
    # → data/dashboard_data.json
    # Copy file này vào thư mục dashboard (cạnh index.html) rồi mở dashboard.
"""
import json
from pathlib import Path

PRED = Path("data/predictions")
OUT = Path("data/dashboard_data.json")


def load_json(fp: Path) -> dict:
    if fp.exists():
        with open(fp, encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_f01() -> dict:
    fwd = load_json(PRED / "forward" / "F01_prediction.json")
    wif = load_json(PRED / "what_if" / "F01_what_if.json")
    s = fwd.get("summary", {})
    jt = (s.get("jts_late") or [{}])[0]

    options = []
    for o in wif.get("scored", []):
        if o.get("option_id") in "ABCDE":
            options.append({
                "id": o["option_id"],
                "name": o["option_name"],
                "p_late": round(o["p_late"] * 100, 1),
                "cost": o["total_cost"],
                "recommended": o.get("is_recommended", False),
            })
    return {
        "incident_id": "INC-0001",
        "station": "STN-M2",
        "duration_h": 8.0,
        "qty_lost": round(s.get("qty_lost", 0)),
        "jt_late": jt.get("jt_id"),
        "shortfall": s.get("total_shortage", 0),
        "p_late": round(jt.get("p_late", 0) * 100, 1),
        "action": s.get("recommended_action"),
        "affected_lots": s.get("affected_lot_ids", [])[:8],
        "what_if": options,
        "optimal": (wif.get("optimal") or {}).get("option_id"),
    }


def build_r01() -> dict:
    r = load_json(PRED / "backward" / "R01_prediction.json")
    top = (r.get("top_causes") or [{}])[0]
    return {
        "lot_ng": r.get("lot_id_ng", "LOT-0403"),
        "top_cause": r.get("top_cause"),
        "cause_type": r.get("top_cause_type"),
        "p_value": top.get("p_value"),
        "lift": top.get("lift"),
        "confidence": r.get("confidence"),
        "isolate_lots": r.get("isolate_lots", []),
    }


def main():
    data = {
        "generated_from": "flowsight-data main",
        "f01": build_f01(),
        "r01": build_r01(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Đã xuất: {OUT}")
    print(f"  F01: mất {data['f01']['qty_lost']} sp, {data['f01']['jt_late']} "
          f"thiếu {data['f01']['shortfall']} sp, optimal={data['f01']['optimal']}")
    print(f"  R01: {data['r01']['top_cause']} (p={data['r01']['p_value']})")


if __name__ == "__main__":
    main()
