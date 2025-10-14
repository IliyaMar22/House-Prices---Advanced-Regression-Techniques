"""Generate sample FAGL03 CSV for testing (no Excel dependency)."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_fagl03(num_months=18):
    """Generate sample FAGL03 data."""
    transactions = []
    
    # Date range: last 18 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * num_months)
    
    current_date = start_date
    doc_id_counter = 100000
    
    # GL accounts from mapping
    gl_accounts = [
        ('400000', 'revenue'), ('400100', 'revenue'), ('400200', 'revenue'),
        ('600100', 'opex'), ('600200', 'opex'), ('600300', 'opex'),
        ('600400', 'opex'), ('600500', 'opex'),
        ('610000', 'payroll'), ('610100', 'payroll'),
        ('650000', 'interest'),
        ('120000', 'receivable'),
        ('230100', 'payable')
    ]
    
    # Generate monthly patterns
    while current_date < end_date:
        month_transactions = []
        
        # Revenue transactions
        for account, acc_type in [g for g in gl_accounts if g[1] == 'revenue']:
            num_trans = random.randint(15, 30)
            
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = random.uniform(5000, 50000)
                
                # Seasonality (higher in Q4)
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
                    'open_amount': round(amount * random.uniform(0, 0.3), 2),
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # OPEX transactions
        for account, acc_type in [g for g in gl_accounts if g[1] == 'opex']:
            num_trans = random.randint(5, 15)
            
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = -random.uniform(1000, 20000)
                
                # Anomaly: spike in marketing in August
                if account == '600100' and current_date.month == 8 and current_date.year == end_date.year:
                    amount *= 2.5
                
                month_transactions.append({
                    'posting_date': trans_date.strftime('%Y-%m-%d'),
                    'doc_id': f'EXP-{doc_id_counter}',
                    'gl_account': account,
                    'amount': round(amount, 2),
                    'currency': 'EUR',
                    'posting_text': f'Expense {doc_id_counter}',
                    'customer_vendor': f'VEND-{random.randint(1, 30):03d}',
                    'due_date': (trans_date + timedelta(days=random.randint(30, 60))).strftime('%Y-%m-%d'),
                    'open_amount': round(amount * random.uniform(0, 0.5), 2),
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # Payroll transactions (once per month)
        for account, acc_type in [g for g in gl_accounts if g[1] == 'payroll']:
            trans_date = current_date.replace(day=25)
            amount = -random.uniform(50000, 70000)
            
            month_transactions.append({
                'posting_date': trans_date.strftime('%Y-%m-%d'),
                'doc_id': f'PAY-{doc_id_counter}',
                'gl_account': account,
                'amount': round(amount, 2),
                'currency': 'EUR',
                'posting_text': f'Payroll {trans_date.strftime("%Y-%m")}',
                'customer_vendor': 'PAYROLL-DEPT',
                'due_date': trans_date.strftime('%Y-%m-%d'),
                'open_amount': 0,
                'company_code': 'BG'
            })
            doc_id_counter += 1
        
        # AR transactions
        for account, acc_type in [g for g in gl_accounts if g[1] == 'receivable']:
            num_trans = random.randint(10, 20)
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = random.uniform(3000, 25000)
                days_past_due = random.randint(-30, 120)
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
                    'open_amount': round(amount, 2),
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        # AP transactions
        for account, acc_type in [g for g in gl_accounts if g[1] == 'payable']:
            num_trans = random.randint(10, 20)
            for _ in range(num_trans):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                amount = -random.uniform(2000, 15000)
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
                    'open_amount': round(amount, 2),
                    'company_code': 'BG'
                })
                doc_id_counter += 1
        
        transactions.extend(month_transactions)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return pd.DataFrame(transactions)

if __name__ == '__main__':
    print("Generating sample FAGL03 data...")
    print("=" * 60)
    
    df = generate_fagl03(num_months=18)
    
    df.to_csv('data/sample_fagl03.csv', index=False)
    print(f"✓ Generated sample_fagl03.csv with {len(df)} transactions")
    print(f"  Date range: {df['posting_date'].min()} to {df['posting_date'].max()}")
    print(f"  Total revenue: €{df[df['amount'] > 0]['amount'].sum()/1000:.1f}K")
    print(f"  Total expenses: €{abs(df[df['amount'] < 0]['amount'].sum())/1000:.1f}K")
    
    print("=" * 60)
    print("✅ Sample data generation complete!")
    print("\nTo run the pipeline with sample data:")
    print("  python -m fin_review.cli \\")
    print("    --mapping data/mapping.csv \\")
    print("    --fagl-file data/sample_fagl03.csv \\")
    print("    --out-dir reports/ \\")
    print("    --generate-dashboard")

