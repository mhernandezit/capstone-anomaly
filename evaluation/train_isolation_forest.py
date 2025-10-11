#!/usr/bin/env python3
"""
Isolation Forest Training with GPU Acceleration
Pre-trains model on realistic SNMP data for fast evaluation.
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

from anomaly_detection.features import SNMPFeatureExtractor

# Try GPU libraries first, fall back to CPU
try:
    import cuml  # noqa: F401
    from cuml.ensemble import IsolationForest as CuMLIsolationForest

    GPU_AVAILABLE = True
    print("[INFO] cuML GPU library available - using GPU acceleration")
except ImportError:
    from sklearn.ensemble import IsolationForest

    GPU_AVAILABLE = False
    print("[INFO] cuML not available - using sklearn CPU")


class IsolationForestTrainer:
    """Trains Isolation Forest on SNMP data with GPU acceleration."""

    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.feature_extractor = SNMPFeatureExtractor(bin_seconds=10)
        self.model = None
        self.feature_names = None
        self.last_data_file = None  # Track for scaler fitting

    def load_training_data(
        self, data_file: str = "data/evaluation/training/snmp_training_data.jsonl"
    ):
        """Load and extract features from training data."""
        self.last_data_file = data_file  # Save for scaler fitting
        print(f"\n[1/3] Loading training data from {data_file}...")

        data_path = Path(data_file)
        if not data_path.exists():
            raise FileNotFoundError(
                "Training data not found. Run: python evaluation/generate_snmp_training_data.py"
            )

        # Load samples
        samples = []
        with open(data_path) as f:
            for line in f:
                samples.append(json.loads(line))

        print(f"      Loaded {len(samples)} samples")

        # Extract features using feature extractor
        print("[2/3] Extracting features...")

        feature_vectors = []
        for i, sample in enumerate(samples):
            # Add to extractor
            self.feature_extractor.add_snmp_metric(sample)

            # Check for completed bins
            if self.feature_extractor.has_completed_bin():
                bin_data = self.feature_extractor.pop_completed_bin()
                feature_vector = self.feature_extractor.get_feature_vector(bin_data)
                feature_vectors.append(feature_vector)

            if (i + 1) % 1000 == 0:
                print(
                    f"      Processed {i+1}/{len(samples)} samples ({len(feature_vectors)} feature vectors)"
                )

        # Convert to numpy array
        X = np.array(feature_vectors)
        self.feature_names = self.feature_extractor.get_feature_names()

        print(f"      Extracted {X.shape[0]} feature vectors with {X.shape[1]} features")
        print(f"      Feature names: {', '.join(self.feature_names[:5])}...")

        return X

    def train_model(self, X, contamination: float = 0.02, n_estimators: int = 200):
        """Train Isolation Forest with GPU acceleration."""
        print("\n[3/3] Training Isolation Forest...")
        print(f"      Contamination: {contamination}")
        print(f"      Estimators: {n_estimators}")
        print(f"      Backend: {'GPU (cuML)' if self.use_gpu else 'CPU (sklearn)'}")

        # Train scaler on this data
        from sklearn.preprocessing import StandardScaler

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        print(f"      Scaler fitted on {len(X)} samples")

        start_time = datetime.now()

        if self.use_gpu:
            # GPU training with cuML
            self.model = CuMLIsolationForest(
                n_estimators=n_estimators,
                contamination=contamination,
                max_samples="auto",
                random_state=42,
            )
        else:
            # CPU training with sklearn
            self.model = IsolationForest(
                n_estimators=n_estimators,
                contamination=contamination,
                max_samples="auto",
                random_state=42,
                n_jobs=-1,  # Use all CPU cores
            )

        self.model.fit(X_scaled)  # Train on scaled data

        training_time = (datetime.now() - start_time).total_seconds()
        print(f"      Training complete in {training_time:.2f}s")

        # Validate
        predictions = self.model.predict(X_scaled)
        anomalies = np.sum(predictions == -1)
        print(
            f"      Detected {anomalies}/{len(X)} anomalies in training data ({anomalies/len(X)*100:.1f}%)"
        )

    def save_model(self, output_file: str = "data/evaluation/models/isolation_forest_trained.pkl"):
        """Save trained model and metadata."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model + metadata + scaler
        model_data = {
            "model": self.model,
            "scaler": self.scaler,  # Fitted scaler from training
            "feature_names": self.feature_names,
            "use_gpu": self.use_gpu,
            "trained_at": datetime.now().isoformat(),
        }

        joblib.dump(model_data, output_path)

        print(f"\n[OK] Model saved to: {output_path}")
        print(f"     Size: {output_path.stat().st_size / 1024:.2f} KB")
        print(f"     Features: {len(self.feature_names)}")

    @staticmethod
    def load_model(model_file: str = "data/evaluation/models/isolation_forest_trained.pkl"):
        """Load pre-trained model."""
        model_path = Path(model_file)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_file}")

        model_data = joblib.load(model_path)
        print(f"[OK] Loaded pre-trained model from {model_file}")
        print(f"     Trained: {model_data['trained_at']}")
        print(f"     Features: {len(model_data['feature_names'])}")
        print(f"     Backend: {'GPU' if model_data['use_gpu'] else 'CPU'}")

        return model_data["model"], model_data["feature_names"]


def main():
    """Train and save Isolation Forest model."""
    print("=" * 80)
    print("ISOLATION FOREST TRAINING (GPU-ACCELERATED)")
    print("=" * 80)

    # Check for training data
    data_file = "data/evaluation/training/snmp_training_data.jsonl"
    if not Path(data_file).exists():
        print(f"\n[ERROR] Training data not found: {data_file}")
        print("[NEXT] Run: python evaluation/generate_snmp_training_data.py")
        return

    # Train model
    trainer = IsolationForestTrainer(use_gpu=True)

    X = trainer.load_training_data(data_file)

    trainer.train_model(
        X,
        contamination=0.02,  # Expect 2% anomalies
        n_estimators=200,  # More trees = better accuracy
    )

    trainer.save_model("data/evaluation/models/isolation_forest_trained.pkl")

    print("\n" + "=" * 80)
    print("[OK] Isolation Forest training complete")
    print("=" * 80)
    print("\n[NEXT] Use pre-trained model in evaluation:")
    print("       python evaluation/run_with_real_pipeline.py")


if __name__ == "__main__":
    main()
