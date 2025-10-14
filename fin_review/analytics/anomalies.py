"""Anomaly detection module for financial data."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List
from dataclasses import dataclass
from scipy import stats
from sklearn.ensemble import IsolationForest

logger = structlog.get_logger()


@dataclass
class Anomaly:
    """Container for a single anomaly."""
    date: str
    bucket: str
    type: str
    amount: float
    expected_amount: float
    deviation: float
    deviation_pct: float
    severity: str  # 'low', 'medium', 'high'
    method: str  # 'zscore', 'mad', 'isolation_forest'
    explanation: Optional[str] = None
    top_contributors: Optional[List[Dict]] = None


@dataclass
class AnomalyResult:
    """Container for anomaly detection results."""
    anomalies: List[Anomaly]
    summary: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'anomalies': [
                {
                    'date': a.date,
                    'bucket': a.bucket,
                    'type': a.type,
                    'amount': a.amount,
                    'expected_amount': a.expected_amount,
                    'deviation': a.deviation,
                    'deviation_pct': a.deviation_pct,
                    'severity': a.severity,
                    'method': a.method,
                    'explanation': a.explanation,
                    'top_contributors': a.top_contributors
                }
                for a in self.anomalies
            ],
            'summary': self.summary
        }


class AnomalyDetector:
    """Detects anomalies in financial data."""
    
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        """
        Initialize anomaly detector.
        
        Args:
            df: Normalized FAGL DataFrame
            config: Configuration dictionary
        """
        self.df = df
        self.config = config or {}
        self.zscore_threshold = self.config.get('anomaly_threshold_zscore', 3.0)
        self.mad_threshold = self.config.get('anomaly_threshold_mad', 3.5)
        self.use_isolation_forest = self.config.get('use_isolation_forest', True)
    
    def detect_all(self) -> AnomalyResult:
        """
        Detect all anomalies using multiple methods.
        
        Returns:
            AnomalyResult object
        """
        logger.info("Starting anomaly detection")
        
        anomalies = []
        
        # Detect using Z-score
        zscore_anomalies = self._detect_zscore_anomalies()
        anomalies.extend(zscore_anomalies)
        
        # Detect using MAD (Median Absolute Deviation)
        mad_anomalies = self._detect_mad_anomalies()
        anomalies.extend(mad_anomalies)
        
        # Detect using Isolation Forest (if enabled)
        if self.use_isolation_forest:
            iso_anomalies = self._detect_isolation_forest_anomalies()
            anomalies.extend(iso_anomalies)
        
        # Remove duplicates (same date + bucket)
        anomalies = self._deduplicate_anomalies(anomalies)
        
        # Add explanations
        for anomaly in anomalies:
            self._explain_anomaly(anomaly)
        
        # Sort by severity and deviation
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        anomalies.sort(
            key=lambda a: (severity_order[a.severity], abs(a.deviation_pct)),
            reverse=False
        )
        
        # Create summary
        summary = self._create_summary(anomalies)
        
        logger.info(
            "Anomaly detection complete",
            total_anomalies=len(anomalies),
            high_severity=summary['high_severity_count']
        )
        
        return AnomalyResult(anomalies=anomalies, summary=summary)
    
    def _detect_zscore_anomalies(self) -> List[Anomaly]:
        """Detect anomalies using Z-score method."""
        anomalies = []
        
        # Group by bucket and month
        monthly = self.df.groupby(['year_month', 'bucket', 'type'])['amount'].sum().reset_index()
        
        # For each bucket, calculate Z-scores
        for bucket in monthly['bucket'].unique():
            bucket_data = monthly[monthly['bucket'] == bucket].copy()
            
            if len(bucket_data) < 6:  # Need sufficient history
                continue
            
            # Calculate Z-scores
            mean = bucket_data['amount'].mean()
            std = bucket_data['amount'].std()
            
            if std == 0:
                continue
            
            bucket_data['zscore'] = (bucket_data['amount'] - mean) / std
            
            # Identify anomalies
            anomalous = bucket_data[abs(bucket_data['zscore']) > self.zscore_threshold]
            
            for _, row in anomalous.iterrows():
                severity = self._determine_severity(abs(row['zscore']), 'zscore')
                
                anomalies.append(Anomaly(
                    date=row['year_month'].strftime('%Y-%m'),
                    bucket=row['bucket'],
                    type=row['type'],
                    amount=float(row['amount']),
                    expected_amount=float(mean),
                    deviation=float(row['amount'] - mean),
                    deviation_pct=float(((row['amount'] - mean) / abs(mean)) * 100) if mean != 0 else 0,
                    severity=severity,
                    method='zscore'
                ))
        
        logger.info(f"Z-score method detected {len(anomalies)} anomalies")
        return anomalies
    
    def _detect_mad_anomalies(self) -> List[Anomaly]:
        """Detect anomalies using Median Absolute Deviation (more robust to outliers)."""
        anomalies = []
        
        # Group by bucket and month
        monthly = self.df.groupby(['year_month', 'bucket', 'type'])['amount'].sum().reset_index()
        
        # For each bucket, calculate MAD scores
        for bucket in monthly['bucket'].unique():
            bucket_data = monthly[monthly['bucket'] == bucket].copy()
            
            if len(bucket_data) < 6:
                continue
            
            # Calculate MAD
            median = bucket_data['amount'].median()
            mad = np.median(np.abs(bucket_data['amount'] - median))
            
            if mad == 0:
                continue
            
            # Modified Z-score using MAD
            bucket_data['mad_score'] = 0.6745 * (bucket_data['amount'] - median) / mad
            
            # Identify anomalies
            anomalous = bucket_data[abs(bucket_data['mad_score']) > self.mad_threshold]
            
            for _, row in anomalous.iterrows():
                severity = self._determine_severity(abs(row['mad_score']), 'mad')
                
                anomalies.append(Anomaly(
                    date=row['year_month'].strftime('%Y-%m'),
                    bucket=row['bucket'],
                    type=row['type'],
                    amount=float(row['amount']),
                    expected_amount=float(median),
                    deviation=float(row['amount'] - median),
                    deviation_pct=float(((row['amount'] - median) / abs(median)) * 100) if median != 0 else 0,
                    severity=severity,
                    method='mad'
                ))
        
        logger.info(f"MAD method detected {len(anomalies)} anomalies")
        return anomalies
    
    def _detect_isolation_forest_anomalies(self) -> List[Anomaly]:
        """Detect anomalies using Isolation Forest machine learning."""
        anomalies = []
        
        # Group by bucket and month
        monthly = self.df.groupby(['year_month', 'bucket', 'type'])['amount'].sum().reset_index()
        
        # For each bucket
        for bucket in monthly['bucket'].unique():
            bucket_data = monthly[monthly['bucket'] == bucket].copy()
            
            if len(bucket_data) < 10:  # Need more data for ML
                continue
            
            # Prepare features
            X = bucket_data[['amount']].values
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42
            )
            predictions = iso_forest.fit_predict(X)
            scores = iso_forest.score_samples(X)
            
            # -1 indicates anomaly
            bucket_data['is_anomaly'] = predictions == -1
            bucket_data['anomaly_score'] = scores
            
            anomalous = bucket_data[bucket_data['is_anomaly']]
            
            # Calculate expected value (median of normal points)
            normal_amounts = bucket_data[~bucket_data['is_anomaly']]['amount']
            expected = normal_amounts.median() if len(normal_amounts) > 0 else bucket_data['amount'].median()
            
            for _, row in anomalous.iterrows():
                # Severity based on how negative the anomaly score is
                severity = self._determine_severity(abs(row['anomaly_score']), 'isolation_forest')
                
                anomalies.append(Anomaly(
                    date=row['year_month'].strftime('%Y-%m'),
                    bucket=row['bucket'],
                    type=row['type'],
                    amount=float(row['amount']),
                    expected_amount=float(expected),
                    deviation=float(row['amount'] - expected),
                    deviation_pct=float(((row['amount'] - expected) / abs(expected)) * 100) if expected != 0 else 0,
                    severity=severity,
                    method='isolation_forest'
                ))
        
        logger.info(f"Isolation Forest detected {len(anomalies)} anomalies")
        return anomalies
    
    def _determine_severity(self, score: float, method: str) -> str:
        """Determine severity level based on score."""
        if method == 'zscore':
            if score > 4:
                return 'high'
            elif score > 3.5:
                return 'medium'
            else:
                return 'low'
        elif method == 'mad':
            if score > 5:
                return 'high'
            elif score > 4:
                return 'medium'
            else:
                return 'low'
        elif method == 'isolation_forest':
            if score < -0.3:
                return 'high'
            elif score < -0.2:
                return 'medium'
            else:
                return 'low'
        
        return 'low'
    
    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Remove duplicate anomalies (same date + bucket)."""
        seen = set()
        unique = []
        
        # Prioritize by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_anomalies = sorted(
            anomalies,
            key=lambda a: (a.date, a.bucket, severity_order[a.severity])
        )
        
        for anomaly in sorted_anomalies:
            key = (anomaly.date, anomaly.bucket)
            if key not in seen:
                seen.add(key)
                unique.append(anomaly)
        
        return unique
    
    def _explain_anomaly(self, anomaly: Anomaly):
        """Add explanation and top contributors to anomaly."""
        # Get data for this anomaly
        year_month = pd.to_datetime(anomaly.date).to_period('M')
        
        anomaly_data = self.df[
            (self.df['year_month'] == year_month) &
            (self.df['bucket'] == anomaly.bucket)
        ].copy()
        
        if len(anomaly_data) == 0:
            return
        
        # Find top contributors
        if 'customer_vendor' in anomaly_data.columns:
            top_vendors = anomaly_data.groupby('customer_vendor')['amount'].sum().abs().nlargest(3)
            anomaly.top_contributors = [
                {'party': party, 'amount': float(amount)}
                for party, amount in top_vendors.items()
            ]
        
        # Generate explanation
        direction = "increase" if anomaly.deviation > 0 else "decrease"
        abs_pct = abs(anomaly.deviation_pct)
        
        explanation_parts = [
            f"{abs_pct:.1f}% {direction} vs expected in {anomaly.bucket}"
        ]
        
        if anomaly.top_contributors and len(anomaly.top_contributors) > 0:
            top_party = anomaly.top_contributors[0]['party']
            top_amount = anomaly.top_contributors[0]['amount']
            pct_of_total = (top_amount / abs(anomaly.amount)) * 100 if anomaly.amount != 0 else 0
            
            explanation_parts.append(
                f"Top contributor: {top_party} ({pct_of_total:.0f}% of total)"
            )
        
        anomaly.explanation = ". ".join(explanation_parts)
    
    def _create_summary(self, anomalies: List[Anomaly]) -> Dict:
        """Create summary statistics for anomalies."""
        if not anomalies:
            return {
                'total_count': 0,
                'high_severity_count': 0,
                'medium_severity_count': 0,
                'low_severity_count': 0,
                'by_type': {},
                'by_bucket': {}
            }
        
        summary = {
            'total_count': len(anomalies),
            'high_severity_count': sum(1 for a in anomalies if a.severity == 'high'),
            'medium_severity_count': sum(1 for a in anomalies if a.severity == 'medium'),
            'low_severity_count': sum(1 for a in anomalies if a.severity == 'low'),
            'by_type': {},
            'by_bucket': {}
        }
        
        # Count by type
        for anomaly in anomalies:
            summary['by_type'][anomaly.type] = summary['by_type'].get(anomaly.type, 0) + 1
            summary['by_bucket'][anomaly.bucket] = summary['by_bucket'].get(anomaly.bucket, 0) + 1
        
        return summary


def detect_anomalies(df: pd.DataFrame, config: Optional[Dict] = None) -> AnomalyResult:
    """
    Convenience function to detect anomalies.
    
    Args:
        df: Normalized FAGL DataFrame
        config: Configuration dictionary
    
    Returns:
        AnomalyResult object
    """
    detector = AnomalyDetector(df, config)
    return detector.detect_all()

