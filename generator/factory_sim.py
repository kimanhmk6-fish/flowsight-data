import simpy
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config.constants import (
    SEED, NUM_DAYS, TARGET_LOTS, STATION_IDS,
    PRODUCT_IDS, START_DATE_STR,
)

np.random.seed(SEED)


class FactorySim:
    """
    Mô phỏng nhà máy 2 line, 10 trạm, 4 sản phẩm, 14 ngày × 2 ca.
    """

    def __init__(self, env: simpy.Environment):
        self.env = env
        self.lots = []           # list[dict] canonical lots
        self.events = []         # list[dict] production events
        self.genealogy = []      # list[dict] SPLIT/MERGE edges
        self.consumption = []    # list[dict] material consumption
        self.current_day = 0
        self.lot_counter = 0
        self.edge_counter = 0

    # ============================================================
    # DAY LOOP
    # ============================================================
    def run_day(self, day: int):
        """Mô phỏng 1 ngày (2 ca). Sinh ~28-30 lots/ngày."""
        self.current_day = day
        print(f"  [Sim] Day D{day}...")

        # TODO: sinh lot theo kế hoạch P1/P2/P3/P4
        #   - P1 và P2 đi qua M2 (bottleneck)
        #   - P3 và P4 chỉ đi qua AS2 (line B)
        #   - ~28 lots/ngày, chia đều 4 sản phẩm

        # TODO: cho mỗi lot chạy qua routing
        #   routing = [INB, M1, M2, HT, AS1, T1, PK, SHP] cho P1/P2
        #   routing = [INB, M1, AS2, T1, PK, SHP] cho P3/P4

        # TODO: xử lý tách mẻ HT
        #   - Mẻ BATCH_HT_B07 (1000 sp) → 5 lots con (200 sp) vào D1
        #   - Mẻ BATCH_HT_B08 (1000 sp) → 5 lots con (200 sp) vào D3

    # ============================================================
    # LOT CREATION
    # ============================================================
    def create_lot(
        self,
        product_id: str,
        qty: int = 200,
        parent_batch: str = None,
        day_idx: int = None,
    ) -> dict:
        """Tạo 1 canonical lot mới. Trả về dict."""
        self.lot_counter += 1
        lot_id = f"LOT_{self.lot_counter:04d}"

        # TODO: tính created_ts từ day_idx + shift + hour
        # TODO: append vào self.lots
        # TODO: gọi _consume_materials(lot)
        pass

    def split_batch(
        self,
        batch_id: str,
        num_children: int = 5,
        qty_per_child: int = 200,
        day_idx: int = 1,
    ):
        """Tách mẻ HT thành nhiều lots con. Ghi genealogy SPLIT."""
        # TODO: tạo num_children lots con với parent_batch=batch_id
        # TODO: append edge SPLIT vào self.genealogy
        pass

    def merge_lots(self, parent_lot_ids: list, child_lot_id: str, day_idx: int):
        """Gộp nhiều lots thành 1 lot mới. Ghi genealogy MERGE."""
        # TODO: append edge MERGE vào self.genealogy
        pass

    # ============================================================
    # STATION PROCESSING
    # ============================================================
    def process_at_station(self, lot: dict, station_id: str, seq_no: int):
        """Lot đi qua 1 trạm. Sinh event START/WARN/ERR/END."""
        # TODO: tính duration từ cycle_time_s × qty
        # TODO: sinh param_temp, param_force, param_vibration
        # TODO: chèn micro anomaly (~4% events) với is_physical_anomaly=True
        # TODO: append event vào self.events
        pass

    def _consume_materials(self, lot: dict):
        """Tiêu hao vật tư theo BOM (FIFO)."""
        # TODO: đọc BOM của product
        # TODO: chọn material_lot theo FIFO (received_ts < lot.created_ts)
        # TODO: append consumption record
        pass

    # ============================================================
    # QC / INCIDENT / SHIPMENT
    # ============================================================
    def generate_qc(self, lot: dict):
        """Sinh QC result cho lot (AUTO + có thể SAMPLE)."""
        # TODO: 2 đặc tính AUTO cho mọi lot
        # TODO: 10% lots có thêm 3 đặc tính SAMPLE
        pass

    def generate_incidents(self):
        """Sinh 20 macro incidents (12 cho F, 8 cho R)."""
        # TODO: hard-code hoặc đọc từ danh sách incidents
        pass

    def generate_shipments(self):
        """Sinh 30 shipments."""
        # TODO
        pass


# ============================================================
# RUN
# ============================================================
def run_simulation() -> FactorySim:
    """Chạy full simulation 14 ngày."""
    env = simpy.Environment()
    factory = FactorySim(env)

    for day in range(NUM_DAYS):
        factory.run_day(day)

    # Post-processing
    factory.generate_incidents()
    factory.generate_shipments()

    return factory


if __name__ == "__main__":
    factory = run_simulation()
    print(f"\n✓ Đã tạo {len(factory.lots)} lots")
    print(f"✓ Đã tạo {len(factory.events)} events")
    print(f"✓ Đã tạo {len(factory.genealogy)} genealogy edges")
