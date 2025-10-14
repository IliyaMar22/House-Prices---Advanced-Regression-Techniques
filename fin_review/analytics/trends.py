"""Trend analysis module for time series patterns."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List
from dataclasses import dataclass
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose

logger = structlog.get_logger()


@dataclass
class TrendResult:
    """Container for trend analysis results."""
    rolling_averages: pd.DataFrame
    seasonality: Optional[Dict]
    trend_direction: Dict
    correlation_matrix: Optional[pd.DataFrame]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'rolling_averages': self.rolling_averages.to_dict('records'),
            'trend_direction': self.trend_direction,
        }
        if self.seasonality:
            result['seasonality'] = self.seasonality
        if self.correlation_matrix is not None:
            result['correlation_matrix'] = self.correlation_matrix.to_dict()
        return result


class TrendAnalyzer:
    """Analyzes time series trends and patterns."""
    
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        """
        Initialize trend analyzer.
        
        Args:
            df: Normalized FAGL DataFrame
            config: Configuration dictionary
        """
        self.df = df
        self.config = config or {}
    
    def analyze_all(self) -> TrendResult:
        """
        Run all trend analyses.
        
        Returns:
            TrendResult object
        """
        logger.info("Starting trend analysis")
        
        rolling_avgs = self._calculate_rolling_averages()
        trend_direction = self._determine_trend_direction()
        
        seasonality = None
        if self.config.get('enable_seasonality', True):
            seasonality = self._detect_seasonality()
        
        correlation_matrix = self._calculate_correlations()
        
        logger.info("Trend analysis complete")
        
        return TrendResult(
            rolling_averages=rolling_avgs,
            seasonality=seasonality,
            trend_direction=trend_direction,
            correlation_matrix=correlation_matrix
        )
    
    def _calculate_rolling_averages(self) -> pd.DataFrame:
        """Calculate rolling averages for key metrics."""
        # Group by month and type
        monthly = self.df.groupby(['year_month', 'type']).agg({
            'amount': 'sum'
        }).reset_index()
        
        monthly['year_month'] = monthly['year_month'].dt.to_timestamp()
        
        # Pivot to have types as columns
        monthly_pivot = monthly.pivot(
            index='year_month',
            columns='type',
            values='amount'
        ).fillna(0)
        
        # Calculate rolling averages
        windows = self.config.get('rolling_windows', [3, 6, 12])
        
        result_dfs = [monthly_pivot.reset_index()]
        
        for window in windows:
            if len(monthly_pivot) >= window:
                rolling = monthly_pivot.rolling(window=window, min_periods=1).mean()
                rolling = rolling.add_suffix(f'_ma{window}')
                result_dfs.append(rolling.reset_index(drop=True))
        
        # Combine all
        result = pd.concat(result_dfs, axis=1)
        
        # Remove duplicate year_month columns
        result = result.loc[:, ~result.columns.duplicated()]
        
        return result
    
    def _determine_trend_direction(self) -> Dict:
        """Determine trend direction (up/down/flat) for key metrics."""
        directions = {}
        
        # Group by month
        monthly = self.df.groupby(['year_month', 'type'])['amount'].sum().reset_index()
        
        for metric_type in monthly['type'].unique():
            type_data = monthly[monthly['type'] == metric_type].copy()
            type_data = type_data.sort_values('year_month')
            
            if len(type_data) < 3:
                directions[metric_type] = 'insufficient_data'
                continue
            
            # Use linear regression to determine trend
            x = np.arange(len(type_data))
            y = type_data['amount'].values
            
            if len(x) > 0 and not np.all(y == 0):
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # Determine direction based on slope and significance
                if p_value < 0.05:  # Significant trend
                    if slope > 0:
                        direction = 'increasing'
                    else:
                        direction = 'decreasing'
                else:
                    direction = 'flat'
                
                directions[metric_type] = {
                    'direction': direction,
                    'slope': float(slope),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'confidence': 'high' if p_value < 0.01 else 'medium'
                }
            else:
                directions[metric_type] = 'no_variation'
        
        return directions
    
    def _detect_seasonality(self) -> Optional[Dict]:
        """Detect seasonality patterns."""
        # Group by month for revenue
        revenue_data = self.df[self.df['type'] == 'Revenue'].copy()
        
        if len(revenue_data) == 0:
            logger.warning("No revenue data for seasonality analysis")
            return None
        
        monthly = revenue_data.groupby('year_month')['amount'].sum()
        
        if len(monthly) < 24:  # Need at least 2 years for good seasonality detection
            logger.warning("Insufficient data for seasonality detection (need >= 24 months)")
            return {'detected': False, 'reason': 'insufficient_data'}
        
        try:
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(
                monthly.values,
                model='additive',
                period=12,
                extrapolate_trend='freq'
            )
            
            # Calculate strength of seasonality
            seasonal_strength = np.var(decomposition.seasonal) / np.var(monthly.values)
            
            # Detect if seasonality is significant
            is_seasonal = seasonal_strength > 0.1  # More than 10% of variance
            
            # Find peak months
            seasonal_pattern = pd.Series(decomposition.seasonal[:12])
            peak_months = seasonal_pattern.nlargest(3).index.tolist()
            trough_months = seasonal_pattern.nsmallest(3).index.tolist()
            
            result = {
                'detected': bool(is_seasonal),
                'strength': float(seasonal_strength),
                'peak_months': [int(m + 1) for m in peak_months],  # 1-indexed
                'trough_months': [int(m + 1) for m in trough_months],
                'confidence': 'high' if seasonal_strength > 0.2 else 'medium'
            }
            
            logger.info(
                "Seasonality analysis complete",
                detected=is_seasonal,
                strength=seasonal_strength
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in seasonality detection: {e}")
            return {'detected': False, 'reason': 'error', 'error': str(e)}
    
    def _calculate_correlations(self) -> Optional[pd.DataFrame]:
        """Calculate correlations between different types."""
        # Get monthly totals by type
        monthly = self.df.groupby(['year_month', 'type'])['amount'].sum().reset_index()
        
        if len(monthly) < 12:
            logger.warning("Insufficient data for correlation analysis")
            return None
        
        # Pivot to wide format
        pivot = monthly.pivot(index='year_month', columns='type', values='amount')
        
        if len(pivot.columns) < 2:
            logger.warning("Need at least 2 types for correlation analysis")
            return None
        
        # Calculate correlation matrix
        corr = pivot.corr()
        
        logger.info("Correlation matrix calculated", shape=corr.shape)
        
        return corr
    
    def identify_change_points(self, metric: str = 'revenue') -> List[Dict]:
        """
        Identify significant change points in a metric.
        
        Args:
            metric: Metric to analyze (revenue, opex, etc.)
        
        Returns:
            List of change points with dates and magnitudes
        """
        # Map metric name to type
        type_mapping = {
            'revenue': 'Revenue',
            'opex': 'OPEX',
            'payroll': 'Payroll',
            'interest': 'Interest'
        }
        
        metric_type = type_mapping.get(metric.lower())
        if not metric_type:
            logger.error(f"Unknown metric: {metric}")
            return []
        
        # Get monthly data
        monthly = self.df[self.df['type'] == metric_type].groupby('year_month')['amount'].sum()
        
        if len(monthly) < 6:
            logger.warning(f"Insufficient data for change point detection in {metric}")
            return []
        
        # Calculate month-over-month percentage changes
        pct_changes = monthly.pct_change()
        
        # Identify significant changes (> 2 standard deviations)
        threshold = 2 * pct_changes.std()
        
        change_points = []
        for date, change in pct_changes.items():
            if abs(change) > threshold and not pd.isna(change):
                change_points.append({
                    'date': date.strftime('%Y-%m'),
                    'change_pct': float(change * 100),
                    'previous_value': float(monthly.loc[monthly.index < date].iloc[-1]),
                    'new_value': float(monthly.loc[date]),
                    'significance': 'high' if abs(change) > 3 * threshold else 'medium'
                })
        
        logger.info(f"Identified {len(change_points)} change points for {metric}")
        
        return sorted(change_points, key=lambda x: abs(x['change_pct']), reverse=True)
    
    def calculate_volatility(self) -> Dict[str, float]:
        """Calculate volatility (coefficient of variation) for each type."""
        volatility = {}
        
        for metric_type in self.df['type'].unique():
            type_data = self.df[self.df['type'] == metric_type]
            monthly = type_data.groupby('year_month')['amount'].sum()
            
            if len(monthly) > 0:
                mean = monthly.mean()
                std = monthly.std()
                
                if mean != 0:
                    cv = (std / abs(mean)) * 100  # Coefficient of variation as percentage
                    volatility[metric_type] = float(cv)
        
        return volatility


def analyze_trends(df: pd.DataFrame, config: Optional[Dict] = None) -> TrendResult:
    """
    Convenience function to analyze trends.
    
    Args:
        df: Normalized FAGL DataFrame
        config: Configuration dictionary
    
    Returns:
        TrendResult object
    """
    analyzer = TrendAnalyzer(df, config)
    return analyzer.analyze_all()

