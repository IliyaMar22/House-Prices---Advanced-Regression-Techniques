"""Detailed Bulgarian ABCOTD Analysis with PDF Report Generation."""

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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import base64
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


def load_bulgarian_data():
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
    
    # Load movements data (full dataset)
    movements_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/movements 2024.XLSX')
    print(f"📋 Loading movements data from: {movements_file}")
    print("⚠️  Loading full dataset (610,333 rows) - this will take time...")
    
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
    
    return mapped_df


def analyze_individual_abcotd(mapped_df):
    """Analyze each ABCOTD category individually."""
    print("\n📈 ANALYZING INDIVIDUAL ABCOTD CATEGORIES")
    print("-" * 50)
    
    # Create monthly aggregation
    mapped_df['year_month'] = mapped_df['posting_date'].dt.to_period('M').astype(str)
    
    # Get all ABCOTD categories with their totals
    abcotd_totals = mapped_df.groupby('ABCOTD')['amount'].sum().abs().sort_values(ascending=False)
    
    print(f"📊 Found {len(abcotd_totals)} ABCOTD categories")
    
    # Create individual analysis for each ABCOTD
    abcotd_analyses = {}
    
    for abcotd in abcotd_totals.index:
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
    
    return abcotd_analyses, abcotd_totals


def create_abcotd_charts(abcotd_analyses):
    """Create individual charts for each ABCOTD category."""
    print("\n📊 CREATING INDIVIDUAL ABCOTD CHARTS")
    print("-" * 50)
    
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
            title=f'{abcotd} - Monthly Analysis 2024',
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
        chart_file = f'bulgarian_abcotd_{safe_abcotd}.html'
        fig.write_html(chart_file)
        chart_files[abcotd] = chart_file
        
        print(f"     ✅ Saved: {chart_file}")
    
    return chart_files


def create_matplotlib_charts_for_pdf(abcotd_analyses):
    """Create matplotlib charts for PDF embedding."""
    print("\n📊 CREATING MATPLOTLIB CHARTS FOR PDF")
    print("-" * 50)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    
    chart_images = {}
    
    for i, (abcotd, analysis) in enumerate(abcotd_analyses.items(), 1):
        print(f"   Creating PDF chart for {i}/{len(abcotd_analyses)}: {abcotd}")
        
        monthly_data = analysis['monthly_data']
        
        if len(monthly_data) == 0:
            continue
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f'{abcotd} - Monthly Analysis 2024', fontsize=16, fontweight='bold')
        
        # Line chart for amounts
        ax1.plot(monthly_data['year_month'], monthly_data['total_amount'], 
                marker='o', linewidth=3, markersize=8, color='#1f77b4')
        ax1.set_title('Monthly Amount Trend', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Amount (лв)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # Format y-axis for amounts
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'лв {x:,.0f}'))
        
        # Bar chart for transaction counts
        ax2.bar(monthly_data['year_month'], monthly_data['transaction_count'], 
               color='#ff7f0e', alpha=0.8)
        ax2.set_title('Monthly Transaction Count', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Month', fontsize=12)
        ax2.set_ylabel('Transaction Count', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Convert to base64 string for PDF
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        chart_images[abcotd] = image_base64
        plt.close(fig)
        
        print(f"     ✅ Created PDF chart for: {abcotd}")
    
    return chart_images


def generate_comprehensive_pdf(abcotd_analyses, abcotd_totals, chart_images, mapping_summary, movements_summary):
    """Generate comprehensive PDF report."""
    print("\n📄 GENERATING COMPREHENSIVE PDF REPORT")
    print("-" * 50)
    
    # Create PDF document
    pdf_file = 'bulgarian_abcotd_detailed_analysis.pdf'
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.darkgreen
    )
    
    # Build PDF content
    story = []
    
    # Title page
    story.append(Paragraph("Bulgarian Financial Analysis 2024", title_style))
    story.append(Paragraph("ABCOTD Detailed Analysis Report", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Executive summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_text = f"""
    This comprehensive report analyzes the complete 2024 financial chronology covering {movements_summary['total_transactions']:,} transactions 
    across {movements_summary['unique_accounts']:,} GL accounts. The analysis maps {mapping_summary['total_accounts']:,} accounts to 
    {len(abcotd_totals)} ABCOTD categories, providing detailed monthly breakdowns for each category.
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Data overview
    story.append(Paragraph("Data Overview", heading_style))
    overview_text = f"""
    <b>Total Transactions:</b> {movements_summary['total_transactions']:,}<br/>
    <b>Date Range:</b> {movements_summary['date_range']['start'].strftime('%B %d, %Y')} to {movements_summary['date_range']['end'].strftime('%B %d, %Y')}<br/>
    <b>Unique Accounts:</b> {movements_summary['unique_accounts']:,}<br/>
    <b>Currency:</b> {movements_summary['currency']}<br/>
    <b>Company:</b> {movements_summary['company_code']}<br/>
    <b>ABCOTD Categories:</b> {len(abcotd_totals)}<br/>
    """
    story.append(Paragraph(overview_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # ABCOTD summary table
    story.append(Paragraph("ABCOTD Categories Summary", heading_style))
    summary_table = "ABCOTD Category | Total Amount (лв) | Transactions | Accounts\n"
    summary_table += "-" * 80 + "\n"
    
    for abcotd, total in abcotd_totals.head(20).items():
        analysis = abcotd_analyses[abcotd]
        summary_table += f"{abcotd[:30]:30s} | {total:>15,.0f} | {analysis['total_transactions']:>11,} | {analysis['unique_accounts']:>7}\n"
    
    story.append(Paragraph(summary_table.replace('\n', '<br/>'), styles['Normal']))
    story.append(PageBreak())
    
    # Individual ABCOTD analysis
    story.append(Paragraph("Individual ABCOTD Analysis", heading_style))
    story.append(Spacer(1, 20))
    
    for i, (abcotd, total) in enumerate(abcotd_totals.items(), 1):
        print(f"   Adding to PDF: {i}/{len(abcotd_totals)} - {abcotd}")
        
        analysis = abcotd_analyses[abcotd]
        
        # ABCOTD header
        story.append(Paragraph(f"{i}. {abcotd}", heading_style))
        
        # ABCOTD details
        details_text = f"""
        <b>Total Amount:</b> лв {analysis['total_amount']:,.2f}<br/>
        <b>Total Transactions:</b> {analysis['total_transactions']:,}<br/>
        <b>Unique Accounts:</b> {analysis['unique_accounts']}<br/>
        <b>Date Range:</b> {analysis['date_range']}<br/>
        <b>Average Transaction:</b> лв {analysis['total_amount']/analysis['total_transactions']:,.2f}<br/>
        """
        story.append(Paragraph(details_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add chart if available
        if abcotd in chart_images:
            try:
                # Convert base64 to image
                img_data = base64.b64decode(chart_images[abcotd])
                img_buffer = io.BytesIO(img_data)
                
                # Create image with appropriate size
                img = Image(img_buffer, width=7*inch, height=5*inch)
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception as e:
                print(f"     ⚠️  Could not add chart for {abcotd}: {e}")
                story.append(Paragraph(f"[Chart for {abcotd} - Error in generation]", styles['Normal']))
        
        # Monthly data table
        monthly_data = analysis['monthly_data']
        if len(monthly_data) > 0:
            story.append(Paragraph("Monthly Breakdown", subheading_style))
            
            # Create monthly table
            monthly_table = "Month | Amount (лв) | Transactions | Accounts\n"
            monthly_table += "-" * 60 + "\n"
            
            for _, row in monthly_data.iterrows():
                monthly_table += f"{row['year_month']:6s} | {row['total_amount']:>12,.0f} | {row['transaction_count']:>11,} | {row['unique_accounts']:>7}\n"
            
            story.append(Paragraph(monthly_table.replace('\n', '<br/>'), styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Add page break every 3 ABCOTD categories
        if i % 3 == 0:
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    
    print(f"✅ PDF report generated: {pdf_file}")
    return pdf_file


def main():
    """Main analysis function."""
    print("🇧🇬 BULGARIAN DETAILED ABCOTD ANALYSIS 2024")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load data
        mapping_df, movements_df, mapping_summary, movements_summary = load_bulgarian_data()
        
        # Map accounts to ABCOTD
        mapped_df = map_accounts_to_abcotd(mapping_df, movements_df)
        
        # Analyze individual ABCOTD categories
        abcotd_analyses, abcotd_totals = analyze_individual_abcotd(mapped_df)
        
        # Create individual charts
        chart_files = create_abcotd_charts(abcotd_analyses)
        
        # Create matplotlib charts for PDF
        chart_images = create_matplotlib_charts_for_pdf(abcotd_analyses)
        
        # Generate comprehensive PDF
        pdf_file = generate_comprehensive_pdf(abcotd_analyses, abcotd_totals, chart_images, mapping_summary, movements_summary)
        
        print(f"\n🎉 DETAILED BULGARIAN ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Generated Files:")
        print(f"   • {pdf_file} (Comprehensive PDF report)")
        print(f"   • {len(chart_files)} individual ABCOTD HTML charts")
        print(f"\n✨ Open the PDF file to view the complete analysis!")
        print(f"✨ Open HTML files for interactive charts!")
        
        return {
            'pdf_file': pdf_file,
            'chart_files': chart_files,
            'abcotd_analyses': abcotd_analyses,
            'abcotd_totals': abcotd_totals
        }
        
    except Exception as e:
        logger.error("Detailed Bulgarian analysis failed", error=str(e))
        print(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    results = main()
