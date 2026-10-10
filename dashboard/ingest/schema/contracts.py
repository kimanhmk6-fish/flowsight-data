"""
contracts.py — Pandera schema contracts cho từng nguồn.
Validate dữ liệu sau khi mapping.
"""
try:
    import pandera as pa
    from pandera import Column, DataFrameSchema
    PANDERA_AVAILABLE = True
except ImportError:
    PANDERA_AVAILABLE = False
    print("⚠ Pandera chưa cài. Chạy: pip install pandera")


if PANDERA_AVAILABLE:
    SRC01_OUTPUT_CONTRACT = DataFrameSchema({
        "raw_row_id": Column(str, nullable=False),
        "lot_ref_raw": Column(str, nullable=False),
        "product_ref_raw": Column(str, nullable=True),
        "line_ref_raw": Column(str, nullable=True),
        "qty_ok_raw": Column(str, nullable=True),
        "qty_ng_raw": Column(str, nullable=True),
        "rate_per_h_raw": Column(str, nullable=True),
        "shift_raw": Column(str, nullable=True),
        "event_ts_raw": Column(str, nullable=True),
    }, strict=False)

    SRC02_IPC_CONTRACT = DataFrameSchema({
        "raw_row_id": Column(str, nullable=False),
        "ipc_event_id_raw": Column(str, nullable=False),
        "station_ref_raw": Column(str, nullable=False),
        "lot_ref_raw": Column(str, nullable=True),
        "event_type_raw": Column(str, nullable=False),
        "event_code_raw": Column(str, nullable=True),
        "param_temp_raw": Column(str, nullable=True),
        "param_force_raw": Column(str, nullable=True),
        "param_vib_raw": Column(str, nullable=True),
        "ts_raw": Column(str, nullable=False),
        "export_ts_raw": Column(str, nullable=True),
    }, strict=False)

    SRC03_QR_CONTRACT = DataFrameSchema({
        "raw_row_id": Column(str, nullable=False),
        "scan_id_raw": Column(str, nullable=False),
        "qr_code_raw": Column(str, nullable=False),
        "parent_qr_code_raw": Column(str, nullable=True),
        "scan_type_raw": Column(str, nullable=False),
        "station_ref_raw": Column(str, nullable=False),
        "ts_raw": Column(str, nullable=False),
        "operator_ref_raw": Column(str, nullable=True),
    }, strict=False)

    SRC04_QC_AUTO_CONTRACT = DataFrameSchema({
        "raw_row_id": Column(str, nullable=False),
        "qc_id_raw": Column(str, nullable=False),
        "lot_ref_raw": Column(str, nullable=False),
        "product_ref_raw": Column(str, nullable=True),
        "station_ref_raw": Column(str, nullable=True),
        "characteristic_raw": Column(str, nullable=True),
        "value_raw": Column(str, nullable=True),
        "lsl_raw": Column(str, nullable=True),
        "usl_raw": Column(str, nullable=True),
        "result_raw": Column(str, nullable=True),
        "ng_code_raw": Column(str, nullable=True),
        "ts_raw": Column(str, nullable=True),
    }, strict=False)

    SRC06_JT_CONTRACT = DataFrameSchema({
        "raw_row_id": Column(str, nullable=False),
        "jt_ref_raw": Column(str, nullable=False),
        "product_ref_raw": Column(str, nullable=True),
        "line_ref_raw": Column(str, nullable=True),
        "qty_raw": Column(str, nullable=True),
        "due_date_raw": Column(str, nullable=True),
        "priority_raw": Column(str, nullable=True),
        "customer_raw": Column(str, nullable=True),
        "status_raw": Column(str, nullable=True),
    }, strict=False)

    CONTRACTS = {
        "SRC-01_output": SRC01_OUTPUT_CONTRACT,
        "SRC-02_ipc": SRC02_IPC_CONTRACT,
        "SRC-03_qr": SRC03_QR_CONTRACT,
        "SRC-04_qc_auto": SRC04_QC_AUTO_CONTRACT,
        "SRC-06_jt": SRC06_JT_CONTRACT,
    }
else:
    CONTRACTS = {}


def validate_contract(df, source_id: str):
    """Validate df against contract. Raise nếu FAIL."""
    if not PANDERA_AVAILABLE:
        return True
    if source_id not in CONTRACTS:
        return True

    contract = CONTRACTS[source_id]
    try:
        contract.validate(df, lazy=True)
        return True
    except pa.errors.SchemaErrors as e:
        print(f"  ⚠ Contract violation for {source_id}:")
        print(e.failure_cases.head(10))
        raise
