"""Bulgarian FAGL03 loader for movements 2024.xlsx data."""

import pandas as pd
import numpy as np
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = structlog.get_logger(__name__)


class BulgarianFAGLLoader:
    """Load and process Bulgarian FAGL03 data from movements 2024.xlsx."""
    
    def __init__(self, movements_file: Path, config=None):
        """
        Initialize Bulgarian FAGL03 loader.
        
        Args:
            movements_file: Path to movements 2024.xlsx file
            config: Configuration object (optional)
        """
        self.movements_file = movements_file
        self.config = config
        self.fagl_df: Optional[pd.DataFrame] = None
        
        # Column mappings based on your description
        self.column_mappings = {
            'posting_date': 'Posting Date',      # Column B
            'document_no': 'Document Number',    # Column E  
            'reference_no': 'Reference Number',  # Column G
            'gl_account': 'G/L Account',         # Column J
            'account_name': 'Account Name',      # Column K
            'debit_amount': 'Debit',             # Column N
            'credit_amount': 'Credit',           # Column O
            'line_item_text': 'Line Item Text',  # Column S
            'currency': 'Currency',              # Column P
            'company_code': 'Company Code',      # Column A
            'fiscal_year': 'Fiscal Year',        # Column L
            'posting_period': 'Posting Period'   # Column M
        }
    
    def _validate_file_exists(self):
        """Validate that movements file exists."""
        if not self.movements_file.exists():
            raise FileNotFoundError(f"Movements file not found: {self.movements_file}")
        
        if self.movements_file.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"Movements file must be Excel format (.xlsx or .xls): {self.movements_file}")
    
    def load(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Load Bulgarian movements file and convert to standard FAGL03 format.
        
        Args:
            sample_size: Optional number of rows to load for testing
            
        Returns:
            Standardized FAGL03 DataFrame
        """
        logger.info("Loading Bulgarian movements file", 
                   file=str(self.movements_file),
                   sample_size=sample_size)
        
        self._validate_file_exists()
        
        # Load Excel file
        try:
            if sample_size:
                logger.info(f"Loading sample of {sample_size:,} rows for testing")
                self.fagl_df = pd.read_excel(self.movements_file, nrows=sample_size)
            else:
                logger.info("Loading full movements file (610,333 rows) - this may take a moment...")
                self.fagl_df = pd.read_excel(self.movements_file)
                
        except Exception as e:
            raise ValueError(f"Could not read movements file: {e}")
        
        logger.info("Movements file loaded", rows=len(self.fagl_df))
        
        # Process and standardize the data
        self._validate_structure()
        self._clean_bulgarian_data()
        self._convert_to_standard_format()
        self._validate_bulgarian_types()
        
        logger.info("Bulgarian FAGL03 processing completed", 
                   final_rows=len(self.fagl_df))
        
        return self.fagl_df
    
    def _validate_structure(self):
        """Validate movements file structure."""
        required_columns = [
            'Posting Date', 'Document Number', 'G/L Account', 
            'Account Name', 'Debit', 'Credit'
        ]
        
        missing_columns = [col for col in required_columns if col not in self.fagl_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in movements file: {missing_columns}")
        
        logger.info("Movements file structure validated", 
                   columns=len(self.fagl_df.columns),
                   rows=len(self.fagl_df))
    
    def _clean_bulgarian_data(self):
        """Clean and standardize Bulgarian movements data."""
        logger.info("Cleaning Bulgarian movements data")
        
        # Convert account IDs to string for consistency
        self.fagl_df['G/L Account'] = self.fagl_df['G/L Account'].astype(str)
        
        # Clean text fields
        text_columns = ['Account Name', 'Reference Number', 'Line Item Text']
        for col in text_columns:
            if col in self.fagl_df.columns:
                self.fagl_df[col] = self.fagl_df[col].astype(str).str.strip()
                self.fagl_df[col] = self.fagl_df[col].replace('nan', '')
        
        # Handle date column
        self.fagl_df['Posting Date'] = pd.to_datetime(self.fagl_df['Posting Date'], errors='coerce')
        
        # Clean numeric columns (Debit, Credit)
        for col in ['Debit', 'Credit']:
            if col in self.fagl_df.columns:
                # Convert to numeric, handling any text values
                self.fagl_df[col] = pd.to_numeric(self.fagl_df[col], errors='coerce')
                self.fagl_df[col] = self.fagl_df[col].fillna(0)
        
        # Remove rows with invalid dates or missing GL accounts
        initial_rows = len(self.fagl_df)
        self.fagl_df = self.fagl_df.dropna(subset=['Posting Date', 'G/L Account'])
        self.fagl_df = self.fagl_df[self.fagl_df['G/L Account'].str.len() >= 4]
        
        removed_rows = initial_rows - len(self.fagl_df)
        if removed_rows > 0:
            logger.warning(f"Removed {removed_rows} rows with invalid data")
        
        logger.info("Bulgarian data cleaning completed", 
                   clean_rows=len(self.fagl_df))
    
    def _convert_to_standard_format(self):
        """Convert Bulgarian movements data to standard FAGL03 format."""
        logger.info("Converting to standard FAGL03 format")
        
        # Create standard FAGL03 format
        standard_df = pd.DataFrame()
        
        # Map columns to standard format
        standard_df['posting_date'] = self.fagl_df['Posting Date']
        standard_df['document_no'] = self.fagl_df['Document Number'].astype(str)
        standard_df['reference_no'] = self.fagl_df['Reference Number'].fillna('')
        standard_df['gl_account'] = self.fagl_df['G/L Account']
        standard_df['account_name'] = self.fagl_df['Account Name']
        standard_df['line_item_text'] = self.fagl_df['Line Item Text'].fillna('')
        
        # Handle currency
        if 'Currency' in self.fagl_df.columns:
            standard_df['currency'] = self.fagl_df['Currency'].fillna('BGN')
        else:
            standard_df['currency'] = 'BGN'  # Default to Bulgarian Lev
        
        # Handle company code
        if 'Company Code' in self.fagl_df.columns:
            standard_df['company_code'] = self.fagl_df['Company Code'].fillna('BG10')
        else:
            standard_df['company_code'] = 'BG10'  # Default Bulgarian company code
        
        # CRITICAL: Convert debit/credit to single amount column
        # Assets and Expenses: Use debit amounts (positive)
        # Revenue, Liabilities, Equity: Use credit amounts (negative)
        
        def calculate_amount(row):
            """Calculate net amount based on Bulgarian accounting logic."""
            debit = float(row['Debit']) if pd.notna(row['Debit']) else 0.0
            credit = float(row['Credit']) if pd.notna(row['Credit']) else 0.0
            
            # For assets and expenses, use debit amounts (positive)
            # For revenue, liabilities, equity, use credit amounts (negative)
            # This creates a standard where positive = assets/expenses, negative = revenue/liabilities/equity
            
            if debit > 0:
                return debit  # Assets and expenses
            elif credit > 0:
                return -credit  # Revenue, liabilities, equity (negative)
            else:
                return 0.0
        
        standard_df['amount'] = self.fagl_df.apply(calculate_amount, axis=1)
        
        # Add additional fields for compatibility
        standard_df['customer_vendor'] = ''  # Not available in movements file
        standard_df['due_date'] = None  # Not available in movements file
        standard_df['open_amount'] = standard_df['amount']  # Assume all amounts are open
        
        # Create posting_text from line_item_text
        standard_df['posting_text'] = standard_df['line_item_text']
        
        self.fagl_df = standard_df
        
        logger.info("Standard FAGL03 format created", 
                   final_rows=len(self.fagl_df),
                   amount_range=f"{self.fagl_df['amount'].min():,.2f} to {self.fagl_df['amount'].max():,.2f}")
    
    def _validate_bulgarian_types(self):
        """Validate Bulgarian data types and consistency."""
        logger.info("Validating Bulgarian data types")
        
        # Check for valid account IDs
        invalid_accounts = self.fagl_df[
            self.fagl_df['gl_account'].str.len() < 4
        ]
        if len(invalid_accounts) > 0:
            logger.warning("Found accounts with short IDs", count=len(invalid_accounts))
        
        # Check date range
        date_range = self.fagl_df['posting_date'].max() - self.fagl_df['posting_date'].min()
        logger.info("Date range validated", 
                   start_date=self.fagl_df['posting_date'].min(),
                   end_date=self.fagl_df['posting_date'].max(),
                   total_days=date_range.days)
        
        # Check amount distribution
        positive_amounts = len(self.fagl_df[self.fagl_df['amount'] > 0])
        negative_amounts = len(self.fagl_df[self.fagl_df['amount'] < 0])
        zero_amounts = len(self.fagl_df[self.fagl_df['amount'] == 0])
        
        logger.info("Amount distribution", 
                   positive=positive_amounts,
                   negative=negative_amounts,
                   zero=zero_amounts)
    
    def get_summary(self) -> Dict:
        """Get summary of Bulgarian FAGL03 data."""
        if self.fagl_df is None:
            raise ValueError("FAGL03 data not loaded. Call load() first.")
        
        return {
            'total_transactions': len(self.fagl_df),
            'date_range': {
                'start': self.fagl_df['posting_date'].min(),
                'end': self.fagl_df['posting_date'].max()
            },
            'unique_accounts': len(self.fagl_df['gl_account'].unique()),
            'total_amount': self.fagl_df['amount'].sum(),
            'positive_amounts': len(self.fagl_df[self.fagl_df['amount'] > 0]),
            'negative_amounts': len(self.fagl_df[self.fagl_df['amount'] < 0]),
            'currency': self.fagl_df['currency'].iloc[0] if len(self.fagl_df) > 0 else 'BGN',
            'company_code': self.fagl_df['company_code'].iloc[0] if len(self.fagl_df) > 0 else 'BG10'
        }


def load_bulgarian_fagl(movements_file: Path, config=None, sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Convenience function to load Bulgarian FAGL03 data.
    
    Args:
        movements_file: Path to movements 2024.xlsx file
        config: Configuration object (optional)
        sample_size: Optional number of rows to load for testing
        
    Returns:
        Standardized FAGL03 DataFrame
    """
    loader = BulgarianFAGLLoader(movements_file, config)
    return loader.load(sample_size=sample_size)
