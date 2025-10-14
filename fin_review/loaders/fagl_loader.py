"""FAGL03 data loader for GL posting exports."""

import pandas as pd
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

logger = structlog.get_logger()


class FAGLLoader:
    """Loads and validates FAGL03 export files."""
    
    # Default column names
    DEFAULT_COLUMNS = {
        'posting_date': 'posting_date',
        'doc_id': 'doc_id',
        'gl_account': 'gl_account',
        'amount': 'amount',
        'currency': 'currency',
        'posting_text': 'posting_text',
        'customer_vendor': 'customer_vendor',
        'due_date': 'due_date',
        'open_amount': 'open_amount',
        'company_code': 'company_code',
    }
    
    REQUIRED_COLUMNS = ['posting_date', 'doc_id', 'gl_account', 'amount']
    
    def __init__(
        self,
        fagl_dir: Optional[str] = None,
        fagl_file: Optional[str] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """
        Initialize FAGL loader.
        
        Args:
            fagl_dir: Directory containing FAGL03 files
            fagl_file: Single FAGL03 file
            column_mapping: Custom column name mapping
        """
        if not fagl_dir and not fagl_file:
            raise ValueError("Either fagl_dir or fagl_file must be provided")
        
        self.fagl_dir = Path(fagl_dir) if fagl_dir else None
        self.fagl_file = Path(fagl_file) if fagl_file else None
        self.column_mapping = column_mapping or self.DEFAULT_COLUMNS
        self.fagl_df: Optional[pd.DataFrame] = None
        
        self._validate_paths()
    
    def _validate_paths(self):
        """Validate that specified paths exist."""
        if self.fagl_file and not self.fagl_file.exists():
            raise FileNotFoundError(f"FAGL file not found: {self.fagl_file}")
        
        if self.fagl_dir and not self.fagl_dir.exists():
            raise FileNotFoundError(f"FAGL directory not found: {self.fagl_dir}")
    
    def load(self) -> pd.DataFrame:
        """
        Load FAGL03 data from file(s).
        
        Returns:
            DataFrame with FAGL03 data
        """
        logger.info("Loading FAGL03 data")
        
        if self.fagl_file:
            self.fagl_df = self._load_single_file(self.fagl_file)
        else:
            self.fagl_df = self._load_directory(self.fagl_dir)
        
        self._map_columns()
        self._validate_structure()
        self._parse_dates()
        self._clean_data()
        
        logger.info(
            "FAGL03 data loaded successfully",
            rows=len(self.fagl_df),
            unique_accounts=self.fagl_df['gl_account'].nunique(),
            date_range=f"{self.fagl_df['posting_date'].min()} to {self.fagl_df['posting_date'].max()}",
            total_amount=self.fagl_df['amount'].sum()
        )
        
        return self.fagl_df
    
    def _load_single_file(self, file_path: Path) -> pd.DataFrame:
        """Load single FAGL03 file."""
        logger.debug("Loading single FAGL file", file=str(file_path))
        
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        return df
    
    def _load_directory(self, dir_path: Path) -> pd.DataFrame:
        """Load all FAGL03 files from directory."""
        logger.debug("Loading FAGL files from directory", dir=str(dir_path))
        
        # Find all CSV and Excel files
        csv_files = list(dir_path.glob("*.csv"))
        excel_files = list(dir_path.glob("*.xlsx")) + list(dir_path.glob("*.xls"))
        all_files = csv_files + excel_files
        
        if not all_files:
            raise FileNotFoundError(f"No FAGL03 files found in {dir_path}")
        
        logger.info(f"Found {len(all_files)} FAGL03 files")
        
        # Load and concatenate all files
        dfs = []
        for file_path in all_files:
            try:
                df = self._load_single_file(file_path)
                df['source_file'] = file_path.name
                dfs.append(df)
                logger.debug(f"Loaded {len(df)} rows from {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")
                continue
        
        if not dfs:
            raise ValueError("No files could be loaded successfully")
        
        return pd.concat(dfs, ignore_index=True)
    
    def _map_columns(self):
        """Map custom column names to standard names."""
        # Create reverse mapping
        reverse_mapping = {v: k for k, v in self.column_mapping.items()}
        
        # Rename columns that exist
        rename_dict = {}
        for source_col, target_col in reverse_mapping.items():
            if source_col in self.fagl_df.columns and source_col != target_col:
                rename_dict[source_col] = target_col
        
        if rename_dict:
            logger.debug("Mapping column names", mapping=rename_dict)
            self.fagl_df = self.fagl_df.rename(columns=rename_dict)
    
    def _validate_structure(self):
        """Validate that required columns exist."""
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in self.fagl_df.columns]
        
        if missing_cols:
            raise ValueError(
                f"Missing required columns in FAGL03 data: {missing_cols}. "
                f"Required columns: {self.REQUIRED_COLUMNS}. "
                f"Available columns: {list(self.fagl_df.columns)}"
            )
        
        logger.debug("FAGL03 structure validated", columns=list(self.fagl_df.columns))
    
    def _parse_dates(self):
        """Parse date columns."""
        date_columns = ['posting_date', 'due_date']
        
        for col in date_columns:
            if col in self.fagl_df.columns:
                try:
                    self.fagl_df[col] = pd.to_datetime(self.fagl_df[col], errors='coerce')
                    
                    # Log any rows with invalid dates
                    invalid_dates = self.fagl_df[col].isna().sum()
                    if invalid_dates > 0:
                        logger.warning(
                            f"Found {invalid_dates} rows with invalid {col}",
                            column=col,
                            invalid_count=invalid_dates
                        )
                except Exception as e:
                    logger.error(f"Error parsing {col}: {e}")
    
    def _clean_data(self):
        """Clean and normalize FAGL03 data."""
        # Convert gl_account to string and strip whitespace
        self.fagl_df['gl_account'] = self.fagl_df['gl_account'].astype(str).str.strip()
        
        # Convert doc_id to string
        self.fagl_df['doc_id'] = self.fagl_df['doc_id'].astype(str)
        
        # Ensure amount is numeric
        if not pd.api.types.is_numeric_dtype(self.fagl_df['amount']):
            self.fagl_df['amount'] = pd.to_numeric(self.fagl_df['amount'], errors='coerce')
        
        # Handle open_amount
        if 'open_amount' in self.fagl_df.columns:
            if not pd.api.types.is_numeric_dtype(self.fagl_df['open_amount']):
                self.fagl_df['open_amount'] = pd.to_numeric(
                    self.fagl_df['open_amount'],
                    errors='coerce'
                )
        else:
            # If open_amount not provided, assume all amounts are open
            self.fagl_df['open_amount'] = self.fagl_df['amount']
            logger.info("open_amount column not found, using amount as open_amount")
        
        # Handle currency
        if 'currency' in self.fagl_df.columns:
            self.fagl_df['currency'] = self.fagl_df['currency'].astype(str).str.strip().str.upper()
        else:
            self.fagl_df['currency'] = 'EUR'  # Default currency
            logger.info("currency column not found, defaulting to EUR")
        
        # Handle customer_vendor
        if 'customer_vendor' in self.fagl_df.columns:
            self.fagl_df['customer_vendor'] = self.fagl_df['customer_vendor'].astype(str).str.strip()
        
        # Handle company_code
        if 'company_code' in self.fagl_df.columns:
            self.fagl_df['company_code'] = self.fagl_df['company_code'].astype(str).str.strip()
        
        # Remove rows with missing required data
        before_count = len(self.fagl_df)
        self.fagl_df = self.fagl_df.dropna(subset=['posting_date', 'amount'])
        after_count = len(self.fagl_df)
        
        if before_count > after_count:
            logger.warning(
                "Removed rows with missing required data",
                removed=before_count - after_count
            )
        
        # Sort by posting_date
        self.fagl_df = self.fagl_df.sort_values('posting_date').reset_index(drop=True)
    
    def filter_by_date_range(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Filter data by date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        
        Returns:
            Filtered DataFrame
        """
        if self.fagl_df is None:
            raise ValueError("FAGL data not loaded. Call load() first.")
        
        df = self.fagl_df.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['posting_date'] >= start_date]
            logger.info(f"Filtered to dates >= {start_date}", rows=len(df))
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['posting_date'] <= end_date]
            logger.info(f"Filtered to dates <= {end_date}", rows=len(df))
        
        return df
    
    def filter_by_entity(self, entity: str) -> pd.DataFrame:
        """
        Filter data by entity/company code.
        
        Args:
            entity: Entity code to filter by
        
        Returns:
            Filtered DataFrame
        """
        if self.fagl_df is None:
            raise ValueError("FAGL data not loaded. Call load() first.")
        
        if 'company_code' not in self.fagl_df.columns:
            logger.warning("company_code column not found, cannot filter by entity")
            return self.fagl_df.copy()
        
        df = self.fagl_df[self.fagl_df['company_code'] == entity].copy()
        logger.info(f"Filtered to entity {entity}", rows=len(df))
        
        return df
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of FAGL data.
        
        Returns:
            Dictionary with summary statistics
        """
        if self.fagl_df is None:
            raise ValueError("FAGL data not loaded. Call load() first.")
        
        summary = {
            'total_rows': len(self.fagl_df),
            'unique_documents': self.fagl_df['doc_id'].nunique(),
            'unique_gl_accounts': self.fagl_df['gl_account'].nunique(),
            'date_range': {
                'min': self.fagl_df['posting_date'].min().strftime('%Y-%m-%d'),
                'max': self.fagl_df['posting_date'].max().strftime('%Y-%m-%d'),
            },
            'amount_stats': {
                'total': float(self.fagl_df['amount'].sum()),
                'mean': float(self.fagl_df['amount'].mean()),
                'min': float(self.fagl_df['amount'].min()),
                'max': float(self.fagl_df['amount'].max()),
            },
            'currencies': self.fagl_df['currency'].value_counts().to_dict(),
        }
        
        if 'company_code' in self.fagl_df.columns:
            summary['entities'] = self.fagl_df['company_code'].unique().tolist()
        
        if 'customer_vendor' in self.fagl_df.columns:
            summary['unique_partners'] = self.fagl_df['customer_vendor'].nunique()
        
        return summary


def load_fagl_data(
    fagl_dir: Optional[str] = None,
    fagl_file: Optional[str] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    entity: Optional[str] = None
) -> pd.DataFrame:
    """
    Convenience function to load and filter FAGL03 data.
    
    Args:
        fagl_dir: Directory containing FAGL03 files
        fagl_file: Single FAGL03 file
        column_mapping: Custom column name mapping
        start_date: Start date filter
        end_date: End date filter
        entity: Entity filter
    
    Returns:
        DataFrame with FAGL03 data
    """
    loader = FAGLLoader(fagl_dir=fagl_dir, fagl_file=fagl_file, column_mapping=column_mapping)
    df = loader.load()
    
    if start_date or end_date:
        df = loader.filter_by_date_range(start_date, end_date)
    
    if entity:
        df = loader.filter_by_entity(entity)
    
    return df

