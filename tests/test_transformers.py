"""Tests for data transformation modules."""

import pytest
import pandas as pd
from fin_review.transformers import validate_data, normalize_data, DataValidator, DataNormalizer


def test_validation_unmapped_gls(sample_fagl_df, sample_mapping_df, config):
    """Test detection of unmapped GL accounts."""
    # Add an unmapped GL account
    fagl_with_unmapped = sample_fagl_df.copy()
    fagl_with_unmapped.loc[0, 'gl_account'] = '999999'  # Unmapped
    
    result = validate_data(fagl_with_unmapped, sample_mapping_df, config)
    
    assert '999999' in result.unmapped_gls


def test_validation_quality_score(sample_fagl_df, sample_mapping_df, config):
    """Test quality score calculation."""
    result = validate_data(sample_fagl_df, sample_mapping_df, config)
    
    assert 0 <= result.quality_score <= 1.0


def test_normalization_adds_temporal_features(sample_fagl_df, sample_mapping_df, config):
    """Test that normalization adds temporal features."""
    result = normalize_data(sample_fagl_df, sample_mapping_df, config)
    
    assert 'year' in result.columns
    assert 'month' in result.columns
    assert 'quarter' in result.columns
    assert 'year_month' in result.columns


def test_normalization_adds_mapping_info(sample_fagl_df, sample_mapping_df, config):
    """Test that mapping information is merged."""
    result = normalize_data(sample_fagl_df, sample_mapping_df, config)
    
    assert 'bucket' in result.columns
    assert 'type' in result.columns
    assert 'is_mapped' in result.columns


def test_normalization_adds_type_flags(sample_fagl_df, sample_mapping_df, config):
    """Test that type flags are added."""
    result = normalize_data(sample_fagl_df, sample_mapping_df, config)
    
    assert 'is_receivable' in result.columns
    assert 'is_payable' in result.columns
    assert 'is_revenue' in result.columns
    assert 'is_opex' in result.columns


def test_normalization_calculates_overdue(sample_fagl_df, sample_mapping_df, config):
    """Test overdue calculation."""
    result = normalize_data(sample_fagl_df, sample_mapping_df, config)
    
    assert 'days_overdue' in result.columns
    assert 'is_overdue' in result.columns


def test_validator_warnings_list(sample_fagl_df, sample_mapping_df, config):
    """Test that validator generates warnings list."""
    validator = DataValidator(sample_fagl_df, sample_mapping_df, config)
    result = validator.validate()
    
    assert isinstance(result.warnings, list)
    assert isinstance(result.errors, list)


def test_normalizer_unmapped_summary(sample_fagl_df, sample_mapping_df, config):
    """Test unmapped GL summary generation."""
    # Add unmapped transactions
    fagl_with_unmapped = sample_fagl_df.copy()
    fagl_with_unmapped.loc[0:5, 'gl_account'] = '999999'
    
    normalizer = DataNormalizer(fagl_with_unmapped, sample_mapping_df, config)
    normalized = normalizer.normalize()
    
    unmapped_summary = normalizer.get_unmapped_summary()
    
    if len(unmapped_summary) > 0:
        assert 'gl_account' in unmapped_summary.columns
        assert 'transaction_count' in unmapped_summary.columns
        assert 'total_amount' in unmapped_summary.columns

