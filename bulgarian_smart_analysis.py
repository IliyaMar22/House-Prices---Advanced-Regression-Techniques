"""
Bulgarian Financial Analysis with Intelligent Insights (Lightweight).

This script performs comprehensive financial analysis using rule-based AI instead of
heavy LLM models, making it suitable for systems with limited RAM/CPU.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import structlog
from datetime import datetime
import warnings
import json
warnings.filterwarnings('ignore')

# Import our modules
import sys
sys.path.append('.')
from fin_review.loaders.bulgarian_mapping_loader import BulgarianMappingLoader
from fin_review.loaders.bulgarian_fagl_loader import BulgarianFAGLLoader
from fin_review.analytics.ratio_analyzer import analyze_financial_ratios
from fin_review.analytics.intelligent_insights import FinancialInsightsGenerator

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def load_bulgarian_data():
    """Load Bulgarian mapping and movements data."""
    print("\n🇧🇬 LOADING BULGARIAN FINANCIAL DATA")
    print("=" * 80)
    
    # Load mapping data
    mapping_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/Mapping export.xlsx')
    print(f"📊 Loading mapping data from: {mapping_file}")
    
    mapping_loader = BulgarianMappingLoader(mapping_file, None)
    mapping_df = mapping_loader.load()
    mapping_summary = mapping_loader.get_bulgarian_summary()
    
    print(f"✅ Mapping loaded: {mapping_summary['total_accounts']:,} accounts")
    
    # Load movements data (full dataset)
    movements_file = Path('/Users/bilyana/Desktop/Chronology & Mapping/movements 2024.XLSX')
    print(f"📈 Loading movements data from: {movements_file}")
    
    fagl_loader = BulgarianFAGLLoader(movements_file, None)
    fagl_df = fagl_loader.load()
    
    print(f"✅ Movements loaded: {len(fagl_df):,} transactions")
    
    return mapping_df, fagl_df, mapping_summary


def map_and_analyze_data(mapping_df, fagl_df):
    """Map GL accounts and perform financial analysis."""
    print("\n🔗 MAPPING GL ACCOUNTS TO CLASSIFICATIONS")
    print("=" * 80)
    
    # Merge mapping with transactions
    mapped_df = fagl_df.merge(
        mapping_df[['gl_account', 'bucket', 'type', 'entity', 'notes']],
        on='gl_account',
        how='left'
    )
    
    # Fill missing mappings
    unmapped = mapped_df['type'].isna().sum()
    if unmapped > 0:
        print(f"⚠️  Warning: {unmapped:,} transactions could not be mapped")
        mapped_df['type'].fillna('Unmapped', inplace=True)
        mapped_df['bucket'].fillna('Unknown', inplace=True)
    
    print(f"✅ Mapped {len(mapped_df):,} transactions successfully")
    
    return mapped_df


def perform_ratio_analysis(mapped_df):
    """Perform comprehensive financial ratio analysis."""
    print("\n📊 PERFORMING FINANCIAL RATIO ANALYSIS")
    print("=" * 80)
    
    ratio_results = analyze_financial_ratios(mapped_df)
    
    # Display key results
    ratios = ratio_results.get('ratios', {})
    going_concern = ratio_results.get('going_concern', {})
    
    print(f"\n📈 KEY FINANCIAL RATIOS:")
    print(f"  • Current Ratio: {ratios.get('liquidity', {}).get('current_ratio', 0):.2f}")
    print(f"  • Quick Ratio: {ratios.get('liquidity', {}).get('quick_ratio', 0):.2f}")
    print(f"  • Debt-to-Equity: {ratios.get('solvency', {}).get('debt_to_equity_ratio', 0):.2f}")
    print(f"  • Gross Margin: {ratios.get('profitability', {}).get('gross_profit_margin', 0):.1f}%")
    print(f"  • Net Margin: {ratios.get('profitability', {}).get('net_profit_margin', 0):.1f}%")
    
    print(f"\n🎯 GOING CONCERN ASSESSMENT:")
    print(f"  • Score: {going_concern.get('overall_score', 0)}/100")
    print(f"  • Status: {going_concern.get('assessment', 'Unknown')}")
    
    return ratio_results


def generate_intelligent_insights(ratio_results, mapped_df):
    """Generate intelligent insights using rule-based analysis."""
    print("\n🤖 GENERATING INTELLIGENT FINANCIAL INSIGHTS")
    print("=" * 80)
    
    insights_gen = FinancialInsightsGenerator()
    
    print("📝 Generating executive summary...")
    exec_summary = insights_gen.generate_executive_summary(ratio_results, mapped_df)
    
    print("⚠️  Assessing financial risks...")
    risks = insights_gen.assess_risks(ratio_results, mapped_df)
    
    print("💡 Developing strategic recommendations...")
    recommendations = insights_gen.generate_recommendations(ratio_results, mapped_df)
    
    print("❓ Answering key financial questions...")
    qa_insights = insights_gen.answer_financial_questions(mapped_df, ratio_results)
    
    return {
        'executive_summary': exec_summary,
        'risks': risks,
        'recommendations': recommendations,
        'qa_insights': qa_insights
    }


def save_insights_report(insights, ratio_results, output_dir):
    """Save intelligent insights to files."""
    print("\n💾 SAVING ANALYSIS REPORTS")
    print("=" * 80)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save executive summary
    summary_file = output_dir / 'executive_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(insights['executive_summary'])
    print(f"✅ Executive summary: {summary_file}")
    
    # Save risk assessment
    risk_file = output_dir / 'risk_assessment.md'
    with open(risk_file, 'w', encoding='utf-8') as f:
        f.write("# FINANCIAL RISK ASSESSMENT\n\n")
        f.write(f"*Analysis Date: {datetime.now().strftime('%B %d, %Y')}*\n\n")
        
        if insights['risks']:
            for i, risk in enumerate(insights['risks'], 1):
                f.write(f"## Risk #{i}: {risk['category']}\n\n")
                f.write(f"**Severity:** {risk['severity']}\n\n")
                f.write(f"**Description:** {risk['description']}\n\n")
                f.write(f"**Impact:** {risk['impact']}\n\n")
                f.write(f"**Mitigation:** {risk['mitigation']}\n\n")
                f.write("---\n\n")
        else:
            f.write("*No significant financial risks identified.*\n")
    
    print(f"✅ Risk assessment: {risk_file}")
    
    # Save recommendations
    rec_file = output_dir / 'strategic_recommendations.md'
    with open(rec_file, 'w', encoding='utf-8') as f:
        f.write("# STRATEGIC RECOMMENDATIONS\n\n")
        f.write(f"*Analysis Date: {datetime.now().strftime('%B %d, %Y')}*\n\n")
        
        for i, rec in enumerate(insights['recommendations'], 1):
            f.write(f"## Recommendation #{i}: {rec['title']}\n\n")
            f.write(f"**Priority:** {rec['priority']}\n\n")
            f.write(f"**Category:** {rec['category']}\n\n")
            f.write(f"**Description:** {rec['description']}\n\n")
            f.write(f"**Action Items:**\n")
            for action in rec['action_items']:
                f.write(f"- {action}\n")
            f.write(f"\n**Expected Impact:** {rec['expected_impact']}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Recommendations: {rec_file}")
    
    # Save Q&A insights
    qa_file = output_dir / 'financial_qa.md'
    with open(qa_file, 'w', encoding='utf-8') as f:
        f.write("# FINANCIAL ANALYSIS Q&A\n\n")
        f.write(f"*Analysis Date: {datetime.now().strftime('%B %d, %Y')}*\n\n")
        
        for i, qa in enumerate(insights['qa_insights'], 1):
            f.write(f"## Q{i}: {qa['question']}\n\n")
            f.write(f"**A:** {qa['answer']}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Q&A insights: {qa_file}")
    
    # Save comprehensive JSON report
    json_file = output_dir / 'complete_analysis.json'
    full_report = {
        'analysis_date': datetime.now().isoformat(),
        'insights': insights,
        'ratio_results': {
            'ratios': ratio_results.get('ratios', {}),
            'going_concern': ratio_results.get('going_concern', {}),
            'balance_sheet': ratio_results.get('balance_sheet', {}),
            'income_statement': ratio_results.get('income_statement', {})
        }
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2, default=str)
    print(f"✅ Complete analysis (JSON): {json_file}")
    
    return output_dir


def create_summary_dashboard(insights, ratio_results, output_dir):
    """Create HTML dashboard with insights."""
    print("\n🌐 CREATING INTERACTIVE DASHBOARD")
    print("=" * 80)
    
    html_file = output_dir / 'intelligent_insights_dashboard.html'
    
    risks_html = ""
    for risk in insights['risks'][:5]:  # Top 5 risks
        severity_color = {'HIGH': '#dc3545', 'MEDIUM': '#ffc107', 'LOW': '#28a745'}.get(risk['severity'], '#6c757d')
        risks_html += f"""
        <div class="risk-card" style="border-left: 4px solid {severity_color};">
            <h4>{risk['category']} <span class="badge" style="background-color: {severity_color};">{risk['severity']}</span></h4>
            <p><strong>Description:</strong> {risk['description']}</p>
            <p><strong>Impact:</strong> {risk['impact']}</p>
            <p><strong>Mitigation:</strong> {risk['mitigation']}</p>
        </div>
        """
    
    recommendations_html = ""
    for rec in insights['recommendations'][:5]:  # Top 5 recommendations
        priority_color = {'HIGH': '#dc3545', 'MEDIUM': '#ffc107', 'LOW': '#28a745'}.get(rec['priority'], '#6c757d')
        actions_html = "".join([f"<li>{action}</li>" for action in rec['action_items'][:4]])
        recommendations_html += f"""
        <div class="recommendation-card">
            <h4>{rec['title']} <span class="badge" style="background-color: {priority_color};">{rec['priority']}</span></h4>
            <p><strong>Category:</strong> {rec['category']}</p>
            <p>{rec['description']}</p>
            <p><strong>Action Items:</strong></p>
            <ul>{actions_html}</ul>
            <p><strong>Expected Impact:</strong> {rec['expected_impact']}</p>
        </div>
        """
    
    qa_html = ""
    for qa in insights['qa_insights']:
        qa_html += f"""
        <div class="qa-card">
            <h4>Q: {qa['question']}</h4>
            <p><strong>A:</strong> {qa['answer']}</p>
        </div>
        """
    
    gc_score = ratio_results.get('going_concern', {}).get('overall_score', 0)
    gc_color = '#28a745' if gc_score >= 70 else '#ffc107' if gc_score >= 50 else '#dc3545'
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligent Financial Insights - Bulgarian Analysis 2024</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .score-section {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: {gc_color};
            color: white;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            font-weight: bold;
            margin: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .risk-card, .recommendation-card, .qa-card {{
            background: #f8f9fa;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            color: white;
            margin-left: 10px;
        }}
        
        .qa-card h4 {{
            color: #495057;
            margin-bottom: 15px;
        }}
        
        ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Intelligent Financial Insights</h1>
            <p>Bulgarian Financial Analysis 2024 • Lightweight Rule-Based AI</p>
            <p style="margin-top: 10px; opacity: 0.8;">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>
        
        <div class="score-section">
            <h2 style="margin-bottom: 20px;">Going Concern Assessment</h2>
            <div class="score-circle">{gc_score}</div>
            <h3 style="margin-top: 20px;">{ratio_results.get('going_concern', {}).get('assessment', 'Unknown')}</h3>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📝 Executive Summary</h2>
                <pre style="white-space: pre-wrap; font-family: inherit; background: #f8f9fa; padding: 20px; border-radius: 8px; line-height: 1.8;">{insights['executive_summary']}</pre>
            </div>
            
            <div class="section">
                <h2>⚠️ Financial Risk Assessment</h2>
                {risks_html if risks_html else '<p>No significant financial risks identified.</p>'}
            </div>
            
            <div class="section">
                <h2>💡 Strategic Recommendations</h2>
                {recommendations_html}
            </div>
            
            <div class="section">
                <h2>❓ Financial Analysis Q&A</h2>
                {qa_html}
            </div>
        </div>
        
        <div class="footer">
            <p>Analysis Type: Rule-Based Intelligent Insights (Lightweight Alternative to LLM)</p>
            <p>This analysis uses financial domain knowledge and rule-based logic to provide insights without requiring heavy AI models.</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Interactive dashboard: {html_file}")
    
    return html_file


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("🤖 BULGARIAN FINANCIAL ANALYSIS - INTELLIGENT INSIGHTS (LIGHTWEIGHT)")
    print("=" * 80)
    print("Using rule-based AI analysis - No heavy LLM models required!")
    print("=" * 80)
    
    # Create output directory
    output_dir = Path('results/intelligent_insights_2024')
    
    try:
        # Load data
        mapping_df, fagl_df, mapping_summary = load_bulgarian_data()
        
        # Map and analyze
        mapped_df = map_and_analyze_data(mapping_df, fagl_df)
        
        # Perform ratio analysis
        ratio_results = perform_ratio_analysis(mapped_df)
        
        # Generate intelligent insights
        insights = generate_intelligent_insights(ratio_results, mapped_df)
        
        # Save reports
        save_insights_report(insights, ratio_results, output_dir)
        
        # Create dashboard
        dashboard_file = create_summary_dashboard(insights, ratio_results, output_dir)
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\n📁 All results saved to: {output_dir}")
        print(f"\n🌐 View interactive dashboard: {dashboard_file}")
        print("\n📄 Generated Files:")
        print(f"  • Executive Summary: {output_dir}/executive_summary.txt")
        print(f"  • Risk Assessment: {output_dir}/risk_assessment.md")
        print(f"  • Recommendations: {output_dir}/strategic_recommendations.md")
        print(f"  • Q&A Insights: {output_dir}/financial_qa.md")
        print(f"  • Complete Analysis (JSON): {output_dir}/complete_analysis.json")
        print(f"  • Interactive Dashboard: {dashboard_file}")
        
        # Auto-open dashboard
        print("\n🚀 Opening dashboard in browser...")
        import subprocess
        import platform
        
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                subprocess.run(['open', str(dashboard_file)], check=False)
            elif system == 'Windows':
                subprocess.run(['start', str(dashboard_file)], shell=True, check=False)
            elif system == 'Linux':
                subprocess.run(['xdg-open', str(dashboard_file)], check=False)
        except Exception as e:
            print(f"⚠️  Could not auto-open dashboard: {e}")
            print(f"   Please open manually: {dashboard_file}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

