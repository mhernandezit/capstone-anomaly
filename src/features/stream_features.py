from collections import defaultdict, deque
from typing import Dict
from src.utils.schema import BGPUpdate, FeatureBin


class FeatureAggregator:
    def __init__(self, bin_seconds: int = 30):
        self.bin_seconds = bin_seconds
        self.current_bin_start = None
        self.current = defaultdict(float)
        self.by_peer: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.closed = deque()
        self.last_paths = {}  # prefix -> last as_path_len for crude churn

    def _bin_of(self, ts: int):
        return ts - (ts % self.bin_seconds)

    def add_update(self, u: BGPUpdate):
        b = self._bin_of(u.ts)
        if self.current_bin_start is None:
            self.current_bin_start = b
        if b > self.current_bin_start:
            # close previous bin
            fb = FeatureBin(
                bin_start=self.current_bin_start,
                bin_end=self.current_bin_start + self.bin_seconds,
                totals=dict(self.current),
                peers={p: dict(m) for p, m in self.by_peer.items()},
            )
            self.closed.append(fb)
            self.current.clear()
            self.by_peer.clear()
            self.current_bin_start = b
        # update counts
        ann = len(u.announce or [])
        wdr = len(u.withdraw or [])
        self.current["ann_total"] += ann
        self.current["wdr_total"] += wdr
        self.by_peer[u.peer]["ann"] += ann
        self.by_peer[u.peer]["wdr"] += wdr
        # crude churn: change in as_path_len
        if u.attrs and "as_path_len" in u.attrs:
            self.current["as_path_churn"] += u.attrs["as_path_len"]
            self.by_peer[u.peer]["as_path_churn"] += u.attrs["as_path_len"]

    def has_closed_bin(self) -> bool:
        return len(self.closed) > 0

    def pop_closed_bin(self) -> FeatureBin:
        return self.closed.popleft()
