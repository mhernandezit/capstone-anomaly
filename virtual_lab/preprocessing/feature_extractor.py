"""
Feature Extraction Pipeline for Virtual Lab

This module implements feature extraction based on the Feltin 2023 paper
"Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data".

The approach focuses on:
1. Multi-scale temporal feature extraction
2. Semantic understanding of network events
3. Correlation analysis between different data sources
4. Feature selection using mutual information
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from sklearn.preprocessing import StandardScaler
from scipy import stats
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureWindow:
    """Represents a time window for feature extraction."""
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    data_points: List[Dict[str, Any]]


@dataclass
class ExtractedFeatures:
    """Container for extracted features from a time window."""
    window_start: datetime
    window_end: datetime
    bgp_features: Dict[str, float]
    syslog_features: Dict[str, float]
    system_features: Dict[str, float]
    interface_features: Dict[str, float]
    correlation_features: Dict[str, float]
    semantic_features: Dict[str, float]


class SemanticFeatureExtractor:
    """
    Extracts semantic features from network telemetry data.
    
    Based on Feltin 2023 paper, this class focuses on understanding
    the semantic meaning of network events and their relationships.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.time_windows = config.get('time_windows', [30, 60, 300])
        self.feature_config = config.get('features', {})
        
        # Feature storage for correlation analysis
        self.feature_history = defaultdict(lambda: deque(maxlen=1000))
        
        # Semantic event patterns
        self.event_patterns = self._initialize_event_patterns()
        
        logger.info("Semantic feature extractor initialized")
    
    def _initialize_event_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize semantic event patterns for network events."""
        return {
            'link_failure': {
                'keywords': ['interface', 'down', 'link', 'failure'],
                'severity_sequence': ['error', 'critical'],
                'temporal_pattern': 'burst',
                'correlation_events': ['bgp_neighbor_down', 'ospf_neighbor_down']
            },
            'bgp_session_reset': {
                'keywords': ['bgp', 'neighbor', 'down', 'reset'],
                'severity_sequence': ['warning', 'error'],
                'temporal_pattern': 'isolated',
                'correlation_events': ['interface_down']
            },
            'prefix_hijack': {
                'keywords': ['bgp', 'announcement', 'suspicious', 'hijack'],
                'severity_sequence': ['warning'],
                'temporal_pattern': 'sustained',
                'correlation_events': ['unusual_as_path', 'rapid_updates']
            },
            'route_flap': {
                'keywords': ['bgp', 'withdrawal', 'announcement', 'flap'],
                'severity_sequence': ['warning', 'error'],
                'temporal_pattern': 'oscillating',
                'correlation_events': ['interface_instability']
            },
            'system_overload': {
                'keywords': ['cpu', 'memory', 'high', 'utilization'],
                'severity_sequence': ['warning', 'error'],
                'temporal_pattern': 'gradual',
                'correlation_events': ['performance_degradation']
            }
        }
    
    def extract_bgp_features(self, bgp_data: List[Dict[str, Any]], window: FeatureWindow) -> Dict[str, float]:
        """Extract BGP-specific features from telemetry data."""
        features = {}
        
        if not bgp_data:
            return self._get_default_bgp_features()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(bgp_data)
        
        # Basic rate features
        features['announcement_rate'] = len(df[df.get('announce', pd.Series()).notna()]) / window.duration_seconds
        features['withdrawal_rate'] = len(df[df.get('withdraw', pd.Series()).notna()]) / window.duration_seconds
        
        # AS path analysis
        if 'attrs' in df.columns:
            as_path_lengths = []
            for attrs in df['attrs'].dropna():
                if isinstance(attrs, dict) and 'as_path_len' in attrs:
                    as_path_lengths.append(attrs['as_path_len'])
            
            if as_path_lengths:
                features['avg_as_path_length'] = np.mean(as_path_lengths)
                features['as_path_variance'] = np.var(as_path_lengths)
                features['as_path_churn'] = np.std(as_path_lengths)
            else:
                features['avg_as_path_length'] = 0.0
                features['as_path_variance'] = 0.0
                features['as_path_churn'] = 0.0
        
        # Peer analysis
        if 'peer' in df.columns:
            unique_peers = df['peer'].nunique()
            features['peer_diversity'] = unique_peers
            features['updates_per_peer'] = len(df) / max(unique_peers, 1)
        else:
            features['peer_diversity'] = 0.0
            features['updates_per_peer'] = 0.0
        
        # Temporal patterns
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], unit='ms')
            if len(timestamps) > 1:
                intervals = timestamps.diff().dt.total_seconds().dropna()
                features['update_interval_mean'] = intervals.mean()
                features['update_interval_std'] = intervals.std()
                features['update_burstiness'] = intervals.std() / max(intervals.mean(), 1e-6)
            else:
                features['update_interval_mean'] = 0.0
                features['update_interval_std'] = 0.0
                features['update_burstiness'] = 0.0
        
        return features
    
    def extract_syslog_features(self, syslog_data: List[Dict[str, Any]], window: FeatureWindow) -> Dict[str, float]:
        """Extract syslog-specific features from telemetry data."""
        features = {}
        
        if not syslog_data:
            return self._get_default_syslog_features()
        
        df = pd.DataFrame(syslog_data)
        
        # Severity distribution
        if 'severity' in df.columns:
            severity_counts = df['severity'].value_counts()
            total_messages = len(df)
            
            features['error_rate'] = severity_counts.get('error', 0) / total_messages
            features['warning_rate'] = severity_counts.get('warning', 0) / total_messages
            features['critical_rate'] = severity_counts.get('critical', 0) / total_messages
            features['info_rate'] = severity_counts.get('info', 0) / total_messages
        else:
            features['error_rate'] = 0.0
            features['warning_rate'] = 0.0
            features['critical_rate'] = 0.0
            features['info_rate'] = 0.0
        
        # Message type analysis
        if 'message_type' in df.columns:
            message_type_counts = df['message_type'].value_counts()
            features['message_type_diversity'] = len(message_type_counts)
            features['most_common_message_type'] = message_type_counts.index[0] if len(message_type_counts) > 0 else 'unknown'
        else:
            features['message_type_diversity'] = 0.0
            features['most_common_message_type'] = 'unknown'
        
        # Temporal patterns
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], unit='ms')
            if len(timestamps) > 1:
                intervals = timestamps.diff().dt.total_seconds().dropna()
                features['message_interval_mean'] = intervals.mean()
                features['message_interval_std'] = intervals.std()
                features['message_burstiness'] = intervals.std() / max(intervals.mean(), 1e-6)
            else:
                features['message_interval_mean'] = 0.0
                features['message_interval_std'] = 0.0
                features['message_burstiness'] = 0.0
        
        # Semantic analysis
        features.update(self._extract_semantic_features(df))
        
        return features
    
    def extract_system_features(self, system_data: List[Dict[str, Any]], window: FeatureWindow) -> Dict[str, float]:
        """Extract system-level features from telemetry data."""
        features = {}
        
        if not system_data:
            return self._get_default_system_features()
        
        df = pd.DataFrame(system_data)
        
        # CPU and memory analysis
        if 'metrics' in df.columns:
            cpu_values = []
            memory_values = []
            temperature_values = []
            
            for metrics in df['metrics'].dropna():
                if isinstance(metrics, dict):
                    if 'cpu_usage_percent' in metrics:
                        cpu_values.append(metrics['cpu_usage_percent'])
                    if 'memory_usage_percent' in metrics:
                        memory_values.append(metrics['memory_usage_percent'])
                    if 'temperature_celsius' in metrics:
                        temperature_values.append(metrics['temperature_celsius'])
            
            if cpu_values:
                features['cpu_mean'] = np.mean(cpu_values)
                features['cpu_std'] = np.std(cpu_values)
                features['cpu_max'] = np.max(cpu_values)
                features['cpu_trend'] = self._calculate_trend(cpu_values)
            else:
                features['cpu_mean'] = 0.0
                features['cpu_std'] = 0.0
                features['cpu_max'] = 0.0
                features['cpu_trend'] = 0.0
            
            if memory_values:
                features['memory_mean'] = np.mean(memory_values)
                features['memory_std'] = np.std(memory_values)
                features['memory_max'] = np.max(memory_values)
                features['memory_trend'] = self._calculate_trend(memory_values)
            else:
                features['memory_mean'] = 0.0
                features['memory_std'] = 0.0
                features['memory_max'] = 0.0
                features['memory_trend'] = 0.0
            
            if temperature_values:
                features['temperature_mean'] = np.mean(temperature_values)
                features['temperature_std'] = np.std(temperature_values)
                features['temperature_max'] = np.max(temperature_values)
                features['temperature_trend'] = self._calculate_trend(temperature_values)
            else:
                features['temperature_mean'] = 0.0
                features['temperature_std'] = 0.0
                features['temperature_max'] = 0.0
                features['temperature_trend'] = 0.0
        
        return features
    
    def extract_interface_features(self, interface_data: List[Dict[str, Any]], window: FeatureWindow) -> Dict[str, float]:
        """Extract interface-level features from telemetry data."""
        features = {}
        
        if not interface_data:
            return self._get_default_interface_features()
        
        df = pd.DataFrame(interface_data)
        
        # Interface status analysis
        if 'metrics' in df.columns:
            up_interfaces = 0
            down_interfaces = 0
            total_bytes_in = 0
            total_bytes_out = 0
            total_errors = 0
            
            for metrics in df['metrics'].dropna():
                if isinstance(metrics, dict):
                    if metrics.get('status') == 'up':
                        up_interfaces += 1
                    else:
                        down_interfaces += 1
                    
                    total_bytes_in += metrics.get('bytes_in', 0)
                    total_bytes_out += metrics.get('bytes_out', 0)
                    total_errors += metrics.get('errors_in', 0) + metrics.get('errors_out', 0)
            
            total_interfaces = up_interfaces + down_interfaces
            features['interface_availability'] = up_interfaces / max(total_interfaces, 1)
            features['total_throughput'] = total_bytes_in + total_bytes_out
            features['error_rate'] = total_errors / max(total_bytes_in + total_bytes_out, 1)
        else:
            features['interface_availability'] = 0.0
            features['total_throughput'] = 0.0
            features['error_rate'] = 0.0
        
        return features
    
    def extract_correlation_features(self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow) -> Dict[str, float]:
        """Extract correlation features between different data sources."""
        features = {}
        
        # Cross-correlation between BGP and syslog
        bgp_data = all_data.get('bgp', [])
        syslog_data = all_data.get('syslog', [])
        
        if bgp_data and syslog_data:
            # Calculate correlation between BGP update rate and syslog error rate
            bgp_rate = len(bgp_data) / window.duration_seconds
            syslog_error_count = sum(1 for msg in syslog_data if msg.get('severity') == 'error')
            syslog_error_rate = syslog_error_count / window.duration_seconds
            
            features['bgp_syslog_correlation'] = self._calculate_correlation(bgp_rate, syslog_error_rate)
        else:
            features['bgp_syslog_correlation'] = 0.0
        
        # Temporal alignment analysis
        features['temporal_alignment'] = self._analyze_temporal_alignment(all_data, window)
        
        # Event sequence analysis
        features['event_sequence_score'] = self._analyze_event_sequences(all_data, window)
        
        return features
    
    def _extract_semantic_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract semantic features based on event patterns."""
        features = {}
        
        # Analyze message content for semantic patterns
        if 'message' in df.columns:
            messages = df['message'].dropna().astype(str)
            
            # Count occurrences of each event pattern
            for pattern_name, pattern_config in self.event_patterns.items():
                keyword_matches = 0
                for message in messages:
                    for keyword in pattern_config['keywords']:
                        if keyword.lower() in message.lower():
                            keyword_matches += 1
                            break
                
                features[f'{pattern_name}_indicator'] = keyword_matches / len(messages) if len(messages) > 0 else 0
        
        # Analyze severity sequences
        if 'severity' in df.columns:
            severity_sequence = df['severity'].tolist()
            features['severity_escalation'] = self._detect_severity_escalation(severity_sequence)
            features['severity_consistency'] = self._calculate_severity_consistency(severity_sequence)
        else:
            features['severity_escalation'] = 0.0
            features['severity_consistency'] = 0.0
        
        return features
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (slope) of a time series."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        return slope
    
    def _calculate_correlation(self, x: float, y: float) -> float:
        """Calculate correlation between two values."""
        # For single values, return 0 (no correlation)
        # In practice, this would be calculated over multiple time windows
        return 0.0
    
    def _analyze_temporal_alignment(self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow) -> float:
        """Analyze temporal alignment between different data sources."""
        # Simple implementation - in practice would analyze timestamp alignment
        return 0.5
    
    def _analyze_event_sequences(self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow) -> float:
        """Analyze event sequences for patterns."""
        # Simple implementation - in practice would analyze event causality
        return 0.5
    
    def _detect_severity_escalation(self, severity_sequence: List[str]) -> float:
        """Detect severity escalation patterns."""
        severity_levels = {'info': 0, 'warning': 1, 'error': 2, 'critical': 3}
        escalation_count = 0
        
        for i in range(1, len(severity_sequence)):
            current_level = severity_levels.get(severity_sequence[i], 0)
            previous_level = severity_levels.get(severity_sequence[i-1], 0)
            if current_level > previous_level:
                escalation_count += 1
        
        return escalation_count / max(len(severity_sequence) - 1, 1)
    
    def _calculate_severity_consistency(self, severity_sequence: List[str]) -> float:
        """Calculate consistency of severity levels."""
        if not severity_sequence:
            return 0.0
        
        # Calculate entropy of severity distribution
        severity_counts = {}
        for severity in severity_sequence:
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        total = len(severity_sequence)
        entropy = 0.0
        for count in severity_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _get_default_bgp_features(self) -> Dict[str, float]:
        """Return default BGP features when no data is available."""
        return {
            'announcement_rate': 0.0,
            'withdrawal_rate': 0.0,
            'avg_as_path_length': 0.0,
            'as_path_variance': 0.0,
            'as_path_churn': 0.0,
            'peer_diversity': 0.0,
            'updates_per_peer': 0.0,
            'update_interval_mean': 0.0,
            'update_interval_std': 0.0,
            'update_burstiness': 0.0
        }
    
    def _get_default_syslog_features(self) -> Dict[str, float]:
        """Return default syslog features when no data is available."""
        return {
            'error_rate': 0.0,
            'warning_rate': 0.0,
            'critical_rate': 0.0,
            'info_rate': 0.0,
            'message_type_diversity': 0.0,
            'message_interval_mean': 0.0,
            'message_interval_std': 0.0,
            'message_burstiness': 0.0,
            'severity_escalation': 0.0,
            'severity_consistency': 0.0
        }
    
    def _get_default_system_features(self) -> Dict[str, float]:
        """Return default system features when no data is available."""
        return {
            'cpu_mean': 0.0,
            'cpu_std': 0.0,
            'cpu_max': 0.0,
            'cpu_trend': 0.0,
            'memory_mean': 0.0,
            'memory_std': 0.0,
            'memory_max': 0.0,
            'memory_trend': 0.0,
            'temperature_mean': 0.0,
            'temperature_std': 0.0,
            'temperature_max': 0.0,
            'temperature_trend': 0.0
        }
    
    def _get_default_interface_features(self) -> Dict[str, float]:
        """Return default interface features when no data is available."""
        return {
            'interface_availability': 0.0,
            'total_throughput': 0.0,
            'error_rate': 0.0
        }


class FeatureSelector:
    """
    Feature selection based on mutual information and correlation analysis.
    
    Implements the approach from Feltin 2023 paper for selecting
    the most informative features for anomaly detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_features = config.get('max_features', 20)
        self.correlation_threshold = config.get('correlation_threshold', 0.8)
        self.method = config.get('method', 'mutual_information')
        
        # Feature importance scores
        self.feature_scores = {}
        self.selected_features = []
        
        logger.info("Feature selector initialized")
    
    def select_features(self, features_df: pd.DataFrame, target_labels: Optional[np.ndarray] = None) -> List[str]:
        """Select the most informative features."""
        if features_df.empty:
            return []
        
        # Remove features with constant values
        constant_features = features_df.columns[features_df.nunique() <= 1].tolist()
        features_df = features_df.drop(columns=constant_features)
        
        if features_df.empty:
            return []
        
        # Calculate mutual information
        if target_labels is not None:
            # Supervised feature selection
            mi_scores = mutual_info_classif(features_df, target_labels)
        else:
            # Unsupervised feature selection (use variance as proxy)
            mi_scores = features_df.var().values
        
        # Create feature importance dictionary
        feature_importance = dict(zip(features_df.columns, mi_scores))
        
        # Remove highly correlated features
        correlation_matrix = features_df.corr().abs()
        upper_tri = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool))
        
        to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > self.correlation_threshold)]
        features_df = features_df.drop(columns=to_drop)
        
        # Select top features
        remaining_features = [f for f in features_df.columns if f not in to_drop]
        remaining_scores = [feature_importance[f] for f in remaining_features]
        
        # Sort by importance and select top features
        sorted_features = sorted(zip(remaining_features, remaining_scores), key=lambda x: x[1], reverse=True)
        selected_features = [f[0] for f in sorted_features[:self.max_features]]
        
        self.feature_scores = feature_importance
        self.selected_features = selected_features
        
        logger.info(f"Selected {len(selected_features)} features from {len(features_df.columns)} total features")
        
        return selected_features
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        return self.feature_scores.copy()
    
    def get_selected_features(self) -> List[str]:
        """Get list of selected features."""
        return self.selected_features.copy()


class PreprocessingPipeline:
    """
    Main preprocessing pipeline that coordinates feature extraction and selection.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.preprocessing_config = self.config.get('preprocessing', {})
        self.feature_extractor = SemanticFeatureExtractor(self.preprocessing_config.get('feature_extraction', {}))
        self.feature_selector = FeatureSelector(self.preprocessing_config.get('feature_selection', {}))
        
        # Data buffers for sliding window processing
        self.data_buffers = {
            'bgp': deque(maxlen=1000),
            'syslog': deque(maxlen=1000),
            'system': deque(maxlen=1000),
            'interface': deque(maxlen=1000)
        }
        
        # Feature history for correlation analysis
        self.feature_history = deque(maxlen=100)
        
        logger.info("Preprocessing pipeline initialized")
    
    def add_data(self, data_type: str, data: List[Dict[str, Any]]):
        """Add new data to the appropriate buffer."""
        if data_type in self.data_buffers:
            self.data_buffers[data_type].extend(data)
    
    def extract_features(self, window_duration: int = 60) -> Optional[ExtractedFeatures]:
        """Extract features from the current data window."""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=window_duration)
        
        # Filter data for the current window
        window_data = {}
        for data_type, buffer in self.data_buffers.items():
            window_data[data_type] = [
                item for item in buffer
                if datetime.fromtimestamp(item.get('timestamp', 0) / 1000) >= window_start
            ]
        
        # Check if we have enough data
        total_data_points = sum(len(data) for data in window_data.values())
        if total_data_points < 10:  # Minimum data points required
            return None
        
        # Create feature window
        feature_window = FeatureWindow(
            start_time=window_start,
            end_time=current_time,
            duration_seconds=window_duration,
            data_points=[]
        )
        
        # Extract features from each data type
        bgp_features = self.feature_extractor.extract_bgp_features(window_data.get('bgp', []), feature_window)
        syslog_features = self.feature_extractor.extract_syslog_features(window_data.get('syslog', []), feature_window)
        system_features = self.feature_extractor.extract_system_features(window_data.get('system', []), feature_window)
        interface_features = self.feature_extractor.extract_interface_features(window_data.get('interface', []), feature_window)
        correlation_features = self.feature_extractor.extract_correlation_features(window_data, feature_window)
        
        # Combine all features
        all_features = {**bgp_features, **syslog_features, **system_features, **interface_features, **correlation_features}
        
        # Extract semantic features
        semantic_features = self.feature_extractor._extract_semantic_features(
            pd.DataFrame(window_data.get('syslog', []))
        )
        
        # Create extracted features object
        extracted_features = ExtractedFeatures(
            window_start=window_start,
            window_end=current_time,
            bgp_features=bgp_features,
            syslog_features=syslog_features,
            system_features=system_features,
            interface_features=interface_features,
            correlation_features=correlation_features,
            semantic_features=semantic_features
        )
        
        # Store in feature history
        self.feature_history.append(extracted_features)
        
        return extracted_features
    
    def select_features(self, features_df: pd.DataFrame, target_labels: Optional[np.ndarray] = None) -> List[str]:
        """Select the most informative features."""
        return self.feature_selector.select_features(features_df, target_labels)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'data_buffer_sizes': {k: len(v) for k, v in self.data_buffers.items()},
            'feature_history_size': len(self.feature_history),
            'selected_features_count': len(self.feature_selector.get_selected_features()),
            'feature_importance': self.feature_selector.get_feature_importance()
        }
