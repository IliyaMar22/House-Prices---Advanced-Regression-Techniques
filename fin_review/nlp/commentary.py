"""NLP commentary generation module for automated insights."""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger()


@dataclass
class Commentary:
    """Container for a single commentary item."""
    category: str  # 'insight', 'risk', 'recommendation'
    title: str
    content: str
    confidence: str  # 'high', 'medium', 'low'
    supporting_metrics: Dict
    priority: int  # 1-10, higher is more important


@dataclass
class CommentaryResult:
    """Container for all commentary."""
    executive_summary: str
    insights: List[Commentary]
    risks: List[Commentary]
    recommendations: List[Commentary]
    email_summary: str
    generated_at: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'executive_summary': self.executive_summary,
            'insights': [
                {
                    'title': c.title,
                    'content': c.content,
                    'confidence': c.confidence,
                    'supporting_metrics': c.supporting_metrics
                }
                for c in self.insights
            ],
            'risks': [
                {
                    'title': c.title,
                    'content': c.content,
                    'confidence': c.confidence,
                    'supporting_metrics': c.supporting_metrics
                }
                for c in self.risks
            ],
            'recommendations': [
                {
                    'title': c.title,
                    'content': c.content,
                    'confidence': c.confidence,
                    'supporting_metrics': c.supporting_metrics
                }
                for c in self.recommendations
            ],
            'email_summary': self.email_summary,
            'generated_at': self.generated_at
        }


class CommentaryGenerator:
    """Generates automated NLP commentary and insights."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        kpis: Dict,
        trends: Dict,
        aging: Dict,
        anomalies: Dict,
        config: Optional[Dict] = None
    ):
        """
        Initialize commentary generator.
        
        Args:
            df: Normalized FAGL DataFrame
            kpis: KPI calculation results
            trends: Trend analysis results
            aging: Aging analysis results
            anomalies: Anomaly detection results
            config: Configuration dictionary
        """
        self.df = df
        self.kpis = kpis
        self.trends = trends
        self.aging = aging
        self.anomalies = anomalies
        self.config = config or {}
        
        self.insights = []
        self.risks = []
        self.recommendations = []
    
    def generate_all(self) -> CommentaryResult:
        """
        Generate all commentary.
        
        Returns:
            CommentaryResult object
        """
        logger.info("Generating NLP commentary")
        
        # Generate insights
        self._generate_growth_insights()
        self._generate_efficiency_insights()
        self._generate_trend_insights()
        
        # Generate risks
        self._generate_anomaly_risks()
        self._generate_aging_risks()
        self._generate_concentration_risks()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Sort by priority
        self.insights.sort(key=lambda x: x.priority, reverse=True)
        self.risks.sort(key=lambda x: x.priority, reverse=True)
        self.recommendations.sort(key=lambda x: x.priority, reverse=True)
        
        # Limit to configured numbers
        top_insights = self.config.get('top_insights', 3)
        top_risks = self.config.get('top_risks', 3)
        max_recommendations = self.config.get('max_recommendations', 5)
        
        self.insights = self.insights[:top_insights]
        self.risks = self.risks[:top_risks]
        self.recommendations = self.recommendations[:max_recommendations]
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary()
        
        # Generate email summary
        email_summary = self._generate_email_summary()
        
        logger.info(
            "Commentary generation complete",
            insights=len(self.insights),
            risks=len(self.risks),
            recommendations=len(self.recommendations)
        )
        
        return CommentaryResult(
            executive_summary=exec_summary,
            insights=self.insights,
            risks=self.risks,
            recommendations=self.recommendations,
            email_summary=email_summary,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _generate_growth_insights(self):
        """Generate insights about growth."""
        growth_metrics = self.kpis.get('growth_metrics', {})
        
        # Revenue growth insight
        if 'latest_revenue_yoy' in growth_metrics:
            yoy_growth = growth_metrics['latest_revenue_yoy']
            
            if not np.isnan(yoy_growth) and abs(yoy_growth) > 5:
                direction = "grew" if yoy_growth > 0 else "declined"
                
                # Find what drove the growth
                revenue_data = self.df[self.df['type'] == 'Revenue']
                if len(revenue_data) > 0:
                    top_bucket = revenue_data.groupby('bucket')['amount'].sum().abs().nlargest(1)
                    if len(top_bucket) > 0:
                        driver = top_bucket.index[0]
                        driver_amount = top_bucket.iloc[0]
                        
                        content = (
                            f"Revenue {direction} {abs(yoy_growth):.1f}% year-over-year, "
                            f"primarily driven by {driver} which contributed "
                            f"€{driver_amount/1000:.1f}K ({(driver_amount / revenue_data['amount'].sum()) * 100:.0f}% of total revenue)."
                        )
                        
                        confidence = 'high' if abs(yoy_growth) > 10 else 'medium'
                        priority = 10 if abs(yoy_growth) > 20 else 8
                        
                        self.insights.append(Commentary(
                            category='insight',
                            title=f"Revenue {direction.capitalize()} {abs(yoy_growth):.1f}% YoY",
                            content=content,
                            confidence=confidence,
                            supporting_metrics={
                                'yoy_growth': yoy_growth,
                                'top_driver': driver,
                                'driver_amount': float(driver_amount)
                            },
                            priority=priority
                        ))
        
        # OPEX efficiency insight
        ratios = self.kpis.get('ratios', {})
        if 'avg_opex_ratio' in ratios:
            opex_ratio = ratios['avg_opex_ratio']
            
            if opex_ratio < 50:  # Good efficiency
                content = (
                    f"Operating expenses are well-controlled at {opex_ratio:.1f}% of revenue, "
                    f"indicating strong operational efficiency."
                )
                
                self.insights.append(Commentary(
                    category='insight',
                    title="Efficient Operations",
                    content=content,
                    confidence='high',
                    supporting_metrics={'opex_ratio': opex_ratio},
                    priority=7
                ))
    
    def _generate_efficiency_insights(self):
        """Generate insights about operational efficiency."""
        ratios = self.kpis.get('ratios', {})
        
        # Payroll efficiency
        if 'latest_payroll_ratio' in ratios:
            payroll_ratio = ratios['latest_payroll_ratio']
            
            if payroll_ratio < 20:  # Efficient payroll
                content = (
                    f"Payroll costs are {payroll_ratio:.1f}% of revenue, "
                    f"demonstrating strong labor efficiency."
                )
                
                self.insights.append(Commentary(
                    category='insight',
                    title="Labor Efficiency",
                    content=content,
                    confidence='high',
                    supporting_metrics={'payroll_ratio': payroll_ratio},
                    priority=6
                ))
    
    def _generate_trend_insights(self):
        """Generate insights from trend analysis."""
        trend_direction = self.trends.get('trend_direction', {})
        
        for metric_type, trend_info in trend_direction.items():
            if isinstance(trend_info, dict):
                direction = trend_info.get('direction')
                confidence = trend_info.get('confidence')
                r_squared = trend_info.get('r_squared', 0)
                
                if direction == 'increasing' and metric_type == 'Revenue' and r_squared > 0.7:
                    content = (
                        f"{metric_type} shows a strong increasing trend with high confidence "
                        f"(R² = {r_squared:.2f}), indicating sustainable growth momentum."
                    )
                    
                    self.insights.append(Commentary(
                        category='insight',
                        title=f"{metric_type} Strong Upward Trend",
                        content=content,
                        confidence=confidence,
                        supporting_metrics=trend_info,
                        priority=8
                    ))
    
    def _generate_anomaly_risks(self):
        """Generate risks from detected anomalies."""
        anomaly_list = self.anomalies.get('anomalies', [])
        
        # Focus on high severity anomalies
        high_severity = [a for a in anomaly_list if a.get('severity') == 'high']
        
        for anomaly in high_severity[:3]:  # Top 3
            bucket = anomaly.get('bucket')
            deviation_pct = anomaly.get('deviation_pct', 0)
            explanation = anomaly.get('explanation', '')
            
            content = (
                f"Significant anomaly detected in {bucket}: {explanation}. "
                f"This represents a {abs(deviation_pct):.1f}% deviation from expected values."
            )
            
            self.risks.append(Commentary(
                category='risk',
                title=f"Anomaly in {bucket}",
                content=content,
                confidence='high',
                supporting_metrics={
                    'bucket': bucket,
                    'deviation_pct': deviation_pct,
                    'date': anomaly.get('date')
                },
                priority=9
            ))
    
    def _generate_aging_risks(self):
        """Generate risks from aging analysis."""
        ar_summary = self.aging.get('ar_summary', {})
        
        # Overdue AR risk
        overdue_pct = ar_summary.get('overdue_pct', 0)
        if overdue_pct > 30:  # More than 30% overdue
            overdue_amount = ar_summary.get('overdue_amount', 0)
            
            content = (
                f"Receivables aging has deteriorated significantly: {overdue_pct:.1f}% "
                f"(€{overdue_amount/1000:.1f}K) of accounts receivable are past due. "
                f"This represents a cash flow risk and may indicate collection challenges."
            )
            
            confidence = 'high' if overdue_pct > 40 else 'medium'
            priority = 10 if overdue_pct > 50 else 8
            
            self.risks.append(Commentary(
                category='risk',
                title="High Overdue Receivables",
                content=content,
                confidence=confidence,
                supporting_metrics={
                    'overdue_pct': overdue_pct,
                    'overdue_amount': overdue_amount
                },
                priority=priority
            ))
        
        # Top overdue customers
        top_overdue_customers = self.aging.get('top_overdue_customers', [])
        if len(top_overdue_customers) > 0:
            top_customer = top_overdue_customers[0]
            party = top_customer.get('party')
            amount = top_customer.get('overdue_amount', 0)
            pct = top_customer.get('pct_of_total_overdue', 0)
            
            if pct > 20:  # Single customer > 20% of overdue
                content = (
                    f"Customer {party} accounts for {pct:.0f}% of overdue receivables "
                    f"(€{abs(amount)/1000:.1f}K), representing significant concentration risk. "
                    f"Immediate escalation recommended."
                )
                
                self.risks.append(Commentary(
                    category='risk',
                    title=f"Concentration Risk: {party}",
                    content=content,
                    confidence='high',
                    supporting_metrics={
                        'party': party,
                        'amount': abs(amount),
                        'pct_of_overdue': pct
                    },
                    priority=9
                ))
    
    def _generate_concentration_risks(self):
        """Generate risks from supplier/customer concentration."""
        # Top vendors concentration
        opex_data = self.df[self.df['type'] == 'OPEX']
        if len(opex_data) > 0 and 'customer_vendor' in opex_data.columns:
            vendor_concentration = opex_data.groupby('customer_vendor')['amount'].sum().abs()
            total_opex = opex_data['amount'].sum()
            
            if len(vendor_concentration) > 0:
                top_5_pct = (vendor_concentration.nlargest(5).sum() / abs(total_opex)) * 100
                
                if top_5_pct > 60:  # Top 5 vendors > 60% of OPEX
                    content = (
                        f"Top 5 suppliers represent {top_5_pct:.0f}% of operating expenses, "
                        f"indicating high supplier concentration risk. Consider diversifying "
                        f"the supplier base to reduce dependency."
                    )
                    
                    self.risks.append(Commentary(
                        category='risk',
                        title="High Supplier Concentration",
                        content=content,
                        confidence='medium',
                        supporting_metrics={'top_5_concentration_pct': top_5_pct},
                        priority=6
                    ))
    
    def _generate_recommendations(self):
        """Generate actionable recommendations."""
        # Recommendation based on overdue AR
        ar_summary = self.aging.get('ar_summary', {})
        overdue_amount = ar_summary.get('overdue_amount', 0)
        
        if overdue_amount > 50000:  # Significant overdue
            cash_impact = overdue_amount * 0.8  # Assume 80% collectible
            
            content = (
                f"Escalate collection efforts for overdue receivables. "
                f"Potential cash impact: €{cash_impact/1000:.1f}K. "
                f"Recommended actions: (1) Review aging report weekly, "
                f"(2) Implement automated payment reminders, "
                f"(3) Consider early payment discounts for chronic late payers."
            )
            
            self.recommendations.append(Commentary(
                category='recommendation',
                title="Improve Collections Process",
                content=content,
                confidence='high',
                supporting_metrics={
                    'overdue_amount': overdue_amount,
                    'estimated_cash_impact': cash_impact
                },
                priority=10
            ))
        
        # Recommendation based on anomalies
        anomaly_summary = self.anomalies.get('summary', {})
        high_severity_count = anomaly_summary.get('high_severity_count', 0)
        
        if high_severity_count > 2:
            content = (
                f"Investigate {high_severity_count} high-severity spending anomalies detected. "
                f"Review with department heads to determine if these are one-off events or "
                f"represent new spending patterns requiring budget adjustments."
            )
            
            self.recommendations.append(Commentary(
                category='recommendation',
                title="Review Spending Anomalies",
                content=content,
                confidence='medium',
                supporting_metrics={'anomaly_count': high_severity_count},
                priority=7
            ))
        
        # Recommendation based on expense ratios
        ratios = self.kpis.get('ratios', {})
        opex_ratio = ratios.get('latest_opex_ratio', 0)
        
        if opex_ratio > 70:  # High expense ratio
            content = (
                f"OPEX ratio of {opex_ratio:.1f}% is high. Consider cost optimization initiatives: "
                f"(1) Review vendor contracts for better rates, "
                f"(2) Evaluate non-essential spending, "
                f"(3) Implement zero-based budgeting for next period."
            )
            
            self.recommendations.append(Commentary(
                category='recommendation',
                title="Optimize Operating Expenses",
                content=content,
                confidence='medium',
                supporting_metrics={'opex_ratio': opex_ratio},
                priority=8
            ))
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary combining all insights."""
        # Get date range
        start_date = self.df['posting_date'].min().strftime('%Y-%m-%d')
        end_date = self.df['posting_date'].max().strftime('%Y-%m-%d')
        
        # Build summary
        lines = [
            f"EXECUTIVE SUMMARY",
            f"Period: {start_date} to {end_date}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "KEY INSIGHTS:",
        ]
        
        for i, insight in enumerate(self.insights, 1):
            confidence_tag = f"[{insight.confidence.upper()}]" if self.config.get('confidence_levels', True) else ""
            lines.append(f"{i}. {insight.title} {confidence_tag}")
            lines.append(f"   {insight.content}")
            if self.config.get('explain_mode', False):
                lines.append(f"   Supporting metrics: {insight.supporting_metrics}")
            lines.append("")
        
        lines.append("TOP RISKS:")
        for i, risk in enumerate(self.risks, 1):
            confidence_tag = f"[{risk.confidence.upper()}]" if self.config.get('confidence_levels', True) else ""
            lines.append(f"{i}. {risk.title} {confidence_tag}")
            lines.append(f"   {risk.content}")
            if self.config.get('explain_mode', False):
                lines.append(f"   Supporting metrics: {risk.supporting_metrics}")
            lines.append("")
        
        lines.append("RECOMMENDED ACTIONS:")
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"{i}. {rec.title}")
            lines.append(f"   {rec.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_email_summary(self) -> str:
        """Generate short email-ready summary (6-8 sentences)."""
        # Get key metrics
        summary_kpis = self.kpis.get('summary_kpis', {})
        growth_metrics = self.kpis.get('growth_metrics', {})
        
        total_revenue = summary_kpis.get('total_revenue', 0)
        yoy_growth = growth_metrics.get('latest_revenue_yoy', 0)
        
        # Build concise summary
        lines = []
        
        # Sentence 1: Overview
        lines.append(
            f"Financial review for period {self.df['posting_date'].min().strftime('%b %Y')} "
            f"to {self.df['posting_date'].max().strftime('%b %Y')}."
        )
        
        # Sentence 2: Revenue
        if not np.isnan(yoy_growth):
            direction = "growth" if yoy_growth > 0 else "decline"
            lines.append(
                f"Revenue totaled €{abs(total_revenue)/1000:.1f}K with {abs(yoy_growth):.1f}% YoY {direction}."
            )
        
        # Sentence 3: Top insight
        if self.insights:
            lines.append(self.insights[0].content)
        
        # Sentence 4: Top risk
        if self.risks:
            lines.append(self.risks[0].content)
        
        # Sentence 5-6: Key recommendations
        for rec in self.recommendations[:2]:
            lines.append(f"{rec.title}: {rec.content.split('.')[0]}.")
        
        # Final sentence
        lines.append("Detailed analysis and supporting data available in the full report.")
        
        return " ".join(lines)


def generate_commentary(
    df: pd.DataFrame,
    kpis: Dict,
    trends: Dict,
    aging: Dict,
    anomalies: Dict,
    config: Optional[Dict] = None
) -> CommentaryResult:
    """
    Convenience function to generate commentary.
    
    Args:
        df: Normalized FAGL DataFrame
        kpis: KPI results
        trends: Trend results
        aging: Aging results
        anomalies: Anomaly results
        config: Configuration dictionary
    
    Returns:
        CommentaryResult object
    """
    generator = CommentaryGenerator(df, kpis, trends, aging, anomalies, config)
    return generator.generate_all()

