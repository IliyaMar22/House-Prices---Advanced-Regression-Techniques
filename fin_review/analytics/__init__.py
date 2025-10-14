"""Analytics modules for KPIs, trends, aging, anomalies, and forecasting."""

from .kpis import KPICalculator, calculate_kpis
from .trends import TrendAnalyzer, analyze_trends
from .aging import AgingAnalyzer, calculate_aging
from .anomalies import AnomalyDetector, detect_anomalies
from .forecasting import Forecaster, generate_forecasts

__all__ = [
    'KPICalculator', 'calculate_kpis',
    'TrendAnalyzer', 'analyze_trends',
    'AgingAnalyzer', 'calculate_aging',
    'AnomalyDetector', 'detect_anomalies',
    'Forecaster', 'generate_forecasts'
]

