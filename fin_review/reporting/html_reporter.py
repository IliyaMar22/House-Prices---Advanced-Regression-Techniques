"""HTML summary report with interactive charts."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import structlog
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

logger = structlog.get_logger()


class HTMLReporter:
    """Generates interactive HTML summary report."""
    
    def __init__(self, output_path: Path, config: Optional[Dict] = None):
        """Initialize HTML reporter."""
        self.output_path = output_path
        self.config = config or {}
    
    def generate_report(
        self,
        commentary: Dict,
        kpis: Dict,
        trends: Dict,
        aging: Dict,
        anomalies: Dict,
        mapped_data: pd.DataFrame
    ):
        """Generate HTML report with interactive charts."""
        logger.info(f"Generating HTML report: {self.output_path}")
        
        html_content = self._build_html(commentary, kpis, trends, aging, anomalies, mapped_data)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated successfully: {self.output_path}")
    
    def _build_html(self, commentary, kpis, trends, aging, anomalies, mapped_data):
        """Build complete HTML document."""
        
        # Create charts
        monthly_chart = self._create_monthly_trends_chart(kpis)
        aging_chart = self._create_aging_chart(aging)
        top_vendors_chart = self._create_top_vendors_chart(mapped_data)
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Financial Review Summary</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #1f4788;
            border-bottom: 3px solid #1f4788;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 30px;
            border-left: 4px solid #2c5aa0;
            padding-left: 15px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .insight-box {{
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .risk-box {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .recommendation-box {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .confidence {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .confidence-high {{
            background-color: #4caf50;
            color: white;
        }}
        .confidence-medium {{
            background-color: #ff9800;
            color: white;
        }}
        .confidence-low {{
            background-color: #9e9e9e;
            color: white;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .chart-container {{
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Financial Analytical Review</h1>
        <p style="color: #666; font-size: 0.9em;">Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        
        {self._build_metrics_section(kpis)}
        
        <h2>📈 Monthly Trends</h2>
        <div class="chart-container">
            {monthly_chart}
        </div>
        
        <h2>💡 Key Insights</h2>
        {self._build_insights_section(commentary)}
        
        <h2>⚠️ Risks & Concerns</h2>
        {self._build_risks_section(commentary)}
        
        <h2>📅 AR/AP Aging Analysis</h2>
        <div class="chart-container">
            {aging_chart}
        </div>
        {self._build_aging_summary(aging)}
        
        <h2>🏢 Top Vendors</h2>
        <div class="chart-container">
            {top_vendors_chart}
        </div>
        
        <h2>🎯 Actionable Recommendations</h2>
        {self._build_recommendations_section(commentary)}
        
        <div class="footer">
            <p>Financial Review Pipeline v1.0.0</p>
            <p>For detailed analysis, see the Excel workbook and PowerPoint presentation</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _build_metrics_section(self, kpis):
        """Build metrics cards section."""
        summary_kpis = kpis.get('summary_kpis', {})
        growth_metrics = kpis.get('growth_metrics', {})
        
        total_revenue = summary_kpis.get('total_revenue', 0)
        total_opex = summary_kpis.get('total_opex', 0)
        net_profit = summary_kpis.get('net_profit', 0)
        yoy_growth = growth_metrics.get('latest_revenue_yoy', 0)
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value">€{total_revenue/1000:.1f}K</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total OPEX</div>
                <div class="metric-value">€{abs(total_opex)/1000:.1f}K</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Net Profit</div>
                <div class="metric-value">€{net_profit/1000:.1f}K</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">YoY Growth</div>
                <div class="metric-value">{yoy_growth:.1f}%</div>
            </div>
        </div>
        """
    
    def _create_monthly_trends_chart(self, kpis):
        """Create monthly trends Plotly chart."""
        monthly_kpis = kpis.get('monthly_kpis', [])
        
        if isinstance(monthly_kpis, list):
            if len(monthly_kpis) == 0:
                return "<p>No monthly data available</p>"
            monthly_df = pd.DataFrame(monthly_kpis)
        else:
            monthly_df = monthly_kpis
        
        if len(monthly_df) == 0:
            return "<p>No monthly data available</p>"
        
        fig = go.Figure()
        
        # Convert year_month to string for x-axis
        if 'year_month' in monthly_df.columns:
            x_values = [str(d) for d in monthly_df['year_month']]
        else:
            x_values = list(range(len(monthly_df)))
        
        if 'revenue' in monthly_df.columns:
            fig.add_trace(go.Scatter(
                x=x_values,
                y=monthly_df['revenue']/1000,
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=8)
            ))
        
        if 'opex' in monthly_df.columns:
            fig.add_trace(go.Scatter(
                x=x_values,
                y=monthly_df['opex'].abs()/1000,
                mode='lines+markers',
                name='OPEX',
                line=dict(color='#d62728', width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Revenue & OPEX Monthly Trends",
            xaxis_title="Month",
            yaxis_title="Amount (€K)",
            hovermode='x unified',
            height=400,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='monthly_trends')
    
    def _create_aging_chart(self, aging):
        """Create AR/AP aging chart."""
        ar_aging = aging.get('ar_aging', [])
        
        if isinstance(ar_aging, list):
            if len(ar_aging) == 0:
                return "<p>No aging data available</p>"
            ar_df = pd.DataFrame(ar_aging)
        else:
            ar_df = ar_aging
        
        if len(ar_df) == 0:
            return "<p>No aging data available</p>"
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=ar_df['aging_bucket'],
            y=ar_df['outstanding_amount']/1000,
            name='AR Outstanding',
            marker_color='#1f77b4',
            text=[f"€{v/1000:.1f}K" for v in ar_df['outstanding_amount']],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Accounts Receivable Aging",
            xaxis_title="Aging Bucket",
            yaxis_title="Amount (€K)",
            height=400,
            template='plotly_white'
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='ar_aging')
    
    def _create_top_vendors_chart(self, mapped_data):
        """Create top vendors bar chart."""
        if 'customer_vendor' not in mapped_data.columns:
            return "<p>No vendor data available</p>"
        
        opex_data = mapped_data[mapped_data['type'] == 'OPEX']
        if len(opex_data) == 0:
            return "<p>No OPEX data available</p>"
        
        top_vendors = opex_data.groupby('customer_vendor')['amount'].sum().abs().nlargest(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=top_vendors.index,
            x=top_vendors.values/1000,
            orientation='h',
            marker_color='#ff7f0e',
            text=[f"€{v/1000:.1f}K" for v in top_vendors.values],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Top 10 Vendors by Spend",
            xaxis_title="Amount (€K)",
            yaxis_title="Vendor",
            height=400,
            template='plotly_white'
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='top_vendors')
    
    def _build_insights_section(self, commentary):
        """Build insights section."""
        insights = commentary.get('insights', [])
        
        html = ""
        for insight in insights[:5]:
            # Handle both objects and dicts
            if hasattr(insight, 'title'):
                title = insight.title
                content = insight.content
                confidence = insight.confidence
            elif isinstance(insight, dict):
                title = insight.get('title', 'Insight')
                content = insight.get('content', '')
                confidence = insight.get('confidence', 'medium')
            else:
                continue
            
            conf_class = f"confidence confidence-{confidence}"
            html += f"""
            <div class="insight-box">
                <strong>{title}</strong>
                <span class="{conf_class}">{confidence.upper()}</span>
                <p>{content}</p>
            </div>
            """
        
        return html if html else "<p>No insights generated</p>"
    
    def _build_risks_section(self, commentary):
        """Build risks section."""
        risks = commentary.get('risks', [])
        
        html = ""
        for risk in risks[:5]:
            # Handle both objects and dicts
            if hasattr(risk, 'title'):
                title = risk.title
                content = risk.content
                confidence = risk.confidence
            elif isinstance(risk, dict):
                title = risk.get('title', 'Risk')
                content = risk.get('content', '')
                confidence = risk.get('confidence', 'medium')
            else:
                continue
            
            conf_class = f"confidence confidence-{confidence}"
            html += f"""
            <div class="risk-box">
                <strong>{title}</strong>
                <span class="{conf_class}">{confidence.upper()}</span>
                <p>{content}</p>
            </div>
            """
        
        return html if html else "<p>No risks identified</p>"
    
    def _build_aging_summary(self, aging):
        """Build aging summary tables."""
        ar_summary = aging.get('ar_summary', {})
        ap_summary = aging.get('ap_summary', {})
        
        ar_outstanding = ar_summary.get('total_outstanding', 0)
        ar_overdue_pct = ar_summary.get('overdue_pct', 0)
        
        ap_outstanding = ap_summary.get('total_outstanding', 0)
        ap_overdue_pct = ap_summary.get('overdue_pct', 0)
        
        return f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            <div style="background: #e3f2fd; padding: 20px; border-radius: 8px;">
                <h3 style="color: #1976d2; margin-top: 0;">Accounts Receivable</h3>
                <p><strong>Total Outstanding:</strong> €{ar_outstanding/1000:.1f}K</p>
                <p><strong>Overdue:</strong> {ar_overdue_pct:.1f}%</p>
            </div>
            <div style="background: #fce4ec; padding: 20px; border-radius: 8px;">
                <h3 style="color: #c2185b; margin-top: 0;">Accounts Payable</h3>
                <p><strong>Total Outstanding:</strong> €{abs(ap_outstanding)/1000:.1f}K</p>
                <p><strong>Overdue:</strong> {ap_overdue_pct:.1f}%</p>
            </div>
        </div>
        """
    
    def _build_recommendations_section(self, commentary):
        """Build recommendations section."""
        recommendations = commentary.get('recommendations', [])
        
        html = ""
        for i, rec in enumerate(recommendations[:5], 1):
            # Handle both objects and dicts
            if hasattr(rec, 'title'):
                title = rec.title
                content = rec.content
            elif isinstance(rec, dict):
                title = rec.get('title', 'Recommendation')
                content = rec.get('content', '')
            else:
                continue
            
            html += f"""
            <div class="recommendation-box">
                <strong>{i}. {title}</strong>
                <p>{content}</p>
            </div>
            """
        
        return html if html else "<p>No recommendations generated</p>"


def generate_html_report(
    output_path: Path,
    commentary: Dict,
    kpis: Dict,
    trends: Dict,
    aging: Dict,
    anomalies: Dict,
    mapped_data: pd.DataFrame,
    config: Optional[Dict] = None
):
    """Generate HTML report."""
    reporter = HTMLReporter(output_path, config)
    reporter.generate_report(commentary, kpis, trends, aging, anomalies, mapped_data)

