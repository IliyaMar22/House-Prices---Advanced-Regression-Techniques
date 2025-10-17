"""
Intelligent Financial Insights Generator - Lightweight Rule-Based AI Alternative.

This module provides intelligent, context-aware financial analysis without requiring
heavy LLM models. It uses financial domain knowledge and rule-based logic to generate
professional insights, risk assessments, and recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class FinancialInsightsGenerator:
    """Generate intelligent financial insights using rule-based analysis."""
    
    def __init__(self):
        self.logger = logger
        
    def generate_executive_summary(self, ratio_results: Dict, mapped_data: pd.DataFrame) -> str:
        """Generate an executive summary of financial performance."""
        
        ratios = ratio_results.get('ratios', {})
        going_concern = ratio_results.get('going_concern', {})
        
        # Extract key metrics
        total_revenue = mapped_data[mapped_data['type'] == 'Revenue']['amount'].sum()
        total_opex = mapped_data[mapped_data['type'] == 'Operating expenses']['amount'].sum()
        total_equity = mapped_data[mapped_data['type'] == 'Equity']['amount'].sum()
        
        liquidity = ratios.get('liquidity', {})
        profitability = ratios.get('profitability', {})
        solvency = ratios.get('solvency', {})
        
        current_ratio = liquidity.get('current_ratio', 0)
        gross_margin = profitability.get('gross_profit_margin', 0)
        net_margin = profitability.get('net_profit_margin', 0)
        debt_to_equity = solvency.get('debt_to_equity_ratio', 0)
        
        gc_score = going_concern.get('overall_score', 0)
        gc_status = going_concern.get('assessment', 'Unknown')
        
        # Build summary
        summary = f"""
EXECUTIVE SUMMARY - BULGARIAN FINANCIAL ANALYSIS
{'=' * 80}

Period: 2024 Financial Year
Analysis Date: {datetime.now().strftime('%B %d, %Y')}

FINANCIAL HIGHLIGHTS
{'-' * 80}

Revenue Performance:
• Total Revenue: {total_revenue:,.0f} BGN
• Operating Expenses: {total_opex:,.0f} BGN
• Total Equity: {total_equity:,.0f} BGN

Key Financial Ratios:
• Current Ratio: {current_ratio:.2f} ({"Healthy" if current_ratio >= 1.5 else "Needs Attention" if current_ratio >= 1.0 else "Critical"})
• Gross Profit Margin: {gross_margin:.1f}% ({"Strong" if gross_margin >= 30 else "Moderate" if gross_margin >= 20 else "Weak"})
• Net Profit Margin: {net_margin:.1f}% ({"Excellent" if net_margin >= 15 else "Good" if net_margin >= 10 else "Needs Improvement"})
• Debt-to-Equity Ratio: {debt_to_equity:.2f} ({"Conservative" if debt_to_equity <= 1.0 else "Moderate" if debt_to_equity <= 2.0 else "Aggressive"})

GOING CONCERN ASSESSMENT
{'-' * 80}

Overall Score: {gc_score}/100
Status: {gc_status}

{self._get_going_concern_commentary(gc_score, gc_status)}

STRATEGIC OUTLOOK
{'-' * 80}

{self._get_strategic_outlook(current_ratio, gross_margin, net_margin, debt_to_equity)}
"""
        
        return summary.strip()
    
    def _get_going_concern_commentary(self, score: float, status: str) -> str:
        """Generate commentary on going concern status."""
        if score >= 70:
            return ("The company demonstrates strong financial health with robust liquidity, "
                   "sustainable profitability, and manageable debt levels. The business is well-positioned "
                   "to continue operations for the foreseeable future without significant financial risk.")
        elif score >= 50:
            return ("The company shows moderate financial health with some areas requiring attention. "
                   "While the business remains viable, management should focus on improving liquidity "
                   "and profitability metrics to strengthen the company's long-term sustainability.")
        else:
            return ("The financial analysis reveals significant concerns regarding the company's ability "
                   "to continue as a going concern. Immediate management attention is required to address "
                   "liquidity issues, improve operational efficiency, and restructure debt obligations.")
    
    def _get_strategic_outlook(self, current_ratio: float, gross_margin: float, 
                               net_margin: float, debt_to_equity: float) -> str:
        """Generate strategic outlook based on key metrics."""
        
        insights = []
        
        # Liquidity insight
        if current_ratio < 1.0:
            insights.append("• LIQUIDITY: Critical - The company faces immediate liquidity challenges. "
                          "Recommend accelerating collections and negotiating extended payment terms.")
        elif current_ratio < 1.5:
            insights.append("• LIQUIDITY: Adequate - Working capital is sufficient but could be optimized. "
                          "Consider improving cash conversion cycles.")
        else:
            insights.append("• LIQUIDITY: Strong - The company maintains healthy working capital reserves. "
                          "Excess liquidity could be deployed for growth initiatives.")
        
        # Profitability insight
        if gross_margin < 20:
            insights.append("• PROFITABILITY: Gross margins are under pressure. Evaluate pricing strategies "
                          "and cost reduction opportunities in the supply chain.")
        elif gross_margin >= 30:
            insights.append("• PROFITABILITY: Strong gross margins indicate effective pricing power and "
                          "operational efficiency. Maintain focus on cost discipline.")
        
        if net_margin < 10:
            insights.append("• OPERATIONAL EFFICIENCY: Net margins suggest room for improvement in operating "
                          "expense management. Conduct detailed OpEx review.")
        
        # Leverage insight
        if debt_to_equity > 2.0:
            insights.append("• CAPITAL STRUCTURE: High leverage levels increase financial risk. "
                          "Prioritize deleveraging through cash generation or equity infusion.")
        elif debt_to_equity < 0.5:
            insights.append("• CAPITAL STRUCTURE: Conservative leverage provides financial flexibility. "
                          "Consider strategic use of debt for growth opportunities.")
        
        return "\n".join(insights) if insights else "• Overall financial position is balanced with no immediate strategic concerns."
    
    def assess_risks(self, ratio_results: Dict, mapped_data: pd.DataFrame) -> List[Dict[str, str]]:
        """Identify and assess financial risks."""
        
        risks = []
        ratios = ratio_results.get('ratios', {})
        
        # Liquidity risks
        liquidity = ratios.get('liquidity', {})
        current_ratio = liquidity.get('current_ratio', 0)
        quick_ratio = liquidity.get('quick_ratio', 0)
        
        if current_ratio < 1.2:
            risks.append({
                'category': 'LIQUIDITY RISK',
                'severity': 'HIGH' if current_ratio < 1.0 else 'MEDIUM',
                'description': f'Current ratio of {current_ratio:.2f} indicates potential short-term liquidity constraints.',
                'impact': 'May struggle to meet short-term obligations without additional financing.',
                'mitigation': 'Accelerate receivables collection, negotiate extended payment terms, or secure credit line.'
            })
        
        if quick_ratio < 0.8:
            risks.append({
                'category': 'LIQUIDITY RISK',
                'severity': 'HIGH',
                'description': f'Quick ratio of {quick_ratio:.2f} suggests over-reliance on inventory for liquidity.',
                'impact': 'Difficulty converting assets to cash quickly in stress scenarios.',
                'mitigation': 'Reduce inventory levels, improve working capital efficiency, maintain cash reserves.'
            })
        
        # Profitability risks
        profitability = ratios.get('profitability', {})
        gross_margin = profitability.get('gross_profit_margin', 0)
        net_margin = profitability.get('net_profit_margin', 0)
        
        if gross_margin < 20:
            risks.append({
                'category': 'PROFITABILITY RISK',
                'severity': 'MEDIUM',
                'description': f'Gross margin of {gross_margin:.1f}% is below healthy benchmarks.',
                'impact': 'Limited pricing power and vulnerability to cost increases.',
                'mitigation': 'Review pricing strategy, negotiate supplier terms, optimize product mix.'
            })
        
        if net_margin < 5:
            risks.append({
                'category': 'PROFITABILITY RISK',
                'severity': 'HIGH',
                'description': f'Net margin of {net_margin:.1f}% indicates thin profitability.',
                'impact': 'Minimal buffer for operational challenges or market downturns.',
                'mitigation': 'Comprehensive cost reduction program, operational efficiency improvements.'
            })
        
        # Solvency risks
        solvency = ratios.get('solvency', {})
        debt_to_equity = solvency.get('debt_to_equity_ratio', 0)
        interest_coverage = solvency.get('interest_coverage_ratio', 0)
        
        if debt_to_equity > 2.5:
            risks.append({
                'category': 'SOLVENCY RISK',
                'severity': 'HIGH',
                'description': f'Debt-to-equity ratio of {debt_to_equity:.2f} indicates high financial leverage.',
                'impact': 'Increased financial risk and potential difficulty accessing additional credit.',
                'mitigation': 'Debt reduction plan, asset sales, or equity capital raise.'
            })
        
        if interest_coverage < 2.5:
            risks.append({
                'category': 'SOLVENCY RISK',
                'severity': 'MEDIUM' if interest_coverage >= 1.5 else 'HIGH',
                'description': f'Interest coverage of {interest_coverage:.2f}x suggests limited debt servicing capacity.',
                'impact': 'Vulnerability to interest rate increases or revenue declines.',
                'mitigation': 'Refinance debt at lower rates, increase EBITDA through operational improvements.'
            })
        
        # Cash flow risks
        cash_flow = ratios.get('cash_flow', {})
        ocf_ratio = cash_flow.get('operating_cash_flow_ratio', 0)
        
        if ocf_ratio < 0.5:
            risks.append({
                'category': 'CASH FLOW RISK',
                'severity': 'HIGH',
                'description': f'Operating cash flow ratio of {ocf_ratio:.2f} indicates weak cash generation.',
                'impact': 'Dependency on external financing for operations and growth.',
                'mitigation': 'Working capital optimization, improve collection processes, reduce inventory.'
            })
        
        # Sort by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        risks.sort(key=lambda x: severity_order.get(x['severity'], 999))
        
        return risks
    
    def generate_recommendations(self, ratio_results: Dict, mapped_data: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate strategic recommendations based on analysis."""
        
        recommendations = []
        ratios = ratio_results.get('ratios', {})
        
        # Analyze trends
        revenue_by_month = mapped_data[mapped_data['type'] == 'Revenue'].groupby(
            mapped_data['posting_date'].dt.to_period('M')
        )['amount'].sum().sort_index()
        
        if len(revenue_by_month) >= 3:
            recent_trend = revenue_by_month.tail(3).pct_change().mean()
            
            if recent_trend < -0.05:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Revenue Growth',
                    'title': 'Address Revenue Decline',
                    'description': f'Revenue shows declining trend of {recent_trend:.1%} over recent months.',
                    'action_items': [
                        'Conduct customer satisfaction survey to identify service gaps',
                        'Review pricing strategy and competitive positioning',
                        'Develop targeted marketing campaign for customer retention',
                        'Explore new revenue streams or product line extensions'
                    ],
                    'expected_impact': 'Stabilize and reverse revenue decline within 6 months'
                })
            elif recent_trend > 0.1:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Growth Optimization',
                    'title': 'Scale Revenue Growth Sustainably',
                    'description': f'Strong revenue growth of {recent_trend:.1%} presents scaling opportunity.',
                    'action_items': [
                        'Ensure operational capacity can support continued growth',
                        'Evaluate working capital requirements for scaling',
                        'Consider strategic investments in infrastructure',
                        'Develop talent acquisition plan for key growth areas'
                    ],
                    'expected_impact': 'Sustain growth trajectory while maintaining profitability'
                })
        
        # Liquidity recommendations
        liquidity = ratios.get('liquidity', {})
        current_ratio = liquidity.get('current_ratio', 0)
        
        if current_ratio < 1.5:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Working Capital',
                'title': 'Improve Liquidity Position',
                'description': 'Current ratio below optimal range requires working capital enhancement.',
                'action_items': [
                    'Implement aggressive receivables collection program',
                    'Negotiate 60-90 day payment terms with key suppliers',
                    'Reduce excess inventory through promotion or liquidation',
                    'Secure revolving credit facility as liquidity backstop'
                ],
                'expected_impact': 'Achieve current ratio of 1.5+ within 6 months'
            })
        
        # Profitability recommendations
        profitability = ratios.get('profitability', {})
        gross_margin = profitability.get('gross_profit_margin', 0)
        
        if gross_margin < 25:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Margin Improvement',
                'title': 'Enhance Gross Profit Margins',
                'description': 'Gross margins below industry benchmarks indicate pricing or cost opportunities.',
                'action_items': [
                    'Conduct detailed cost analysis by product/service line',
                    'Negotiate volume discounts with top 10 suppliers',
                    'Implement value-based pricing for premium offerings',
                    'Eliminate or re-price low-margin products'
                ],
                'expected_impact': 'Increase gross margin by 3-5 percentage points'
            })
        
        # OpEx efficiency
        opex_to_revenue = abs(mapped_data[mapped_data['type'] == 'Operating expenses']['amount'].sum()) / \
                         abs(mapped_data[mapped_data['type'] == 'Revenue']['amount'].sum())
        
        if opex_to_revenue > 0.35:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Cost Management',
                'title': 'Optimize Operating Expense Structure',
                'description': f'OpEx ratio of {opex_to_revenue:.1%} suggests efficiency opportunities.',
                'action_items': [
                    'Conduct zero-based budgeting exercise for all departments',
                    'Automate repetitive processes to reduce labor costs',
                    'Renegotiate service contracts and subscriptions',
                    'Implement cost control dashboard with monthly targets'
                ],
                'expected_impact': 'Reduce OpEx ratio to 30-32% of revenue'
            })
        
        # Digital transformation
        recommendations.append({
            'priority': 'LOW',
            'category': 'Strategic Initiative',
            'title': 'Digital Transformation & Automation',
            'description': 'Leverage technology to improve efficiency and decision-making.',
            'action_items': [
                'Implement automated financial reporting and analytics',
                'Deploy AI-powered forecasting tools',
                'Digitize manual processes to reduce errors and save time',
                'Invest in data infrastructure for real-time business insights'
            ],
            'expected_impact': 'Long-term operational efficiency and competitive advantage'
        })
        
        return recommendations
    
    def answer_financial_questions(self, mapped_data: pd.DataFrame, ratio_results: Dict) -> List[Dict[str, str]]:
        """Answer common financial analysis questions."""
        
        qa_pairs = []
        
        # Calculate key metrics
        total_revenue = abs(mapped_data[mapped_data['type'] == 'Revenue']['amount'].sum())
        total_opex = abs(mapped_data[mapped_data['type'] == 'Operating expenses']['amount'].sum())
        total_equity = abs(mapped_data[mapped_data['type'] == 'Equity']['amount'].sum())
        
        ratios = ratio_results.get('ratios', {})
        
        # Q1: Financial Health
        current_ratio = ratios.get('liquidity', {}).get('current_ratio', 0)
        debt_to_equity = ratios.get('solvency', {}).get('debt_to_equity_ratio', 0)
        
        if current_ratio >= 1.5 and debt_to_equity <= 1.5:
            health = "excellent"
            details = "strong liquidity, manageable leverage, and stable operations"
        elif current_ratio >= 1.0 and debt_to_equity <= 2.5:
            health = "good"
            details = "adequate liquidity and moderate leverage levels"
        else:
            health = "requiring attention"
            details = "liquidity constraints and/or high leverage"
        
        qa_pairs.append({
            'question': 'What is the overall financial health of the company?',
            'answer': f'The company is in {health} financial health based on key indicators including {details}. '
                     f'The current ratio of {current_ratio:.2f} indicates {"strong" if current_ratio >= 1.5 else "adequate" if current_ratio >= 1.0 else "weak"} '
                     f'short-term liquidity, while the debt-to-equity ratio of {debt_to_equity:.2f} reflects '
                     f'{"conservative" if debt_to_equity <= 1.0 else "moderate" if debt_to_equity <= 2.0 else "aggressive"} financial leverage.'
        })
        
        # Q2: Profitability
        gross_margin = ratios.get('profitability', {}).get('gross_profit_margin', 0)
        net_margin = ratios.get('profitability', {}).get('net_profit_margin', 0)
        
        qa_pairs.append({
            'question': 'How profitable is the business?',
            'answer': f'The company demonstrates {"strong" if net_margin >= 15 else "moderate" if net_margin >= 10 else "weak"} '
                     f'profitability with a gross profit margin of {gross_margin:.1f}% and net profit margin of {net_margin:.1f}%. '
                     f'{"This indicates effective cost management and pricing power." if gross_margin >= 30 else "There are opportunities to improve margins through cost optimization and pricing strategies." if gross_margin >= 20 else "Margin improvement should be a strategic priority."}'
        })
        
        # Q3: Key Concerns
        concerns = []
        if current_ratio < 1.2:
            concerns.append("liquidity constraints")
        if net_margin < 10:
            concerns.append("thin profit margins")
        if debt_to_equity > 2.0:
            concerns.append("high financial leverage")
        
        qa_pairs.append({
            'question': 'What are the main financial concerns?',
            'answer': f'{"The primary concerns are: " + ", ".join(concerns) + "." if concerns else "There are no critical financial concerns at this time."} '
                     f'{"Management should prioritize addressing these areas to strengthen financial stability." if concerns else "The company should maintain disciplined financial management to preserve its strong position."}'
        })
        
        # Q4: Investment Worthiness
        gc_score = ratio_results.get('going_concern', {}).get('overall_score', 0)
        
        if gc_score >= 70:
            worthiness = "attractive"
            reason = "strong financial fundamentals, stable cash flows, and low financial risk"
        elif gc_score >= 50:
            worthiness = "moderate"
            reason = "acceptable financial health with some areas requiring improvement"
        else:
            worthiness = "high-risk"
            reason = "significant financial challenges and going concern uncertainties"
        
        investment_advice = (
            "Investors should feel confident in the company's ability to generate returns." if gc_score >= 70 
            else "Investors should conduct thorough due diligence and consider the identified risks." if gc_score >= 50 
            else "High-risk investors only, with substantial risk mitigation required."
        )
        
        qa_pairs.append({
            'question': 'Is this a good investment opportunity?',
            'answer': f'Based on the financial analysis, this represents a {worthiness} investment opportunity due to {reason}. '
                     f'The going concern score of {gc_score}/100 reflects the company\'s financial stability. '
                     f'{investment_advice}'
        })
        
        # Q5: Revenue Trends
        revenue_by_month = mapped_data[mapped_data['type'] == 'Revenue'].groupby(
            mapped_data['posting_date'].dt.to_period('M')
        )['amount'].sum().sort_index()
        
        if len(revenue_by_month) >= 3:
            recent_trend = revenue_by_month.tail(3).pct_change().mean()
            trend_direction = "growing" if recent_trend > 0.02 else "declining" if recent_trend < -0.02 else "stable"
            
            trend_commentary = (
                "This positive momentum should be sustained through continued market expansion and customer retention." if recent_trend > 0.05
                else "The decline requires immediate attention to identify and address root causes." if recent_trend < -0.05
                else "Stable revenue provides a foundation for margin improvement initiatives."
            )
            
            qa_pairs.append({
                'question': 'What are the revenue trends?',
                'answer': f'Revenue is {trend_direction} with a recent monthly trend of {recent_trend:.1%}. {trend_commentary}'
            })
        
        return qa_pairs
    
    def generate_full_llm_style_report(self, ratio_results: Dict, mapped_data: pd.DataFrame) -> Dict:
        """Generate comprehensive LLM-style analysis report."""
        
        return {
            'executive_summary': self.generate_executive_summary(ratio_results, mapped_data),
            'risk_assessment': self.assess_risks(ratio_results, mapped_data),
            'recommendations': self.generate_recommendations(ratio_results, mapped_data),
            'qa_insights': self.answer_financial_questions(mapped_data, ratio_results),
            'generated_at': datetime.now().isoformat(),
            'analysis_type': 'Rule-Based Intelligent Insights (Lightweight Alternative to LLM)'
        }

