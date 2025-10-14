"""Create sample Excel mapping file without requiring openpyxl initially."""

import pandas as pd
from pathlib import Path

# Create mapping data
mapping_data = [
    {'gl_account': '400000', 'bucket': 'Revenue - Product A', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Product A Sales'},
    {'gl_account': '400100', 'bucket': 'Revenue - Product B', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Product B Sales'},
    {'gl_account': '400200', 'bucket': 'Revenue - Services', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Service Revenue'},
    {'gl_account': '600100', 'bucket': 'OPEX - Marketing', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Marketing advertising'},
    {'gl_account': '600200', 'bucket': 'OPEX - IT Services', 'type': 'OPEX', 'entity': 'BG', 'notes': 'IT and software'},
    {'gl_account': '600300', 'bucket': 'OPEX - Office Rent', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Office rental costs'},
    {'gl_account': '600400', 'bucket': 'OPEX - Utilities', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Electricity water etc'},
    {'gl_account': '600500', 'bucket': 'OPEX - Professional Services', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Consultants legal'},
    {'gl_account': '610000', 'bucket': 'Payroll - Salaries', 'type': 'Payroll', 'entity': 'BG', 'notes': 'Gross salaries'},
    {'gl_account': '610100', 'bucket': 'Payroll - Benefits', 'type': 'Payroll', 'entity': 'BG', 'notes': 'Employee benefits'},
    {'gl_account': '650000', 'bucket': 'Interest - Bank Loans', 'type': 'Interest', 'entity': 'BG', 'notes': 'Interest expenses'},
    {'gl_account': '120000', 'bucket': 'Receivables - Customers', 'type': 'Receivable', 'entity': 'BG', 'notes': 'Trade debtors'},
    {'gl_account': '230100', 'bucket': 'Payables - Suppliers', 'type': 'Payable', 'entity': 'BG', 'notes': 'Trade creditors'},
]

df = pd.DataFrame(mapping_data)

# Try to save as Excel, fall back to CSV if openpyxl not available
try:
    df.to_excel('data/mapping.xlsx', sheet_name='mapping', index=False)
    print("✓ Created mapping.xlsx")
except Exception as e:
    print(f"Note: Could not create Excel file ({e})")
    print("Creating CSV instead for testing...")
    df.to_csv('data/mapping.csv', index=False)
    print("✓ Created mapping.csv")

