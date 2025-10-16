"""Comprehensive Bulgarian Financial Ratio Analysis with Going Concern Assessment."""

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
    print("🇧🇬 LOADING BULGARIAN FINANCIAL DATA FOR RATIO ANALYSIS")
    print("=" * 70)
    
    # Load mapping data
    mapping_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/Mapping export.xlsx')
    print(f"📊 Loading mapping data from: {mapping_file}")
    
    mapping_loader = BulgarianMappingLoader(mapping_file, None)
    mapping_df = mapping_loader.load()
    mapping_summary = mapping_loader.get_bulgarian_summary()
    
    print(f"✅ Mapping loaded: {mapping_summary['total_accounts']:,} accounts")
    
    # Load movements data (full dataset)
    movements_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/movements 2024.XLSX')
    print(f"📋 Loading movements data from: {movements_file}")
    print("⚠️  Loading full dataset (610,333 rows) for comprehensive ratio analysis...")
    
    movements_loader = BulgarianFAGLLoader(movements_file, None)
    movements_df = movements_loader.load()  # Full dataset
    movements_summary = movements_loader.get_summary()
    
    print(f"✅ Movements loaded: {movements_summary['total_transactions']:,} transactions")
    print(f"   Date range: {movements_summary['date_range']['start'].strftime('%Y-%m-%d')} to {movements_summary['date_range']['end'].strftime('%Y-%m-%d')}")
    
    return mapping_df, movements_df, mapping_summary, movements_summary


def map_accounts_to_abcotd(mapping_df, movements_df):
    """Map movements accounts to ABCOTD classifications."""
    print("\n🔗 MAPPING ACCOUNTS TO ABCOTD FOR RATIO ANALYSIS")
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
    
    print(f"📊 Mapping Results for Ratio Analysis:")
    print(f"   Total transactions: {total_transactions:,}")
    print(f"   Mapped transactions: {mapped_transactions:,} ({mapped_transactions/total_transactions*100:.1f}%)")
    print(f"   Unmapped transactions: {unmapped_transactions:,} ({unmapped_transactions/total_transactions*100:.1f}%)")
    
    return mapped_df


def perform_ratio_analysis(mapped_df):
    """Perform comprehensive financial ratio analysis."""
    print("\n📊 PERFORMING COMPREHENSIVE FINANCIAL RATIO ANALYSIS")
    print("-" * 50)
    
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


def create_ratio_visualizations(ratios, going_concern):
    """Create comprehensive ratio visualizations."""
    print("\n📈 CREATING RATIO VISUALIZATION CHARTS")
    print("-" * 50)
    
    applicable_ratios = [r for r in ratios if r.applicable]
    
    # Create ratio dashboard
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
        title='Bulgarian Financial Ratio Analysis Dashboard 2024',
        title_font_size=16,
        height=800,
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(title_text="Ratio Value", row=2, col=1)
    
    # Save dashboard
    dashboard_file = 'bulgarian_ratio_analysis_dashboard.html'
    fig.write_html(dashboard_file)
    print(f"✅ Ratio dashboard saved: {dashboard_file}")
    
    # Create going concern assessment chart
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
        title='Going Concern Assessment Scores',
        xaxis_title='Financial Health Categories',
        yaxis_title='Score (0-100)',
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    # Add benchmark lines
    fig_gc.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="Strong")
    fig_gc.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Adequate")
    fig_gc.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Concerning")
    
    # Save going concern chart
    gc_file = 'bulgarian_going_concern_assessment.html'
    fig_gc.write_html(gc_file)
    print(f"✅ Going concern chart saved: {gc_file}")
    
    return dashboard_file, gc_file


def create_matplotlib_charts_for_pdf(ratios, going_concern):
    """Create matplotlib charts for PDF embedding."""
    print("\n📊 CREATING MATPLOTLIB CHARTS FOR PDF")
    print("-" * 50)
    
    plt.style.use('seaborn-v0_8')
    chart_images = {}
    
    # Create ratio summary chart
    applicable_ratios = [r for r in ratios if r.applicable]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Group by category and status
    categories = ['Liquidity', 'Solvency', 'Cash Flow', 'Profitability', 'Efficiency']
    status_counts = {cat: {'excellent': 0, 'good': 0, 'warning': 0, 'critical': 0} for cat in categories}
    
    for ratio in applicable_ratios:
        if ratio.category in status_counts:
            status_counts[ratio.category][ratio.status] += 1
    
    # Create stacked bar chart
    bottom = np.zeros(len(categories))
    colors = {'excellent': '#2E8B57', 'good': '#32CD32', 'warning': '#FFD700', 'critical': '#DC143C'}
    
    for status in ['excellent', 'good', 'warning', 'critical']:
        values = [status_counts[cat][status] for cat in categories]
        ax.bar(categories, values, bottom=bottom, label=status.title(), color=colors[status])
        bottom += values
    
    ax.set_title('Financial Ratio Analysis by Category and Status', fontsize=16, fontweight='bold')
    ax.set_ylabel('Number of Ratios', fontsize=12)
    ax.legend(title='Status')
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    chart_images['ratio_summary'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    # Create going concern scores chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Liquidity', 'Solvency', 'Cash Flow']
    scores = [going_concern.liquidity_score, going_concern.solvency_score, going_concern.cash_flow_score]
    colors_gc = ['#2E8B57' if score >= 75 else '#32CD32' if score >= 50 else '#FFD700' if score >= 25 else '#DC143C' for score in scores]
    
    bars = ax.bar(categories, scores, color=colors_gc)
    ax.set_title('Going Concern Assessment Scores', fontsize=16, fontweight='bold')
    ax.set_ylabel('Score (0-100)', fontsize=12)
    ax.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, score in zip(bars, scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{score:.1f}/100', ha='center', va='bottom', fontweight='bold')
    
    # Add benchmark lines
    ax.axhline(y=75, color='green', linestyle='--', alpha=0.7, label='Strong')
    ax.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Adequate')
    ax.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Concerning')
    ax.legend()
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    chart_images['going_concern'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    print(f"✅ Created {len(chart_images)} charts for PDF embedding")
    
    return chart_images


def generate_comprehensive_ratio_pdf(ratios, going_concern, chart_images, movements_summary):
    """Generate comprehensive ratio analysis PDF report."""
    print("\n📄 GENERATING COMPREHENSIVE RATIO ANALYSIS PDF REPORT")
    print("-" * 50)
    
    # Create PDF document
    pdf_file = 'bulgarian_financial_ratio_analysis.pdf'
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
    story.append(Paragraph("Bulgarian Financial Ratio Analysis 2024", title_style))
    story.append(Paragraph("Comprehensive Going Concern Assessment", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Executive summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_text = f"""
    This comprehensive financial ratio analysis covers the complete 2024 financial chronology with {movements_summary['total_transactions']:,} transactions.
    The analysis calculates {len([r for r in ratios if r.applicable])} applicable financial ratios across liquidity, solvency, cash flow, 
    profitability, and efficiency categories to assess the entity's going concern status.
    
    <b>Going Concern Assessment: {going_concern.overall_status.upper()}</b><br/>
    <b>Overall Financial Health Score: {((going_concern.liquidity_score + going_concern.solvency_score + going_concern.cash_flow_score) / 3):.1f}/100</b>
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Going concern assessment
    story.append(Paragraph("Going Concern Assessment", heading_style))
    gc_text = f"""
    <b>Overall Status:</b> {going_concern.overall_status.upper()}<br/>
    <b>Liquidity Score:</b> {going_concern.liquidity_score:.1f}/100<br/>
    <b>Solvency Score:</b> {going_concern.solvency_score:.1f}/100<br/>
    <b>Cash Flow Score:</b> {going_concern.cash_flow_score:.1f}/100<br/>
    """
    story.append(Paragraph(gc_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Key risks
    if going_concern.key_risks:
        story.append(Paragraph("Key Financial Risks", subheading_style))
        for risk in going_concern.key_risks:
            story.append(Paragraph(f"• {risk}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Key strengths
    if going_concern.key_strengths:
        story.append(Paragraph("Key Financial Strengths", subheading_style))
        for strength in going_concern.key_strengths:
            story.append(Paragraph(f"• {strength}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Recommendations
    if going_concern.recommendations:
        story.append(Paragraph("Key Recommendations", subheading_style))
        for rec in going_concern.recommendations:
            story.append(Paragraph(f"• {rec}", styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Add charts
    if 'ratio_summary' in chart_images:
        try:
            img_data = base64.b64decode(chart_images['ratio_summary'])
            img_buffer = io.BytesIO(img_data)
            img = Image(img_buffer, width=7*inch, height=5*inch)
            story.append(img)
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"     ⚠️  Could not add ratio summary chart: {e}")
    
    if 'going_concern' in chart_images:
        try:
            img_data = base64.b64decode(chart_images['going_concern'])
            img_buffer = io.BytesIO(img_data)
            img = Image(img_buffer, width=7*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"     ⚠️  Could not add going concern chart: {e}")
    
    story.append(PageBreak())
    
    # Detailed ratio analysis by category
    categories = ['Liquidity', 'Solvency', 'Cash Flow', 'Profitability', 'Efficiency']
    
    for category in categories:
        category_ratios = [r for r in ratios if r.category == category and r.applicable]
        
        if category_ratios:
            story.append(Paragraph(f"{category} Ratios", heading_style))
            story.append(Spacer(1, 12))
            
            # Create ratio table
            table_data = [['Ratio', 'Value', 'Benchmark', 'Status', 'Interpretation']]
            
            for ratio in category_ratios:
                status_colors = {
                    'excellent': 'green',
                    'good': 'lime',
                    'warning': 'orange', 
                    'critical': 'red'
                }
                
                table_data.append([
                    ratio.ratio_name.replace('_', ' ').title(),
                    f"{ratio.value:.4f}",
                    ratio.benchmark,
                    ratio.status.title(),
                    ratio.interpretation[:100] + "..." if len(ratio.interpretation) > 100 else ratio.interpretation
                ])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
    
    # Detailed going concern analysis
    story.append(Paragraph("Detailed Going Concern Analysis", heading_style))
    story.append(Paragraph(going_concern.detailed_analysis, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    
    print(f"✅ Comprehensive ratio analysis PDF generated: {pdf_file}")
    return pdf_file


def main():
    """Main ratio analysis function."""
    print("🇧🇬 BULGARIAN FINANCIAL RATIO ANALYSIS 2024")
    print("=" * 70)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load data
        mapping_df, movements_df, mapping_summary, movements_summary = load_bulgarian_data()
        
        # Map accounts to ABCOTD
        mapped_df = map_accounts_to_abcotd(mapping_df, movements_df)
        
        # Perform ratio analysis
        ratios, going_concern = perform_ratio_analysis(mapped_df)
        
        # Create visualizations
        dashboard_file, gc_file = create_ratio_visualizations(ratios, going_concern)
        
        # Create matplotlib charts for PDF
        chart_images = create_matplotlib_charts_for_pdf(ratios, going_concern)
        
        # Generate comprehensive PDF
        pdf_file = generate_comprehensive_ratio_pdf(ratios, going_concern, chart_images, movements_summary)
        
        print(f"\n🎉 COMPREHENSIVE RATIO ANALYSIS COMPLETE!")
        print("=" * 70)
        print(f"📊 Generated Files:")
        print(f"   • {pdf_file} (Comprehensive ratio analysis report)")
        print(f"   • {dashboard_file} (Interactive ratio dashboard)")
        print(f"   • {gc_file} (Going concern assessment)")
        print(f"\n🎯 Key Results:")
        print(f"   • Going Concern Status: {going_concern.overall_status.upper()}")
        print(f"   • Liquidity Score: {going_concern.liquidity_score:.1f}/100")
        print(f"   • Solvency Score: {going_concern.solvency_score:.1f}/100")
        print(f"   • Cash Flow Score: {going_concern.cash_flow_score:.1f}/100")
        print(f"   • Ratios Calculated: {len([r for r in ratios if r.applicable])}")
        print(f"   • Key Risks Identified: {len(going_concern.key_risks)}")
        print(f"   • Recommendations Provided: {len(going_concern.recommendations)}")
        
        return {
            'pdf_file': pdf_file,
            'dashboard_file': dashboard_file,
            'gc_file': gc_file,
            'ratios': ratios,
            'going_concern': going_concern
        }
        
    except Exception as e:
        logger.error("Bulgarian ratio analysis failed", error=str(e))
        print(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    results = main()
