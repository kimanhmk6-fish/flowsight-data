"""
step4_material_check.py — Bước 4: Material Check (Drum-Buffer-Rope).
"""
import pandas as pd


def compute_material_check(
    tables: dict,
    product_id: str,
    required_qty: float,
) -> dict:
    """
    Kiểm tra vật tư có đủ để bù required_qty không.
    """
    bom = pd.read_csv("data/master/bom.csv") if __import__("pathlib").Path("data/master/bom.csv").exists() else pd.DataFrame()

    if len(bom) == 0:
        return {"status": "no_bom", "materials": []}

    product_bom = bom[bom["product_id"] == product_id]
    materials_needed = []

    mat_cons = tables.get("material_consumption", pd.DataFrame())

    for _, b in product_bom.iterrows():
        comp_id = b["component_id"]
        qty_per_unit = float(b["qty_per_unit"])
        scrap_factor = float(b.get("scrap_factor", 1.002))

        required = required_qty * qty_per_unit * scrap_factor

        # Available từ material_consumption
        if len(mat_cons) > 0:
            available = mat_cons[mat_cons["component_id"] == comp_id]["qty_consumed"].sum()
        else:
            available = 0

        materials_needed.append({
            "component_id": comp_id,
            "qty_per_unit": qty_per_unit,
            "required": round(required, 1),
            "available": round(available, 1),
            "sufficient": available >= required,
        })

    all_sufficient = all(m["sufficient"] for m in materials_needed)

    return {
        "product_id": product_id,
        "required_qty": required_qty,
        "materials": materials_needed,
        "all_sufficient": all_sufficient,
        "status": "ok" if all_sufficient else "shortage",
    }
