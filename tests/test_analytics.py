"""Tests for analytics modules."""

import pytest
import pandas as pd
from fin_review.analytics import calculate_kpis, calculate_aging, detect_anomalies


def test_kpi_calculator_basic_metrics(normalized_df, config):
    """Test basic KPI calculations."""
    result = calculate_kpis(normalized_df, config)
    
    assert result.summary_kpis is not None
    assert 'total_revenue' in result.summary_kpis
    assert 'total_opex' in result.summary_kpis
    assert 'total_transactions' in result.summary_kpis


def test_kpi_monthly_aggregation(normalized_df, config):
    """Test monthly KPI aggregation."""
    result = calculate_kpis(normalized_df, config)
    
    assert result.monthly_kpis is not None
    assert len(result.monthly_kpis) > 0
    assert 'year_month' in result.monthly_kpis.columns


def test_aging_analysis_buckets(normalized_df, config):
    """Test that aging buckets are created correctly."""
    result = calculate_aging(normalized_df, config)
    
    # Check AR aging
    assert result.ar_aging is not None
    if len(result.ar_aging) > 0:
        assert 'aging_bucket' in result.ar_aging.columns
        assert 'outstanding_amount' in result.ar_aging.columns


def test_aging_summary_metrics(normalized_df, config):
    """Test aging summary metrics."""
    result = calculate_aging(normalized_df, config)
    
    assert 'total_outstanding' in result.ar_summary
    assert 'overdue_pct' in result.ar_summary
    assert result.ar_summary['overdue_pct'] >= 0
    assert result.ar_summary['overdue_pct'] <= 100


def test_anomaly_detection_runs(normalized_df, config):
    """Test that anomaly detection runs without errors."""
    result = detect_anomalies(normalized_df, config)
    
    assert result.anomalies is not None
    assert result.summary is not None
    assert 'total_count' in result.summary


def test_anomaly_severity_levels(normalized_df, config):
    """Test that anomalies have valid severity levels."""
    result = detect_anomalies(normalized_df, config)
    
    valid_severities = ['low', 'medium', 'high']
    
    for anomaly in result.anomalies:
        assert anomaly.severity in valid_severities


def test_kpi_top_items(normalized_df, config):
    """Test top items retrieval."""
    from fin_review.analytics.kpis import KPICalculator
    
    calculator = KPICalculator(normalized_df, config)
    top_buckets = calculator.get_top_items(group_by='bucket', n=5)
    
    assert len(top_buckets) <= 5
    if len(top_buckets) > 0:
        assert 'bucket' in top_buckets.columns
        assert 'total_amount' in top_buckets.columns

