"""KPI calculation module for financial metrics."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class KPIResult:
    """Container for KPI calculation results."""
    monthly_kpis: pd.DataFrame
    summary_kpis: Dict
    growth_metrics: Dict
    ratios: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'monthly_kpis': self.monthly_kpis.to_dict('records'),
            'summary_kpis': self.summary_kpis,
            'growth_metrics': self.growth_metrics,
            'ratios': self.ratios,
        }


class KPICalculator:
    """Calculates financial KPIs and metrics."""
    
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        """
        Initialize KPI calculator.
        
        Args:
            df: Normalized FAGL DataFrame with mapping information
            config: Configuration dictionary
        """
        self.df = df
        self.config = config or {}
    
    def calculate_all(self) -> KPIResult:
        """
        Calculate all KPIs.
        
        Returns:
            KPIResult object with all metrics
        """
        logger.info("Calculating KPIs")
        
        monthly_kpis = self._calculate_monthly_kpis()
        summary_kpis = self._calculate_summary_kpis()
        
        growth_metrics = {}
        ratios = {}
        
        if self.config.get('enable_growth_metrics', True):
            growth_metrics = self._calculate_growth_metrics(monthly_kpis)
        
        if self.config.get('enable_ratios', True):
            ratios = self._calculate_ratios(monthly_kpis)
        
        logger.info("KPI calculation complete")
        
        return KPIResult(
            monthly_kpis=monthly_kpis,
            summary_kpis=summary_kpis,
            growth_metrics=growth_metrics,
            ratios=ratios
        )
    
    def _calculate_monthly_kpis(self) -> pd.DataFrame:
        """Calculate monthly KPIs by type and bucket."""
        # Group by year_month and type
        monthly = self.df.groupby(['year_month', 'type']).agg({
            'amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        monthly.columns = ['year_month', 'type', 'amount', 'transaction_count']
        
        # Pivot to have types as columns
        monthly_pivot = monthly.pivot(
            index='year_month',
            columns='type',
            values='amount'
        ).fillna(0)
        
        # Convert period to datetime for easier handling
        monthly_pivot.index = monthly_pivot.index.to_timestamp()
        
        # Calculate derived metrics
        if 'Revenue' in monthly_pivot.columns:
            monthly_pivot['revenue'] = monthly_pivot['Revenue']
        else:
            monthly_pivot['revenue'] = 0
        
        if 'OPEX' in monthly_pivot.columns:
            monthly_pivot['opex'] = monthly_pivot['OPEX']
        else:
            monthly_pivot['opex'] = 0
        
        if 'Payroll' in monthly_pivot.columns:
            monthly_pivot['payroll'] = monthly_pivot['Payroll']
        else:
            monthly_pivot['payroll'] = 0
        
        # Calculate margins
        monthly_pivot['gross_profit'] = monthly_pivot['revenue'] - monthly_pivot['opex']
        monthly_pivot['gross_margin_pct'] = np.where(
            monthly_pivot['revenue'] != 0,
            (monthly_pivot['gross_profit'] / monthly_pivot['revenue']) * 100,
            0
        )
        
        # Calculate expense ratios
        monthly_pivot['opex_ratio'] = np.where(
            monthly_pivot['revenue'] != 0,
            (monthly_pivot['opex'] / monthly_pivot['revenue']) * 100,
            0
        )
        
        monthly_pivot['payroll_ratio'] = np.where(
            monthly_pivot['revenue'] != 0,
            (monthly_pivot['payroll'] / monthly_pivot['revenue']) * 100,
            0
        )
        
        monthly_pivot['payroll_of_opex'] = np.where(
            monthly_pivot['opex'] != 0,
            (monthly_pivot['payroll'] / monthly_pivot['opex']) * 100,
            0
        )
        
        return monthly_pivot.reset_index()
    
    def _calculate_summary_kpis(self) -> Dict:
        """Calculate summary KPIs across entire period."""
        summary = {}
        
        # Total by type
        by_type = self.df.groupby('type')['amount'].sum().to_dict()
        summary['total_by_type'] = by_type
        
        # Total revenue
        summary['total_revenue'] = by_type.get('Revenue', 0)
        
        # Total expenses
        summary['total_opex'] = by_type.get('OPEX', 0)
        summary['total_payroll'] = by_type.get('Payroll', 0)
        summary['total_expenses'] = summary['total_opex'] + summary['total_payroll']
        
        # Net profit
        summary['net_profit'] = summary['total_revenue'] - summary['total_expenses']
        
        # Margins
        if summary['total_revenue'] != 0:
            summary['net_margin_pct'] = (
                summary['net_profit'] / summary['total_revenue']
            ) * 100
        else:
            summary['net_margin_pct'] = 0
        
        # Top buckets by amount
        top_buckets = self.df.groupby('bucket')['amount'].sum().abs().nlargest(10)
        summary['top_10_buckets'] = top_buckets.to_dict()
        
        # Transaction counts
        summary['total_transactions'] = len(self.df)
        summary['transactions_by_type'] = self.df.groupby('type').size().to_dict()
        
        # Average transaction size
        summary['avg_transaction_size'] = self.df['amount'].mean()
        
        # Date range
        summary['start_date'] = self.df['posting_date'].min().strftime('%Y-%m-%d')
        summary['end_date'] = self.df['posting_date'].max().strftime('%Y-%m-%d')
        
        return summary
    
    def _calculate_growth_metrics(self, monthly_kpis: pd.DataFrame) -> Dict:
        """Calculate YoY, MoM growth rates and CAGR."""
        growth = {}
        
        if len(monthly_kpis) < 2:
            logger.warning("Insufficient data for growth calculations")
            return growth
        
        # Sort by date
        monthly = monthly_kpis.sort_values('year_month')
        
        # Calculate MoM growth for revenue
        if 'revenue' in monthly.columns:
            monthly['revenue_mom_growth'] = monthly['revenue'].pct_change() * 100
            growth['latest_revenue_mom'] = monthly['revenue_mom_growth'].iloc[-1]
            growth['avg_revenue_mom'] = monthly['revenue_mom_growth'].mean()
        
        # Calculate YoY growth
        if len(monthly) >= 13:  # Need at least 13 months for YoY
            monthly['revenue_yoy_growth'] = monthly['revenue'].pct_change(periods=12) * 100
            growth['latest_revenue_yoy'] = monthly['revenue_yoy_growth'].iloc[-1]
            growth['avg_revenue_yoy'] = monthly['revenue_yoy_growth'].mean()
        
        # Calculate CAGR for revenue (if > 1 year of data)
        if len(monthly) >= 12:
            first_value = monthly['revenue'].iloc[0]
            last_value = monthly['revenue'].iloc[-1]
            periods = len(monthly) / 12  # years
            
            if first_value > 0 and last_value > 0:
                cagr = (((last_value / first_value) ** (1 / periods)) - 1) * 100
                growth['revenue_cagr'] = cagr
        
        # OPEX growth
        if 'opex' in monthly.columns:
            monthly['opex_mom_growth'] = monthly['opex'].pct_change() * 100
            growth['latest_opex_mom'] = monthly['opex_mom_growth'].iloc[-1]
            growth['avg_opex_mom'] = monthly['opex_mom_growth'].mean()
        
        return growth
    
    def _calculate_ratios(self, monthly_kpis: pd.DataFrame) -> Dict:
        """Calculate financial ratios."""
        ratios = {}
        
        if len(monthly_kpis) == 0:
            return ratios
        
        # Latest month ratios
        latest = monthly_kpis.iloc[-1]
        
        if 'gross_margin_pct' in latest:
            ratios['latest_gross_margin'] = float(latest['gross_margin_pct'])
        
        if 'opex_ratio' in latest:
            ratios['latest_opex_ratio'] = float(latest['opex_ratio'])
        
        if 'payroll_ratio' in latest:
            ratios['latest_payroll_ratio'] = float(latest['payroll_ratio'])
        
        # Average ratios
        ratios['avg_gross_margin'] = monthly_kpis['gross_margin_pct'].mean()
        ratios['avg_opex_ratio'] = monthly_kpis['opex_ratio'].mean()
        
        # Run rates (monthly average * 12)
        ratios['revenue_run_rate'] = monthly_kpis['revenue'].tail(3).mean() * 12
        ratios['opex_run_rate'] = monthly_kpis['opex'].tail(3).mean() * 12
        
        return ratios
    
    def calculate_dso(self) -> Optional[float]:
        """
        Calculate Days Sales Outstanding (DSO).
        
        Returns:
            DSO value or None if insufficient data
        """
        if not self.config.get('calculate_dso', True):
            return None
        
        # Filter receivables
        ar = self.df[self.df['is_receivable'] == True].copy()
        
        if len(ar) == 0:
            logger.warning("No receivables data for DSO calculation")
            return None
        
        # Get average daily revenue (from last 90 days)
        recent_date = ar['posting_date'].max()
        start_date = recent_date - pd.Timedelta(days=90)
        
        recent_revenue = self.df[
            (self.df['is_revenue'] == True) &
            (self.df['posting_date'] >= start_date)
        ]['amount'].sum()
        
        if recent_revenue <= 0:
            return None
        
        avg_daily_revenue = recent_revenue / 90
        
        # Calculate total outstanding receivables
        if 'open_amount' in ar.columns:
            outstanding = ar['open_amount'].sum()
        else:
            outstanding = ar['amount'].sum()
        
        if avg_daily_revenue > 0:
            dso = outstanding / avg_daily_revenue
            logger.info(f"DSO calculated: {dso:.1f} days")
            return dso
        
        return None
    
    def calculate_dpo(self) -> Optional[float]:
        """
        Calculate Days Payables Outstanding (DPO).
        
        Returns:
            DPO value or None if insufficient data
        """
        if not self.config.get('calculate_dpo', True):
            return None
        
        # Filter payables
        ap = self.df[self.df['is_payable'] == True].copy()
        
        if len(ap) == 0:
            logger.warning("No payables data for DPO calculation")
            return None
        
        # Get average daily OPEX (from last 90 days)
        recent_date = ap['posting_date'].max()
        start_date = recent_date - pd.Timedelta(days=90)
        
        recent_opex = self.df[
            (self.df['is_opex'] == True) &
            (self.df['posting_date'] >= start_date)
        ]['amount'].sum()
        
        if recent_opex <= 0:
            return None
        
        avg_daily_opex = recent_opex / 90
        
        # Calculate total outstanding payables
        if 'open_amount' in ap.columns:
            outstanding = ap['open_amount'].sum()
        else:
            outstanding = ap['amount'].sum()
        
        if avg_daily_opex > 0:
            dpo = outstanding / avg_daily_opex
            logger.info(f"DPO calculated: {dpo:.1f} days")
            return dpo
        
        return None
    
    def get_top_items(
        self,
        type_filter: Optional[str] = None,
        group_by: str = 'bucket',
        n: int = 10
    ) -> pd.DataFrame:
        """
        Get top N items by amount.
        
        Args:
            type_filter: Filter by type (e.g., 'OPEX', 'Revenue')
            group_by: Column to group by ('bucket', 'customer_vendor', 'gl_account')
            n: Number of top items to return
        
        Returns:
            DataFrame with top items
        """
        df = self.df.copy()
        
        if type_filter:
            df = df[df['type'] == type_filter]
        
        if group_by not in df.columns:
            logger.error(f"Column {group_by} not found in data")
            return pd.DataFrame()
        
        top = df.groupby(group_by).agg({
            'amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        top.columns = [group_by, 'total_amount', 'transaction_count']
        top = top.sort_values('total_amount', key=abs, ascending=False).head(n)
        
        # Calculate percentage of total
        total = df['amount'].sum()
        if total != 0:
            top['pct_of_total'] = (top['total_amount'] / total) * 100
        else:
            top['pct_of_total'] = 0
        
        return top


def calculate_kpis(df: pd.DataFrame, config: Optional[Dict] = None) -> KPIResult:
    """
    Convenience function to calculate KPIs.
    
    Args:
        df: Normalized FAGL DataFrame
        config: Configuration dictionary
    
    Returns:
        KPIResult object
    """
    calculator = KPICalculator(df, config)
    return calculator.calculate_all()

