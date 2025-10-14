"""Forecasting module for time series predictions."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List
from dataclasses import dataclass
import warnings

logger = structlog.get_logger()


@dataclass
class ForecastResult:
    """Container for forecast results."""
    forecasts: pd.DataFrame
    summary: Dict
    method_used: str
    confidence_level: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'forecasts': self.forecasts.to_dict('records'),
            'summary': self.summary,
            'method_used': self.method_used,
            'confidence_level': self.confidence_level
        }


class Forecaster:
    """Generates forecasts for financial metrics."""
    
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        """
        Initialize forecaster.
        
        Args:
            df: Normalized FAGL DataFrame
            config: Configuration dictionary
        """
        self.df = df
        self.config = config or {}
        self.forecast_periods = self.config.get('forecast_periods', 6)
        self.confidence_level = self.config.get('forecast_confidence_level', 0.95)
    
    def forecast_all(self) -> ForecastResult:
        """
        Generate forecasts for all major metrics.
        
        Returns:
            ForecastResult object
        """
        if not self.config.get('enable_forecasting', True):
            logger.info("Forecasting disabled")
            return self._empty_result()
        
        logger.info(f"Generating forecasts for {self.forecast_periods} periods")
        
        # Try different forecasting methods in order of preference
        try:
            # Try pmdarima ARIMA
            result = self._forecast_arima()
            logger.info("Using ARIMA forecasting")
            return result
        except Exception as e:
            logger.warning(f"ARIMA forecasting failed: {e}, falling back to moving average")
            
            try:
                # Fallback to moving average
                result = self._forecast_moving_average()
                logger.info("Using moving average forecasting")
                return result
            except Exception as e:
                logger.error(f"All forecasting methods failed: {e}")
                return self._empty_result()
    
    def _forecast_arima(self) -> ForecastResult:
        """Forecast using ARIMA model from pmdarima."""
        try:
            from pmdarima import auto_arima
        except ImportError:
            raise ImportError("pmdarima not installed. Install with: pip install pmdarima")
        
        forecasts = []
        
        # Forecast for each major type
        for metric_type in ['Revenue', 'OPEX', 'Payroll']:
            type_data = self.df[self.df['type'] == metric_type]
            
            if len(type_data) == 0:
                continue
            
            # Get monthly data
            monthly = type_data.groupby('year_month')['amount'].sum()
            
            if len(monthly) < 12:  # Need at least 12 months
                logger.warning(f"Insufficient data for {metric_type} forecasting (need >= 12 months)")
                continue
            
            # Fit ARIMA model
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                model = auto_arima(
                    monthly.values,
                    seasonal=True,
                    m=12,  # Monthly seasonality
                    suppress_warnings=True,
                    error_action='ignore',
                    stepwise=True,
                    max_p=3,
                    max_q=3,
                    max_P=2,
                    max_Q=2
                )
            
            # Generate forecast
            forecast_values, conf_int = model.predict(
                n_periods=self.forecast_periods,
                return_conf_int=True,
                alpha=1 - self.confidence_level
            )
            
            # Create forecast dates
            last_date = monthly.index[-1].to_timestamp()
            forecast_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=self.forecast_periods,
                freq='M'
            )
            
            # Store forecasts
            for i, date in enumerate(forecast_dates):
                forecasts.append({
                    'date': date.strftime('%Y-%m'),
                    'type': metric_type,
                    'forecast': float(forecast_values[i]),
                    'lower_bound': float(conf_int[i, 0]),
                    'upper_bound': float(conf_int[i, 1]),
                })
        
        forecasts_df = pd.DataFrame(forecasts)
        
        summary = self._create_forecast_summary(forecasts_df)
        
        return ForecastResult(
            forecasts=forecasts_df,
            summary=summary,
            method_used='ARIMA',
            confidence_level=self.confidence_level
        )
    
    def _forecast_moving_average(self) -> ForecastResult:
        """Forecast using weighted moving average (fallback method)."""
        forecasts = []
        
        # Forecast for each major type
        for metric_type in ['Revenue', 'OPEX', 'Payroll']:
            type_data = self.df[self.df['type'] == metric_type]
            
            if len(type_data) == 0:
                continue
            
            # Get monthly data
            monthly = type_data.groupby('year_month')['amount'].sum()
            
            if len(monthly) < 3:
                continue
            
            # Calculate weighted moving average (more weight to recent months)
            recent_months = min(6, len(monthly))
            recent_values = monthly.values[-recent_months:]
            
            # Weights: more recent months get higher weight
            weights = np.arange(1, recent_months + 1)
            weights = weights / weights.sum()
            
            base_forecast = np.average(recent_values, weights=weights)
            
            # Calculate trend
            if len(monthly) >= 6:
                trend = (monthly.values[-1] - monthly.values[-6]) / 6
            else:
                trend = 0
            
            # Calculate variability for confidence intervals
            std = monthly.std()
            z_score = 1.96 if self.confidence_level >= 0.95 else 1.645
            
            # Create forecast dates
            last_date = monthly.index[-1].to_timestamp()
            forecast_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=self.forecast_periods,
                freq='M'
            )
            
            # Generate forecasts
            for i, date in enumerate(forecast_dates):
                forecast_value = base_forecast + (trend * (i + 1))
                margin = z_score * std * np.sqrt(i + 1)
                
                forecasts.append({
                    'date': date.strftime('%Y-%m'),
                    'type': metric_type,
                    'forecast': float(forecast_value),
                    'lower_bound': float(forecast_value - margin),
                    'upper_bound': float(forecast_value + margin),
                })
        
        forecasts_df = pd.DataFrame(forecasts)
        
        summary = self._create_forecast_summary(forecasts_df)
        
        return ForecastResult(
            forecasts=forecasts_df,
            summary=summary,
            method_used='Weighted Moving Average',
            confidence_level=self.confidence_level
        )
    
    def _create_forecast_summary(self, forecasts_df: pd.DataFrame) -> Dict:
        """Create summary of forecasts."""
        if len(forecasts_df) == 0:
            return {}
        
        summary = {}
        
        for metric_type in forecasts_df['type'].unique():
            type_forecasts = forecasts_df[forecasts_df['type'] == metric_type]
            
            # Get historical average
            historical = self.df[self.df['type'] == metric_type].groupby('year_month')['amount'].sum()
            historical_avg = historical.mean() if len(historical) > 0 else 0
            
            # Get forecast average
            forecast_avg = type_forecasts['forecast'].mean()
            
            # Calculate expected growth
            growth = ((forecast_avg - historical_avg) / abs(historical_avg)) * 100 if historical_avg != 0 else 0
            
            summary[metric_type] = {
                'forecast_avg': float(forecast_avg),
                'historical_avg': float(historical_avg),
                'expected_growth_pct': float(growth),
                'forecast_range': {
                    'min': float(type_forecasts['lower_bound'].min()),
                    'max': float(type_forecasts['upper_bound'].max())
                }
            }
        
        return summary
    
    def _empty_result(self) -> ForecastResult:
        """Return empty forecast result."""
        return ForecastResult(
            forecasts=pd.DataFrame(),
            summary={},
            method_used='None',
            confidence_level=self.confidence_level
        )
    
    def forecast_metric(self, metric_type: str) -> Optional[pd.DataFrame]:
        """
        Forecast a specific metric.
        
        Args:
            metric_type: Type to forecast (e.g., 'Revenue', 'OPEX')
        
        Returns:
            DataFrame with forecasts or None
        """
        type_data = self.df[self.df['type'] == metric_type]
        
        if len(type_data) == 0:
            logger.warning(f"No data found for {metric_type}")
            return None
        
        monthly = type_data.groupby('year_month')['amount'].sum()
        
        if len(monthly) < 3:
            logger.warning(f"Insufficient data for {metric_type} forecasting")
            return None
        
        # Use simple moving average for single metric
        recent_avg = monthly.tail(3).mean()
        
        last_date = monthly.index[-1].to_timestamp()
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=self.forecast_periods,
            freq='M'
        )
        
        forecasts = pd.DataFrame({
            'date': [d.strftime('%Y-%m') for d in forecast_dates],
            'forecast': [recent_avg] * self.forecast_periods
        })
        
        return forecasts


def generate_forecasts(df: pd.DataFrame, config: Optional[Dict] = None) -> ForecastResult:
    """
    Convenience function to generate forecasts.
    
    Args:
        df: Normalized FAGL DataFrame
        config: Configuration dictionary
    
    Returns:
        ForecastResult object
    """
    forecaster = Forecaster(df, config)
    return forecaster.forecast_all()

