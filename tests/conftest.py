"""Pytest configuration and fixtures."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


@pytest.fixture
def sample_mapping_df():
    """Sample mapping DataFrame."""
    data = [
        {'gl_account': '400000', 'bucket': 'Revenue - Product A', 'type': 'Revenue', 'entity': 'BG'},
        {'gl_account': '600100', 'bucket': 'OPEX - Marketing', 'type': 'OPEX', 'entity': 'BG'},
        {'gl_account': '610000', 'bucket': 'Payroll - Salaries', 'type': 'Payroll', 'entity': 'BG'},
        {'gl_account': '120000', 'bucket': 'Receivables - Customers', 'type': 'Receivable', 'entity': 'BG'},
        {'gl_account': '230100', 'bucket': 'Payables - Suppliers', 'type': 'Payable', 'entity': 'BG'},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def sample_fagl_df():
    """Sample FAGL03 DataFrame."""
    np.random.seed(42)
    
    data = []
    current_date = datetime(2024, 1, 1)
    
    for i in range(100):
        data.append({
            'posting_date': current_date + timedelta(days=i),
            'doc_id': f'DOC-{i:05d}',
            'gl_account': np.random.choice(['400000', '600100', '610000', '120000', '230100']),
            'amount': np.random.uniform(-10000, 10000),
            'currency': 'EUR',
            'posting_text': f'Transaction {i}',
            'customer_vendor': f'PARTY-{np.random.randint(1, 10):03d}',
            'due_date': current_date + timedelta(days=i+30),
            'open_amount': np.random.uniform(0, 1000),
            'company_code': 'BG'
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def normalized_df(sample_fagl_df, sample_mapping_df):
    """Sample normalized DataFrame with mapping."""
    from fin_review.transformers import normalize_data
    return normalize_data(sample_fagl_df, sample_mapping_df)


@pytest.fixture
def config():
    """Sample configuration."""
    return {
        'amount_sign_convention': 'positive_debit',
        'default_currency': 'EUR',
        'aging_buckets': [
            [0, 0, "Current"],
            [1, 30, "0-30 days"],
            [31, 60, "31-60 days"],
            [61, 90, "61-90 days"],
            [91, 999999, ">90 days"],
        ],
        'enable_growth_metrics': True,
        'enable_ratios': True,
        'enable_seasonality': True,
        'enable_anomaly_detection': True,
        'anomaly_threshold_zscore': 3.0,
        'enable_forecasting': True,
        'forecast_periods': 6,
    }

