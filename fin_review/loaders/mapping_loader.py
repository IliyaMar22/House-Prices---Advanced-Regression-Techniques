"""Mapping file loader for GL account to bucket mappings."""

import pandas as pd
import structlog
from pathlib import Path
from typing import Dict, List, Optional

logger = structlog.get_logger()


class MappingLoader:
    """Loads and validates mapping Excel file."""
    
    REQUIRED_COLUMNS = ['gl_account', 'bucket', 'type']
    OPTIONAL_COLUMNS = ['entity', 'notes']
    VALID_TYPES = ['Revenue', 'OPEX', 'Payroll', 'Interest', 'Receivable', 'Payable', 'Other']
    
    def __init__(self, mapping_file: str):
        """
        Initialize mapping loader.
        
        Args:
            mapping_file: Path to mapping Excel file
        """
        self.mapping_file = Path(mapping_file)
        self.mapping_df: Optional[pd.DataFrame] = None
        self._validate_file_exists()
    
    def _validate_file_exists(self):
        """Validate that mapping file exists."""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found: {self.mapping_file}")
        
        if self.mapping_file.suffix not in ['.xlsx', '.xls', '.csv']:
            raise ValueError(f"Mapping file must be Excel or CSV format (.xlsx, .xls, or .csv): {self.mapping_file}")
    
    def load(self) -> pd.DataFrame:
        """
        Load mapping file and validate structure.
        
        Returns:
            DataFrame with mapping data
        """
        logger.info("Loading mapping file", file=str(self.mapping_file))
        
        # Handle CSV files
        if self.mapping_file.suffix == '.csv':
            self.mapping_df = pd.read_csv(self.mapping_file)
        else:
            # Handle Excel files
            try:
                # Try to read 'mapping' sheet first
                self.mapping_df = pd.read_excel(self.mapping_file, sheet_name='mapping')
            except ValueError:
                # If 'mapping' sheet doesn't exist, try first sheet
                logger.warning("Sheet 'mapping' not found, using first sheet")
                self.mapping_df = pd.read_excel(self.mapping_file, sheet_name=0)
        
        self._validate_structure()
        self._clean_data()
        self._validate_types()
        
        logger.info(
            "Mapping loaded successfully",
            rows=len(self.mapping_df),
            unique_accounts=self.mapping_df['gl_account'].nunique(),
            unique_buckets=self.mapping_df['bucket'].nunique()
        )
        
        return self.mapping_df
    
    def _validate_structure(self):
        """Validate that required columns exist."""
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in self.mapping_df.columns]
        
        if missing_cols:
            raise ValueError(
                f"Missing required columns in mapping file: {missing_cols}. "
                f"Required columns: {self.REQUIRED_COLUMNS}"
            )
        
        logger.debug("Mapping structure validated", columns=list(self.mapping_df.columns))
    
    def _clean_data(self):
        """Clean and normalize mapping data."""
        # Convert gl_account to string and strip whitespace
        self.mapping_df['gl_account'] = self.mapping_df['gl_account'].astype(str).str.strip()
        
        # Strip whitespace from string columns
        for col in ['bucket', 'type']:
            self.mapping_df[col] = self.mapping_df[col].astype(str).str.strip()
        
        # Handle optional columns
        for col in self.OPTIONAL_COLUMNS:
            if col not in self.mapping_df.columns:
                self.mapping_df[col] = None
            elif col == 'entity':
                self.mapping_df[col] = self.mapping_df[col].astype(str).str.strip()
        
        # Remove duplicates
        duplicates = self.mapping_df.duplicated(subset=['gl_account'], keep='first')
        if duplicates.any():
            dup_accounts = self.mapping_df[duplicates]['gl_account'].tolist()
            logger.warning(
                "Duplicate GL accounts found, keeping first occurrence",
                duplicates=dup_accounts
            )
            self.mapping_df = self.mapping_df[~duplicates]
        
        # Remove rows with missing required data
        before_count = len(self.mapping_df)
        self.mapping_df = self.mapping_df.dropna(subset=self.REQUIRED_COLUMNS)
        after_count = len(self.mapping_df)
        
        if before_count > after_count:
            logger.warning(
                "Removed rows with missing required data",
                removed=before_count - after_count
            )
    
    def _validate_types(self):
        """Validate that type column contains valid values."""
        invalid_types = self.mapping_df[~self.mapping_df['type'].isin(self.VALID_TYPES)]
        
        if not invalid_types.empty:
            invalid_values = invalid_types['type'].unique().tolist()
            logger.warning(
                "Invalid types found in mapping",
                invalid_types=invalid_values,
                valid_types=self.VALID_TYPES,
                affected_rows=len(invalid_types)
            )
            # Set invalid types to 'Other'
            self.mapping_df.loc[~self.mapping_df['type'].isin(self.VALID_TYPES), 'type'] = 'Other'
    
    def get_mapping_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Get mapping as dictionary for fast lookups.
        
        Returns:
            Dictionary mapping gl_account to {bucket, type, entity}
        """
        if self.mapping_df is None:
            raise ValueError("Mapping not loaded. Call load() first.")
        
        mapping_dict = {}
        for _, row in self.mapping_df.iterrows():
            mapping_dict[row['gl_account']] = {
                'bucket': row['bucket'],
                'type': row['type'],
                'entity': row.get('entity'),
                'notes': row.get('notes')
            }
        
        return mapping_dict
    
    def get_buckets_by_type(self, type_filter: str) -> List[str]:
        """
        Get list of buckets for a specific type.
        
        Args:
            type_filter: Type to filter by (e.g., 'Revenue', 'OPEX')
        
        Returns:
            List of bucket names
        """
        if self.mapping_df is None:
            raise ValueError("Mapping not loaded. Call load() first.")
        
        filtered = self.mapping_df[self.mapping_df['type'] == type_filter]
        return sorted(filtered['bucket'].unique().tolist())
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of mapping.
        
        Returns:
            Dictionary with summary statistics
        """
        if self.mapping_df is None:
            raise ValueError("Mapping not loaded. Call load() first.")
        
        summary = {
            'total_accounts': len(self.mapping_df),
            'unique_buckets': self.mapping_df['bucket'].nunique(),
            'accounts_by_type': self.mapping_df['type'].value_counts().to_dict(),
            'buckets_by_type': self.mapping_df.groupby('type')['bucket'].nunique().to_dict(),
        }
        
        if 'entity' in self.mapping_df.columns and self.mapping_df['entity'].notna().any():
            summary['entities'] = self.mapping_df['entity'].unique().tolist()
        
        return summary


def load_mapping(mapping_file: str) -> pd.DataFrame:
    """
    Convenience function to load mapping file.
    
    Args:
        mapping_file: Path to mapping Excel file
    
    Returns:
        DataFrame with mapping data
    """
    loader = MappingLoader(mapping_file)
    return loader.load()

