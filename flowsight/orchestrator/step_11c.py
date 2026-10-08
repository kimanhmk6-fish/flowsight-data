import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

from flowsight.reconstruct.lot_builder import build_canonical_lots
from flowsight.reconstruct.genealogy_builder import (
    build_genealogy_from_scans, validate_genealogy_conservation,
)
from flowsight.reconstruct.allocation_builder import build_jt_allocation
from flowsight.reconstruct.consumption_builder import build_material_consumption
from flowsight.reconstruct.shipment_builder import build_shipment
from flowsight.reconstruct.event_builder import build_lot_events
from flowsight.reconstruct.qc_builder import build_qc_results
from flowsight.reconstruct.auditor import save_reconstruction_audit

from flowsight.storage.loader import verify_load

from flowsight.graph.genealogy_graph import build_genealogy_graph, query_upstream, query_downstream
from flowsight.graph.dependency_graph import build_dependency_graph
from flowsight.graph.serializer import save_graph, export_graphml
from flowsight.graph.config import AUDIT_DIR


def _load_resolved() -> dict:
    """Load 9 file resolved parquet từ 11B."""
    from flowsight.resolve.config import RESOLVED_DIR

    sources = {}
    for src_dir in RESOLVED_DIR.iterdir():
        if not src_dir.is_dir():
            continue
        for f in src_dir.glob("resolved_*.parquet"):
            source_id = src_dir.name
            sources[source_id] = pd.read_parquet(f)
    return sources


def run_step_11c():
    """Chạy toàn bộ Bước 11C."""
    t0 = time.time()

    print("=" * 70)
    print("  FLOWSIGHT — BƯỚC 11C")
    print("  Relationship Reconstruction + Storage + Graph")
    print("=" * 70)

    # ============================================================
    # LOAD RESOLVED (từ 11B)
    # ============================================================
    print("\n[Load] Loading resolved data (từ 11B)...")
    resolved = _load_resolved()
    for sid, df in resolved.items():
        print(f"  ✓ {sid}: {len(df)} rows")

    # ============================================================
    # TẦNG 11C-1: RELATIONSHIP RECONSTRUCTION
    # ============================================================
    print("\n" + "=" * 70)
    print("  TẦNG 11C-1: RELATIONSHIP RECONSTRUCTION")
    print("=" * 70)

    # 1a. Canonical lots
    if "SRC-01_output" in resolved:
        lots = build_canonical_lots(resolved["SRC-01_output"])
    else:
        print("  ⚠ Missing SRC-01_output")
        lots = pd.DataFrame()

    # 1b. Genealogy
    if "SRC-03_qr" in resolved:
        genealogy = build_genealogy_from_scans(resolved["SRC-03_qr"], lots)
        conservation = validate_genealogy_conservation(genealogy, lots)
    else:
        genealogy = pd.DataFrame()
        conservation = {"total_splits": 0, "violations": 0}

    # 1c. Allocation (JT → lots)
    if "SRC-06_jt" in resolved and len(lots) > 0:
        allocation = build_jt_allocation(lots, resolved["SRC-06_jt"])
    else:
        allocation = pd.DataFrame()
        print("  ⚠ Missing SRC-06_jt or no lots")

    # 1d. Material consumption
    if len(lots) > 0:
        consumption = build_material_consumption(lots)
    else:
        consumption = pd.DataFrame()

    # 1e. Shipment
    if "SRC-08_shipping" in resolved:
        shipment = build_shipment(resolved["SRC-08_shipping"])
    else:
        shipment = pd.DataFrame()

    # 1f. Lot events
    if "SRC-02_ipc" in resolved:
        events = build_lot_events(resolved["SRC-02_ipc"])
    else:
        events = pd.DataFrame()

    # 1g. QC results
    qc_auto = resolved.get("SRC-04_qc_auto", pd.DataFrame())
    qc_sample = resolved.get("SRC-05_qc_sampling", pd.DataFrame())
    qc = build_qc_results(qc_auto, qc_sample)

    # Save reconstruction audit
    save_reconstruction_audit({
        "tables_built": {
            "lot": len(lots),
            "lot_edge": len(genealogy),
            "lot_event": len(events),
            "material_consumption": len(consumption),
            "jt_allocation": len(allocation),
            "shipment": len(shipment),
            "qc_result": len(qc),
        },
        "conservation_check": conservation,
    })

    # ============================================================
    # TẦNG 11C-2: STORAGE
    # ============================================================
    print("\n" + "=" * 70)
    print("  TẦNG 11C-2: STORAGE")
    print("=" * 70)

    storage_report = verify_load()

    # ============================================================
    # TẦNG 11C-3: GRAPH
    # ============================================================
    print("\n" + "=" * 70)
    print("  TẦNG 11C-3: GRAPH")
    print("=" * 70)

    # 3a. Genealogy graph
    G_genealogy = build_genealogy_graph()
    if G_genealogy.number_of_nodes() > 0:
        save_graph(G_genealogy, "genealogy")
        export_graphml(G_genealogy, "genealogy")

        # Test queries
        test_nodes = ["LOT-0403", "LOT-0147", "BATCH-HT-B07"]
        for node in test_nodes:
            if node in G_genealogy:
                up = query_upstream(G_genealogy, node)
                down = query_downstream(G_genealogy, node)
                print(f"  ✓ Test {node}: upstream={len(up)}, downstream={len(down)}")
                break

    # 3b. Dependency graph
    G_dependency = build_dependency_graph()
    if G_dependency.number_of_nodes() > 0:
        save_graph(G_dependency, "dependency")
        export_graphml(G_dependency, "dependency")

    # ============================================================
    # SUMMARY
    # ============================================================
    elapsed = time.time() - t0

    report = {
        "step": "11C",
        "run_at": datetime.now(time.timezone.utc).isoformat(),
        "elapsed_sec": round(elapsed, 2),
        "tables_built": {
            "lot": len(lots),
            "lot_edge": len(genealogy),
            "lot_event": len(events),
            "material_consumption": len(consumption),
            "jt_allocation": len(allocation),
            "shipment": len(shipment),
            "qc_result": len(qc),
        },
        "conservation_check": conservation,
        "storage": storage_report,
        "graph": {
            "genealogy_nodes": G_genealogy.number_of_nodes(),
            "genealogy_edges": G_genealogy.number_of_edges(),
            "dependency_nodes": G_dependency.number_of_nodes(),
            "dependency_edges": G_dependency.number_of_edges(),
        },
    }

    with open(AUDIT_DIR / "step_11c_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print(f"  BƯỚC 11C HOÀN TẤT trong {elapsed:.2f}s")
    print(f"  Tables built: {len([v for v in report['tables_built'].values() if v > 0])}")
    print(f"  Total rows: {sum(report['tables_built'].values()):,}")
    print(f"  Genealogy: {G_genealogy.number_of_nodes()} nodes, {G_genealogy.number_of_edges()} edges")
    print(f"  Dependency: {G_dependency.number_of_nodes()} nodes, {G_dependency.number_of_edges()} edges")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_step_11c()
