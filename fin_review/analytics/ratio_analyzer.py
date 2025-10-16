"""Comprehensive Financial Ratio Analysis for Going Concern Assessment."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import structlog
from datetime import datetime, date

logger = structlog.get_logger(__name__)


@dataclass
class RatioResult:
    """Container for financial ratio analysis results."""
    ratio_name: str
    value: float
    benchmark: str
    interpretation: str
    category: str
    formula: str
    status: str  # 'excellent', 'good', 'warning', 'critical'
    applicable: bool = True
    missing_data: Optional[List[str]] = None


@dataclass
class GoingConcernAssessment:
    """Container for going concern assessment results."""
    overall_status: str  # 'strong', 'adequate', 'concerning', 'critical'
    liquidity_score: float
    solvency_score: float
    cash_flow_score: float
    key_risks: List[str]
    key_strengths: List[str]
    recommendations: List[str]
    detailed_analysis: str


class FinancialRatioAnalyzer:
    """Comprehensive financial ratio analysis for going concern assessment."""
    
    def __init__(self, config=None):
        """
        Initialize financial ratio analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.ratios: List[RatioResult] = []
        self.balance_sheet_data: Optional[pd.DataFrame] = None
        self.income_statement_data: Optional[pd.DataFrame] = None
        self.cash_flow_data: Optional[pd.DataFrame] = None
        
        # Define ratio configurations
        self.ratio_configs = {
            # Liquidity Ratios
            'current_ratio': {
                'formula': 'Current Assets / Current Liabilities',
                'benchmark': '> 1.5 is good, < 1 is concern',
                'category': 'Liquidity',
                'thresholds': {'excellent': 2.0, 'good': 1.5, 'warning': 1.0, 'critical': 0.5}
            },
            'quick_ratio': {
                'formula': '(Current Assets - Inventories) / Current Liabilities',
                'benchmark': '> 1 is healthy',
                'category': 'Liquidity',
                'thresholds': {'excellent': 1.5, 'good': 1.0, 'warning': 0.8, 'critical': 0.5}
            },
            'cash_ratio': {
                'formula': '(Cash + Marketable Securities) / Current Liabilities',
                'benchmark': '> 0.5 is okay, > 1 is strong',
                'category': 'Liquidity',
                'thresholds': {'excellent': 1.0, 'good': 0.5, 'warning': 0.3, 'critical': 0.1}
            },
            'operating_cash_flow_ratio': {
                'formula': 'Cash Flow from Operations / Current Liabilities',
                'benchmark': '> 1 is ideal',
                'category': 'Liquidity',
                'thresholds': {'excellent': 1.5, 'good': 1.0, 'warning': 0.8, 'critical': 0.5}
            },
            'working_capital': {
                'formula': 'Current Assets - Current Liabilities',
                'benchmark': 'Positive value preferred',
                'category': 'Liquidity',
                'thresholds': {'excellent': 1000000, 'good': 500000, 'warning': 0, 'critical': -500000}
            },
            'net_working_capital_ratio': {
                'formula': '(Current Assets - Current Liabilities) / Total Assets',
                'benchmark': '> 0.1 is decent',
                'category': 'Liquidity',
                'thresholds': {'excellent': 0.2, 'good': 0.1, 'warning': 0.05, 'critical': 0.0}
            },
            
            # Solvency Ratios
            'debt_to_equity_ratio': {
                'formula': 'Total Debt / Total Equity',
                'benchmark': '< 1.5 is typical; > 2 is high risk',
                'category': 'Solvency',
                'thresholds': {'excellent': 0.5, 'good': 1.5, 'warning': 2.0, 'critical': 3.0}
            },
            'equity_ratio': {
                'formula': 'Total Equity / Total Assets',
                'benchmark': '> 0.4 is good',
                'category': 'Solvency',
                'thresholds': {'excellent': 0.6, 'good': 0.4, 'warning': 0.3, 'critical': 0.2}
            },
            'debt_ratio': {
                'formula': 'Total Debt / Total Assets',
                'benchmark': '< 0.5 preferred',
                'category': 'Solvency',
                'thresholds': {'excellent': 0.3, 'good': 0.5, 'warning': 0.7, 'critical': 0.8}
            },
            'interest_coverage_ratio': {
                'formula': 'EBIT / Interest Expense',
                'benchmark': '> 3 is strong, < 1.5 is concerning',
                'category': 'Solvency',
                'thresholds': {'excellent': 5.0, 'good': 3.0, 'warning': 1.5, 'critical': 1.0}
            },
            'fixed_charge_coverage_ratio': {
                'formula': '(EBIT + Lease Payments) / (Interest + Lease Payments)',
                'benchmark': '> 2 is safe',
                'category': 'Solvency',
                'thresholds': {'excellent': 3.0, 'good': 2.0, 'warning': 1.5, 'critical': 1.0}
            },
            'long_term_debt_to_capitalization': {
                'formula': 'Long-term Debt / (Long-term Debt + Equity)',
                'benchmark': '< 0.5 ideal',
                'category': 'Solvency',
                'thresholds': {'excellent': 0.3, 'good': 0.5, 'warning': 0.7, 'critical': 0.8}
            },
            
            # Cash Flow Ratios
            'cash_flow_to_debt_ratio': {
                'formula': 'Operating Cash Flow / Total Debt',
                'benchmark': '> 0.2–0.3 is healthy',
                'category': 'Cash Flow',
                'thresholds': {'excellent': 0.4, 'good': 0.3, 'warning': 0.2, 'critical': 0.1}
            },
            'free_cash_flow': {
                'formula': 'Operating Cash Flow - Capital Expenditures',
                'benchmark': 'Positive value is good',
                'category': 'Cash Flow',
                'thresholds': {'excellent': 1000000, 'good': 500000, 'warning': 0, 'critical': -500000}
            },
            'free_cash_flow_to_revenue': {
                'formula': 'Free Cash Flow / Revenue',
                'benchmark': '> 5% is considered healthy',
                'category': 'Cash Flow',
                'thresholds': {'excellent': 0.1, 'good': 0.05, 'warning': 0.02, 'critical': 0.0}
            },
            'current_liability_coverage_ratio': {
                'formula': 'Free Cash Flow / Current Liabilities',
                'benchmark': '> 1 is ideal',
                'category': 'Cash Flow',
                'thresholds': {'excellent': 1.5, 'good': 1.0, 'warning': 0.8, 'critical': 0.5}
            },
            
            # Profitability Ratios
            'net_profit_margin': {
                'formula': 'Net Income / Revenue',
                'benchmark': 'Varies by industry, but positive is essential',
                'category': 'Profitability',
                'thresholds': {'excellent': 0.15, 'good': 0.10, 'warning': 0.05, 'critical': 0.0}
            },
            'return_on_assets': {
                'formula': 'Net Income / Total Assets',
                'benchmark': '> 5% generally decent',
                'category': 'Profitability',
                'thresholds': {'excellent': 0.10, 'good': 0.05, 'warning': 0.03, 'critical': 0.0}
            },
            'return_on_equity': {
                'formula': 'Net Income / Equity',
                'benchmark': '> 10–15% is strong',
                'category': 'Profitability',
                'thresholds': {'excellent': 0.20, 'good': 0.15, 'warning': 0.10, 'critical': 0.05}
            },
            'asset_turnover': {
                'formula': 'Revenue / Total Assets',
                'benchmark': '> 1 indicates efficient use of assets',
                'category': 'Efficiency',
                'thresholds': {'excellent': 1.5, 'good': 1.0, 'warning': 0.8, 'critical': 0.5}
            }
        }
    
    def analyze(self, mapped_df: pd.DataFrame) -> Tuple[List[RatioResult], GoingConcernAssessment]:
        """
        Perform comprehensive financial ratio analysis.
        
        Args:
            mapped_df: Mapped financial data with ABCOTD classifications
            
        Returns:
            Tuple of (ratios, going_concern_assessment)
        """
        logger.info("Starting comprehensive financial ratio analysis")
        
        # Prepare financial statements data
        self._prepare_financial_statements(mapped_df)
        
        # Calculate all applicable ratios
        self._calculate_ratios()
        
        # Perform going concern assessment
        going_concern = self._assess_going_concern()
        
        logger.info("Financial ratio analysis completed", 
                   ratios_calculated=len(self.ratios),
                   applicable_ratios=len([r for r in self.ratios if r.applicable]))
        
        return self.ratios, going_concern
    
    def _prepare_financial_statements(self, mapped_df: pd.DataFrame):
        """Prepare financial statements data from mapped transactions."""
        logger.info("Preparing financial statements data")
        
        # Aggregate by ABCOTD categories
        aggregated = mapped_df.groupby(['ABCOTD', 'bucket']).agg({
            'amount': 'sum'
        }).reset_index()
        
        # Create balance sheet data
        self.balance_sheet_data = self._create_balance_sheet(aggregated)
        
        # Create income statement data
        self.income_statement_data = self._create_income_statement(aggregated)
        
        # Create cash flow data (estimated from available data)
        self.cash_flow_data = self._create_cash_flow_statement(aggregated)
        
        logger.info("Financial statements prepared",
                   balance_sheet_items=len(self.balance_sheet_data),
                   income_statement_items=len(self.income_statement_data),
                   cash_flow_items=len(self.cash_flow_data))
    
    def _create_balance_sheet(self, aggregated: pd.DataFrame) -> pd.DataFrame:
        """Create balance sheet from aggregated ABCOTD data."""
        balance_sheet = {}
        
        # Current Assets
        current_assets = aggregated[
            aggregated['ABCOTD'].isin([
                'Cash and cash equivalents',
                'Inventory',
                'Receivables - trade accounts',
                'Other receivables',
                'Prepaid expenses and accrued income'
            ])
        ]['amount'].sum()
        balance_sheet['Current Assets'] = abs(current_assets)
        
        # Non-Current Assets
        non_current_assets = aggregated[
            aggregated['ABCOTD'].isin([
                'Property, plant, and equipment',
                'Intangibles - other',
                'Leases - right of use assets',
                'Deferred tax asset or liability'
            ])
        ]['amount'].sum()
        balance_sheet['Non-Current Assets'] = abs(non_current_assets)
        
        # Total Assets
        balance_sheet['Total Assets'] = balance_sheet['Current Assets'] + balance_sheet['Non-Current Assets']
        
        # Current Liabilities
        current_liabilities = aggregated[
            aggregated['ABCOTD'].isin([
                'Payables - trade accounts',
                'Other payables',
                'Deferred revenue'
            ])
        ]['amount'].sum()
        balance_sheet['Current Liabilities'] = abs(current_liabilities)
        
        # Non-Current Liabilities
        non_current_liabilities = aggregated[
            aggregated['ABCOTD'].isin([
                'Lease liabilities',
                'Deferred tax asset or liability'
            ])
        ]['amount'].sum()
        balance_sheet['Non-Current Liabilities'] = abs(non_current_liabilities)
        
        # Total Liabilities
        balance_sheet['Total Liabilities'] = balance_sheet['Current Liabilities'] + balance_sheet['Non-Current Liabilities']
        
        # Equity
        equity = aggregated[aggregated['ABCOTD'] == 'Equity']['amount'].sum()
        balance_sheet['Total Equity'] = abs(equity)
        
        return pd.DataFrame([balance_sheet])
    
    def _create_income_statement(self, aggregated: pd.DataFrame) -> pd.DataFrame:
        """Create income statement from aggregated ABCOTD data."""
        income_statement = {}
        
        # Revenue
        revenue = aggregated[aggregated['ABCOTD'] == 'Revenue']['amount'].sum()
        income_statement['Revenue'] = abs(revenue)
        
        # Cost of Sales
        cost_of_sales = aggregated[aggregated['ABCOTD'] == 'Cost of sales']['amount'].sum()
        income_statement['Cost of Sales'] = abs(cost_of_sales)
        
        # Gross Profit
        income_statement['Gross Profit'] = income_statement['Revenue'] - income_statement['Cost of Sales']
        
        # Operating Expenses
        operating_expenses = aggregated[aggregated['ABCOTD'] == 'Operating expenses']['amount'].sum()
        income_statement['Operating Expenses'] = abs(operating_expenses)
        
        # Payroll
        payroll = aggregated[aggregated['ABCOTD'] == 'Payroll']['amount'].sum()
        income_statement['Payroll'] = abs(payroll)
        
        # Depreciation
        depreciation = aggregated[
            aggregated['ABCOTD'].isin([
                'Depreciation of property, plant, and equipment',
                'Depreciation/amortization of rights of use assets',
                'Amortization of intangibles - other'
            ])
        ]['amount'].sum()
        income_statement['Depreciation'] = abs(depreciation)
        
        # Other Expenses
        other_expenses = aggregated[aggregated['ABCOTD'] == 'Other expenses']['amount'].sum()
        income_statement['Other Expenses'] = abs(other_expenses)
        
        # Total Operating Expenses
        income_statement['Total Operating Expenses'] = (
            income_statement['Operating Expenses'] + 
            income_statement['Payroll'] + 
            income_statement['Depreciation'] + 
            income_statement['Other Expenses']
        )
        
        # EBIT (Earnings Before Interest and Taxes)
        income_statement['EBIT'] = income_statement['Gross Profit'] - income_statement['Total Operating Expenses']
        
        # Interest Expense (estimated)
        interest_expense = aggregated[aggregated['ABCOTD'] == 'Interest on lease obligations']['amount'].sum()
        income_statement['Interest Expense'] = abs(interest_expense)
        
        # Income Tax
        income_tax = aggregated[aggregated['ABCOTD'] == 'Income tax expense or benefit']['amount'].sum()
        income_statement['Income Tax'] = abs(income_tax)
        
        # Net Income
        income_statement['Net Income'] = (
            income_statement['EBIT'] - 
            income_statement['Interest Expense'] - 
            income_statement['Income Tax']
        )
        
        return pd.DataFrame([income_statement])
    
    def _create_cash_flow_statement(self, aggregated: pd.DataFrame) -> pd.DataFrame:
        """Create cash flow statement from aggregated ABCOTD data."""
        cash_flow = {}
        
        # Operating Cash Flow (estimated from revenue and expenses)
        revenue = aggregated[aggregated['ABCOTD'] == 'Revenue']['amount'].sum()
        operating_expenses = aggregated[
            aggregated['ABCOTD'].isin([
                'Cost of sales',
                'Operating expenses',
                'Payroll',
                'Other expenses'
            ])
        ]['amount'].sum()
        
        # Rough estimate of operating cash flow
        cash_flow['Operating Cash Flow'] = abs(revenue) - abs(operating_expenses)
        
        # Capital Expenditures (estimated from depreciation)
        depreciation = aggregated[
            aggregated['ABCOTD'].isin([
                'Depreciation of property, plant, and equipment',
                'Depreciation/amortization of rights of use assets',
                'Amortization of intangibles - other'
            ])
        ]['amount'].sum()
        
        # Estimate CapEx as 1.5x depreciation (rough approximation)
        cash_flow['Capital Expenditures'] = abs(depreciation) * 1.5
        
        # Free Cash Flow
        cash_flow['Free Cash Flow'] = cash_flow['Operating Cash Flow'] - cash_flow['Capital Expenditures']
        
        # Cash and Cash Equivalents
        cash = aggregated[aggregated['ABCOTD'] == 'Cash and cash equivalents']['amount'].sum()
        cash_flow['Cash and Cash Equivalents'] = abs(cash)
        
        return pd.DataFrame([cash_flow])
    
    def _calculate_ratios(self):
        """Calculate all applicable financial ratios."""
        logger.info("Calculating financial ratios")
        
        for ratio_name, config in self.ratio_configs.items():
            try:
                value = self._calculate_single_ratio(ratio_name, config)
                
                if value is not None:
                    status = self._determine_status(value, config['thresholds'])
                    interpretation = self._get_interpretation(ratio_name, value, status)
                    
                    ratio_result = RatioResult(
                        ratio_name=ratio_name,
                        value=value,
                        benchmark=config['benchmark'],
                        interpretation=interpretation,
                        category=config['category'],
                        formula=config['formula'],
                        status=status,
                        applicable=True
                    )
                else:
                    ratio_result = RatioResult(
                        ratio_name=ratio_name,
                        value=0.0,
                        benchmark=config['benchmark'],
                        interpretation="Not applicable - insufficient data",
                        category=config['category'],
                        formula=config['formula'],
                        status='warning',
                        applicable=False,
                        missing_data=self._get_missing_data(ratio_name)
                    )
                
                self.ratios.append(ratio_result)
                
            except Exception as e:
                logger.warning(f"Could not calculate ratio {ratio_name}: {e}")
                self.ratios.append(RatioResult(
                    ratio_name=ratio_name,
                    value=0.0,
                    benchmark=config['benchmark'],
                    interpretation=f"Calculation error: {str(e)}",
                    category=config['category'],
                    formula=config['formula'],
                    status='critical',
                    applicable=False
                ))
    
    def _calculate_single_ratio(self, ratio_name: str, config: Dict) -> Optional[float]:
        """Calculate a single financial ratio."""
        try:
            if ratio_name == 'current_ratio':
                current_assets = self.balance_sheet_data['Current Assets'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                return current_assets / current_liabilities if current_liabilities != 0 else None
                
            elif ratio_name == 'quick_ratio':
                current_assets = self.balance_sheet_data['Current Assets'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                # Estimate inventory as 20% of current assets (rough approximation)
                inventory = current_assets * 0.2
                quick_assets = current_assets - inventory
                return quick_assets / current_liabilities if current_liabilities != 0 else None
                
            elif ratio_name == 'cash_ratio':
                cash = self.cash_flow_data['Cash and Cash Equivalents'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                return cash / current_liabilities if current_liabilities != 0 else None
                
            elif ratio_name == 'operating_cash_flow_ratio':
                operating_cash_flow = self.cash_flow_data['Operating Cash Flow'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                return operating_cash_flow / current_liabilities if current_liabilities != 0 else None
                
            elif ratio_name == 'working_capital':
                current_assets = self.balance_sheet_data['Current Assets'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                return current_assets - current_liabilities
                
            elif ratio_name == 'net_working_capital_ratio':
                current_assets = self.balance_sheet_data['Current Assets'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                total_assets = self.balance_sheet_data['Total Assets'].iloc[0]
                working_capital = current_assets - current_liabilities
                return working_capital / total_assets if total_assets != 0 else None
                
            elif ratio_name == 'debt_to_equity_ratio':
                total_debt = self.balance_sheet_data['Total Liabilities'].iloc[0]
                total_equity = self.balance_sheet_data['Total Equity'].iloc[0]
                return total_debt / total_equity if total_equity != 0 else None
                
            elif ratio_name == 'equity_ratio':
                total_equity = self.balance_sheet_data['Total Equity'].iloc[0]
                total_assets = self.balance_sheet_data['Total Assets'].iloc[0]
                return total_equity / total_assets if total_assets != 0 else None
                
            elif ratio_name == 'debt_ratio':
                total_debt = self.balance_sheet_data['Total Liabilities'].iloc[0]
                total_assets = self.balance_sheet_data['Total Assets'].iloc[0]
                return total_debt / total_assets if total_assets != 0 else None
                
            elif ratio_name == 'interest_coverage_ratio':
                ebit = self.income_statement_data['EBIT'].iloc[0]
                interest_expense = self.income_statement_data['Interest Expense'].iloc[0]
                return ebit / interest_expense if interest_expense != 0 else None
                
            elif ratio_name == 'cash_flow_to_debt_ratio':
                operating_cash_flow = self.cash_flow_data['Operating Cash Flow'].iloc[0]
                total_debt = self.balance_sheet_data['Total Liabilities'].iloc[0]
                return operating_cash_flow / total_debt if total_debt != 0 else None
                
            elif ratio_name == 'free_cash_flow':
                return self.cash_flow_data['Free Cash Flow'].iloc[0]
                
            elif ratio_name == 'free_cash_flow_to_revenue':
                free_cash_flow = self.cash_flow_data['Free Cash Flow'].iloc[0]
                revenue = self.income_statement_data['Revenue'].iloc[0]
                return free_cash_flow / revenue if revenue != 0 else None
                
            elif ratio_name == 'current_liability_coverage_ratio':
                free_cash_flow = self.cash_flow_data['Free Cash Flow'].iloc[0]
                current_liabilities = self.balance_sheet_data['Current Liabilities'].iloc[0]
                return free_cash_flow / current_liabilities if current_liabilities != 0 else None
                
            elif ratio_name == 'net_profit_margin':
                net_income = self.income_statement_data['Net Income'].iloc[0]
                revenue = self.income_statement_data['Revenue'].iloc[0]
                return net_income / revenue if revenue != 0 else None
                
            elif ratio_name == 'return_on_assets':
                net_income = self.income_statement_data['Net Income'].iloc[0]
                total_assets = self.balance_sheet_data['Total Assets'].iloc[0]
                return net_income / total_assets if total_assets != 0 else None
                
            elif ratio_name == 'return_on_equity':
                net_income = self.income_statement_data['Net Income'].iloc[0]
                total_equity = self.balance_sheet_data['Total Equity'].iloc[0]
                return net_income / total_equity if total_equity != 0 else None
                
            elif ratio_name == 'asset_turnover':
                revenue = self.income_statement_data['Revenue'].iloc[0]
                total_assets = self.balance_sheet_data['Total Assets'].iloc[0]
                return revenue / total_assets if total_assets != 0 else None
                
            # Add more ratios as needed
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error calculating {ratio_name}: {e}")
            return None
    
    def _determine_status(self, value: float, thresholds: Dict[str, float]) -> str:
        """Determine status based on ratio value and thresholds."""
        if value >= thresholds['excellent']:
            return 'excellent'
        elif value >= thresholds['good']:
            return 'good'
        elif value >= thresholds['warning']:
            return 'warning'
        else:
            return 'critical'
    
    def _get_interpretation(self, ratio_name: str, value: float, status: str) -> str:
        """Get interpretation text for a ratio."""
        interpretations = {
            'current_ratio': {
                'excellent': f"Excellent liquidity position (Current Ratio: {value:.2f}). The entity has strong ability to meet short-term obligations.",
                'good': f"Good liquidity position (Current Ratio: {value:.2f}). The entity can comfortably meet short-term obligations.",
                'warning': f"Moderate liquidity concern (Current Ratio: {value:.2f}). The entity may face challenges meeting short-term obligations.",
                'critical': f"Critical liquidity issue (Current Ratio: {value:.2f}). The entity may struggle to meet short-term obligations."
            },
            'quick_ratio': {
                'excellent': f"Excellent quick liquidity (Quick Ratio: {value:.2f}). Strong ability to meet obligations without relying on inventory sales.",
                'good': f"Good quick liquidity (Quick Ratio: {value:.2f}). Adequate liquid assets to meet short-term obligations.",
                'warning': f"Concerning quick liquidity (Quick Ratio: {value:.2f}). Limited liquid assets relative to short-term obligations.",
                'critical': f"Critical quick liquidity issue (Quick Ratio: {value:.2f}). Insufficient liquid assets to meet short-term obligations."
            },
            'cash_ratio': {
                'excellent': f"Excellent cash position (Cash Ratio: {value:.2f}). Strong ability to cover liabilities with cash alone.",
                'good': f"Good cash position (Cash Ratio: {value:.2f}). Adequate cash reserves relative to current liabilities.",
                'warning': f"Moderate cash concern (Cash Ratio: {value:.2f}). Limited cash reserves relative to current liabilities.",
                'critical': f"Critical cash shortage (Cash Ratio: {value:.2f}). Insufficient cash to cover current liabilities."
            },
            'debt_to_equity_ratio': {
                'excellent': f"Excellent capital structure (Debt-to-Equity: {value:.2f}). Low leverage indicates strong financial stability.",
                'good': f"Good capital structure (Debt-to-Equity: {value:.2f}). Moderate leverage with acceptable risk levels.",
                'warning': f"High leverage concern (Debt-to-Equity: {value:.2f}). Elevated debt levels may increase financial risk.",
                'critical': f"Critical leverage issue (Debt-to-Equity: {value:.2f}). Excessive debt levels pose significant solvency risk."
            }
        }
        
        if ratio_name in interpretations and status in interpretations[ratio_name]:
            return interpretations[ratio_name][status]
        else:
            return f"Ratio value: {value:.4f} (Status: {status.title()})"
    
    def _get_missing_data(self, ratio_name: str) -> List[str]:
        """Get list of missing data elements for a ratio."""
        # This would be implemented based on specific ratio requirements
        return []
    
    def _assess_going_concern(self) -> GoingConcernAssessment:
        """Perform comprehensive going concern assessment."""
        logger.info("Performing going concern assessment")
        
        # Calculate scores for each category
        liquidity_score = self._calculate_liquidity_score()
        solvency_score = self._calculate_solvency_score()
        cash_flow_score = self._calculate_cash_flow_score()
        
        # Determine overall status
        overall_status = self._determine_overall_status(liquidity_score, solvency_score, cash_flow_score)
        
        # Identify key risks and strengths
        key_risks = self._identify_key_risks()
        key_strengths = self._identify_key_strengths()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(key_risks)
        
        # Create detailed analysis
        detailed_analysis = self._create_detailed_analysis(overall_status, liquidity_score, solvency_score, cash_flow_score)
        
        return GoingConcernAssessment(
            overall_status=overall_status,
            liquidity_score=liquidity_score,
            solvency_score=solvency_score,
            cash_flow_score=cash_flow_score,
            key_risks=key_risks,
            key_strengths=key_strengths,
            recommendations=recommendations,
            detailed_analysis=detailed_analysis
        )
    
    def _calculate_liquidity_score(self) -> float:
        """Calculate liquidity score (0-100)."""
        liquidity_ratios = [r for r in self.ratios if r.category == 'Liquidity' and r.applicable]
        
        if not liquidity_ratios:
            return 50.0  # Neutral if no data
        
        scores = []
        for ratio in liquidity_ratios:
            if ratio.status == 'excellent':
                scores.append(90)
            elif ratio.status == 'good':
                scores.append(75)
            elif ratio.status == 'warning':
                scores.append(50)
            else:  # critical
                scores.append(25)
        
        return np.mean(scores)
    
    def _calculate_solvency_score(self) -> float:
        """Calculate solvency score (0-100)."""
        solvency_ratios = [r for r in self.ratios if r.category == 'Solvency' and r.applicable]
        
        if not solvency_ratios:
            return 50.0  # Neutral if no data
        
        scores = []
        for ratio in solvency_ratios:
            if ratio.status == 'excellent':
                scores.append(90)
            elif ratio.status == 'good':
                scores.append(75)
            elif ratio.status == 'warning':
                scores.append(50)
            else:  # critical
                scores.append(25)
        
        return np.mean(scores)
    
    def _calculate_cash_flow_score(self) -> float:
        """Calculate cash flow score (0-100)."""
        cash_flow_ratios = [r for r in self.ratios if r.category == 'Cash Flow' and r.applicable]
        
        if not cash_flow_ratios:
            return 50.0  # Neutral if no data
        
        scores = []
        for ratio in cash_flow_ratios:
            if ratio.status == 'excellent':
                scores.append(90)
            elif ratio.status == 'good':
                scores.append(75)
            elif ratio.status == 'warning':
                scores.append(50)
            else:  # critical
                scores.append(25)
        
        return np.mean(scores)
    
    def _determine_overall_status(self, liquidity_score: float, solvency_score: float, cash_flow_score: float) -> str:
        """Determine overall going concern status."""
        overall_score = (liquidity_score + solvency_score + cash_flow_score) / 3
        
        if overall_score >= 80:
            return 'strong'
        elif overall_score >= 60:
            return 'adequate'
        elif overall_score >= 40:
            return 'concerning'
        else:
            return 'critical'
    
    def _identify_key_risks(self) -> List[str]:
        """Identify key going concern risks."""
        risks = []
        
        critical_ratios = [r for r in self.ratios if r.status == 'critical' and r.applicable]
        
        for ratio in critical_ratios:
            if ratio.category == 'Liquidity':
                risks.append(f"Critical liquidity risk: {ratio.ratio_name.replace('_', ' ').title()} indicates severe short-term financial stress")
            elif ratio.category == 'Solvency':
                risks.append(f"Critical solvency risk: {ratio.ratio_name.replace('_', ' ').title()} indicates high long-term financial risk")
            elif ratio.category == 'Cash Flow':
                risks.append(f"Critical cash flow risk: {ratio.ratio_name.replace('_', ' ').title()} indicates severe cash generation problems")
        
        warning_ratios = [r for r in self.ratios if r.status == 'warning' and r.applicable]
        for ratio in warning_ratios[:3]:  # Top 3 warning ratios
            risks.append(f"Moderate risk: {ratio.ratio_name.replace('_', ' ').title()} requires monitoring")
        
        return risks[:5]  # Limit to top 5 risks
    
    def _identify_key_strengths(self) -> List[str]:
        """Identify key financial strengths."""
        strengths = []
        
        excellent_ratios = [r for r in self.ratios if r.status == 'excellent' and r.applicable]
        
        for ratio in excellent_ratios:
            if ratio.category == 'Liquidity':
                strengths.append(f"Strong liquidity: {ratio.ratio_name.replace('_', ' ').title()} indicates excellent short-term financial health")
            elif ratio.category == 'Solvency':
                strengths.append(f"Strong solvency: {ratio.ratio_name.replace('_', ' ').title()} indicates excellent long-term financial stability")
            elif ratio.category == 'Cash Flow':
                strengths.append(f"Strong cash flow: {ratio.ratio_name.replace('_', ' ').title()} indicates excellent cash generation")
        
        return strengths[:5]  # Limit to top 5 strengths
    
    def _generate_recommendations(self, key_risks: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        critical_liquidity = any('liquidity risk' in risk.lower() for risk in key_risks)
        critical_solvency = any('solvency risk' in risk.lower() for risk in key_risks)
        critical_cash_flow = any('cash flow risk' in risk.lower() for risk in key_risks)
        
        if critical_liquidity:
            recommendations.append("URGENT: Implement immediate liquidity management measures including cash flow forecasting and working capital optimization")
        
        if critical_solvency:
            recommendations.append("CRITICAL: Restructure debt obligations and consider equity infusion to improve capital structure")
        
        if critical_cash_flow:
            recommendations.append("HIGH PRIORITY: Implement aggressive cash flow improvement measures including cost reduction and revenue enhancement")
        
        recommendations.append("Establish monthly financial monitoring and early warning systems")
        recommendations.append("Develop contingency plans for various stress scenarios")
        recommendations.append("Consider external financing options to strengthen financial position")
        
        return recommendations[:6]  # Limit to top 6 recommendations
    
    def _create_detailed_analysis(self, overall_status: str, liquidity_score: float, solvency_score: float, cash_flow_score: float) -> str:
        """Create detailed going concern analysis."""
        
        analysis = f"""
COMPREHENSIVE GOING CONCERN ASSESSMENT
=====================================

OVERALL ASSESSMENT: {overall_status.upper()}

The entity's going concern status is assessed as {overall_status.upper()} based on comprehensive analysis of liquidity, solvency, and cash flow metrics.

DETAILED SCORES:
- Liquidity Score: {liquidity_score:.1f}/100
- Solvency Score: {solvency_score:.1f}/100  
- Cash Flow Score: {cash_flow_score:.1f}/100

LIQUIDITY ANALYSIS:
The entity's liquidity position scores {liquidity_score:.1f}/100, indicating {'strong' if liquidity_score >= 75 else 'adequate' if liquidity_score >= 50 else 'concerning' if liquidity_score >= 25 else 'critical'} short-term financial health. This assessment is based on current ratio, quick ratio, cash ratio, and working capital metrics.

SOLVENCY ANALYSIS:
The entity's solvency position scores {solvency_score:.1f}/100, indicating {'strong' if solvency_score >= 75 else 'adequate' if solvency_score >= 50 else 'concerning' if solvency_score >= 25 else 'critical'} long-term financial stability. This assessment considers debt-to-equity ratio, equity ratio, and interest coverage metrics.

CASH FLOW ANALYSIS:
The entity's cash flow generation scores {cash_flow_score:.1f}/100, indicating {'strong' if cash_flow_score >= 75 else 'adequate' if cash_flow_score >= 50 else 'concerning' if cash_flow_score >= 25 else 'critical'} cash generation capability. This assessment is based on operating cash flow ratios and free cash flow metrics.

GOING CONCERN CONCLUSION:
Based on the comprehensive analysis, the entity {'demonstrates strong financial health and is expected to continue operating as a going concern' if overall_status == 'strong' else 'shows adequate financial health with some areas requiring attention, but is expected to continue as a going concern' if overall_status == 'adequate' else 'exhibits concerning financial indicators that require immediate management attention to ensure going concern status' if overall_status == 'concerning' else 'faces critical financial challenges that may threaten its going concern status and requires urgent intervention'}.

This assessment should be reviewed regularly and updated as new financial information becomes available.
"""
        
        return analysis.strip()


def analyze_financial_ratios(mapped_df: pd.DataFrame, config=None) -> Tuple[List[RatioResult], GoingConcernAssessment]:
    """
    Convenience function to perform financial ratio analysis.
    
    Args:
        mapped_df: Mapped financial data with ABCOTD classifications
        config: Configuration object (optional)
        
    Returns:
        Tuple of (ratios, going_concern_assessment)
    """
    analyzer = FinancialRatioAnalyzer(config)
    return analyzer.analyze(mapped_df)
