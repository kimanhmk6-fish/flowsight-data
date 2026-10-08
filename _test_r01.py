from flowsight.engines.shared.graph_loader import load_canonical_tables, load_genealogy_graph
from flowsight.engines.backward.cause_engine import BackwardCauseEngine

tables = load_canonical_tables()
G = load_genealogy_graph()

engine = BackwardCauseEngine(tables, G)
case = {
    "case_id": "R01",
    "lot_id_ng": "LOT-0403",
    "qc_station": "STN-LAB",
    "qc_characteristic": "Luc ep",
}

result = engine.diagnose(case)
print("Status:", result["status"])
print("N candidates:", result.get("n_candidates", 0))

if result["status"] == "RESOLVED":
    top1 = result["top_causes"][0]
    print(f"Top-1: {top1['candidate_id']} ({top1['candidate_type']})")
    print(f"  score={top1['score']:.3f}, p={top1['p_value']:.4f}, lift={top1['lift']:.2f}")
else:
    print("Message:", result.get("message"))
