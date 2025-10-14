"""Tests for NLP commentary generation."""

import pytest
from fin_review.nlp import generate_commentary, CommentaryGenerator


def test_commentary_generation_basic(normalized_df, config):
    """Test basic commentary generation."""
    from fin_review.analytics import calculate_kpis, analyze_trends, calculate_aging, detect_anomalies
    
    kpis = calculate_kpis(normalized_df, config).to_dict()
    trends = analyze_trends(normalized_df, config).to_dict()
    aging = calculate_aging(normalized_df, config).to_dict()
    anomalies = detect_anomalies(normalized_df, config).to_dict()
    
    result = generate_commentary(normalized_df, kpis, trends, aging, anomalies, config)
    
    assert result.executive_summary is not None
    assert len(result.executive_summary) > 0


def test_commentary_has_insights(normalized_df, config):
    """Test that insights are generated."""
    from fin_review.analytics import calculate_kpis, analyze_trends, calculate_aging, detect_anomalies
    
    kpis = calculate_kpis(normalized_df, config).to_dict()
    trends = analyze_trends(normalized_df, config).to_dict()
    aging = calculate_aging(normalized_df, config).to_dict()
    anomalies = detect_anomalies(normalized_df, config).to_dict()
    
    result = generate_commentary(normalized_df, kpis, trends, aging, anomalies, config)
    
    assert isinstance(result.insights, list)
    assert isinstance(result.risks, list)
    assert isinstance(result.recommendations, list)


def test_commentary_email_summary(normalized_df, config):
    """Test email summary generation."""
    from fin_review.analytics import calculate_kpis, analyze_trends, calculate_aging, detect_anomalies
    
    kpis = calculate_kpis(normalized_df, config).to_dict()
    trends = analyze_trends(normalized_df, config).to_dict()
    aging = calculate_aging(normalized_df, config).to_dict()
    anomalies = detect_anomalies(normalized_df, config).to_dict()
    
    result = generate_commentary(normalized_df, kpis, trends, aging, anomalies, config)
    
    assert result.email_summary is not None
    assert len(result.email_summary) > 0
    # Email summary should be concise
    assert len(result.email_summary) < 2000  # Reasonable email length


def test_commentary_confidence_levels(normalized_df, config):
    """Test that commentary items have confidence levels."""
    from fin_review.analytics import calculate_kpis, analyze_trends, calculate_aging, detect_anomalies
    
    config['confidence_levels'] = True
    
    kpis = calculate_kpis(normalized_df, config).to_dict()
    trends = analyze_trends(normalized_df, config).to_dict()
    aging = calculate_aging(normalized_df, config).to_dict()
    anomalies = detect_anomalies(normalized_df, config).to_dict()
    
    result = generate_commentary(normalized_df, kpis, trends, aging, anomalies, config)
    
    valid_confidence = ['high', 'medium', 'low']
    
    for insight in result.insights:
        assert insight.confidence in valid_confidence
    
    for risk in result.risks:
        assert risk.confidence in valid_confidence

