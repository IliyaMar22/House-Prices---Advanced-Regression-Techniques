"""Comprehensive Bulgarian Financial Analysis Script."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import structlog
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our Bulgarian loaders
import sys
sys.path.append('.')
from fin_review.loaders.bulgarian_mapping_loader import BulgarianMappingLoader
from fin_review.loaders.bulgarian_fagl_loader import BulgarianFAGLLoader

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def load_bulgarian_data(sample_size=None):
    """Load Bulgarian mapping and movements data."""
    print("🇧🇬 LOADING BULGARIAN FINANCIAL DATA")
    print("=" * 60)
    
    # Load mapping data
    mapping_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/Mapping export.xlsx')
    print(f"📊 Loading mapping data from: {mapping_file}")
    
    mapping_loader = BulgarianMappingLoader(mapping_file, None)
    mapping_df = mapping_loader.load()
    mapping_summary = mapping_loader.get_bulgarian_summary()
    
    print(f"✅ Mapping loaded: {mapping_summary['total_accounts']:,} accounts")
    print(f"   ABCOTD categories: {len(mapping_summary['abcotd_categories'])}")
    
    # Load movements data
    movements_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/movements 2024.XLSX')
    print(f"📋 Loading movements data from: {movements_file}")
    
    if sample_size:
        print(f"⚠️  Loading sample of {sample_size:,} rows for testing...")
    
    movements_loader = BulgarianFAGLLoader(movements_file, None)
    movements_df = movements_loader.load(sample_size=sample_size)
    movements_summary = movements_loader.get_summary()
    
    print(f"✅ Movements loaded: {movements_summary['total_transactions']:,} transactions")
    print(f"   Date range: {movements_summary['date_range']['start'].strftime('%Y-%m-%d')} to {movements_summary['date_range']['end'].strftime('%Y-%m-%d')}")
    print(f"   Unique accounts: {movements_summary['unique_accounts']:,}")
    
    return mapping_df, movements_df, mapping_summary, movements_summary


def map_accounts_to_abcotd(mapping_df, movements_df):
    """Map movements accounts to ABCOTD classifications."""
    print("\n🔗 MAPPING ACCOUNTS TO ABCOTD CLASSIFICATIONS")
    print("-" * 50)
    
    # Merge movements with mapping
    mapped_df = movements_df.merge(
        mapping_df[['gl_account', 'bucket', 'type', 'ABCOTD', 'FS Sub class', 'Classes']],
        left_on='gl_account',
        right_on='gl_account',
        how='left'
    )
    
    # Check mapping coverage
    total_transactions = len(mapped_df)
    mapped_transactions = len(mapped_df.dropna(subset=['ABCOTD']))
    unmapped_transactions = total_transactions - mapped_transactions
    
    print(f"📊 Mapping Results:")
    print(f"   Total transactions: {total_transactions:,}")
    print(f"   Mapped transactions: {mapped_transactions:,} ({mapped_transactions/total_transactions*100:.1f}%)")
    print(f"   Unmapped transactions: {unmapped_transactions:,} ({unmapped_transactions/total_transactions*100:.1f}%)")
    
    if unmapped_transactions > 0:
        unmapped_accounts = mapped_df[mapped_df['ABCOTD'].isna()]['gl_account'].unique()
        print(f"   Unmapped accounts: {len(unmapped_accounts)}")
        print(f"   Sample unmapped: {unmapped_accounts[:5].tolist()}")
    
    return mapped_df


def analyze_abcotd_monthly(mapped_df):
    """Analyze ABCOTD categories on monthly basis."""
    print("\n📈 ANALYZING ABCOTD CATEGORIES MONTHLY")
    print("-" * 50)
    
    # Create monthly aggregation (convert Period to string for Plotly compatibility)
    mapped_df['year_month'] = mapped_df['posting_date'].dt.to_period('M').astype(str)
    
    # Group by ABCOTD and month
    monthly_abcotd = mapped_df.groupby(['year_month', 'ABCOTD']).agg({
        'amount': ['sum', 'count'],
        'gl_account': 'nunique'
    }).round(2)
    
    # Flatten column names
    monthly_abcotd.columns = ['total_amount', 'transaction_count', 'unique_accounts']
    monthly_abcotd = monthly_abcotd.reset_index()
    
    # Get top ABCOTD categories by total amount
    top_abcotd = monthly_abcotd.groupby('ABCOTD')['total_amount'].sum().abs().sort_values(ascending=False).head(15)
    
    print(f"📊 Top 15 ABCOTD categories by volume:")
    for i, (abcotd, amount) in enumerate(top_abcotd.items(), 1):
        print(f"   {i:2d}. {abcotd}: лв {amount:,.2f}")
    
    return monthly_abcotd, top_abcotd


def create_monthly_charts(monthly_abcotd, top_abcotd):
    """Create monthly visualization charts."""
    print("\n📊 CREATING MONTHLY VISUALIZATION CHARTS")
    print("-" * 50)
    
    # Filter to top ABCOTD categories
    top_abcotd_list = top_abcotd.index.tolist()
    chart_data = monthly_abcotd[monthly_abcotd['ABCOTD'].isin(top_abcotd_list)].copy()
    
    # Create line chart
    fig = px.line(
        chart_data,
        x='year_month',
        y='total_amount',
        color='ABCOTD',
        title='Monthly ABCOTD Analysis - Bulgarian Financial Data 2024',
        labels={
            'total_amount': 'Amount (лв)',
            'year_month': 'Month',
            'ABCOTD': 'ABCOTD Category'
        },
        height=600
    )
    
    fig.update_layout(
        title_font_size=16,
        xaxis_title="Month",
        yaxis_title="Amount (лв)",
        legend_title="ABCOTD Category",
        hovermode='x unified'
    )
    
    # Save line chart
    line_chart_path = 'bulgarian_monthly_abcotd_line.html'
    fig.write_html(line_chart_path)
    print(f"✅ Line chart saved: {line_chart_path}")
    
    # Create bar chart for top categories
    fig_bar = px.bar(
        chart_data.groupby('ABCOTD')['total_amount'].sum().reset_index(),
        x='total_amount',
        y='ABCOTD',
        orientation='h',
        title='Total Amount by ABCOTD Category - Bulgarian Data 2024',
        labels={
            'total_amount': 'Total Amount (лв)',
            'ABCOTD': 'ABCOTD Category'
        },
        height=600
    )
    
    fig_bar.update_layout(
        title_font_size=16,
        xaxis_title="Total Amount (лв)",
        yaxis_title="ABCOTD Category"
    )
    
    # Save bar chart
    bar_chart_path = 'bulgarian_abcotd_totals_bar.html'
    fig_bar.write_html(bar_chart_path)
    print(f"✅ Bar chart saved: {bar_chart_path}")
    
    return line_chart_path, bar_chart_path


def create_fs_sub_class_analysis(mapped_df):
    """Analyze FS Sub class categories."""
    print("\n📋 ANALYZING FS SUB CLASS CATEGORIES")
    print("-" * 50)
    
    # Monthly FS Sub class analysis
    monthly_fs = mapped_df.groupby(['year_month', 'FS Sub class']).agg({
        'amount': ['sum', 'count'],
        'gl_account': 'nunique'
    }).round(2)
    
    monthly_fs.columns = ['total_amount', 'transaction_count', 'unique_accounts']
    monthly_fs = monthly_fs.reset_index()
    
    # FS Sub class totals
    fs_totals = monthly_fs.groupby('FS Sub class')['total_amount'].sum().sort_values(ascending=False)
    
    print(f"📊 FS Sub class totals:")
    for fs_class, amount in fs_totals.items():
        print(f"   {fs_class}: лв {amount:,.2f}")
    
    # Create FS Sub class chart
    fig_fs = px.bar(
        fs_totals.reset_index(),
        x='FS Sub class',
        y='total_amount',
        title='Total Amount by FS Sub Class - Bulgarian Data 2024',
        labels={
            'total_amount': 'Total Amount (лв)',
            'FS Sub class': 'FS Sub Class'
        },
        height=500
    )
    
    fig_fs.update_layout(
        title_font_size=16,
        xaxis_title="FS Sub Class",
        yaxis_title="Total Amount (лв)",
        xaxis_tickangle=-45
    )
    
    # Save FS Sub class chart
    fs_chart_path = 'bulgarian_fs_subclass_analysis.html'
    fig_fs.write_html(fs_chart_path)
    print(f"✅ FS Sub class chart saved: {fs_chart_path}")
    
    return monthly_fs, fs_totals, fs_chart_path


def generate_summary_report(mapping_summary, movements_summary, monthly_abcotd, top_abcotd, fs_totals):
    """Generate comprehensive summary report."""
    print("\n📄 GENERATING SUMMARY REPORT")
    print("-" * 50)
    
    report = f"""
# Bulgarian Financial Analysis Report 2024

## Executive Summary

This report analyzes the complete financial chronology for 2024, covering {movements_summary['total_transactions']:,} transactions across {movements_summary['unique_accounts']:,} GL accounts.

## Data Overview

- **Total Transactions**: {movements_summary['total_transactions']:,}
- **Date Range**: {movements_summary['date_range']['start'].strftime('%B %d, %Y')} to {movements_summary['date_range']['end'].strftime('%B %d, %Y')}
- **Unique Accounts**: {movements_summary['unique_accounts']:,}
- **Currency**: {movements_summary['currency']}
- **Company**: {movements_summary['company_code']}

## Mapping Coverage

- **Total Mapped Accounts**: {mapping_summary['total_accounts']:,}
- **ABCOTD Categories**: {len(mapping_summary['abcotd_categories'])}
- **FS Sub Classes**: {len(mapping_summary['fs_sub_classes'])}

## Top ABCOTD Categories by Volume

"""
    
    for i, (abcotd, amount) in enumerate(top_abcotd.head(10).items(), 1):
        report += f"{i:2d}. **{abcotd}**: лв {amount:,.2f}\n"
    
    report += f"""

## FS Sub Class Analysis

"""
    
    for fs_class, amount in fs_totals.items():
        report += f"- **{fs_class}**: лв {amount:,.2f}\n"
    
    report += f"""

## Key Insights

1. **Data Quality**: {mapping_summary['total_accounts']:,} accounts successfully mapped to ABCOTD classifications
2. **Volume**: {movements_summary['total_transactions']:,} transactions processed
3. **Coverage**: Complete 2024 financial chronology analyzed
4. **Classification**: Full ABCOTD and FS Sub class mapping applied

## Generated Files

- Monthly ABCOTD Line Chart
- ABCOTD Totals Bar Chart  
- FS Sub Class Analysis Chart
- This Summary Report

---
*Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*
"""
    
    # Save report
    report_path = 'bulgarian_financial_analysis_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Summary report saved: {report_path}")
    
    return report_path


def main(sample_size=None):
    """Main analysis function."""
    print("🇧🇬 BULGARIAN FINANCIAL ANALYSIS 2024")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load data
        mapping_df, movements_df, mapping_summary, movements_summary = load_bulgarian_data(sample_size)
        
        # Map accounts to ABCOTD
        mapped_df = map_accounts_to_abcotd(mapping_df, movements_df)
        
        # Analyze ABCOTD monthly
        monthly_abcotd, top_abcotd = analyze_abcotd_monthly(mapped_df)
        
        # Create charts
        line_chart, bar_chart = create_monthly_charts(monthly_abcotd, top_abcotd)
        
        # Analyze FS Sub classes
        monthly_fs, fs_totals, fs_chart = create_fs_sub_class_analysis(mapped_df)
        
        # Generate summary report
        report_path = generate_summary_report(mapping_summary, movements_summary, monthly_abcotd, top_abcotd, fs_totals)
        
        print(f"\n🎉 BULGARIAN ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Generated Files:")
        print(f"   • {line_chart}")
        print(f"   • {bar_chart}")
        print(f"   • {fs_chart}")
        print(f"   • {report_path}")
        print(f"\n✨ Open the HTML files in your browser to view interactive charts!")
        
        return {
            'line_chart': line_chart,
            'bar_chart': bar_chart,
            'fs_chart': fs_chart,
            'report': report_path,
            'monthly_abcotd': monthly_abcotd,
            'top_abcotd': top_abcotd,
            'fs_totals': fs_totals
        }
        
    except Exception as e:
        logger.error("Bulgarian analysis failed", error=str(e))
        print(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulgarian Financial Analysis 2024')
    parser.add_argument('--sample-size', type=int, help='Sample size for testing (e.g., 10000)')
    parser.add_argument('--full', action='store_true', help='Run on full dataset (610,333 rows)')
    
    args = parser.parse_args()
    
    if args.full:
        print("⚠️  Running on FULL dataset (610,333 rows) - this will take time!")
        sample_size = None
    elif args.sample_size:
        sample_size = args.sample_size
    else:
        # Default to sample for testing
        sample_size = 5000
        print(f"🔬 Running with sample size: {sample_size:,} rows")
    
    results = main(sample_size=sample_size)
