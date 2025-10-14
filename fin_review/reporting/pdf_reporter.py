"""PDF summary report generation module."""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import structlog
from pathlib import Path
from typing import Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import pandas as pd
import io

logger = structlog.get_logger()


class PDFReporter:
    """Generates PDF summary report with charts and tables."""
    
    def __init__(self, output_path: Path, config: Optional[Dict] = None):
        """
        Initialize PDF reporter.
        
        Args:
            output_path: Path to output PDF file
            config: Configuration dictionary
        """
        self.output_path = output_path
        self.config = config or {}
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=20
        )
    
    def generate_report(
        self,
        commentary: Dict,
        kpis: Dict,
        aging: Dict,
        anomalies: Dict,
        mapped_data: pd.DataFrame
    ):
        """
        Generate comprehensive PDF report.
        
        Args:
            commentary: Commentary results
            kpis: KPI results
            aging: Aging results
            anomalies: Anomaly results
            mapped_data: Normalized FAGL DataFrame
        """
        logger.info(f"Generating PDF report: {self.output_path}")
        
        # Create PDF document
        doc = SimpleDocTemplate(str(self.output_path), pagesize=letter)
        
        # Build story
        self._add_title_page(commentary)
        self._add_executive_summary(commentary)
        self._add_key_metrics(kpis)
        self._add_monthly_trends_chart(kpis)
        self._add_aging_analysis(aging)
        self._add_top_vendors_chart(mapped_data)
        self._add_anomalies_table(anomalies)
        self._add_recommendations(commentary)
        
        # Build PDF
        doc.build(self.story)
        
        logger.info(f"PDF report generated successfully: {self.output_path}")
    
    def _add_title_page(self, commentary: Dict):
        """Add title page."""
        self.story.append(Spacer(1, 2*inch))
        
        title = Paragraph("Financial Analytical Review", self.title_style)
        self.story.append(title)
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        
        subtitle = Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            subtitle_style
        )
        self.story.append(subtitle)
        
        self.story.append(PageBreak())
    
    def _add_executive_summary(self, commentary: Dict):
        """Add executive summary section."""
        heading = Paragraph("Executive Summary", self.heading_style)
        self.story.append(heading)
        
        exec_summary = commentary.get('executive_summary', '')
        
        # Split into paragraphs and sections
        lines = exec_summary.split('\n')
        current_section = []
        
        for line in lines:
            if line.strip():
                # Check if it's a section header (all caps)
                if line.strip().isupper() and len(line.strip()) > 3:
                    if current_section:
                        p = Paragraph('<br/>'.join(current_section), self.styles['Normal'])
                        self.story.append(p)
                        self.story.append(Spacer(1, 0.15*inch))
                        current_section = []
                    
                    # Add section header
                    section_style = ParagraphStyle(
                        'Section',
                        parent=self.styles['Heading3'],
                        fontSize=12,
                        textColor=colors.HexColor('#1f4788'),
                        spaceAfter=8
                    )
                    p = Paragraph(f"<b>{line.strip()}</b>", section_style)
                    self.story.append(p)
                else:
                    current_section.append(line.strip())
        
        # Add remaining
        if current_section:
            p = Paragraph('<br/>'.join(current_section), self.styles['Normal'])
            self.story.append(p)
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_key_metrics(self, kpis: Dict):
        """Add key metrics table."""
        heading = Paragraph("Key Financial Metrics", self.heading_style)
        self.story.append(heading)
        
        summary_kpis = kpis.get('summary_kpis', {})
        growth_metrics = kpis.get('growth_metrics', {})
        ratios = kpis.get('ratios', {})
        
        # Create table data
        data = [
            ['Metric', 'Value'],
            ['Total Revenue', f"€{summary_kpis.get('total_revenue', 0)/1000:.1f}K"],
            ['Total OPEX', f"€{summary_kpis.get('total_opex', 0)/1000:.1f}K"],
            ['Total Payroll', f"€{summary_kpis.get('total_payroll', 0)/1000:.1f}K"],
            ['Net Profit', f"€{summary_kpis.get('net_profit', 0)/1000:.1f}K"],
            ['Net Margin %', f"{summary_kpis.get('net_margin_pct', 0):.1f}%"],
        ]
        
        if 'latest_revenue_yoy' in growth_metrics:
            data.append(['YoY Revenue Growth', f"{growth_metrics['latest_revenue_yoy']:.1f}%"])
        
        # Create table
        table = Table(data, colWidths=[3.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_monthly_trends_chart(self, kpis: Dict):
        """Add monthly trends chart."""
        monthly_kpis = kpis.get('monthly_kpis', [])
        
        if isinstance(monthly_kpis, list):
            if len(monthly_kpis) == 0:
                return
            monthly_df = pd.DataFrame(monthly_kpis)
        else:
            monthly_df = monthly_kpis
        
        if len(monthly_df) == 0:
            return
        
        heading = Paragraph("Monthly Trends", self.heading_style)
        self.story.append(heading)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(7, 4))
        
        if 'revenue' in monthly_df.columns:
            ax.plot(range(len(monthly_df)), monthly_df['revenue']/1000, 
                   marker='o', label='Revenue', linewidth=2, color='#2ca02c')
        
        if 'opex' in monthly_df.columns:
            ax.plot(range(len(monthly_df)), monthly_df['opex']/1000, 
                   marker='s', label='OPEX', linewidth=2, color='#d62728')
        
        ax.set_xlabel('Month', fontsize=10)
        ax.set_ylabel('Amount (€K)', fontsize=10)
        ax.set_title('Revenue & OPEX Monthly Trends', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Add to PDF
        img = Image(buf, width=6*inch, height=3.5*inch)
        self.story.append(img)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_aging_analysis(self, aging: Dict):
        """Add AR/AP aging analysis."""
        heading = Paragraph("AR/AP Aging Analysis", self.heading_style)
        self.story.append(heading)
        
        # AR Summary
        ar_summary = aging.get('ar_summary', {})
        
        subheading = Paragraph("<b>Accounts Receivable</b>", self.styles['Heading3'])
        self.story.append(subheading)
        
        ar_text = f"""
        <b>Total Outstanding:</b> €{ar_summary.get('total_outstanding', 0)/1000:.1f}K<br/>
        <b>Overdue Percentage:</b> {ar_summary.get('overdue_pct', 0):.1f}%<br/>
        <b>Overdue Amount:</b> €{ar_summary.get('overdue_amount', 0)/1000:.1f}K
        """
        
        p = Paragraph(ar_text, self.styles['Normal'])
        self.story.append(p)
        self.story.append(Spacer(1, 0.2*inch))
        
        # AP Summary
        ap_summary = aging.get('ap_summary', {})
        
        subheading = Paragraph("<b>Accounts Payable</b>", self.styles['Heading3'])
        self.story.append(subheading)
        
        ap_text = f"""
        <b>Total Outstanding:</b> €{ap_summary.get('total_outstanding', 0)/1000:.1f}K<br/>
        <b>Overdue Percentage:</b> {ap_summary.get('overdue_pct', 0):.1f}%<br/>
        <b>Overdue Amount:</b> €{ap_summary.get('overdue_amount', 0)/1000:.1f}K
        """
        
        p = Paragraph(ap_text, self.styles['Normal'])
        self.story.append(p)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_top_vendors_chart(self, mapped_data: pd.DataFrame):
        """Add top vendors bar chart."""
        if 'customer_vendor' not in mapped_data.columns:
            return
        
        heading = Paragraph("Top 10 Vendors by Spend", self.heading_style)
        self.story.append(heading)
        
        # Get top vendors
        opex_data = mapped_data[mapped_data['type'] == 'OPEX']
        if len(opex_data) == 0:
            return
        
        top_vendors = opex_data.groupby('customer_vendor')['amount'].sum().abs().nlargest(10)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(range(len(top_vendors)), top_vendors.values/1000, color='#1f77b4')
        ax.set_yticks(range(len(top_vendors)))
        ax.set_yticklabels(top_vendors.index)
        ax.set_xlabel('Amount (€K)', fontsize=10)
        ax.set_title('Top 10 Vendors by Spend', fontsize=12, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Add to PDF
        img = Image(buf, width=6*inch, height=3.5*inch)
        self.story.append(img)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_anomalies_table(self, anomalies: Dict):
        """Add anomalies table."""
        anomaly_list = anomalies.get('anomalies', [])
        
        if not anomaly_list:
            return
        
        heading = Paragraph("Detected Anomalies (Top 10)", self.heading_style)
        self.story.append(heading)
        
        # Prepare table data
        data = [['Date', 'Bucket', 'Deviation %', 'Severity']]
        
        for anomaly in anomaly_list[:10]:
            if hasattr(anomaly, '__dict__'):
                anom_dict = anomaly.__dict__
            else:
                anom_dict = anomaly
            
            data.append([
                str(anom_dict.get('date', '')),
                str(anom_dict.get('bucket', ''))[:30],
                f"{anom_dict.get('deviation_pct', 0):.1f}%",
                str(anom_dict.get('severity', '')).upper()
            ])
        
        # Create table
        table = Table(data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_recommendations(self, commentary: Dict):
        """Add recommendations section."""
        heading = Paragraph("Actionable Recommendations", self.heading_style)
        self.story.append(heading)
        
        recommendations = commentary.get('recommendations', [])
        
        for i, rec in enumerate(recommendations[:5], 1):
            # Handle both Commentary objects and dicts
            if hasattr(rec, 'title'):
                rec_title = f"<b>{i}. {rec.title}</b>"
                rec_content = rec.content
            elif isinstance(rec, dict):
                rec_title = f"<b>{i}. {rec.get('title', 'Recommendation')}</b>"
                rec_content = rec.get('content', '')
            else:
                continue
            
            p_title = Paragraph(rec_title, self.styles['Normal'])
            self.story.append(p_title)
            
            p_content = Paragraph(rec_content, self.styles['Normal'])
            self.story.append(p_content)
            self.story.append(Spacer(1, 0.15*inch))


def generate_pdf_report(
    output_path: Path,
    commentary: Dict,
    kpis: Dict,
    aging: Dict,
    anomalies: Dict,
    mapped_data: pd.DataFrame,
    config: Optional[Dict] = None
):
    """
    Convenience function to generate PDF report.
    
    Args:
        output_path: Path to output PDF file
        commentary: Commentary results
        kpis: KPI results
        aging: Aging results
        anomalies: Anomaly results
        mapped_data: Normalized FAGL DataFrame
        config: Configuration dictionary
    """
    reporter = PDFReporter(output_path, config)
    reporter.generate_report(commentary, kpis, aging, anomalies, mapped_data)

