"""
Feature Extraction Pipeline for Network Anomaly Detection

This module implements feature extraction based on the Feltin 2023 paper
"Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data".

The approach focuses on:
1. Multi-scale temporal feature extraction
2. Semantic understanding of network events
3. Correlation analysis between different data sources
4. Feature selection using mutual information
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from sklearn.feature_selection import mutual_info_classif

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
        """
        Initialize the SemanticFeatureExtractor with configuration parameters.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - time_windows (List[int]): List of time window durations in seconds
                - features (Dict): Feature extraction configuration parameters

        Returns:
            None

        Side Effects:
            - Initializes feature history storage for correlation analysis
            - Sets up semantic event patterns for network event recognition
            - Configures logging for the feature extractor
        """
        self.config = config
        self.time_windows = config.get("time_windows", [30, 60, 300])
        self.feature_config = config.get("features", {})

        # Feature storage for correlation analysis
        self.feature_history = defaultdict(lambda: deque(maxlen=1000))

        # Semantic event patterns
        self.event_patterns = self._initialize_event_patterns()

        logger.info("Semantic feature extractor initialized")

    def _initialize_event_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize semantic event patterns for network event recognition.

        Creates a dictionary of predefined event patterns with their characteristics
        including keywords, severity sequences, temporal patterns, and correlation events.

        Args:
            None

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping event types to their patterns:
                - keywords (List[str]): Keywords associated with the event type
                - severity_sequence (List[str]): Expected severity progression
                - temporal_pattern (str): Temporal behavior pattern (burst, isolated, etc.)
                - correlation_events (List[str]): Events that typically correlate

        Event Types Included:
            - link_failure: Physical link failures
            - bgp_session_reset: BGP neighbor session resets
            - prefix_hijack: Potential BGP prefix hijacking
            - route_flap: Route announcement/withdrawal oscillations
            - system_overload: System resource exhaustion
        """
        return {
            "link_failure": {
                "keywords": ["interface", "down", "link", "failure"],
                "severity_sequence": ["error", "critical"],
                "temporal_pattern": "burst",
                "correlation_events": ["bgp_neighbor_down", "ospf_neighbor_down"],
            },
            "bgp_session_reset": {
                "keywords": ["bgp", "neighbor", "down", "reset"],
                "severity_sequence": ["warning", "error"],
                "temporal_pattern": "isolated",
                "correlation_events": ["interface_down"],
            },
            "prefix_hijack": {
                "keywords": ["bgp", "announcement", "suspicious", "hijack"],
                "severity_sequence": ["warning"],
                "temporal_pattern": "sustained",
                "correlation_events": ["unusual_as_path", "rapid_updates"],
            },
            "route_flap": {
                "keywords": ["bgp", "withdrawal", "announcement", "flap"],
                "severity_sequence": ["warning", "error"],
                "temporal_pattern": "oscillating",
                "correlation_events": ["interface_instability"],
            },
            "system_overload": {
                "keywords": ["cpu", "memory", "high", "utilization"],
                "severity_sequence": ["warning", "error"],
                "temporal_pattern": "gradual",
                "correlation_events": ["performance_degradation"],
            },
        }

    def extract_bgp_features(
        self, bgp_data: List[Dict[str, Any]], window: FeatureWindow
    ) -> Dict[str, float]:
        """
        Extract BGP-specific features from telemetry data within a time window.

        Analyzes BGP routing updates to extract features related to announcement rates,
        withdrawal patterns, AS path characteristics, peer diversity, and temporal patterns.

        Args:
            bgp_data (List[Dict[str, Any]]): List of BGP update messages containing:
                - announce (List[str], optional): Announced prefixes
                - withdraw (List[str], optional): Withdrawn prefixes
                - attrs (Dict, optional): BGP attributes including AS path length
                - peer (str, optional): Source peer IP address
                - timestamp (int): Message timestamp in milliseconds

            window (FeatureWindow): Time window containing:
                - start_time (datetime): Window start time
                - end_time (datetime): Window end time
                - duration_seconds (int): Window duration in seconds

        Returns:
            Dict[str, float]: Dictionary of BGP features:
                - announcement_rate (float): Announcements per second
                - withdrawal_rate (float): Withdrawals per second
                - avg_as_path_length (float): Average AS path length
                - as_path_variance (float): Variance in AS path lengths
                - as_path_churn (float): Standard deviation of AS path lengths
                - peer_diversity (float): Number of unique peers
                - updates_per_peer (float): Average updates per peer
                - update_interval_mean (float): Mean time between updates
                - update_interval_std (float): Std dev of update intervals
                - update_burstiness (float): Coefficient of variation of intervals

        Note:
            Returns default values (0.0) if no BGP data is provided or if required
            fields are missing from the data.
        """
        features = {}

        if not bgp_data:
            return self._get_default_bgp_features()

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(bgp_data)

        # Basic rate features
        features["announcement_rate"] = (
            len(df[df.get("announce", pd.Series()).notna()]) / window.duration_seconds
        )
        features["withdrawal_rate"] = (
            len(df[df.get("withdraw", pd.Series()).notna()]) / window.duration_seconds
        )

        # AS path analysis
        if "attrs" in df.columns:
            as_path_lengths = []
            for attrs in df["attrs"].dropna():
                if isinstance(attrs, dict) and "as_path_len" in attrs:
                    as_path_lengths.append(attrs["as_path_len"])

            if as_path_lengths:
                features["avg_as_path_length"] = np.mean(as_path_lengths)
                features["as_path_variance"] = np.var(as_path_lengths)
                features["as_path_churn"] = np.std(as_path_lengths)
            else:
                features["avg_as_path_length"] = 0.0
                features["as_path_variance"] = 0.0
                features["as_path_churn"] = 0.0

        # Peer analysis
        if "peer" in df.columns:
            unique_peers = df["peer"].nunique()
            features["peer_diversity"] = unique_peers
            features["updates_per_peer"] = len(df) / max(unique_peers, 1)
        else:
            features["peer_diversity"] = 0.0
            features["updates_per_peer"] = 0.0

        # Temporal patterns
        if "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"], unit="ms")
            if len(timestamps) > 1:
                intervals = timestamps.diff().dt.total_seconds().dropna()
                features["update_interval_mean"] = intervals.mean()
                features["update_interval_std"] = intervals.std()
                features["update_burstiness"] = intervals.std() / max(intervals.mean(), 1e-6)
            else:
                features["update_interval_mean"] = 0.0
                features["update_interval_std"] = 0.0
                features["update_burstiness"] = 0.0

        return features

    def extract_syslog_features(
        self, syslog_data: List[Dict[str, Any]], window: FeatureWindow
    ) -> Dict[str, float]:
        """
        Extract syslog-specific features from telemetry data within a time window.

        Analyzes system log messages to extract features related to severity distribution,
        message types, temporal patterns, and semantic event detection.

        Args:
            syslog_data (List[Dict[str, Any]]): List of syslog messages containing:
                - severity (str, optional): Message severity level (error, warning, info, critical)
                - message_type (str, optional): Type of log message
                - timestamp (int): Message timestamp in milliseconds
                - message (str, optional): Full log message text

            window (FeatureWindow): Time window containing:
                - start_time (datetime): Window start time
                - end_time (datetime): Window end time
                - duration_seconds (int): Window duration in seconds

        Returns:
            Dict[str, float]: Dictionary of syslog features:
                - error_rate (float): Proportion of error messages
                - warning_rate (float): Proportion of warning messages
                - critical_rate (float): Proportion of critical messages
                - info_rate (float): Proportion of info messages
                - message_type_diversity (float): Number of unique message types
                - most_common_message_type (str): Most frequent message type
                - message_interval_mean (float): Mean time between messages
                - message_interval_std (float): Std dev of message intervals
                - message_burstiness (float): Coefficient of variation of intervals
                - semantic_event_scores (Dict): Scores for detected semantic events

        Note:
            Returns default values (0.0) if no syslog data is provided or if required
            fields are missing from the data.
        """
        features = {}

        if not syslog_data:
            return self._get_default_syslog_features()

        df = pd.DataFrame(syslog_data)

        # Severity distribution
        if "severity" in df.columns:
            severity_counts = df["severity"].value_counts()
            total_messages = len(df)

            features["error_rate"] = severity_counts.get("error", 0) / total_messages
            features["warning_rate"] = severity_counts.get("warning", 0) / total_messages
            features["critical_rate"] = severity_counts.get("critical", 0) / total_messages
            features["info_rate"] = severity_counts.get("info", 0) / total_messages
        else:
            features["error_rate"] = 0.0
            features["warning_rate"] = 0.0
            features["critical_rate"] = 0.0
            features["info_rate"] = 0.0

        # Message type analysis
        if "message_type" in df.columns:
            message_type_counts = df["message_type"].value_counts()
            features["message_type_diversity"] = len(message_type_counts)
            features["most_common_message_type"] = (
                message_type_counts.index[0] if len(message_type_counts) > 0 else "unknown"
            )
        else:
            features["message_type_diversity"] = 0.0
            features["most_common_message_type"] = "unknown"

        # Temporal patterns
        if "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"], unit="ms")
            if len(timestamps) > 1:
                intervals = timestamps.diff().dt.total_seconds().dropna()
                features["message_interval_mean"] = intervals.mean()
                features["message_interval_std"] = intervals.std()
                features["message_burstiness"] = intervals.std() / max(intervals.mean(), 1e-6)
            else:
                features["message_interval_mean"] = 0.0
                features["message_interval_std"] = 0.0
                features["message_burstiness"] = 0.0

        # Semantic analysis
        features.update(self._extract_semantic_features(df))

        return features

    def extract_system_features(
        self, system_data: List[Dict[str, Any]], window: FeatureWindow
    ) -> Dict[str, float]:
        """
        Extract system-level features from telemetry data within a time window.

        Analyzes system metrics to extract features related to CPU usage, memory utilization,
        temperature, and other system performance indicators.

        Args:
            system_data (List[Dict[str, Any]]): List of system metric records containing:
                - metrics (Dict, optional): System metrics including:
                    - cpu_usage_percent (float): CPU utilization percentage
                    - memory_usage_percent (float): Memory utilization percentage
                    - temperature_celsius (float): System temperature in Celsius
                - timestamp (int): Metric timestamp in milliseconds

            window (FeatureWindow): Time window containing:
                - start_time (datetime): Window start time
                - end_time (datetime): Window end time
                - duration_seconds (int): Window duration in seconds

        Returns:
            Dict[str, float]: Dictionary of system features:
                - cpu_mean (float): Mean CPU usage percentage
                - cpu_std (float): Standard deviation of CPU usage
                - cpu_max (float): Maximum CPU usage percentage
                - cpu_trend (float): CPU usage trend (positive/negative slope)
                - memory_mean (float): Mean memory usage percentage
                - memory_std (float): Standard deviation of memory usage
                - memory_max (float): Maximum memory usage percentage
                - memory_trend (float): Memory usage trend
                - temperature_mean (float): Mean temperature in Celsius
                - temperature_std (float): Standard deviation of temperature
                - temperature_max (float): Maximum temperature
                - temperature_trend (float): Temperature trend

        Note:
            Returns default values (0.0) if no system data is provided or if required
            metrics are missing from the data.
        """
        features = {}

        if not system_data:
            return self._get_default_system_features()

        df = pd.DataFrame(system_data)

        # CPU and memory analysis
        if "metrics" in df.columns:
            cpu_values = []
            memory_values = []
            temperature_values = []

            for metrics in df["metrics"].dropna():
                if isinstance(metrics, dict):
                    if "cpu_usage_percent" in metrics:
                        cpu_values.append(metrics["cpu_usage_percent"])
                    if "memory_usage_percent" in metrics:
                        memory_values.append(metrics["memory_usage_percent"])
                    if "temperature_celsius" in metrics:
                        temperature_values.append(metrics["temperature_celsius"])

            if cpu_values:
                features["cpu_mean"] = np.mean(cpu_values)
                features["cpu_std"] = np.std(cpu_values)
                features["cpu_max"] = np.max(cpu_values)
                features["cpu_trend"] = self._calculate_trend(cpu_values)
            else:
                features["cpu_mean"] = 0.0
                features["cpu_std"] = 0.0
                features["cpu_max"] = 0.0
                features["cpu_trend"] = 0.0

            if memory_values:
                features["memory_mean"] = np.mean(memory_values)
                features["memory_std"] = np.std(memory_values)
                features["memory_max"] = np.max(memory_values)
                features["memory_trend"] = self._calculate_trend(memory_values)
            else:
                features["memory_mean"] = 0.0
                features["memory_std"] = 0.0
                features["memory_max"] = 0.0
                features["memory_trend"] = 0.0

            if temperature_values:
                features["temperature_mean"] = np.mean(temperature_values)
                features["temperature_std"] = np.std(temperature_values)
                features["temperature_max"] = np.max(temperature_values)
                features["temperature_trend"] = self._calculate_trend(temperature_values)
            else:
                features["temperature_mean"] = 0.0
                features["temperature_std"] = 0.0
                features["temperature_max"] = 0.0
                features["temperature_trend"] = 0.0

        return features

    def extract_interface_features(
        self, interface_data: List[Dict[str, Any]], window: FeatureWindow
    ) -> Dict[str, float]:
        """
        Extract interface-specific features from telemetry data within a time window.

        Analyzes network interface metrics to extract features related to link status,
        traffic patterns, error rates, and interface utilization.

        Args:
            interface_data (List[Dict[str, Any]]): List of interface metric records containing:
                - interface_name (str, optional): Name of the network interface
                - status (str, optional): Interface status (up, down, unknown)
                - metrics (Dict, optional): Interface metrics including:
                    - bytes_in (int): Incoming bytes
                    - bytes_out (int): Outgoing bytes
                    - packets_in (int): Incoming packets
                    - packets_out (int): Outgoing packets
                    - errors_in (int): Incoming error count
                    - errors_out (int): Outgoing error count
                - timestamp (int): Metric timestamp in milliseconds

            window (FeatureWindow): Time window containing:
                - start_time (datetime): Window start time
                - end_time (datetime): Window end time
                - duration_seconds (int): Window duration in seconds

        Returns:
            Dict[str, float]: Dictionary of interface features:
                - interface_count (float): Number of unique interfaces
                - up_interfaces (float): Number of interfaces in 'up' status
                - down_interfaces (float): Number of interfaces in 'down' status
                - total_bytes_in (float): Total incoming bytes
                - total_bytes_out (float): Total outgoing bytes
                - total_packets_in (float): Total incoming packets
                - total_packets_out (float): Total outgoing packets
                - error_rate_in (float): Incoming error rate
                - error_rate_out (float): Outgoing error rate
                - utilization_ratio (float): Ratio of used to available capacity

        Note:
            Returns default values (0.0) if no interface data is provided or if required
            fields are missing from the data.
        """
        features = {}

        if not interface_data:
            return self._get_default_interface_features()

        df = pd.DataFrame(interface_data)

        # Interface status analysis
        if "metrics" in df.columns:
            up_interfaces = 0
            down_interfaces = 0
            total_bytes_in = 0
            total_bytes_out = 0
            total_errors = 0

            for metrics in df["metrics"].dropna():
                if isinstance(metrics, dict):
                    if metrics.get("status") == "up":
                        up_interfaces += 1
                    else:
                        down_interfaces += 1

                    total_bytes_in += metrics.get("bytes_in", 0)
                    total_bytes_out += metrics.get("bytes_out", 0)
                    total_errors += metrics.get("errors_in", 0) + metrics.get("errors_out", 0)

            total_interfaces = up_interfaces + down_interfaces
            features["interface_availability"] = up_interfaces / max(total_interfaces, 1)
            features["total_throughput"] = total_bytes_in + total_bytes_out
            features["error_rate"] = total_errors / max(total_bytes_in + total_bytes_out, 1)
        else:
            features["interface_availability"] = 0.0
            features["total_throughput"] = 0.0
            features["error_rate"] = 0.0

        return features

    def extract_correlation_features(
        self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow
    ) -> Dict[str, float]:
        """
        Extract correlation features between different data sources within a time window.

        Analyzes relationships and correlations between BGP updates, syslog messages,
        system metrics, and interface data to identify cross-domain patterns.

        Args:
            all_data (Dict[str, List[Dict[str, Any]]]): Dictionary containing:
                - bgp (List[Dict]): BGP update messages
                - syslog (List[Dict]): System log messages
                - system (List[Dict]): System metric records
                - interface (List[Dict]): Interface metric records

            window (FeatureWindow): Time window containing:
                - start_time (datetime): Window start time
                - end_time (datetime): Window end time
                - duration_seconds (int): Window duration in seconds

        Returns:
            Dict[str, float]: Dictionary of correlation features:
                - bgp_syslog_correlation (float): Correlation between BGP rate and syslog error rate
                - temporal_alignment (float): Temporal alignment score across data sources
                - event_sequence_score (float): Score for event sequence patterns
                - cross_domain_consistency (float): Consistency across different data domains
                - anomaly_co_occurrence (float): Co-occurrence of anomalies across sources

        Note:
            Returns 0.0 for correlation features when insufficient data is available
            for meaningful correlation analysis.
        """
        features = {}

        # Cross-correlation between BGP and syslog
        bgp_data = all_data.get("bgp", [])
        syslog_data = all_data.get("syslog", [])

        if bgp_data and syslog_data:
            # Calculate correlation between BGP update rate and syslog error rate
            bgp_rate = len(bgp_data) / window.duration_seconds
            syslog_error_count = sum(1 for msg in syslog_data if msg.get("severity") == "error")
            syslog_error_rate = syslog_error_count / window.duration_seconds

            features["bgp_syslog_correlation"] = self._calculate_correlation(
                bgp_rate, syslog_error_rate
            )
        else:
            features["bgp_syslog_correlation"] = 0.0

        # Temporal alignment analysis
        features["temporal_alignment"] = self._analyze_temporal_alignment(all_data, window)

        # Event sequence analysis
        features["event_sequence_score"] = self._analyze_event_sequences(all_data, window)

        return features

    def _extract_semantic_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract semantic features based on predefined event patterns.

        Analyzes log messages to detect semantic patterns that correspond to
        known network events such as link failures, BGP resets, and system overload.

        Args:
            df (pd.DataFrame): DataFrame containing log messages with columns:
                - message (str, optional): Full log message text
                - severity (str, optional): Message severity level
                - timestamp (int, optional): Message timestamp

        Returns:
            Dict[str, float]: Dictionary of semantic feature scores:
                - link_failure_score (float): Score for link failure patterns
                - bgp_reset_score (float): Score for BGP session reset patterns
                - prefix_hijack_score (float): Score for prefix hijacking patterns
                - route_flap_score (float): Score for route flapping patterns
                - system_overload_score (float): Score for system overload patterns
                - overall_semantic_score (float): Combined semantic event score

        Note:
            Scores range from 0.0 (no pattern detected) to 1.0 (strong pattern match).
            Uses keyword matching and severity sequence analysis for pattern detection.
        """
        features = {}

        # Analyze message content for semantic patterns
        if "message" in df.columns:
            messages = df["message"].dropna().astype(str)

            # Count occurrences of each event pattern
            for pattern_name, pattern_config in self.event_patterns.items():
                keyword_matches = 0
                for message in messages:
                    for keyword in pattern_config["keywords"]:
                        if keyword.lower() in message.lower():
                            keyword_matches += 1
                            break

                features[f"{pattern_name}_indicator"] = (
                    keyword_matches / len(messages) if len(messages) > 0 else 0
                )

        # Analyze severity sequences
        if "severity" in df.columns:
            severity_sequence = df["severity"].tolist()
            features["severity_escalation"] = self._detect_severity_escalation(severity_sequence)
            features["severity_consistency"] = self._calculate_severity_consistency(
                severity_sequence
            )
        else:
            features["severity_escalation"] = 0.0
            features["severity_consistency"] = 0.0

        return features

    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend (slope) of a time series using linear regression.

        Computes the slope of a linear fit to the time series data, indicating
        whether the values are increasing (positive) or decreasing (negative) over time.

        Args:
            values (List[float]): Time series data points

        Returns:
            float: Slope of the linear trend:
                - Positive values indicate increasing trend
                - Negative values indicate decreasing trend
                - Zero indicates no trend
                - Returns 0.0 if insufficient data points (< 2)
        """
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        return slope

    def _calculate_correlation(self, x: float, y: float) -> float:
        """
        Calculate correlation between two scalar values.

        For single values, this is a placeholder that returns 0.0.
        In practice, correlation would be calculated over multiple time windows
        using historical data to establish meaningful relationships.

        Args:
            x (float): First value for correlation calculation
            y (float): Second value for correlation calculation

        Returns:
            float: Correlation coefficient (currently returns 0.0 for single values)

        Note:
            This is a simplified implementation. A full implementation would
            maintain historical data and calculate Pearson correlation over time.
        """
        # For single values, return 0 (no correlation)
        # In practice, this would be calculated over multiple time windows
        return 0.0

    def _analyze_temporal_alignment(
        self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow
    ) -> float:
        """
        Analyze temporal alignment between different data sources.

        Evaluates how well events from different data sources (BGP, syslog, system, interface)
        are temporally aligned, which can indicate correlated network events.

        Args:
            all_data (Dict[str, List[Dict[str, Any]]]): Dictionary containing data from all sources
            window (FeatureWindow): Time window for analysis

        Returns:
            float: Temporal alignment score (0.0 to 1.0):
                - 1.0 indicates perfect temporal alignment
                - 0.0 indicates no temporal alignment
                - Currently returns 0.5 as placeholder

        Note:
            This is a simplified implementation. A full implementation would analyze
            timestamp distributions and event co-occurrence patterns.
        """
        # Simple implementation - in practice would analyze timestamp alignment
        return 0.5

    def _analyze_event_sequences(
        self, all_data: Dict[str, List[Dict[str, Any]]], window: FeatureWindow
    ) -> float:
        """
        Analyze event sequences for patterns across data sources.

        Identifies sequential patterns in events that may indicate causal relationships
        or common failure modes across different network components.

        Args:
            all_data (Dict[str, List[Dict[str, Any]]]): Dictionary containing data from all sources
            window (FeatureWindow): Time window for analysis

        Returns:
            float: Event sequence pattern score (0.0 to 1.0):
                - 1.0 indicates strong sequential patterns
                - 0.0 indicates no sequential patterns
                - Currently returns 0.3 as placeholder

        Note:
            This is a simplified implementation. A full implementation would analyze
            event causality chains and temporal dependencies.
        """
        # Simple implementation - in practice would analyze event causality
        return 0.5

    def _detect_severity_escalation(self, severity_sequence: List[str]) -> float:
        """
        Detect severity escalation patterns in log messages.

        Analyzes a sequence of severity levels to identify escalation patterns
        that may indicate worsening network conditions or cascading failures.

        Args:
            severity_sequence (List[str]): List of severity levels in chronological order
                - Valid levels: 'info', 'warning', 'error', 'critical'

        Returns:
            float: Escalation score (0.0 to 1.0):
                - 1.0 indicates strong escalation pattern
                - 0.0 indicates no escalation
                - 0.5 indicates moderate escalation

        Note:
            Escalation is detected by analyzing the progression from lower to higher
            severity levels over time.
        """
        severity_levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        escalation_count = 0

        for i in range(1, len(severity_sequence)):
            current_level = severity_levels.get(severity_sequence[i], 0)
            previous_level = severity_levels.get(severity_sequence[i - 1], 0)
            if current_level > previous_level:
                escalation_count += 1

        return escalation_count / max(len(severity_sequence) - 1, 1)

    def _calculate_severity_consistency(self, severity_sequence: List[str]) -> float:
        """
        Calculate consistency of severity levels in log messages.

        Measures how consistent the severity levels are across a sequence of log messages,
        which can indicate whether the network is in a stable state or experiencing
        variable conditions.

        Args:
            severity_sequence (List[str]): List of severity levels in chronological order
                - Valid levels: 'info', 'warning', 'error', 'critical'

        Returns:
            float: Consistency score (0.0 to 1.0):
                - 1.0 indicates perfect consistency (all same severity)
                - 0.0 indicates maximum inconsistency
                - Returns 0.0 if sequence is empty

        Note:
            Consistency is calculated as the inverse of the variance in severity levels,
            normalized to the 0-1 range.
        """
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
        """
        Return default BGP features when no data is available.

        Provides a consistent set of default values for all BGP features
        when no BGP data is present in the time window.

        Args:
            None

        Returns:
            Dict[str, float]: Dictionary of default BGP features with all values set to 0.0:
                - announcement_rate, withdrawal_rate, avg_as_path_length
                - as_path_variance, as_path_churn, peer_diversity
                - updates_per_peer, update_interval_mean, update_interval_std
                - update_burstiness

        Note:
            These default values ensure consistent feature vector dimensions
            even when no BGP data is available for analysis.
        """
        return {
            "announcement_rate": 0.0,
            "withdrawal_rate": 0.0,
            "avg_as_path_length": 0.0,
            "as_path_variance": 0.0,
            "as_path_churn": 0.0,
            "peer_diversity": 0.0,
            "updates_per_peer": 0.0,
            "update_interval_mean": 0.0,
            "update_interval_std": 0.0,
            "update_burstiness": 0.0,
        }

    def _get_default_syslog_features(self) -> Dict[str, float]:
        """
        Return default syslog features when no data is available.

        Provides a consistent set of default values for all syslog features
        when no syslog data is present in the time window.

        Args:
            None

        Returns:
            Dict[str, float]: Dictionary of default syslog features with all values set to 0.0:
                - error_rate, warning_rate, critical_rate, info_rate
                - message_type_diversity, message_interval_mean
                - message_interval_std, message_burstiness
                - semantic event scores

        Note:
            These default values ensure consistent feature vector dimensions
            even when no syslog data is available for analysis.
        """
        return {
            "error_rate": 0.0,
            "warning_rate": 0.0,
            "critical_rate": 0.0,
            "info_rate": 0.0,
            "message_type_diversity": 0.0,
            "message_interval_mean": 0.0,
            "message_interval_std": 0.0,
            "message_burstiness": 0.0,
            "severity_escalation": 0.0,
            "severity_consistency": 0.0,
        }

    def _get_default_system_features(self) -> Dict[str, float]:
        """
        Return default system features when no data is available.

        Provides a consistent set of default values for all system features
        when no system metric data is present in the time window.

        Args:
            None

        Returns:
            Dict[str, float]: Dictionary of default system features with all values set to 0.0:
                - cpu_mean, cpu_std, cpu_max, cpu_trend
                - memory_mean, memory_std, memory_max, memory_trend
                - temperature_mean, temperature_std, temperature_max, temperature_trend

        Note:
            These default values ensure consistent feature vector dimensions
            even when no system metric data is available for analysis.
        """
        return {
            "cpu_mean": 0.0,
            "cpu_std": 0.0,
            "cpu_max": 0.0,
            "cpu_trend": 0.0,
            "memory_mean": 0.0,
            "memory_std": 0.0,
            "memory_max": 0.0,
            "memory_trend": 0.0,
            "temperature_mean": 0.0,
            "temperature_std": 0.0,
            "temperature_max": 0.0,
            "temperature_trend": 0.0,
        }

    def _get_default_interface_features(self) -> Dict[str, float]:
        """
        Return default interface features when no data is available.

        Provides a consistent set of default values for all interface features
        when no interface metric data is present in the time window.

        Args:
            None

        Returns:
            Dict[str, float]: Dictionary of default interface features with all values set to 0.0:
                - interface_count, up_interfaces, down_interfaces
                - total_bytes_in, total_bytes_out, total_packets_in, total_packets_out
                - error_rate_in, error_rate_out, utilization_ratio

        Note:
            These default values ensure consistent feature vector dimensions
            even when no interface metric data is available for analysis.
        """
        return {"interface_availability": 0.0, "total_throughput": 0.0, "error_rate": 0.0}


class FeatureSelector:
    """
    Feature selection based on mutual information and correlation analysis.

    Implements the approach from Feltin 2023 paper for selecting
    the most informative features for anomaly detection.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the FeatureSelector with configuration parameters.

        Sets up feature selection parameters and tracking variables for
        mutual information and correlation-based feature selection.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - max_features (int): Maximum number of features to select (default: 20)
                - correlation_threshold (float): Maximum correlation threshold for redundancy removal (default: 0.8)
                - method (str): Feature selection method (default: 'mutual_information')

        Returns:
            None

        Side Effects:
            - Initializes feature scores tracking dictionary
            - Initializes selected features list
            - Configures logging for the feature selector
        """
        self.config = config
        self.max_features = config.get("max_features", 20)
        self.correlation_threshold = config.get("correlation_threshold", 0.8)
        self.method = config.get("method", "mutual_information")

        # Feature importance scores
        self.feature_scores = {}
        self.selected_features = []

        logger.info("Feature selector initialized")

    def select_features(
        self, features_df: pd.DataFrame, target_labels: Optional[np.ndarray] = None
    ) -> List[str]:
        """
        Select the most informative features using mutual information and correlation analysis.

        Implements feature selection based on mutual information scores and removes
        highly correlated features to reduce redundancy while maintaining informativeness.

        Args:
            features_df (pd.DataFrame): DataFrame containing feature values with features as columns
            target_labels (Optional[np.ndarray]): Target labels for supervised feature selection
                - If None, uses unsupervised mutual information
                - If provided, uses supervised mutual information

        Returns:
            List[str]: List of selected feature names ordered by importance

        Note:
            - Features are selected based on mutual information scores
            - Highly correlated features (above threshold) are removed
            - Maximum number of features is limited by max_features parameter
        """
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
        upper_tri = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )

        to_drop = [
            column
            for column in upper_tri.columns
            if any(upper_tri[column] > self.correlation_threshold)
        ]
        features_df = features_df.drop(columns=to_drop)

        # Select top features
        remaining_features = [f for f in features_df.columns if f not in to_drop]
        remaining_scores = [feature_importance[f] for f in remaining_features]

        # Sort by importance and select top features
        sorted_features = sorted(
            zip(remaining_features, remaining_scores), key=lambda x: x[1], reverse=True
        )
        selected_features = [f[0] for f in sorted_features[: self.max_features]]

        self.feature_scores = feature_importance
        self.selected_features = selected_features

        logger.info(
            f"Selected {len(selected_features)} features from {len(features_df.columns)} total features"
        )

        return selected_features

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores from the last feature selection.

        Returns a copy of the feature importance scores calculated during
        the most recent feature selection operation.

        Args:
            None

        Returns:
            Dict[str, float]: Dictionary mapping feature names to their importance scores

        Note:
            Scores are based on mutual information values calculated during
            the select_features() method call.
        """
        return self.feature_scores.copy()

    def get_selected_features(self) -> List[str]:
        """
        Get list of selected features from the last feature selection.

        Returns a copy of the list of feature names that were selected
        during the most recent feature selection operation.

        Args:
            None

        Returns:
            List[str]: List of selected feature names ordered by importance

        Note:
            Features are ordered by their mutual information scores
            from highest to lowest importance.
        """
        return self.selected_features.copy()


class PreprocessingPipeline:
    """
    Main preprocessing pipeline that coordinates feature extraction and selection.
    """

    def __init__(self, config_path: str):
        """
        Initialize the PreprocessingPipeline with configuration from YAML file.

        Loads configuration from a YAML file and initializes the feature extractor,
        feature selector, and data buffers for sliding window processing.

        Args:
            config_path (str): Path to the YAML configuration file containing:
                - preprocessing.feature_extraction: Configuration for feature extraction
                - preprocessing.feature_selection: Configuration for feature selection

        Returns:
            None

        Side Effects:
            - Loads configuration from YAML file
            - Initializes SemanticFeatureExtractor and FeatureSelector
            - Creates data buffers for different data types
            - Initializes feature history for correlation analysis
            - Configures logging for the preprocessing pipeline

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
        """
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.preprocessing_config = self.config.get("preprocessing", {})
        self.feature_extractor = SemanticFeatureExtractor(
            self.preprocessing_config.get("feature_extraction", {})
        )
        self.feature_selector = FeatureSelector(
            self.preprocessing_config.get("feature_selection", {})
        )

        # Data buffers for sliding window processing
        self.data_buffers = {
            "bgp": deque(maxlen=1000),
            "syslog": deque(maxlen=1000),
            "system": deque(maxlen=1000),
            "interface": deque(maxlen=1000),
        }

        # Feature history for correlation analysis
        self.feature_history = deque(maxlen=100)

        logger.info("Preprocessing pipeline initialized")

    def add_data(self, data_type: str, data: List[Dict[str, Any]]):
        """
        Add new data to the appropriate buffer for processing.

        Adds incoming telemetry data to the appropriate buffer based on data type.
        Data is stored in a deque with a maximum size to prevent memory overflow.

        Args:
            data_type (str): Type of data being added ('bgp', 'syslog', 'system', 'interface')
            data (List[Dict[str, Any]]): List of data records to add to the buffer

        Returns:
            None

        Side Effects:
            - Adds data to the appropriate buffer
            - Automatically removes old data if buffer exceeds maximum size
            - Logs warning if data_type is not recognized

        Note:
            Valid data types are: 'bgp', 'syslog', 'system', 'interface'
        """
        if data_type in self.data_buffers:
            self.data_buffers[data_type].extend(data)

    def extract_features(self, window_duration: int = 60) -> Optional[ExtractedFeatures]:
        """
        Extract features from the current data window using sliding window approach.

        Processes data from all buffers within the specified time window and extracts
        comprehensive features including BGP, syslog, system, interface, correlation,
        and semantic features.

        Args:
            window_duration (int): Duration of the time window in seconds (default: 60)

        Returns:
            Optional[ExtractedFeatures]: Extracted features object containing:
                - window_start (datetime): Start time of the window
                - window_end (datetime): End time of the window
                - bgp_features (Dict[str, float]): BGP-specific features
                - syslog_features (Dict[str, float]): Syslog-specific features
                - system_features (Dict[str, float]): System metric features
                - interface_features (Dict[str, float]): Interface metric features
                - correlation_features (Dict[str, float]): Cross-domain correlation features
                - semantic_features (Dict[str, float]): Semantic event features
            Returns None if insufficient data is available

        Note:
            - Uses current time as the end of the window
            - Filters data based on timestamp within the window
            - Returns None if no data is available in any buffer
        """
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=window_duration)

        # Filter data for the current window
        window_data = {}
        for data_type, buffer in self.data_buffers.items():
            window_data[data_type] = [
                item
                for item in buffer
                if datetime.fromtimestamp(item.get("timestamp", 0) / 1000) >= window_start
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
            data_points=[],
        )

        # Extract features from each data type
        bgp_features = self.feature_extractor.extract_bgp_features(
            window_data.get("bgp", []), feature_window
        )
        syslog_features = self.feature_extractor.extract_syslog_features(
            window_data.get("syslog", []), feature_window
        )
        system_features = self.feature_extractor.extract_system_features(
            window_data.get("system", []), feature_window
        )
        interface_features = self.feature_extractor.extract_interface_features(
            window_data.get("interface", []), feature_window
        )
        correlation_features = self.feature_extractor.extract_correlation_features(
            window_data, feature_window
        )

        # Extract semantic features
        semantic_features = self.feature_extractor._extract_semantic_features(
            pd.DataFrame(window_data.get("syslog", []))
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
            semantic_features=semantic_features,
        )

        # Store in feature history
        self.feature_history.append(extracted_features)

        return extracted_features

    def select_features(
        self, features_df: pd.DataFrame, target_labels: Optional[np.ndarray] = None
    ) -> List[str]:
        """
        Select the most informative features using the configured feature selector.

        Delegates feature selection to the internal FeatureSelector instance,
        which uses mutual information and correlation analysis to select features.

        Args:
            features_df (pd.DataFrame): DataFrame containing feature values
            target_labels (Optional[np.ndarray]): Target labels for supervised selection

        Returns:
            List[str]: List of selected feature names ordered by importance

        Note:
            This method is a wrapper around the FeatureSelector.select_features() method.
        """
        return self.feature_selector.select_features(features_df, target_labels)

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics for the preprocessing pipeline.

        Returns statistics about the current state of the pipeline including
        buffer sizes, feature history, and processing metrics.

        Args:
            None

        Returns:
            Dict[str, Any]: Dictionary containing processing statistics:
                - buffer_sizes (Dict[str, int]): Current size of each data buffer
                - feature_history_size (int): Number of features in history
                - total_processed_windows (int): Total number of processed windows
                - last_processing_time (datetime): Time of last feature extraction

        Note:
            Statistics are updated in real-time as data is processed.
        """
        return {
            "data_buffer_sizes": {k: len(v) for k, v in self.data_buffers.items()},
            "feature_history_size": len(self.feature_history),
            "selected_features_count": len(self.feature_selector.get_selected_features()),
            "feature_importance": self.feature_selector.get_feature_importance(),
        }
