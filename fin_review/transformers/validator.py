"""Data validation module for FAGL and mapping data."""

import pandas as pd
import structlog
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    quality_score: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    unmapped_gls: List[str] = field(default_factory=list)
    missing_dates_count: int = 0
    missing_amounts_count: int = 0
    currency_issues: Dict[str, int] = field(default_factory=dict)
    date_gaps: List[Tuple[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_valid': self.is_valid,
            'quality_score': self.quality_score,
            'warnings': self.warnings,
            'errors': self.errors,
            'unmapped_gls_count': len(self.unmapped_gls),
            'missing_dates_count': self.missing_dates_count,
            'missing_amounts_count': self.missing_amounts_count,
            'currency_issues': self.currency_issues,
            'date_gaps_count': len(self.date_gaps),
        }


class DataValidator:
    """Validates FAGL and mapping data quality."""
    
    def __init__(
        self,
        fagl_df: pd.DataFrame,
        mapping_df: pd.DataFrame,
        config: Optional[Dict] = None
    ):
        """
        Initialize validator.
        
        Args:
            fagl_df: FAGL03 DataFrame
            mapping_df: Mapping DataFrame
            config: Configuration dictionary
        """
        self.fagl_df = fagl_df
        self.mapping_df = mapping_df
        self.config = config or {}
        self.result = ValidationResult(is_valid=True, quality_score=1.0)
    
    def validate(self) -> ValidationResult:
        """
        Run all validation checks.
        
        Returns:
            ValidationResult object
        """
        logger.info("Starting data validation")
        
        # Run validation checks
        self._check_unmapped_gls()
        self._check_missing_data()
        self._check_date_continuity()
        self._check_currency_consistency()
        self._check_amount_reasonableness()
        self._check_duplicates()
        
        # Calculate overall quality score
        self._calculate_quality_score()
        
        # Determine if data is valid
        self.result.is_valid = (
            len(self.result.errors) == 0 and
            self.result.quality_score >= self.config.get('min_data_quality_score', 0.7)
        )
        
        logger.info(
            "Validation complete",
            is_valid=self.result.is_valid,
            quality_score=self.result.quality_score,
            warnings=len(self.result.warnings),
            errors=len(self.result.errors)
        )
        
        return self.result
    
    def _check_unmapped_gls(self):
        """Check for GL accounts in FAGL that are not in mapping."""
        if not self.config.get('warn_unmapped_gls', True):
            return
        
        fagl_accounts = set(self.fagl_df['gl_account'].unique())
        mapped_accounts = set(self.mapping_df['gl_account'].unique())
        
        unmapped = fagl_accounts - mapped_accounts
        
        if unmapped:
            self.result.unmapped_gls = sorted(unmapped)
            
            # Calculate impact
            unmapped_rows = self.fagl_df[self.fagl_df['gl_account'].isin(unmapped)]
            unmapped_amount = unmapped_rows['amount'].sum()
            total_amount = self.fagl_df['amount'].sum()
            unmapped_pct = (len(unmapped_rows) / len(self.fagl_df)) * 100
            amount_pct = (abs(unmapped_amount) / abs(total_amount)) * 100 if total_amount != 0 else 0
            
            self.result.warnings.append(
                f"Found {len(unmapped)} unmapped GL accounts "
                f"({unmapped_pct:.1f}% of rows, {amount_pct:.1f}% of amount)"
            )
            
            logger.warning(
                "Unmapped GL accounts detected",
                count=len(unmapped),
                accounts=list(unmapped)[:10],  # Log first 10
                unmapped_rows=len(unmapped_rows),
                unmapped_amount=unmapped_amount
            )
    
    def _check_missing_data(self):
        """Check for missing critical data."""
        # Check posting dates
        missing_dates = self.fagl_df['posting_date'].isna().sum()
        if missing_dates > 0:
            self.result.missing_dates_count = missing_dates
            pct = (missing_dates / len(self.fagl_df)) * 100
            self.result.warnings.append(
                f"Missing posting_date in {missing_dates} rows ({pct:.1f}%)"
            )
        
        # Check amounts
        missing_amounts = self.fagl_df['amount'].isna().sum()
        if missing_amounts > 0:
            self.result.missing_amounts_count = missing_amounts
            pct = (missing_amounts / len(self.fagl_df)) * 100
            self.result.errors.append(
                f"Missing amount in {missing_amounts} rows ({pct:.1f}%)"
            )
        
        # Check open_amount for AR/AP analysis
        if 'open_amount' in self.fagl_df.columns:
            missing_open = self.fagl_df['open_amount'].isna().sum()
            if missing_open > 0:
                pct = (missing_open / len(self.fagl_df)) * 100
                self.result.warnings.append(
                    f"Missing open_amount in {missing_open} rows ({pct:.1f}%) - "
                    "AR/AP aging may be affected"
                )
        
        # Check due_date for aging analysis
        if 'due_date' in self.fagl_df.columns:
            missing_due = self.fagl_df['due_date'].isna().sum()
            if missing_due > 0:
                pct = (missing_due / len(self.fagl_df)) * 100
                self.result.warnings.append(
                    f"Missing due_date in {missing_due} rows ({pct:.1f}%) - "
                    "aging analysis may be incomplete"
                )
    
    def _check_date_continuity(self):
        """Check for gaps in posting dates."""
        if not self.config.get('check_date_continuity', True):
            return
        
        # Get date range
        dates = pd.to_datetime(self.fagl_df['posting_date'].dropna())
        if len(dates) == 0:
            return
        
        min_date = dates.min()
        max_date = dates.max()
        
        # Check for month gaps
        monthly_data = self.fagl_df.groupby(
            pd.Grouper(key='posting_date', freq='M')
        ).size()
        
        # Find months with no data
        all_months = pd.date_range(start=min_date, end=max_date, freq='M')
        missing_months = []
        
        for month in all_months:
            if month not in monthly_data.index or monthly_data[month] == 0:
                missing_months.append(month.strftime('%Y-%m'))
        
        if missing_months:
            self.result.date_gaps = [(m, m) for m in missing_months]
            self.result.warnings.append(
                f"Found {len(missing_months)} months with no data: {missing_months[:5]}"
            )
            logger.warning("Date gaps detected", missing_months=missing_months)
    
    def _check_currency_consistency(self):
        """Check currency consistency."""
        if not self.config.get('check_currency_consistency', True):
            return
        
        if 'currency' not in self.fagl_df.columns:
            return
        
        currency_counts = self.fagl_df['currency'].value_counts()
        
        if len(currency_counts) > 1:
            self.result.currency_issues = currency_counts.to_dict()
            
            default_currency = self.config.get('default_currency', 'EUR')
            non_default = currency_counts.drop(default_currency, errors='ignore').sum()
            pct = (non_default / len(self.fagl_df)) * 100
            
            self.result.warnings.append(
                f"Multiple currencies detected: {dict(currency_counts)} - "
                f"{pct:.1f}% of data is not in {default_currency}"
            )
            logger.info("Currency distribution", currencies=dict(currency_counts))
    
    def _check_amount_reasonableness(self):
        """Check for unreasonable amounts."""
        amounts = self.fagl_df['amount'].dropna()
        
        if len(amounts) == 0:
            return
        
        # Check for zero amounts
        zero_count = (amounts == 0).sum()
        if zero_count > 0:
            pct = (zero_count / len(amounts)) * 100
            if pct > 5:  # More than 5% zero amounts
                self.result.warnings.append(
                    f"High number of zero amounts: {zero_count} ({pct:.1f}%)"
                )
        
        # Check for extreme outliers (beyond 5 std devs)
        mean = amounts.mean()
        std = amounts.std()
        
        if std > 0:
            outliers = amounts[abs(amounts - mean) > 5 * std]
            if len(outliers) > 0:
                self.result.warnings.append(
                    f"Found {len(outliers)} extreme outliers (>5 std deviations)"
                )
                logger.info(
                    "Extreme outliers detected",
                    count=len(outliers),
                    max=outliers.max(),
                    min=outliers.min()
                )
    
    def _check_duplicates(self):
        """Check for potential duplicate entries."""
        # Check for exact duplicates
        duplicates = self.fagl_df.duplicated(
            subset=['posting_date', 'doc_id', 'gl_account', 'amount'],
            keep=False
        )
        
        dup_count = duplicates.sum()
        if dup_count > 0:
            pct = (dup_count / len(self.fagl_df)) * 100
            self.result.warnings.append(
                f"Found {dup_count} potential duplicate entries ({pct:.1f}%)"
            )
    
    def _calculate_quality_score(self):
        """Calculate overall data quality score (0-1)."""
        score = 1.0
        
        # Deduct for unmapped GLs
        if self.result.unmapped_gls:
            unmapped_pct = len(self.result.unmapped_gls) / max(
                self.fagl_df['gl_account'].nunique(), 1
            )
            score -= min(unmapped_pct * 0.3, 0.3)  # Max 30% deduction
        
        # Deduct for missing data
        if self.result.missing_dates_count > 0:
            missing_pct = self.result.missing_dates_count / len(self.fagl_df)
            score -= min(missing_pct * 0.5, 0.3)  # Max 30% deduction
        
        if self.result.missing_amounts_count > 0:
            missing_pct = self.result.missing_amounts_count / len(self.fagl_df)
            score -= min(missing_pct * 0.5, 0.4)  # Max 40% deduction
        
        # Deduct for date gaps
        if self.result.date_gaps:
            score -= min(len(self.result.date_gaps) * 0.02, 0.1)  # Max 10% deduction
        
        self.result.quality_score = max(score, 0.0)


def validate_data(
    fagl_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    config: Optional[Dict] = None
) -> ValidationResult:
    """
    Convenience function to validate data.
    
    Args:
        fagl_df: FAGL03 DataFrame
        mapping_df: Mapping DataFrame
        config: Configuration dictionary
    
    Returns:
        ValidationResult object
    """
    validator = DataValidator(fagl_df, mapping_df, config)
    return validator.validate()

