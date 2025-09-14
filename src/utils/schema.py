from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class BGPUpdate(BaseModel):
    ts: int
    peer: str
    type: str  # "UPDATE" | "NOTIFICATION" | etc.
    announce: Optional[List[str]] = None
    withdraw: Optional[List[str]] = None
    attrs: Optional[Dict[str, Any]] = None


class FeatureBin(BaseModel):
    bin_start: int
    bin_end: int
    totals: Dict[str, float]
    peers: Dict[str, Dict[str, float]]  # peer → {ann, wdr, prefixes, as_path_churn}
