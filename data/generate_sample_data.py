"""Generate sample data for testing the financial review pipeline."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_mapping():
    """Generate sample mapping Excel file."""
    mapping_data = [
        # Revenue accounts
        {'gl_account': '400000', 'bucket': 'Revenue - Product A', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Product A Sales'},
        {'gl_account': '400100', 'bucket': 'Revenue - Product B', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Product B Sales'},
        {'gl_account': '400200', 'bucket': 'Revenue - Services', 'type': 'Revenue', 'entity': 'BG', 'notes': 'Service Revenue'},
        
        # OPEX accounts
        {'gl_account': '600100', 'bucket': 'OPEX - Marketing', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Marketing advertising'},
        {'gl_account': '600200', 'bucket': 'OPEX - IT Services', 'type': 'OPEX', 'entity': 'BG', 'notes': 'IT and software'},
        {'gl_account': '600300', 'bucket': 'OPEX - Office Rent', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Office rental costs'},
        {'gl_account': '600400', 'bucket': 'OPEX - Utilities', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Electricity, water, etc'},
        {'gl_account': '600500', 'bucket': 'OPEX - Professional Services', 'type': 'OPEX', 'entity': 'BG', 'notes': 'Consultants, legal'},
        
        # Payroll accounts
        {'gl_account': '610000', 'bucket': 'Payroll - Salaries', 'type': 'Payroll', 'entity': 'BG', 'notes': 'Gross salaries'},
        {'gl_account': '610100', 'bucket': 'Payroll - Benefits', 'type': 'Payroll', 'entity': 'BG', 'notes': 'Employee benefits'},
        
        # Interest
        {'gl_account': '650000', 'bucket': 'Interest - Bank Loans', 'type': 'Interest', 'entity': 'BG', 'notes': 'Interest expenses'},
        
        # Receivables
        {'gl_account': '120000', 'bucket': 'Receivables - Customers', 'type': 'Receivable', 'entity': 'BG', 'notes': 'Trade debtors'},
        
        # Payables
        {'gl_account': '230100', 'bucket': 'Payables - Suppliers', 'type': 'Payable', 'entity': 'BG', 'notes': 'Trade creditors'},
    ]
    
    df = pd.DataFrame(mapping_data)
    
    # Save to Excel
    df.to_excel('data/mapping.xlsx', sheet_name='mapping', index=False)
    print(f"✓ Generated mapping.xlsx with {len(df)} GL accounts")
    
    return df

def generate_fagl03(mapping_df, num_months=18):
    """Generate sample FAGL03 data."""
    transactions = []
    
    # Date range: last 18 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * num_months)
    
    current_date = start_date
    doc_id_counter = 100000
    
    # Generate monthly patterns
    while current_date < end_date:
        month_transactions = []
        
        # Revenue transactions
        revenue_accounts = mapping_df[mapping_df['type'] == 'Revenue']['gl_account'].tolist()
        for account in revenue_accounts:
            # Generate 15-30 revenue transactions per month per account
            num_trans = random.randint(15, 30)
            
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = random.uniform(5000, 50000)  # Random revenue amount
                
                # Add some seasonality (higher in Q4)
                if current_date.month in [10, 11, 12]:
                    amount *= 1.3
                
                month_transactions.append({
                    'posting_date': trans_date.strftime('%Y-%m-%d'),
                    'doc_id': f'INV-{doc_id_counter}',
                    'gl_account': account,
                    'amount': round(amount, 2),
                    'currency': 'EUR',
                    'posting_text': f'Sales Invoice {doc_id_counter}',
                    'customer_vendor': f'CUST-{random.randint(1, 20):03d}',
                    'due_date': (trans_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'open_amount': round(amount * random.uniform(0, 0.3), 2),  # 0-30% still open
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # OPEX transactions
        opex_accounts = mapping_df[mapping_df['type'] == 'OPEX']['gl_account'].tolist()
        for account in opex_accounts:
            # Generate 5-15 expense transactions per month per account
            num_trans = random.randint(5, 15)
            
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = -random.uniform(1000, 20000)  # Negative for expenses
                
                # Add anomaly: spike in marketing in one specific month
                if account == '600100' and current_date.month == 8 and current_date.year == end_date.year:
                    amount *= 2.5  # Big marketing campaign
                
                month_transactions.append({
                    'posting_date': trans_date.strftime('%Y-%m-%d'),
                    'doc_id': f'EXP-{doc_id_counter}',
                    'gl_account': account,
                    'amount': round(amount, 2),
                    'currency': 'EUR',
                    'posting_text': f'Expense {doc_id_counter}',
                    'customer_vendor': f'VEND-{random.randint(1, 30):03d}',
                    'due_date': (trans_date + timedelta(days=random.randint(30, 60))).strftime('%Y-%m-%d'),
                    'open_amount': round(amount * random.uniform(0, 0.5), 2),  # 0-50% still open
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # Payroll transactions (once per month)
        payroll_accounts = mapping_df[mapping_df['type'] == 'Payroll']['gl_account'].tolist()
        for account in payroll_accounts:
            trans_date = current_date.replace(day=25)  # Payroll on 25th
            amount = -random.uniform(50000, 70000)  # Monthly payroll
            
            month_transactions.append({
                'posting_date': trans_date.strftime('%Y-%m-%d'),
                'doc_id': f'PAY-{doc_id_counter}',
                'gl_account': account,
                'amount': round(amount, 2),
                'currency': 'EUR',
                'posting_text': f'Payroll {trans_date.strftime("%Y-%m")}',
                'customer_vendor': 'PAYROLL-DEPT',
                'due_date': trans_date.strftime('%Y-%m-%d'),
                'open_amount': 0,  # Payroll always paid
                'company_code': 'BG'
            })
            doc_id_counter += 1
        
        # Receivables and Payables
        # AR
        ar_accounts = mapping_df[mapping_df['type'] == 'Receivable']['gl_account'].tolist()
        for account in ar_accounts:
            num_trans = random.randint(10, 20)
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = random.uniform(3000, 25000)
                
                # Create some overdue items
                days_past_due = random.randint(-30, 120)  # Some overdue, some not
                due_date = trans_date + timedelta(days=30 - days_past_due)
                
                month_transactions.append({
                    'posting_date': trans_date.strftime('%Y-%m-%d'),
                    'doc_id': f'AR-{doc_id_counter}',
                    'gl_account': account,
                    'amount': round(amount, 2),
                    'currency': 'EUR',
                    'posting_text': f'Accounts Receivable',
                    'customer_vendor': f'CUST-{random.randint(1, 20):03d}',
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'open_amount': round(amount, 2),  # All open
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # AP
        ap_accounts = mapping_df[mapping_df['type'] == 'Payable']['gl_account'].tolist()
        for account in ap_accounts:
            num_trans = random.randint(10, 20)
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = -random.uniform(2000, 15000)
                
                # Create some overdue items
                days_past_due = random.randint(-30, 90)
                due_date = trans_date + timedelta(days=45 - days_past_due)
                
                month_transactions.append({
                    'posting_date': trans_date.strftime('%Y-%m-%d'),
                    'doc_id': f'AP-{doc_id_counter}',
                    'gl_account': account,
                    'amount': round(amount, 2),
                    'currency': 'EUR',
                    'posting_text': f'Accounts Payable',
                    'customer_vendor': f'VEND-{random.randint(1, 30):03d}',
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'open_amount': round(amount, 2),  # All open
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        transactions.extend(month_transactions)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    df = pd.DataFrame(transactions)
    
    # Save to CSV
    df.to_csv('data/sample_fagl03.csv', index=False)
    print(f"✓ Generated sample_fagl03.csv with {len(df)} transactions")
    print(f"  Date range: {df['posting_date'].min()} to {df['posting_date'].max()}")
    print(f"  Total revenue: €{df[df['amount'] > 0]['amount'].sum()/1000:.1f}K")
    print(f"  Total expenses: €{abs(df[df['amount'] < 0]['amount'].sum())/1000:.1f}K")
    
    return df

if __name__ == '__main__':
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    print("Generating sample data...")
    print("=" * 60)
    
    # Generate mapping
    mapping_df = generate_mapping()
    
    # Generate FAGL03 data
    fagl_df = generate_fagl03(mapping_df)
    
    print("=" * 60)
    print("✅ Sample data generation complete!")
    print("\nTo run the pipeline with sample data:")
    print("  python -m fin_review.cli \\")
    print("    --mapping data/mapping.xlsx \\")
    print("    --fagl-file data/sample_fagl03.csv \\")
    print("    --out-dir reports/ \\")
    print("    --generate-dashboard")

