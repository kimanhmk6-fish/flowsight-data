"""
cost_model.py — Model chi phí cho mỗi phương án.
"""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional




@dataclass
class CostBreakdown:
    overtime_cost: float
    changeover_cost: float
    shipping_cost: float
    penalty_cost: float
    total_cost: float
    currency: str = "VND"




class CostModel:
    """Cost model đọc từ yaml."""


    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path("data/config/cost_config.yaml")


        if not config_path.exists():
            raise FileNotFoundError(f"Cost config không tồn tại: {config_path}")


        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)


        self.currency = self.config.get("currency", "VND")


    def compute_overtime_cost(self, ot_hours: float, n_operators: int = 5) -> float:
        """Chi phí tăng ca."""
        if ot_hours <= 0:
            return 0.0
        hourly = self.config["labor"]["operator_hourly_rate"]
        multiplier = self.config["overtime"]["hourly_multiplier"]
        energy = self.config["overtime"]["energy_cost_per_hour"]


        labor_cost = ot_hours * hourly * multiplier * n_operators
        energy_cost = ot_hours * energy
        return labor_cost + energy_cost


    def compute_changeover_cost(self, n_changeovers: int = 1) -> float:
        """Chi phí đổi khuôn."""
        if n_changeovers <= 0:
            return 0.0
        return self.config["changeover"]["fixed_cost"] * n_changeovers


    def compute_expedite_shipping_cost(self, n_late_jts: int, expedite: bool = False) -> float:
        """Chi phí vận chuyển."""
        if n_late_jts <= 0:
            return 0.0
        base = self.config["shipping"]["normal_cost_per_truck"]
        if expedite:
            return base * self.config["shipping"]["expedite_multiplier"] * n_late_jts
        return base * n_late_jts


    def compute_penalty_cost(self, n_late_jts: int, avg_delay_hours: float) -> float:
        """Chi phí phạt trễ."""
        if n_late_jts <= 0 or avg_delay_hours <= 0:
            return 0.0
        penalty_per_hour = self.config["shipping"]["late_penalty_per_hour"]
        return n_late_jts * avg_delay_hours * penalty_per_hour


    def compute_total(
        self,
        ot_hours: float = 0,
        n_changeovers: int = 0,
        n_expedite_shipments: int = 0,
        n_late_jts: int = 0,
        avg_delay_hours: float = 0,
        use_expedite: bool = False,
    ) -> CostBreakdown:
        """Tính tổng chi phí."""
        ot = self.compute_overtime_cost(ot_hours)
        ch = self.compute_changeover_cost(n_changeovers)
        sh = self.compute_expedite_shipping_cost(n_expedite_shipments, use_expedite)
        pen = self.compute_penalty_cost(n_late_jts, avg_delay_hours)


        total = ot + ch + sh + pen


        return CostBreakdown(
            overtime_cost=round(ot, 0),
            changeover_cost=round(ch, 0),
            shipping_cost=round(sh, 0),
            penalty_cost=round(pen, 0),
            total_cost=round(total, 0),
            currency=self.currency,
        )
