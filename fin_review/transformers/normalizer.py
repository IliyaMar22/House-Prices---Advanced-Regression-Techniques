"""Data normalization module for FAGL data."""

import pandas as pd
import structlog
from typing import Dict, Optional

logger = structlog.get_logger()


class DataNormalizer:
    """Normalizes and enriches FAGL data with mapping information."""
    
    def __init__(
        self,
        fagl_df: pd.DataFrame,
        mapping_df: pd.DataFrame,
        config: Optional[Dict] = None
    ):
        """
        Initialize normalizer.
        
        Args:
            fagl_df: FAGL03 DataFrame
            mapping_df: Mapping DataFrame
            config: Configuration dictionary
        """
        self.fagl_df = fagl_df.copy()
        self.mapping_df = mapping_df
        self.config = config or {}
        self.normalized_df: Optional[pd.DataFrame] = None
    
    def normalize(self) -> pd.DataFrame:
        """
        Normalize FAGL data.
        
        Returns:
            Normalized DataFrame with mapping information
        """
        logger.info("Starting data normalization")
        
        self._normalize_amounts()
        self._add_temporal_features()
        self._merge_mapping()
        self._enrich_ar_ap_flags()
        self._calculate_overdue()
        
        self.normalized_df = self.fagl_df
        
        logger.info(
            "Normalization complete",
            rows=len(self.normalized_df),
            columns=len(self.normalized_df.columns)
        )
        
        return self.normalized_df
    
    def _normalize_amounts(self):
        """Normalize amount sign convention."""
        convention = self.config.get('amount_sign_convention', 'positive_debit')
        
        if convention == 'positive_credit':
            # Flip the sign
            logger.info("Converting amounts from positive_credit to positive_debit convention")
            self.fagl_df['amount'] = -self.fagl_df['amount']
            if 'open_amount' in self.fagl_df.columns:
                self.fagl_df['open_amount'] = -self.fagl_df['open_amount']
        
        # Ensure numeric types
        self.fagl_df['amount'] = pd.to_numeric(self.fagl_df['amount'], errors='coerce')
        if 'open_amount' in self.fagl_df.columns:
            self.fagl_df['open_amount'] = pd.to_numeric(
                self.fagl_df['open_amount'],
                errors='coerce'
            )
    
    def _add_temporal_features(self):
        """Add year, quarter, month columns."""
        self.fagl_df['year'] = self.fagl_df['posting_date'].dt.year
        self.fagl_df['quarter'] = self.fagl_df['posting_date'].dt.quarter
        self.fagl_df['month'] = self.fagl_df['posting_date'].dt.month
        self.fagl_df['year_month'] = self.fagl_df['posting_date'].dt.to_period('M')
        self.fagl_df['year_quarter'] = self.fagl_df['posting_date'].dt.to_period('Q')
        
        # Add day of week and week of year for seasonality analysis
        self.fagl_df['day_of_week'] = self.fagl_df['posting_date'].dt.dayofweek
        self.fagl_df['week_of_year'] = self.fagl_df['posting_date'].dt.isocalendar().week
        
        logger.debug("Added temporal features")
    
    def _merge_mapping(self):
        """Merge mapping information into FAGL data."""
        # Create mapping lookup
        mapping_dict = {}
        for _, row in self.mapping_df.iterrows():
            mapping_dict[row['gl_account']] = {
                'bucket': row['bucket'],
                'type': row['type'],
                'entity_mapped': row.get('entity'),
                'notes': row.get('notes')
            }
        
        # Map to FAGL data
        self.fagl_df['bucket'] = self.fagl_df['gl_account'].map(
            lambda x: mapping_dict.get(x, {}).get('bucket', 'Unmapped')
        )
        self.fagl_df['type'] = self.fagl_df['gl_account'].map(
            lambda x: mapping_dict.get(x, {}).get('type', 'Other')
        )
        self.fagl_df['entity_mapped'] = self.fagl_df['gl_account'].map(
            lambda x: mapping_dict.get(x, {}).get('entity_mapped')
        )
        
        # Mark unmapped rows
        self.fagl_df['is_mapped'] = self.fagl_df['bucket'] != 'Unmapped'
        
        unmapped_count = (~self.fagl_df['is_mapped']).sum()
        if unmapped_count > 0:
            logger.warning(
                "Unmapped rows after merge",
                count=unmapped_count,
                pct=(unmapped_count / len(self.fagl_df)) * 100
            )
        
        logger.info("Merged mapping data", mapped_rows=self.fagl_df['is_mapped'].sum())
    
    def _enrich_ar_ap_flags(self):
        """Add AR/AP flags based on type."""
        self.fagl_df['is_receivable'] = self.fagl_df['type'] == 'Receivable'
        self.fagl_df['is_payable'] = self.fagl_df['type'] == 'Payable'
        self.fagl_df['is_revenue'] = self.fagl_df['type'] == 'Revenue'
        self.fagl_df['is_opex'] = self.fagl_df['type'] == 'OPEX'
        self.fagl_df['is_payroll'] = self.fagl_df['type'] == 'Payroll'
        
        logger.debug(
            "Added type flags",
            receivables=self.fagl_df['is_receivable'].sum(),
            payables=self.fagl_df['is_payable'].sum(),
            revenue=self.fagl_df['is_revenue'].sum(),
            opex=self.fagl_df['is_opex'].sum()
        )
    
    def _calculate_overdue(self):
        """Calculate overdue days and flag overdue items."""
        if 'due_date' not in self.fagl_df.columns:
            logger.info("due_date column not available, skipping overdue calculation")
            self.fagl_df['days_overdue'] = 0
            self.fagl_df['is_overdue'] = False
            return
        
        # Use the latest date in data as "current date" for overdue calculation
        current_date = self.fagl_df['posting_date'].max()
        
        # Calculate days overdue (negative means not due yet)
        self.fagl_df['days_overdue'] = (
            (current_date - self.fagl_df['due_date']).dt.days
        )
        
        # Flag overdue based on threshold
        overdue_threshold = self.config.get('overdue_threshold_days', 0)
        self.fagl_df['is_overdue'] = self.fagl_df['days_overdue'] > overdue_threshold
        
        # Only consider open items as potentially overdue
        if 'open_amount' in self.fagl_df.columns:
            self.fagl_df['is_overdue'] = (
                self.fagl_df['is_overdue'] & 
                (self.fagl_df['open_amount'].notna()) &
                (self.fagl_df['open_amount'] != 0)
            )
        
        overdue_count = self.fagl_df['is_overdue'].sum()
        if overdue_count > 0:
            logger.info(
                "Overdue items identified",
                count=overdue_count,
                threshold_days=overdue_threshold
            )
    
    def get_unmapped_summary(self) -> pd.DataFrame:
        """
        Get summary of unmapped GL accounts.
        
        Returns:
            DataFrame with unmapped GL summary
        """
        if self.normalized_df is None:
            raise ValueError("Data not normalized. Call normalize() first.")
        
        unmapped = self.normalized_df[~self.normalized_df['is_mapped']]
        
        if len(unmapped) == 0:
            return pd.DataFrame(columns=['gl_account', 'transaction_count', 'total_amount'])
        
        summary = unmapped.groupby('gl_account').agg({
            'doc_id': 'count',
            'amount': 'sum'
        }).reset_index()
        
        summary.columns = ['gl_account', 'transaction_count', 'total_amount']
        summary = summary.sort_values('total_amount', key=abs, ascending=False)
        
        return summary


def normalize_data(
    fagl_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Convenience function to normalize data.
    
    Args:
        fagl_df: FAGL03 DataFrame
        mapping_df: Mapping DataFrame
        config: Configuration dictionary
    
    Returns:
        Normalized DataFrame
    """
    normalizer = DataNormalizer(fagl_df, mapping_df, config)
    return normalizer.normalize()

