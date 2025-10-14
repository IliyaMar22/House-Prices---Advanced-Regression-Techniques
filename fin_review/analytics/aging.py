"""Aging analysis module for AR and AP."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger()


@dataclass
class AgingResult:
    """Container for aging analysis results."""
    ar_aging: pd.DataFrame
    ap_aging: pd.DataFrame
    ar_summary: Dict
    ap_summary: Dict
    overdue_items: pd.DataFrame
    top_overdue_customers: pd.DataFrame
    top_overdue_vendors: pd.DataFrame
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'ar_aging': self.ar_aging.to_dict('records'),
            'ap_aging': self.ap_aging.to_dict('records'),
            'ar_summary': self.ar_summary,
            'ap_summary': self.ap_summary,
            'overdue_items_count': len(self.overdue_items),
            'top_overdue_customers': self.top_overdue_customers.to_dict('records'),
            'top_overdue_vendors': self.top_overdue_vendors.to_dict('records'),
        }


class AgingAnalyzer:
    """Analyzes aging for receivables and payables."""
    
    def __init__(self, df: pd.DataFrame, config: Optional[Dict] = None):
        """
        Initialize aging analyzer.
        
        Args:
            df: Normalized FAGL DataFrame
            config: Configuration dictionary
        """
        self.df = df
        self.config = config or {}
        
        # Get aging buckets from config
        self.aging_buckets = self.config.get('aging_buckets', [
            [0, 0, "Current"],
            [1, 30, "0-30 days"],
            [31, 60, "31-60 days"],
            [61, 90, "61-90 days"],
            [91, 999999, ">90 days"],
        ])
        
        # Use latest posting date as "current date" for aging
        self.current_date = self.df['posting_date'].max()
    
    def analyze_all(self) -> AgingResult:
        """
        Run all aging analyses.
        
        Returns:
            AgingResult object
        """
        logger.info("Starting aging analysis", current_date=self.current_date.strftime('%Y-%m-%d'))
        
        # Analyze AR
        ar_aging, ar_summary = self._analyze_ar()
        
        # Analyze AP
        ap_aging, ap_summary = self._analyze_ap()
        
        # Get overdue items
        overdue_items = self._get_overdue_items()
        
        # Get top overdue parties
        top_overdue_customers = self._get_top_overdue('Receivable')
        top_overdue_vendors = self._get_top_overdue('Payable')
        
        logger.info(
            "Aging analysis complete",
            ar_buckets=len(ar_aging),
            ap_buckets=len(ap_aging),
            overdue_items=len(overdue_items)
        )
        
        return AgingResult(
            ar_aging=ar_aging,
            ap_aging=ap_aging,
            ar_summary=ar_summary,
            ap_summary=ap_summary,
            overdue_items=overdue_items,
            top_overdue_customers=top_overdue_customers,
            top_overdue_vendors=top_overdue_vendors
        )
    
    def _analyze_ar(self) -> Tuple[pd.DataFrame, Dict]:
        """Analyze accounts receivable aging."""
        # Filter receivables with open amounts
        ar = self.df[self.df['is_receivable'] == True].copy()
        
        if len(ar) == 0:
            logger.warning("No receivables data found")
            return pd.DataFrame(), {'total_outstanding': 0, 'item_count': 0}
        
        # Filter only open items
        if 'open_amount' in ar.columns:
            ar = ar[ar['open_amount'].notna() & (ar['open_amount'] != 0)]
        
        # Calculate aging
        ar = self._assign_aging_buckets(ar)
        
        # Aggregate by aging bucket
        aging_summary = ar.groupby('aging_bucket').agg({
            'open_amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        aging_summary.columns = ['aging_bucket', 'outstanding_amount', 'item_count']
        
        # Calculate percentages
        total_outstanding = aging_summary['outstanding_amount'].sum()
        if total_outstanding != 0:
            aging_summary['pct_of_total'] = (
                aging_summary['outstanding_amount'] / total_outstanding
            ) * 100
        else:
            aging_summary['pct_of_total'] = 0
        
        # Sort by bucket order
        bucket_order = [b[2] for b in self.aging_buckets]
        aging_summary['bucket_order'] = aging_summary['aging_bucket'].map(
            {name: i for i, name in enumerate(bucket_order)}
        )
        aging_summary = aging_summary.sort_values('bucket_order').drop('bucket_order', axis=1)
        
        # Create summary dict
        summary = {
            'total_outstanding': float(total_outstanding),
            'item_count': int(aging_summary['item_count'].sum()),
            'overdue_amount': float(
                aging_summary[~aging_summary['aging_bucket'].str.contains('Current', na=False)]
                ['outstanding_amount'].sum()
            ),
            'overdue_pct': 0.0
        }
        
        if total_outstanding != 0:
            summary['overdue_pct'] = (summary['overdue_amount'] / total_outstanding) * 100
        
        logger.info(
            "AR aging analyzed",
            total=total_outstanding,
            overdue_pct=summary['overdue_pct']
        )
        
        return aging_summary, summary
    
    def _analyze_ap(self) -> Tuple[pd.DataFrame, Dict]:
        """Analyze accounts payable aging."""
        # Filter payables with open amounts
        ap = self.df[self.df['is_payable'] == True].copy()
        
        if len(ap) == 0:
            logger.warning("No payables data found")
            return pd.DataFrame(), {'total_outstanding': 0, 'item_count': 0}
        
        # Filter only open items
        if 'open_amount' in ap.columns:
            ap = ap[ap['open_amount'].notna() & (ap['open_amount'] != 0)]
        
        # Calculate aging
        ap = self._assign_aging_buckets(ap)
        
        # Aggregate by aging bucket
        aging_summary = ap.groupby('aging_bucket').agg({
            'open_amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        aging_summary.columns = ['aging_bucket', 'outstanding_amount', 'item_count']
        
        # Calculate percentages
        total_outstanding = aging_summary['outstanding_amount'].sum()
        if total_outstanding != 0:
            aging_summary['pct_of_total'] = (
                aging_summary['outstanding_amount'] / total_outstanding
            ) * 100
        else:
            aging_summary['pct_of_total'] = 0
        
        # Sort by bucket order
        bucket_order = [b[2] for b in self.aging_buckets]
        aging_summary['bucket_order'] = aging_summary['aging_bucket'].map(
            {name: i for i, name in enumerate(bucket_order)}
        )
        aging_summary = aging_summary.sort_values('bucket_order').drop('bucket_order', axis=1)
        
        # Create summary dict
        summary = {
            'total_outstanding': float(total_outstanding),
            'item_count': int(aging_summary['item_count'].sum()),
            'overdue_amount': float(
                aging_summary[~aging_summary['aging_bucket'].str.contains('Current', na=False)]
                ['outstanding_amount'].sum()
            ),
            'overdue_pct': 0.0
        }
        
        if total_outstanding != 0:
            summary['overdue_pct'] = (summary['overdue_amount'] / total_outstanding) * 100
        
        logger.info(
            "AP aging analyzed",
            total=total_outstanding,
            overdue_pct=summary['overdue_pct']
        )
        
        return aging_summary, summary
    
    def _assign_aging_buckets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign aging buckets based on days overdue."""
        df = df.copy()
        
        # Calculate days overdue
        if 'days_overdue' not in df.columns:
            if 'due_date' in df.columns and df['due_date'].notna().any():
                df['days_overdue'] = (self.current_date - df['due_date']).dt.days
            else:
                # If no due date, use posting date + 30 days as default
                logger.warning("No due_date available, using posting_date + 30 days")
                default_due = df['posting_date'] + pd.Timedelta(days=30)
                df['days_overdue'] = (self.current_date - default_due).dt.days
        
        # Assign to buckets
        df['aging_bucket'] = 'Unknown'
        
        for min_days, max_days, bucket_name in self.aging_buckets:
            mask = (df['days_overdue'] >= min_days) & (df['days_overdue'] <= max_days)
            df.loc[mask, 'aging_bucket'] = bucket_name
        
        return df
    
    def _get_overdue_items(self) -> pd.DataFrame:
        """Get all overdue items."""
        overdue = self.df[self.df['is_overdue'] == True].copy()
        
        if len(overdue) == 0:
            return pd.DataFrame()
        
        # Select relevant columns
        cols = ['posting_date', 'doc_id', 'gl_account', 'bucket', 'type',
                'customer_vendor', 'due_date', 'days_overdue', 'open_amount']
        
        available_cols = [c for c in cols if c in overdue.columns]
        result = overdue[available_cols].copy()
        
        # Sort by days overdue descending
        if 'days_overdue' in result.columns:
            result = result.sort_values('days_overdue', ascending=False)
        
        return result
    
    def _get_top_overdue(self, item_type: str, n: int = 10) -> pd.DataFrame:
        """
        Get top N overdue customers or vendors.
        
        Args:
            item_type: 'Receivable' or 'Payable'
            n: Number of top items
        
        Returns:
            DataFrame with top overdue parties
        """
        # Filter by type and overdue
        data = self.df[
            (self.df['type'] == item_type) &
            (self.df['is_overdue'] == True)
        ].copy()
        
        if len(data) == 0 or 'customer_vendor' not in data.columns:
            return pd.DataFrame()
        
        # Group by customer/vendor
        top = data.groupby('customer_vendor').agg({
            'open_amount': 'sum',
            'doc_id': 'count',
            'days_overdue': 'max'
        }).reset_index()
        
        top.columns = ['party', 'overdue_amount', 'item_count', 'max_days_overdue']
        
        # Sort by overdue amount
        top = top.sort_values('overdue_amount', key=abs, ascending=False).head(n)
        
        # Calculate percentage of total overdue
        total_overdue = data['open_amount'].sum()
        if total_overdue != 0:
            top['pct_of_total_overdue'] = (top['overdue_amount'] / total_overdue) * 100
        else:
            top['pct_of_total_overdue'] = 0
        
        return top
    
    def calculate_aging_deterioration(self) -> Optional[Dict]:
        """
        Calculate how aging has deteriorated over time.
        
        Returns:
            Dictionary with deterioration metrics
        """
        # Compare current month to 3 months ago
        three_months_ago = self.current_date - pd.Timedelta(days=90)
        
        # Current AR aging
        current_ar = self.df[
            (self.df['is_receivable'] == True) &
            (self.df['posting_date'] >= three_months_ago)
        ].copy()
        
        if len(current_ar) == 0:
            return None
        
        # Historical AR aging (3-6 months ago)
        six_months_ago = self.current_date - pd.Timedelta(days=180)
        historical_ar = self.df[
            (self.df['is_receivable'] == True) &
            (self.df['posting_date'] >= six_months_ago) &
            (self.df['posting_date'] < three_months_ago)
        ].copy()
        
        if len(historical_ar) == 0:
            return None
        
        # Calculate overdue percentages
        current_overdue_pct = (current_ar['is_overdue'].sum() / len(current_ar)) * 100
        hist_overdue_pct = (historical_ar['is_overdue'].sum() / len(historical_ar)) * 100
        
        deterioration = current_overdue_pct - hist_overdue_pct
        
        return {
            'current_overdue_pct': float(current_overdue_pct),
            'historical_overdue_pct': float(hist_overdue_pct),
            'deterioration_pct': float(deterioration),
            'is_deteriorating': deterioration > 5  # More than 5% increase
        }


def calculate_aging(df: pd.DataFrame, config: Optional[Dict] = None) -> AgingResult:
    """
    Convenience function to calculate aging.
    
    Args:
        df: Normalized FAGL DataFrame
        config: Configuration dictionary
    
    Returns:
        AgingResult object
    """
    analyzer = AgingAnalyzer(df, config)
    return analyzer.analyze_all()

