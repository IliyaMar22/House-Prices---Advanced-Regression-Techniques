"""Bulgarian mapping loader for financial review pipeline."""

import pandas as pd
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..config import Config

logger = structlog.get_logger(__name__)


class BulgarianMappingLoader:
    """Load and process Bulgarian financial mapping data."""
    
    def __init__(self, mapping_file: Path, config: Config):
        """
        Initialize Bulgarian mapping loader.
        
        Args:
            mapping_file: Path to Bulgarian mapping Excel file
            config: Configuration object
        """
        self.mapping_file = mapping_file
        self.config = config
        self.mapping_df: Optional[pd.DataFrame] = None
        
    def _validate_file_exists(self):
        """Validate that Bulgarian mapping file exists."""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Bulgarian mapping file not found: {self.mapping_file}")
        
        if self.mapping_file.suffix not in ['.xlsx', '.xls', '.csv']:
            raise ValueError(f"Mapping file must be Excel or CSV format (.xlsx, .xls, or .csv): {self.mapping_file}")
    
    def load(self) -> pd.DataFrame:
        """
        Load Bulgarian mapping file and validate structure.
        
        Returns:
            Processed mapping DataFrame with Bulgarian classifications
        """
        logger.info("Loading Bulgarian mapping file", file=str(self.mapping_file))
        
        self._validate_file_exists()
        
        # Load Excel file
        try:
            self.mapping_df = pd.read_excel(self.mapping_file)
        except Exception as e:
            raise ValueError(f"Could not read Bulgarian mapping file: {e}")
        
        self._validate_structure()
        self._clean_bulgarian_data()
        self._validate_bulgarian_types()
        self._create_bulgarian_classifications()
        
        logger.info("Bulgarian mapping loaded successfully", 
                   accounts=len(self.mapping_df),
                   fs_sub_classes=len(self.mapping_df['FS Sub class'].unique()),
                   abcotd_categories=len(self.mapping_df['ABCOTD'].unique()))
        
        return self.mapping_df
    
    def _validate_structure(self):
        """Validate Bulgarian mapping file structure."""
        required_columns = [
            'ID', 'Account name', 'FS Sub class', 'FS Line', 
            'ABCOTD', 'Content area', 'Classes'
        ]
        
        missing_columns = [col for col in required_columns if col not in self.mapping_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in Bulgarian mapping: {missing_columns}")
        
        logger.info("Bulgarian mapping structure validated", 
                   columns=len(self.mapping_df.columns),
                   rows=len(self.mapping_df))
    
    def _clean_bulgarian_data(self):
        """Clean and standardize Bulgarian mapping data."""
        logger.info("Cleaning Bulgarian mapping data")
        
        # Clean account IDs - convert to string for consistency
        self.mapping_df['gl_account'] = self.mapping_df['ID'].astype(str).str.replace('.0', '', regex=False)
        
        # Clean Bulgarian text fields
        text_columns = ['Account name', 'FS Line', 'FS Sub class', 'ABCOTD', 'Content area', 'Note line']
        for col in text_columns:
            if col in self.mapping_df.columns:
                self.mapping_df[col] = self.mapping_df[col].astype(str).str.strip()
                # Handle NaN values
                self.mapping_df[col] = self.mapping_df[col].replace('nan', '')
        
        # Standardize class names
        self.mapping_df['Classes'] = self.mapping_df['Classes'].str.strip()
        
        # Remove any completely empty rows
        self.mapping_df = self.mapping_df.dropna(subset=['gl_account', 'Account name'])
        
        logger.info("Bulgarian data cleaning completed", 
                   clean_rows=len(self.mapping_df))
    
    def _validate_bulgarian_types(self):
        """Validate Bulgarian data types and consistency."""
        logger.info("Validating Bulgarian data types")
        
        # Check for valid account IDs
        invalid_accounts = self.mapping_df[
            self.mapping_df['gl_account'].str.len() < 4
        ]
        if len(invalid_accounts) > 0:
            logger.warning("Found accounts with short IDs", count=len(invalid_accounts))
        
        # Check Bulgarian class consistency
        expected_classes = ['Assets', 'Liabilities', 'Equity', 'Profit (loss)']
        invalid_classes = self.mapping_df[
            ~self.mapping_df['Classes'].isin(expected_classes)
        ]
        if len(invalid_classes) > 0:
            logger.warning("Found unexpected Bulgarian classes", 
                          classes=invalid_classes['Classes'].unique().tolist())
        
        # Check FS Sub class consistency
        expected_fs_sub_classes = [
            'Equity', 'Non-current assets', 'Current Assets', 
            'Current liabilities', 'Profit (loss)'
        ]
        invalid_fs_sub = self.mapping_df[
            ~self.mapping_df['FS Sub class'].isin(expected_fs_sub_classes)
        ]
        if len(invalid_fs_sub) > 0:
            logger.warning("Found unexpected FS Sub classes", 
                          classes=invalid_fs_sub['FS Sub class'].unique().tolist())
    
    def _create_bulgarian_classifications(self):
        """Create standardized classifications for Bulgarian data."""
        logger.info("Creating Bulgarian classifications")
        
        # Create standardized bucket mapping based on ABCOTD and FS Sub class
        def get_bucket_type(row):
            """Determine bucket type from Bulgarian classifications."""
            fs_sub_class = str(row.get('FS Sub class', '')).lower()
            abcotd = str(row.get('ABCOTD', '')).lower()
            classes = str(row.get('Classes', '')).lower()
            
            # P&L items (from ABCOTD)
            revenue_keywords = ['revenue', 'other income']
            expense_keywords = [
                'cost of sales', 'operating expenses', 'payroll', 'other expenses',
                'income tax', 'interest', 'depreciation', 'amortization'
            ]
            
            # Balance Sheet items
            asset_keywords = [
                'cash', 'inventory', 'receivables', 'property', 'intangibles',
                'prepaid', 'deferred tax asset'
            ]
            liability_keywords = [
                'payables', 'deferred revenue', 'lease liabilities',
                'deferred tax liability'
            ]
            equity_keywords = ['equity']
            
            # Check ABCOTD first (most specific)
            if any(keyword in abcotd for keyword in revenue_keywords):
                return 'Revenue'
            elif any(keyword in abcotd for keyword in expense_keywords):
                return 'OPEX'
            elif any(keyword in abcotd for keyword in asset_keywords):
                if 'current' in fs_sub_class:
                    return 'Current Assets'
                else:
                    return 'Non-current Assets'
            elif any(keyword in abcotd for keyword in liability_keywords):
                if 'current' in fs_sub_class:
                    return 'Current Liabilities'
                else:
                    return 'Non-current Liabilities'
            elif any(keyword in abcotd for keyword in equity_keywords):
                return 'Equity'
            
            # Fallback to FS Sub class
            elif 'profit' in fs_sub_class or 'loss' in fs_sub_class:
                return 'P&L'
            elif 'assets' in fs_sub_class:
                if 'current' in fs_sub_class:
                    return 'Current Assets'
                else:
                    return 'Non-current Assets'
            elif 'liabilities' in fs_sub_class:
                if 'current' in fs_sub_class:
                    return 'Current Liabilities'
                else:
                    return 'Non-current Liabilities'
            elif 'equity' in fs_sub_class:
                return 'Equity'
            
            # Final fallback to Classes
            elif 'profit' in classes or 'loss' in classes:
                return 'P&L'
            elif 'assets' in classes:
                return 'Assets'
            elif 'liabilities' in classes:
                return 'Liabilities'
            elif 'equity' in classes:
                return 'Equity'
            
            return 'Other'
        
        # Apply bucket classification
        self.mapping_df['bucket'] = self.mapping_df.apply(get_bucket_type, axis=1)
        
        # Create entity classification (default to single entity for now)
        self.mapping_df['entity'] = 'Main Entity'
        
        # Create type classification
        def get_type_classification(row):
            """Determine account type for Bulgarian data."""
            bucket = row.get('bucket', '')
            abcotd = str(row.get('ABCOTD', '')).lower()
            
            if bucket in ['Revenue']:
                return 'Revenue'
            elif bucket in ['OPEX']:
                if 'payroll' in abcotd:
                    return 'Payroll'
                elif 'depreciation' in abcotd or 'amortization' in abcotd:
                    return 'Depreciation'
                else:
                    return 'Operating Expense'
            elif 'receivables' in abcotd:
                return 'AR'
            elif 'payables' in abcotd:
                return 'AP'
            elif 'cash' in abcotd:
                return 'Cash'
            elif 'inventory' in abcotd:
                return 'Inventory'
            else:
                return 'Other'
        
        self.mapping_df['type'] = self.mapping_df.apply(get_type_classification, axis=1)
        
        # Create notes from Bulgarian descriptions
        self.mapping_df['notes'] = (
            self.mapping_df['Account name'].fillna('') + ' | ' +
            self.mapping_df['FS Line'].fillna('') + ' | ' +
            self.mapping_df['ABCOTD'].fillna('')
        ).str.replace(' |  | ', ' | ', regex=False).str.replace(' | $', '', regex=True)
        
        logger.info("Bulgarian classifications created", 
                   buckets=self.mapping_df['bucket'].value_counts().to_dict(),
                   types=self.mapping_df['type'].value_counts().to_dict())
    
    def get_bulgarian_summary(self) -> Dict:
        """Get summary of Bulgarian mapping data."""
        if self.mapping_df is None:
            raise ValueError("Bulgarian mapping not loaded. Call load() first.")
        
        return {
            'total_accounts': len(self.mapping_df),
            'fs_sub_classes': self.mapping_df['FS Sub class'].value_counts().to_dict(),
            'classes': self.mapping_df['Classes'].value_counts().to_dict(),
            'abcotd_categories': self.mapping_df['ABCOTD'].value_counts().to_dict(),
            'bucket_distribution': self.mapping_df['bucket'].value_counts().to_dict(),
            'type_distribution': self.mapping_df['type'].value_counts().to_dict(),
            'unmapped_accounts': len(self.mapping_df[self.mapping_df['bucket'] == 'Other'])
        }
    
    def get_standard_mapping(self) -> pd.DataFrame:
        """Get mapping in standard format for the pipeline."""
        if self.mapping_df is None:
            raise ValueError("Bulgarian mapping not loaded. Call load() first.")
        
        # Return in standard format expected by the pipeline
        standard_columns = [
            'gl_account', 'bucket', 'type', 'entity', 'notes'
        ]
        
        return self.mapping_df[standard_columns].copy()


def load_bulgarian_mapping(mapping_file: Path, config: Config) -> pd.DataFrame:
    """
    Convenience function to load Bulgarian mapping data.
    
    Args:
        mapping_file: Path to Bulgarian mapping Excel file
        config: Configuration object
        
    Returns:
        Standardized mapping DataFrame
    """
    loader = BulgarianMappingLoader(mapping_file, config)
    loader.load()
    return loader.get_standard_mapping()
