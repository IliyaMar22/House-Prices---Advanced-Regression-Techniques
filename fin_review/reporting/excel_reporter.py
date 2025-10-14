"""Excel report generation module."""

import pandas as pd
import structlog
from pathlib import Path
from typing import Dict, Optional
import xlsxwriter
from datetime import datetime

logger = structlog.get_logger()


class ExcelReporter:
    """Generates Excel reports with multiple sheets."""
    
    def __init__(self, output_path: Path, config: Optional[Dict] = None):
        """
        Initialize Excel reporter.
        
        Args:
            output_path: Path to output Excel file
            config: Configuration dictionary
        """
        self.output_path = output_path
        self.config = config or {}
        self.writer = None
        self.workbook = None
    
    def generate_report(
        self,
        mapped_data: pd.DataFrame,
        kpis: Dict,
        trends: Dict,
        aging: Dict,
        anomalies: Dict,
        forecasts: Optional[Dict] = None
    ):
        """
        Generate complete Excel report.
        
        Args:
            mapped_data: Normalized and mapped FAGL DataFrame
            kpis: KPI results
            trends: Trend analysis results
            aging: Aging analysis results
            anomalies: Anomaly detection results
            forecasts: Forecast results (optional)
        """
        logger.info(f"Generating Excel report: {self.output_path}")
        
        # Create Excel writer
        self.writer = pd.ExcelWriter(self.output_path, engine='xlsxwriter')
        self.workbook = self.writer.book
        
        # Define formats
        header_format = self.workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        currency_format = self.workbook.add_format({'num_format': '€#,##0.00'})
        percent_format = self.workbook.add_format({'num_format': '0.0%'})
        
        # Generate sheets based on config
        requested_sheets = self.config.get('excel_sheets', [
            'summary', 'monthly_trends', 'kpis', 'ar_aging', 'ap_aging',
            'top_vendors', 'top_customers', 'anomalies', 'forecast'
        ])
        
        if 'summary' in requested_sheets:
            self._create_summary_sheet(kpis, header_format, currency_format, percent_format)
        
        if 'monthly_trends' in requested_sheets:
            self._create_monthly_trends_sheet(kpis.get('monthly_kpis'), header_format, currency_format)
        
        if 'kpis' in requested_sheets:
            self._create_kpis_sheet(kpis, header_format, currency_format, percent_format)
        
        if 'ar_aging' in requested_sheets:
            self._create_ar_aging_sheet(aging, header_format, currency_format, percent_format)
        
        if 'ap_aging' in requested_sheets:
            self._create_ap_aging_sheet(aging, header_format, currency_format, percent_format)
        
        if 'top_vendors' in requested_sheets:
            self._create_top_vendors_sheet(mapped_data, header_format, currency_format)
        
        if 'top_customers' in requested_sheets:
            self._create_top_customers_sheet(mapped_data, header_format, currency_format)
        
        if 'anomalies' in requested_sheets:
            self._create_anomalies_sheet(anomalies, header_format, currency_format, percent_format)
        
        if 'forecast' in requested_sheets and forecasts:
            self._create_forecast_sheet(forecasts, header_format, currency_format)
        
        # Close writer
        self.writer.close()
        
        logger.info(f"Excel report generated successfully: {self.output_path}")
    
    def _create_summary_sheet(self, kpis: Dict, header_format, currency_format, percent_format):
        """Create summary overview sheet."""
        summary_kpis = kpis.get('summary_kpis', {})
        growth_metrics = kpis.get('growth_metrics', {})
        ratios = kpis.get('ratios', {})
        
        # Create summary data
        data = []
        
        # Revenue section
        data.append(['REVENUE METRICS', ''])
        data.append(['Total Revenue', summary_kpis.get('total_revenue', 0)])
        if 'latest_revenue_yoy' in growth_metrics:
            data.append(['YoY Growth %', growth_metrics['latest_revenue_yoy'] / 100])
        if 'revenue_run_rate' in ratios:
            data.append(['Revenue Run Rate (Annual)', ratios['revenue_run_rate']])
        data.append(['', ''])
        
        # Expense section
        data.append(['EXPENSE METRICS', ''])
        data.append(['Total OPEX', summary_kpis.get('total_opex', 0)])
        data.append(['Total Payroll', summary_kpis.get('total_payroll', 0)])
        data.append(['Total Expenses', summary_kpis.get('total_expenses', 0)])
        data.append(['', ''])
        
        # Profitability section
        data.append(['PROFITABILITY', ''])
        data.append(['Net Profit', summary_kpis.get('net_profit', 0)])
        data.append(['Net Margin %', summary_kpis.get('net_margin_pct', 0) / 100])
        if 'avg_gross_margin' in ratios:
            data.append(['Avg Gross Margin %', ratios['avg_gross_margin'] / 100])
        data.append(['', ''])
        
        # Efficiency section
        data.append(['EFFICIENCY RATIOS', ''])
        if 'latest_opex_ratio' in ratios:
            data.append(['OPEX Ratio %', ratios['latest_opex_ratio'] / 100])
        if 'latest_payroll_ratio' in ratios:
            data.append(['Payroll Ratio %', ratios['latest_payroll_ratio'] / 100])
        
        df = pd.DataFrame(data, columns=['Metric', 'Value'])
        df.to_excel(self.writer, sheet_name='Summary', index=False, header=False)
        
        # Apply formats
        worksheet = self.writer.sheets['Summary']
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20, currency_format)
        
        # Apply percent format to rows with %
        for i, row in enumerate(data):
            if len(row) > 0 and '%' in str(row[0]):
                worksheet.write(i, 1, row[1], percent_format)
    
    def _create_monthly_trends_sheet(self, monthly_kpis, header_format, currency_format):
        """Create monthly trends sheet."""
        # Handle both DataFrame and dict (list of records)
        if isinstance(monthly_kpis, list):
            if len(monthly_kpis) == 0:
                return
            monthly_kpis = pd.DataFrame(monthly_kpis)
        
        if monthly_kpis is None or len(monthly_kpis) == 0:
            return
        
        # Select key columns
        cols = ['year_month', 'revenue', 'opex', 'payroll', 'gross_margin_pct', 'opex_ratio']
        available_cols = [c for c in cols if c in monthly_kpis.columns]
        
        df = monthly_kpis[available_cols].copy()
        
        # Format year_month
        if 'year_month' in df.columns:
            df['year_month'] = df['year_month'].dt.strftime('%Y-%m')
        
        df.to_excel(self.writer, sheet_name='Monthly Trends', index=False)
        
        # Apply formats
        worksheet = self.writer.sheets['Monthly Trends']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:D', 15, currency_format)
        
        # Add chart
        chart = self.workbook.add_chart({'type': 'line'})
        chart.add_series({
            'name': 'Revenue',
            'categories': ['Monthly Trends', 1, 0, len(df), 0],
            'values': ['Monthly Trends', 1, 1, len(df), 1],
        })
        if 'opex' in df.columns:
            chart.add_series({
                'name': 'OPEX',
                'categories': ['Monthly Trends', 1, 0, len(df), 0],
                'values': ['Monthly Trends', 1, 2, len(df), 2],
            })
        
        chart.set_title({'name': 'Revenue and OPEX Trends'})
        chart.set_x_axis({'name': 'Month'})
        chart.set_y_axis({'name': 'Amount (€)'})
        chart.set_size({'width': 720, 'height': 400})
        
        worksheet.insert_chart('G2', chart)
    
    def _create_kpis_sheet(self, kpis: Dict, header_format, currency_format, percent_format):
        """Create detailed KPIs sheet."""
        growth_metrics = kpis.get('growth_metrics', {})
        ratios = kpis.get('ratios', {})
        
        data = []
        
        # Growth metrics
        data.append(['GROWTH METRICS', '', ''])
        data.append(['Metric', 'Value', 'Period'])
        
        for key, value in growth_metrics.items():
            if not pd.isna(value):
                metric_name = key.replace('_', ' ').title()
                data.append([metric_name, value, 'Latest'])
        
        data.append(['', '', ''])
        
        # Ratios
        data.append(['FINANCIAL RATIOS', '', ''])
        data.append(['Ratio', 'Value', 'Period'])
        
        for key, value in ratios.items():
            if not pd.isna(value):
                ratio_name = key.replace('_', ' ').title()
                data.append([ratio_name, value, 'Latest'])
        
        df = pd.DataFrame(data)
        df.to_excel(self.writer, sheet_name='KPIs', index=False, header=False)
        
        worksheet = self.writer.sheets['KPIs']
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
    
    def _create_ar_aging_sheet(self, aging: Dict, header_format, currency_format, percent_format):
        """Create AR aging sheet."""
        ar_aging = aging.get('ar_aging')
        ar_summary = aging.get('ar_summary', {})
        
        # Convert list to DataFrame if needed
        if isinstance(ar_aging, list):
            if len(ar_aging) == 0:
                return
            ar_aging = pd.DataFrame(ar_aging)
        
        if ar_aging is None or len(ar_aging) == 0:
            return
        
        ar_aging.to_excel(self.writer, sheet_name='AR Aging', index=False)
        
        worksheet = self.writer.sheets['AR Aging']
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20, currency_format)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15, percent_format)
        
        # Add summary at bottom
        row = len(ar_aging) + 3
        worksheet.write(row, 0, 'Total Outstanding:')
        worksheet.write(row, 1, ar_summary.get('total_outstanding', 0), currency_format)
        worksheet.write(row + 1, 0, 'Overdue %:')
        worksheet.write(row + 1, 1, ar_summary.get('overdue_pct', 0) / 100, percent_format)
        
        # Add chart
        chart = self.workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'AR Aging',
            'categories': ['AR Aging', 1, 0, len(ar_aging), 0],
            'values': ['AR Aging', 1, 1, len(ar_aging), 1],
        })
        chart.set_title({'name': 'Accounts Receivable Aging'})
        chart.set_size({'width': 600, 'height': 400})
        worksheet.insert_chart('F2', chart)
    
    def _create_ap_aging_sheet(self, aging: Dict, header_format, currency_format, percent_format):
        """Create AP aging sheet."""
        ap_aging = aging.get('ap_aging')
        ap_summary = aging.get('ap_summary', {})
        
        # Convert list to DataFrame if needed
        if isinstance(ap_aging, list):
            if len(ap_aging) == 0:
                return
            ap_aging = pd.DataFrame(ap_aging)
        
        if ap_aging is None or len(ap_aging) == 0:
            return
        
        ap_aging.to_excel(self.writer, sheet_name='AP Aging', index=False)
        
        worksheet = self.writer.sheets['AP Aging']
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20, currency_format)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15, percent_format)
        
        # Add summary
        row = len(ap_aging) + 3
        worksheet.write(row, 0, 'Total Outstanding:')
        worksheet.write(row, 1, ap_summary.get('total_outstanding', 0), currency_format)
        worksheet.write(row + 1, 0, 'Overdue %:')
        worksheet.write(row + 1, 1, ap_summary.get('overdue_pct', 0) / 100, percent_format)
    
    def _create_top_vendors_sheet(self, mapped_data: pd.DataFrame, header_format, currency_format):
        """Create top vendors sheet."""
        if 'customer_vendor' not in mapped_data.columns:
            return
        
        opex_data = mapped_data[mapped_data['type'] == 'OPEX']
        
        if len(opex_data) == 0:
            return
        
        top_vendors = opex_data.groupby('customer_vendor').agg({
            'amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        top_vendors.columns = ['Vendor', 'Total Amount', 'Transaction Count']
        top_vendors = top_vendors.sort_values('Total Amount', key=abs, ascending=False).head(20)
        
        top_vendors.to_excel(self.writer, sheet_name='Top Vendors', index=False)
        
        worksheet = self.writer.sheets['Top Vendors']
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20, currency_format)
        worksheet.set_column('C:C', 18)
    
    def _create_top_customers_sheet(self, mapped_data: pd.DataFrame, header_format, currency_format):
        """Create top customers sheet."""
        if 'customer_vendor' not in mapped_data.columns:
            return
        
        revenue_data = mapped_data[mapped_data['type'] == 'Revenue']
        
        if len(revenue_data) == 0:
            return
        
        top_customers = revenue_data.groupby('customer_vendor').agg({
            'amount': 'sum',
            'doc_id': 'count'
        }).reset_index()
        
        top_customers.columns = ['Customer', 'Total Amount', 'Transaction Count']
        top_customers = top_customers.sort_values('Total Amount', key=abs, ascending=False).head(20)
        
        top_customers.to_excel(self.writer, sheet_name='Top Customers', index=False)
        
        worksheet = self.writer.sheets['Top Customers']
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20, currency_format)
        worksheet.set_column('C:C', 18)
    
    def _create_anomalies_sheet(self, anomalies: Dict, header_format, currency_format, percent_format):
        """Create anomalies sheet."""
        anomaly_list = anomalies.get('anomalies', [])
        
        if not anomaly_list:
            return
        
        # Handle both list of Anomaly objects and list of dicts
        data = []
        for anomaly in anomaly_list:
            if hasattr(anomaly, '__dict__'):
                anomaly = anomaly.__dict__
            data.append({
                'Date': anomaly.get('date'),
                'Bucket': anomaly.get('bucket'),
                'Type': anomaly.get('type'),
                'Amount': anomaly.get('amount'),
                'Expected': anomaly.get('expected_amount'),
                'Deviation %': anomaly.get('deviation_pct') / 100,
                'Severity': anomaly.get('severity'),
                'Method': anomaly.get('method'),
                'Explanation': anomaly.get('explanation')
            })
        
        df = pd.DataFrame(data)
        df.to_excel(self.writer, sheet_name='Anomalies', index=False)
        
        worksheet = self.writer.sheets['Anomalies']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:E', 15, currency_format)
        worksheet.set_column('F:F', 15, percent_format)
        worksheet.set_column('G:H', 15)
        worksheet.set_column('I:I', 50)
    
    def _create_forecast_sheet(self, forecasts: Dict, header_format, currency_format):
        """Create forecast sheet."""
        forecast_df = forecasts.get('forecasts')
        
        # Convert list to DataFrame if needed
        if isinstance(forecast_df, list):
            if len(forecast_df) == 0:
                return
            forecast_df = pd.DataFrame(forecast_df)
        
        if forecast_df is None or len(forecast_df) == 0:
            return
        
        forecast_df.to_excel(self.writer, sheet_name='Forecast', index=False)
        
        worksheet = self.writer.sheets['Forecast']
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:E', 18, currency_format)


def generate_excel_report(
    output_path: Path,
    mapped_data: pd.DataFrame,
    kpis: Dict,
    trends: Dict,
    aging: Dict,
    anomalies: Dict,
    forecasts: Optional[Dict] = None,
    config: Optional[Dict] = None
):
    """
    Convenience function to generate Excel report.
    
    Args:
        output_path: Path to output Excel file
        mapped_data: Normalized FAGL DataFrame
        kpis: KPI results
        trends: Trend results
        aging: Aging results
        anomalies: Anomaly results
        forecasts: Forecast results (optional)
        config: Configuration dictionary
    """
    reporter = ExcelReporter(output_path, config)
    reporter.generate_report(mapped_data, kpis, trends, aging, anomalies, forecasts)

