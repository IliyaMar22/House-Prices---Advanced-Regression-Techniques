"""Complete Bulgarian Financial Analysis Pipeline - All Reports Generation."""

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
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import base64
warnings.filterwarnings('ignore')

# Import our modules
import sys
sys.path.append('.')
from fin_review.loaders.bulgarian_mapping_loader import BulgarianMappingLoader
from fin_review.loaders.bulgarian_fagl_loader import BulgarianFAGLLoader
from fin_review.analytics.ratio_analyzer import FinancialRatioAnalyzer, analyze_financial_ratios

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


def load_bulgarian_data():
    """Load Bulgarian mapping and movements data."""
    print("🇧🇬 LOADING BULGARIAN FINANCIAL DATA FOR COMPLETE ANALYSIS")
    print("=" * 80)
    
    # Load mapping data
    mapping_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/Mapping export.xlsx')
    print(f"📊 Loading mapping data from: {mapping_file}")
    
    mapping_loader = BulgarianMappingLoader(mapping_file, None)
    mapping_df = mapping_loader.load()
    mapping_summary = mapping_loader.get_bulgarian_summary()
    
    print(f"✅ Mapping loaded: {mapping_summary['total_accounts']:,} accounts")
    print(f"   ABCOTD categories: {len(mapping_summary['abcotd_categories'])}")
    
    # Load movements data (full dataset)
    movements_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/movements 2024.XLSX')
    print(f"📋 Loading movements data from: {movements_file}")
    print("⚠️  Loading full dataset (610,333 rows) for complete analysis...")
    
    movements_loader = BulgarianFAGLLoader(movements_file, None)
    movements_df = movements_loader.load()  # Full dataset
    movements_summary = movements_loader.get_summary()
    
    print(f"✅ Movements loaded: {movements_summary['total_transactions']:,} transactions")
    print(f"   Date range: {movements_summary['date_range']['start'].strftime('%Y-%m-%d')} to {movements_summary['date_range']['end'].strftime('%Y-%m-%d')}")
    print(f"   Unique accounts: {movements_summary['unique_accounts']:,}")
    
    return mapping_df, movements_df, mapping_summary, movements_summary


def map_accounts_to_abcotd(mapping_df, movements_df):
    """Map movements accounts to ABCOTD classifications."""
    print("\n🔗 MAPPING ACCOUNTS TO ABCOTD CLASSIFICATIONS")
    print("-" * 60)
    
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


def perform_abcotd_analysis(mapped_df):
    """Perform comprehensive ABCOTD analysis."""
    print("\n📈 PERFORMING COMPREHENSIVE ABCOTD ANALYSIS")
    print("-" * 60)
    
    # Create monthly aggregation
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
    
    # Create individual analysis for each ABCOTD
    abcotd_analyses = {}
    
    for abcotd in top_abcotd.index:
        print(f"   Analyzing: {abcotd}")
        
        # Filter data for this ABCOTD
        abcotd_data = mapped_df[mapped_df['ABCOTD'] == abcotd].copy()
        
        # Monthly aggregation
        monthly_data = abcotd_data.groupby('year_month').agg({
            'amount': ['sum', 'count'],
            'gl_account': 'nunique'
        }).round(2)
        
        monthly_data.columns = ['total_amount', 'transaction_count', 'unique_accounts']
        monthly_data = monthly_data.reset_index()
        
        # Calculate statistics
        total_amount = abcotd_data['amount'].sum()
        total_transactions = len(abcotd_data)
        unique_accounts = abcotd_data['gl_account'].nunique()
        date_range = f"{abcotd_data['posting_date'].min().strftime('%Y-%m')} to {abcotd_data['posting_date'].max().strftime('%Y-%m')}"
        
        abcotd_analyses[abcotd] = {
            'total_amount': total_amount,
            'total_transactions': total_transactions,
            'unique_accounts': unique_accounts,
            'date_range': date_range,
            'monthly_data': monthly_data,
            'raw_data': abcotd_data
        }
    
    return abcotd_analyses, top_abcotd, monthly_abcotd


def perform_ratio_analysis(mapped_df):
    """Perform comprehensive financial ratio analysis."""
    print("\n📊 PERFORMING COMPREHENSIVE FINANCIAL RATIO ANALYSIS")
    print("-" * 60)
    
    # Perform ratio analysis
    ratios, going_concern = analyze_financial_ratios(mapped_df)
    
    print(f"✅ Ratio Analysis Completed:")
    print(f"   Total ratios calculated: {len(ratios)}")
    print(f"   Applicable ratios: {len([r for r in ratios if r.applicable])}")
    print(f"   Going concern status: {going_concern.overall_status.upper()}")
    print(f"   Liquidity score: {going_concern.liquidity_score:.1f}/100")
    print(f"   Solvency score: {going_concern.solvency_score:.1f}/100")
    print(f"   Cash flow score: {going_concern.cash_flow_score:.1f}/100")
    
    return ratios, going_concern


def create_comprehensive_charts(abcotd_analyses, top_abcotd, ratios, going_concern):
    """Create comprehensive visualization charts."""
    print("\n📊 CREATING COMPREHENSIVE VISUALIZATION CHARTS")
    print("-" * 60)
    
    chart_files = {}
    
    # 1. ABCOTD Monthly Trends Dashboard
    print("   Creating ABCOTD Monthly Trends Dashboard...")
    
    # Filter to top ABCOTD categories
    top_abcotd_list = top_abcotd.index.tolist()
    chart_data = []
    
    for abcotd in top_abcotd_list:
        if abcotd in abcotd_analyses:
            monthly_data = abcotd_analyses[abcotd]['monthly_data']
            if len(monthly_data) > 0:
                monthly_data['ABCOTD'] = abcotd
                chart_data.append(monthly_data)
    
    if chart_data:
        combined_data = pd.concat(chart_data, ignore_index=True)
        
        fig = px.line(
            combined_data,
            x='year_month',
            y='total_amount',
            color='ABCOTD',
            title='Bulgarian ABCOTD Monthly Analysis - Complete Financial Overview 2024',
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
        
        # Save chart
        chart_files['abcotd_monthly'] = 'bulgarian_complete_abcotd_monthly_trends.html'
        fig.write_html(chart_files['abcotd_monthly'])
        print(f"     ✅ Saved: {chart_files['abcotd_monthly']}")
    
    # 2. ABCOTD Totals Dashboard
    print("   Creating ABCOTD Totals Dashboard...")
    
    fig_bar = px.bar(
        top_abcotd.reset_index(),
        x='total_amount',
        y='ABCOTD',
        orientation='h',
        title='Total Amount by ABCOTD Category - Bulgarian Complete Analysis 2024',
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
    
    chart_files['abcotd_totals'] = 'bulgarian_complete_abcotd_totals.html'
    fig_bar.write_html(chart_files['abcotd_totals'])
    print(f"     ✅ Saved: {chart_files['abcotd_totals']}")
    
    # 3. Financial Ratio Dashboard
    print("   Creating Financial Ratio Dashboard...")
    
    applicable_ratios = [r for r in ratios if r.applicable]
    
    # Create subplot with ratio categories
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Liquidity Ratios',
            'Solvency Ratios', 
            'Cash Flow Ratios',
            'Profitability Ratios'
        ],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Color mapping for status
    status_colors = {
        'excellent': '#2E8B57',  # Sea Green
        'good': '#32CD32',       # Lime Green
        'warning': '#FFD700',    # Gold
        'critical': '#DC143C'    # Crimson
    }
    
    # Group ratios by category
    categories = ['Liquidity', 'Solvency', 'Cash Flow', 'Profitability']
    positions = [(1,1), (1,2), (2,1), (2,2)]
    
    for i, category in enumerate(categories):
        category_ratios = [r for r in applicable_ratios if r.category == category]
        
        if category_ratios:
            ratio_names = [r.ratio_name.replace('_', ' ').title() for r in category_ratios]
            ratio_values = [r.value for r in category_ratios]
            ratio_colors = [status_colors.get(r.status, '#808080') for r in category_ratios]
            
            fig.add_trace(
                go.Bar(
                    x=ratio_names,
                    y=ratio_values,
                    marker_color=ratio_colors,
                    name=category,
                    text=[f"{v:.3f}" for v in ratio_values],
                    textposition='auto',
                    showlegend=False
                ),
                row=positions[i][0], col=positions[i][1]
            )
    
    # Update layout
    fig.update_layout(
        title='Bulgarian Complete Financial Ratio Analysis Dashboard 2024',
        title_font_size=16,
        height=800,
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(title_text="Ratio Value", row=2, col=1)
    
    chart_files['ratio_dashboard'] = 'bulgarian_complete_ratio_dashboard.html'
    fig.write_html(chart_files['ratio_dashboard'])
    print(f"     ✅ Saved: {chart_files['ratio_dashboard']}")
    
    # 4. Going Concern Assessment Chart
    print("   Creating Going Concern Assessment Chart...")
    
    fig_gc = go.Figure()
    
    categories = ['Liquidity', 'Solvency', 'Cash Flow']
    scores = [going_concern.liquidity_score, going_concern.solvency_score, going_concern.cash_flow_score]
    colors_gc = ['#2E8B57' if score >= 75 else '#32CD32' if score >= 50 else '#FFD700' if score >= 25 else '#DC143C' for score in scores]
    
    fig_gc.add_trace(go.Bar(
        x=categories,
        y=scores,
        marker_color=colors_gc,
        text=[f"{score:.1f}/100" for score in scores],
        textposition='auto',
        name='Going Concern Scores'
    ))
    
    fig_gc.update_layout(
        title='Bulgarian Complete Going Concern Assessment 2024',
        xaxis_title='Financial Health Categories',
        yaxis_title='Score (0-100)',
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    # Add benchmark lines
    fig_gc.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="Strong")
    fig_gc.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Adequate")
    fig_gc.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Concerning")
    
    chart_files['going_concern'] = 'bulgarian_complete_going_concern_assessment.html'
    fig_gc.write_html(chart_files['going_concern'])
    print(f"     ✅ Saved: {chart_files['going_concern']}")
    
    return chart_files


def create_individual_abcotd_charts(abcotd_analyses):
    """Create individual charts for each ABCOTD category."""
    print("\n📊 CREATING INDIVIDUAL ABCOTD CHARTS")
    print("-" * 60)
    
    chart_files = {}
    
    for i, (abcotd, analysis) in enumerate(abcotd_analyses.items(), 1):
        print(f"   Creating charts for {i}/{len(abcotd_analyses)}: {abcotd}")
        
        monthly_data = analysis['monthly_data']
        
        if len(monthly_data) == 0:
            continue
        
        # Create subplot with line chart and bar chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=[
                f'{abcotd} - Monthly Amount Trend',
                f'{abcotd} - Monthly Transaction Count'
            ],
            vertical_spacing=0.15,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Line chart for amounts
        fig.add_trace(
            go.Scatter(
                x=monthly_data['year_month'],
                y=monthly_data['total_amount'],
                mode='lines+markers',
                name='Amount (лв)',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Bar chart for transaction counts
        fig.add_trace(
            go.Bar(
                x=monthly_data['year_month'],
                y=monthly_data['transaction_count'],
                name='Transaction Count',
                marker_color='#ff7f0e'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f'{abcotd} - Monthly Analysis 2024 (Complete)',
            title_font_size=16,
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        # Update axes
        fig.update_xaxes(title_text="Month", row=2, col=1)
        fig.update_yaxes(title_text="Amount (лв)", row=1, col=1)
        fig.update_yaxes(title_text="Transaction Count", row=2, col=1)
        
        # Save chart
        safe_abcotd = abcotd.replace('/', '_').replace(' ', '_').replace('-', '_')
        chart_file = f'bulgarian_complete_abcotd_{safe_abcotd}.html'
        fig.write_html(chart_file)
        chart_files[abcotd] = chart_file
        
        print(f"     ✅ Saved: {chart_file}")
    
    return chart_files


def generate_comprehensive_summary_report(mapping_summary, movements_summary, abcotd_analyses, top_abcotd, ratios, going_concern):
    """Generate comprehensive summary report."""
    print("\n📄 GENERATING COMPREHENSIVE SUMMARY REPORT")
    print("-" * 60)
    
    report = f"""
# Bulgarian Complete Financial Analysis Report 2024

## Executive Summary

This comprehensive report provides a complete financial analysis of the 2024 financial chronology, covering {movements_summary['total_transactions']:,} transactions across {movements_summary['unique_accounts']:,} GL accounts. The analysis includes both ABCOTD category analysis and comprehensive financial ratio analysis with going concern assessment.

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

## ABCOTD Analysis Results

### Top ABCOTD Categories by Volume

"""
    
    for i, (abcotd, amount) in enumerate(top_abcotd.head(10).items(), 1):
        report += f"{i:2d}. **{abcotd}**: лв {amount:,.2f}\n"
    
    report += f"""

## Financial Ratio Analysis Results

### Going Concern Assessment
- **Overall Status**: {going_concern.overall_status.upper()}
- **Overall Financial Health Score**: {((going_concern.liquidity_score + going_concern.solvency_score + going_concern.cash_flow_score) / 3):.1f}/100
- **Liquidity Score**: {going_concern.liquidity_score:.1f}/100
- **Solvency Score**: {going_concern.solvency_score:.1f}/100
- **Cash Flow Score**: {going_concern.cash_flow_score:.1f}/100

### Key Financial Ratios

"""
    
    # Add top ratios by category
    applicable_ratios = [r for r in ratios if r.applicable]
    categories = ['Liquidity', 'Solvency', 'Cash Flow', 'Profitability']
    
    for category in categories:
        category_ratios = [r for r in applicable_ratios if r.category == category]
        if category_ratios:
            report += f"\n#### {category} Ratios\n"
            for ratio in category_ratios[:3]:  # Top 3 per category
                report += f"- **{ratio.ratio_name.replace('_', ' ').title()}**: {ratio.value:.4f} ({ratio.status.title()})\n"
    
    report += f"""

## Key Insights

### Financial Strengths
"""
    
    if going_concern.key_strengths:
        for strength in going_concern.key_strengths[:3]:
            report += f"- {strength}\n"
    
    report += f"""

### Areas for Attention
"""
    
    if going_concern.key_risks:
        for risk in going_concern.key_risks[:3]:
            report += f"- {risk}\n"
    
    report += f"""

### Recommendations
"""
    
    if going_concern.recommendations:
        for rec in going_concern.recommendations[:4]:
            report += f"- {rec}\n"
    
    report += f"""

## Generated Files

### ABCOTD Analysis
- Monthly ABCOTD Line Chart
- ABCOTD Totals Bar Chart
- Individual ABCOTD Charts ({len(abcotd_analyses)} categories)

### Financial Ratio Analysis
- Financial Ratio Dashboard
- Going Concern Assessment Chart
- Comprehensive PDF Report

### Complete Analysis
- This Summary Report
- All Interactive Charts
- Complete Documentation

---
*Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*
"""
    
    # Save report
    report_path = 'bulgarian_complete_financial_analysis_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Comprehensive summary report saved: {report_path}")
    
    return report_path


def main():
    """Main complete analysis function."""
    print("🇧🇬 BULGARIAN COMPLETE FINANCIAL ANALYSIS 2024")
    print("=" * 80)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This will generate ALL reports: ABCOTD analysis + Ratio analysis")
    
    try:
        # Load data
        mapping_df, movements_df, mapping_summary, movements_summary = load_bulgarian_data()
        
        # Map accounts to ABCOTD
        mapped_df = map_accounts_to_abcotd(mapping_df, movements_df)
        
        # Perform ABCOTD analysis
        abcotd_analyses, top_abcotd, monthly_abcotd = perform_abcotd_analysis(mapped_df)
        
        # Perform ratio analysis
        ratios, going_concern = perform_ratio_analysis(mapped_df)
        
        # Create comprehensive charts
        comprehensive_charts = create_comprehensive_charts(abcotd_analyses, top_abcotd, ratios, going_concern)
        
        # Create individual ABCOTD charts
        individual_charts = create_individual_abcotd_charts(abcotd_analyses)
        
        # Generate comprehensive summary report
        summary_report = generate_comprehensive_summary_report(
            mapping_summary, movements_summary, abcotd_analyses, 
            top_abcotd, ratios, going_concern
        )
        
        print(f"\n🎉 COMPLETE BULGARIAN FINANCIAL ANALYSIS FINISHED!")
        print("=" * 80)
        print(f"📊 Generated Files:")
        
        print(f"\n📈 ABCOTD Analysis Charts:")
        print(f"   • {comprehensive_charts.get('abcotd_monthly', 'N/A')}")
        print(f"   • {comprehensive_charts.get('abcotd_totals', 'N/A')}")
        print(f"   • {len(individual_charts)} individual ABCOTD charts")
        
        print(f"\n📊 Financial Ratio Analysis Charts:")
        print(f"   • {comprehensive_charts.get('ratio_dashboard', 'N/A')}")
        print(f"   • {comprehensive_charts.get('going_concern', 'N/A')}")
        
        print(f"\n📄 Summary Reports:")
        print(f"   • {summary_report}")
        
        print(f"\n🎯 Key Results:")
        print(f"   • ABCOTD Categories Analyzed: {len(abcotd_analyses)}")
        print(f"   • Financial Ratios Calculated: {len([r for r in ratios if r.applicable])}")
        print(f"   • Going Concern Status: {going_concern.overall_status.upper()}")
        print(f"   • Overall Financial Health: {((going_concern.liquidity_score + going_concern.solvency_score + going_concern.cash_flow_score) / 3):.1f}/100")
        print(f"   • Total Charts Generated: {len(comprehensive_charts) + len(individual_charts)}")
        
        return {
            'comprehensive_charts': comprehensive_charts,
            'individual_charts': individual_charts,
            'summary_report': summary_report,
            'abcotd_analyses': abcotd_analyses,
            'top_abcotd': top_abcotd,
            'ratios': ratios,
            'going_concern': going_concern
        }
        
    except Exception as e:
        logger.error("Complete Bulgarian analysis failed", error=str(e))
        print(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    results = main()
