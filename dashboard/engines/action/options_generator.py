"""
options_generator.py — Sinh các phương án hành động.
"""
from dataclasses import dataclass, asdict




@dataclass
class ActionOption:
    option_id: str
    name: str
    description: str
    ot_hours: float
    n_changeovers: int
    expedite: bool
    use_alternative: bool
    priority_reorder: bool




def generate_standard_options(
    incident_duration_h: float,
    has_alternative_line: bool = True,
) -> list:
    """Sinh 5-7 phương án chuẩn cho 1 incident."""


    options = [
        ActionOption(
            option_id="A", name="Do nothing",
            description="Để yên, chấp nhận rủi ro",
            ot_hours=0, n_changeovers=0, expedite=False,
            use_alternative=False, priority_reorder=False,
        ),
        ActionOption(
            option_id="B", name="OT2 — Tăng ca 2h",
            description="Tăng ca 2h ngày hôm sau để bù sản lượng",
            ot_hours=2, n_changeovers=0, expedite=False,
            use_alternative=False, priority_reorder=False,
        ),
        ActionOption(
            option_id="C", name="OT4 — Tăng ca 4h",
            description="Tăng ca 4h để bù hoàn toàn sản lượng",
            ot_hours=4, n_changeovers=0, expedite=False,
            use_alternative=False, priority_reorder=False,
        ),
        ActionOption(
            option_id="D", name="Resequencing",
            description="Đổi thứ tự sản xuất để ưu tiên JT gấp",
            ot_hours=0, n_changeovers=1, expedite=False,
            use_alternative=False, priority_reorder=True,
        ),
        ActionOption(
            option_id="E", name="Resequencing + OT2",
            description="Đổi thứ tự + tăng ca 2h. Kết hợp tối ưu.",
            ot_hours=2, n_changeovers=1, expedite=False,
            use_alternative=False, priority_reorder=True,
        ),
    ]


    if has_alternative_line:
        options.append(ActionOption(
            option_id="F", name="Alternative Line",
            description="Chuyển tải sang line dự phòng",
            ot_hours=0, n_changeovers=0, expedite=False,
            use_alternative=True, priority_reorder=False,
        ))


    options.append(ActionOption(
        option_id="G", name="Expedite shipping",
        description="Giao hàng hỏa tốc (nhưng vẫn trễ)",
        ot_hours=0, n_changeovers=0, expedite=True,
        use_alternative=False, priority_reorder=False,
    ))


    return options




def options_to_dict(options: list) -> list:
    return [asdict(o) for o in options]
