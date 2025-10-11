from collections import deque

import numpy as np

from anomaly_detection.utils.schema import FeatureBin


class MPDetector:
    """Streaming Matrix-Profile-ish detector using rolling z-norm and discord score.
    For speed/clarity, this is a simplified approximation; upgrade to `stumpy` later.
    """

    def __init__(self, window_bins: int = 64, series_key: str = "wdr_total"):
        self.window_bins = window_bins
        self.series_key = series_key
        self.buf = deque(maxlen=window_bins * 2)

    def update(self, fb: FeatureBin) -> float:
        x = fb.totals.get(self.series_key, 0.0)
        self.buf.append(float(x))
        arr = np.array(self.buf, dtype=float)
        if len(arr) < self.window_bins + 4:
            return 0.0
        # Simple discord-like score: z-score of last value vs. rolling window
        w = arr[-self.window_bins :]
        mu = w.mean()
        sd = w.std() + 1e-9
        z = (w[-1] - mu) / sd
        return float(abs(z))
