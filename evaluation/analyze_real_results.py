#!/usr/bin/env python3
"""Analyze REAL ML pipeline results."""

import json
from pathlib import Path


class RealResultsAnalyzer:
    """Analyze real Matrix Profile + Isolation Forest results."""

    def __init__(self):
        self.ground_truth = []
        self.alerts = []

    def load_data(self):
        """Load ground truth and real alerts."""
        # Load ground truth
        gt_file = Path("data/evaluation/ground_truth.json")
        if gt_file.exists():
            with open(gt_file) as f:
                self.ground_truth = json.load(f)

        # Load REAL pipeline results
        results_file = Path("data/evaluation/real_pipeline_results.json")
        if results_file.exists():
            with open(results_file) as f:
                data = json.load(f)
                self.alerts = data.get("alerts", [])

        print(f"[OK] Loaded {len(self.ground_truth)} ground truth scenarios")
        print(f"[OK] Loaded {len(self.alerts)} REAL alerts from ML pipeline")

    def calculate_metrics(self):
        """Calculate F1, Delay, Hit@k from REAL detections."""
        if not self.alerts:
            print("[ERROR] No alerts found - run evaluation first")
            return

        # Match alerts to ground truth (60s window)
        matched = []
        for gt in self.ground_truth:
            for alert in self.alerts:
                if abs(alert["timestamp"] - gt["timestamp"]) < 60:
                    matched.append(
                        {"gt": gt, "alert": alert, "delay": alert["timestamp"] - gt["timestamp"]}
                    )
                    break

        tp = len(matched)
        fp = len(self.alerts) - tp
        fn = len(self.ground_truth) - tp

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Detection delays
        delays = [m["delay"] for m in matched]
        if delays:
            delays.sort()
            mean_delay = sum(delays) / len(delays)
            median_delay = delays[len(delays) // 2]
            p95_delay = delays[int(len(delays) * 0.95)] if len(delays) > 1 else delays[0]
        else:
            mean_delay = median_delay = p95_delay = 0

        # Display results
        print("\n" + "=" * 80)
        print("REAL ML PIPELINE METRICS")
        print("=" * 80)

        print("\nDETECTOR BREAKDOWN:")
        by_detector = {}
        for alert in self.alerts:
            det = alert["detector"]
            by_detector[det] = by_detector.get(det, 0) + 1

        for detector, count in by_detector.items():
            print(f"  {detector:25s}: {count} detections")

        print("\nF1 METRICS (from REAL algorithms):")
        print(
            f"  Precision: {precision:.3f} (target >= 0.90) {'[OK]' if precision >= 0.90 else '[FAIL]'}"
        )
        print(
            f"  Recall:    {recall:.3f} (target >= 0.85) {'[OK]' if recall >= 0.85 else '[FAIL]'}"
        )
        print(f"  F1 Score:  {f1:.3f} (target >= 0.875) {'[OK]' if f1 >= 0.875 else '[FAIL]'}")
        print(f"  TP: {tp}, FP: {fp}, FN: {fn}")

        print("\nDETECTION DELAY:")
        print(f"  Mean:   {mean_delay:.2f}s (target <= 60s) {'✓' if mean_delay <= 60 else 'X'}")
        print(f"  Median: {median_delay:.2f}s")
        print(f"  P95:    {p95_delay:.2f}s")

        print("\nALGORITHM PERFORMANCE:")
        mp_alerts = [a for a in self.alerts if a["detector"] == "matrix_profile"]
        if_alerts = [a for a in self.alerts if a["detector"] == "isolation_forest"]

        print(f"  Matrix Profile:    {len(mp_alerts)} BGP anomalies detected")
        print(f"  Isolation Forest:  {len(if_alerts)} SNMP anomalies detected")

        # Check targets
        targets_met = precision >= 0.90 and recall >= 0.85 and f1 >= 0.875 and mean_delay <= 60

        print("\n" + "=" * 80)
        if targets_met:
            print("[OK] REAL ALGORITHMS MEET ALL TARGETS")
        else:
            print("[INFO] Adjust thresholds - see recommendations below")
        print("=" * 80)

        # Recommendations
        if not targets_met:
            print("\nRECOMMENDATIONS:")
            if precision < 0.90:
                print("  - Increase discord_threshold in Matrix Profile (reduce FP)")
                print("  - Increase contamination in Isolation Forest (reduce FP)")
            if recall < 0.85:
                print("  - Decrease discord_threshold in Matrix Profile (increase sensitivity)")
                print("  - Decrease contamination in Isolation Forest (increase sensitivity)")
            if mean_delay > 60:
                print("  - Reduce bin_duration (faster detection)")
                print("  - Reduce window_bins in Matrix Profile (faster convergence)")

        # Save metrics
        metrics = {
            "f1": {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "fn": fn,
            },
            "delay": {"mean": mean_delay, "median": median_delay, "p95": p95_delay},
            "detectors": by_detector,
            "targets_met": targets_met,
        }

        metrics_file = Path("data/evaluation/metrics/real_pipeline_metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"\n[OK] Metrics saved to: {metrics_file}")


if __name__ == "__main__":
    analyzer = RealResultsAnalyzer()
    analyzer.load_data()
    analyzer.calculate_metrics()
