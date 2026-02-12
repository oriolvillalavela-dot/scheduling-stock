from typing import List, Optional
from pydantic import BaseModel

class StockSettings(BaseModel):
    eq_aryl: float
    M_aryl: float
    eq_alkyl: float
    M_alkyl: float
    mg_aryl_per_well: float = 0.1  # mg per well basis for aryl
    overage_pct: float = 10.0
    include_controls: bool = False

class OtherReagent(BaseModel):
    name: str
    eq: float
    M: float
    smiles: Optional[str] = None

class StockPlanRequest(BaseModel):
    day: int
    include_next_day: bool = False
    settings: StockSettings
    other_reagents: List[OtherReagent] = []

class WellCell(BaseModel):
    well: str
    is_control: bool
    alkyl_id: Optional[str] = None
    aryl_id: Optional[str] = None

class PlatePreview(BaseModel):
    plate_number: int
    day_number: int
    cells: List[WellCell]
