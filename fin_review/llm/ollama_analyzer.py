"""LLM-Powered Financial Analysis using Ollama (Free & Local)."""

import json
from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
import requests
from pathlib import Path

logger = structlog.get_logger(__name__)


@dataclass
class LLMAnalysis:
    """Container for LLM-generated analysis."""
    executive_summary: str
    key_insights: List[str]
    risk_assessment: str
    recommendations: List[str]
    trend_analysis: str
    anomaly_explanations: List[str]
    model_used: str


class OllamaFinancialAnalyzer:
    """
    LLM-powered financial analysis using Ollama (100% free and local).
    
    Provides intelligent, context-aware analysis of financial data.
    """
    
    def __init__(self, model: str = "llama3.1:8b", ollama_host: str = "http://localhost:11434"):
        """
        Initialize Ollama Financial Analyzer.
        
        Args:
            model: Ollama model to use (default: llama3.1:8b)
            ollama_host: Ollama server host (default: http://localhost:11434)
        """
        self.model = model
        self.ollama_host = ollama_host
        self.available = self._check_ollama_available()
        
        if self.available:
            logger.info("Ollama LLM initialized successfully", model=model)
        else:
            logger.warning("Ollama not available - using fallback mode", 
                         instructions="Install Ollama from https://ollama.ai and run 'ollama pull llama3.1:8b'")
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available and running."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call Ollama API with the given prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            
        Returns:
            LLM response text
        """
        if not self.available:
            return self._fallback_analysis(prompt)
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                logger.error("Ollama API error", status=response.status_code)
                return self._fallback_analysis(prompt)
                
        except Exception as e:
            logger.error("Ollama call failed", error=str(e))
            return self._fallback_analysis(prompt)
    
    def _fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis when Ollama is not available."""
        return f"[LLM Analysis Not Available - Ollama not running. Please install Ollama and run 'ollama pull {self.model}']"
    
    def analyze_financial_data(
        self, 
        kpis: Dict[str, Any],
        ratios: List[Any],
        going_concern: Any,
        abcotd_data: Dict[str, Any],
        anomalies: Optional[List[Any]] = None
    ) -> LLMAnalysis:
        """
        Perform comprehensive LLM-powered financial analysis.
        
        Args:
            kpis: Financial KPIs dictionary
            ratios: List of financial ratios
            going_concern: Going concern assessment
            abcotd_data: ABCOTD analysis data
            anomalies: List of detected anomalies (optional)
            
        Returns:
            LLMAnalysis object with comprehensive insights
        """
        logger.info("Starting LLM-powered financial analysis")
        
        # Prepare financial context
        context = self._prepare_context(kpis, ratios, going_concern, abcotd_data, anomalies)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(context)
        
        # Generate key insights
        key_insights = self._generate_key_insights(context)
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(context, ratios, going_concern)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(context, ratios, going_concern)
        
        # Generate trend analysis
        trend_analysis = self._generate_trend_analysis(context, abcotd_data)
        
        # Generate anomaly explanations
        anomaly_explanations = self._generate_anomaly_explanations(context, anomalies) if anomalies else []
        
        return LLMAnalysis(
            executive_summary=executive_summary,
            key_insights=key_insights,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            trend_analysis=trend_analysis,
            anomaly_explanations=anomaly_explanations,
            model_used=self.model if self.available else "fallback"
        )
    
    def _prepare_context(
        self, 
        kpis: Dict[str, Any],
        ratios: List[Any],
        going_concern: Any,
        abcotd_data: Dict[str, Any],
        anomalies: Optional[List[Any]] = None
    ) -> str:
        """Prepare financial context for LLM analysis."""
        
        # Extract key metrics
        context_parts = []
        
        # Going concern status
        context_parts.append(f"Going Concern Status: {going_concern.overall_status.upper()}")
        context_parts.append(f"Liquidity Score: {going_concern.liquidity_score:.1f}/100")
        context_parts.append(f"Solvency Score: {going_concern.solvency_score:.1f}/100")
        context_parts.append(f"Cash Flow Score: {going_concern.cash_flow_score:.1f}/100")
        
        # Key ratios
        context_parts.append("\nKey Financial Ratios:")
        applicable_ratios = [r for r in ratios if r.applicable]
        for ratio in applicable_ratios[:10]:  # Top 10 ratios
            context_parts.append(f"- {ratio.ratio_name.replace('_', ' ').title()}: {ratio.value:.4f} ({ratio.status})")
        
        # ABCOTD summary
        context_parts.append("\nTop Financial Categories (ABCOTD):")
        for category, amount in list(abcotd_data.items())[:10]:  # Top 10
            if isinstance(amount, (int, float)):
                context_parts.append(f"- {category}: лв {amount:,.2f}")
        
        # Anomalies
        if anomalies:
            context_parts.append(f"\nDetected Anomalies: {len(anomalies)}")
        
        return "\n".join(context_parts)
    
    def _generate_executive_summary(self, context: str) -> str:
        """Generate executive summary using LLM."""
        
        system_prompt = """You are an expert financial analyst specializing in Bulgarian accounting, 
        IFRS standards, and going concern assessments. Provide clear, actionable insights for C-level executives.
        Focus on Bulgarian business context and use Bulgarian currency (лв - Bulgarian Lev) where applicable."""
        
        user_prompt = f"""Based on the following financial data for a Bulgarian company in 2024, 
        provide a comprehensive executive summary (3-4 paragraphs):

{context}

The summary should:
1. Highlight overall financial health and performance
2. Identify key achievements and concerns
3. Provide context for major metrics
4. Be written in professional business language suitable for board presentations

Executive Summary:"""
        
        return self._call_ollama(user_prompt, system_prompt)
    
    def _generate_key_insights(self, context: str) -> List[str]:
        """Generate key insights using LLM."""
        
        system_prompt = """You are an expert financial analyst. Provide specific, actionable insights 
        based on financial data. Each insight should be concise (1-2 sentences) and highlight important findings."""
        
        user_prompt = f"""Based on this financial data:

{context}

Provide 5-7 key insights. Format each as a bullet point. Focus on:
- Performance highlights
- Areas of concern
- Trends and patterns
- Competitive advantages
- Operational efficiency

Key Insights (return as a JSON array of strings):"""
        
        response = self._call_ollama(user_prompt, system_prompt)
        
        # Parse insights from response
        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                insights.append(line.lstrip('-•* ').strip())
            elif line and not line.startswith('[') and not line.startswith('{'):
                if len(line) > 20:  # Filter out very short lines
                    insights.append(line)
        
        return insights[:7] if insights else ["Analysis pending - Ollama not available"]
    
    def _generate_risk_assessment(self, context: str, ratios: List[Any], going_concern: Any) -> str:
        """Generate risk assessment using LLM."""
        
        system_prompt = """You are a risk assessment expert specializing in financial analysis. 
        Provide comprehensive risk evaluation focusing on liquidity, solvency, and operational risks."""
        
        # Identify concerning ratios
        critical_ratios = [r for r in ratios if r.applicable and r.status == 'critical']
        warning_ratios = [r for r in ratios if r.applicable and r.status == 'warning']
        
        user_prompt = f"""Based on this financial data:

{context}

Critical Ratios: {len(critical_ratios)}
Warning Ratios: {len(warning_ratios)}
Going Concern Status: {going_concern.overall_status}

Provide a comprehensive risk assessment (2-3 paragraphs) covering:
1. Immediate risks requiring attention
2. Medium-term concerns
3. Strategic risks
4. Overall risk profile

Risk Assessment:"""
        
        return self._call_ollama(user_prompt, system_prompt)
    
    def _generate_recommendations(self, context: str, ratios: List[Any], going_concern: Any) -> List[str]:
        """Generate actionable recommendations using LLM."""
        
        system_prompt = """You are a strategic financial advisor. Provide specific, actionable recommendations 
        that management can implement to improve financial performance and mitigate risks."""
        
        user_prompt = f"""Based on this financial analysis:

{context}

Liquidity Score: {going_concern.liquidity_score:.1f}/100
Solvency Score: {going_concern.solvency_score:.1f}/100
Cash Flow Score: {going_concern.cash_flow_score:.1f}/100

Provide 5-8 specific, prioritized recommendations. Each should be:
- Actionable (clear steps)
- Measurable (specific targets)
- Realistic (achievable)
- Impactful (significant value)

Format as bullet points.

Recommendations:"""
        
        response = self._call_ollama(user_prompt, system_prompt)
        
        # Parse recommendations
        recommendations = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                recommendations.append(line.lstrip('-•*0123456789. ').strip())
            elif line and len(line) > 30:  # Longer lines might be recommendations
                recommendations.append(line)
        
        return recommendations[:8] if recommendations else ["Recommendations pending - Ollama not available"]
    
    def _generate_trend_analysis(self, context: str, abcotd_data: Dict[str, Any]) -> str:
        """Generate trend analysis using LLM."""
        
        system_prompt = """You are a financial trends analyst. Identify patterns, seasonality, 
        and significant trends in financial data."""
        
        user_prompt = f"""Analyze the trends in this Bulgarian company's financial data:

{context}

Provide a trend analysis (2-3 paragraphs) covering:
1. Revenue and expense trends
2. Seasonal patterns (if any)
3. Growth trajectory
4. Emerging patterns

Trend Analysis:"""
        
        return self._call_ollama(user_prompt, system_prompt)
    
    def _generate_anomaly_explanations(self, context: str, anomalies: List[Any]) -> List[str]:
        """Generate explanations for detected anomalies using LLM."""
        
        if not anomalies or len(anomalies) == 0:
            return []
        
        system_prompt = """You are an expert in financial anomaly analysis. Explain why anomalies 
        might have occurred and their potential business implications."""
        
        user_prompt = f"""Given this financial context:

{context}

{len(anomalies)} anomalies were detected in the financial data.

For each anomaly, provide:
1. Possible business reasons
2. Whether it's concerning or expected
3. Recommended follow-up actions

Provide 3-5 potential explanations for these anomalies:"""
        
        response = self._call_ollama(user_prompt, system_prompt)
        
        # Parse explanations
        explanations = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                explanations.append(line.lstrip('-•* ').strip())
            elif line and len(line) > 30:
                explanations.append(line)
        
        return explanations[:5] if explanations else []
    
    def answer_question(self, context: str, question: str) -> str:
        """
        Answer a natural language question about the financial data.
        
        Args:
            context: Financial context
            question: User's question
            
        Returns:
            Answer to the question
        """
        system_prompt = """You are a financial expert assistant. Answer questions about financial 
        data clearly and accurately. Use specific numbers and cite your reasoning."""
        
        user_prompt = f"""Financial Context:
{context}

Question: {question}

Provide a clear, concise answer with specific details and reasoning:"""
        
        return self._call_ollama(user_prompt, system_prompt)
    
    def generate_multilingual_summary(self, analysis: LLMAnalysis, language: str = "bulgarian") -> str:
        """
        Generate summary in specified language.
        
        Args:
            analysis: LLMAnalysis object
            language: Target language (bulgarian, english, german, etc.)
            
        Returns:
            Translated summary
        """
        system_prompt = f"""You are a professional translator specializing in financial documents. 
        Translate the following financial analysis to {language} while maintaining accuracy of 
        financial terms and numbers."""
        
        user_prompt = f"""Translate this financial analysis to {language}:

Executive Summary:
{analysis.executive_summary}

Key Insights:
{chr(10).join(f'- {insight}' for insight in analysis.key_insights)}

Risk Assessment:
{analysis.risk_assessment}

Maintain all numbers, percentages, and financial terms accurately.

Translation:"""
        
        return self._call_ollama(user_prompt, system_prompt)


def analyze_with_ollama(
    kpis: Dict[str, Any],
    ratios: List[Any],
    going_concern: Any,
    abcotd_data: Dict[str, Any],
    anomalies: Optional[List[Any]] = None,
    model: str = "llama3.1:8b"
) -> LLMAnalysis:
    """
    Convenience function for Ollama-powered financial analysis.
    
    Args:
        kpis: Financial KPIs
        ratios: Financial ratios
        going_concern: Going concern assessment
        abcotd_data: ABCOTD analysis data
        anomalies: Detected anomalies (optional)
        model: Ollama model to use
        
    Returns:
        LLMAnalysis object
    """
    analyzer = OllamaFinancialAnalyzer(model=model)
    return analyzer.analyze_financial_data(kpis, ratios, going_concern, abcotd_data, anomalies)

