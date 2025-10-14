# Financial Analytical Review Pipeline

A comprehensive, automated financial analytical review system for P&L, Receivables, and Payables analysis. This pipeline ingests SAP FAGL03 exports and user-defined mapping files to produce actionable financial insights, interactive dashboards, and executive reports.

## Features

### Core Analytics
- **P&L Analysis**: Revenue, OPEX, Payroll, Interest with trend analysis and variance detection
- **AR/AP Analysis**: Open items, aging buckets, DSO/DPO, overdue analysis
- **KPI Calculation**: YoY/MoM growth, CAGR, expense ratios, margins
- **Anomaly Detection**: Statistical anomaly detection with explainable drivers
- **Forecasting**: Time-series forecasts with confidence intervals

### Advanced Features
- **Explainable AI**: Automatic drill-down to identify variance drivers (GL accounts, vendors, customers)
- **NLP Commentary**: Auto-generated executive summaries with confidence levels
- **Actionable Recommendations**: Prioritized suggestions based on cash flow impact
- **Interactive Dashboard**: Streamlit app with drill-through to source transactions
- **Audit Trail**: Complete reproducibility with file checksums and manifests
- **Multi-entity Support**: Consolidation and per-entity views

## Installation

```bash
# Clone the repository
cd financial-review-pipeline

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Prepare Your Data

Create a mapping Excel file with sheet name `mapping`:

| gl_account | bucket | type | entity | notes |
|------------|--------|------|--------|-------|
| 600100 | OPEX - Marketing | OPEX | BG | Marketing advertising |
| 610000 | Payroll - Salaries | Payroll | BG | Gross salaries |
| 400000 | Revenue - Product A | Revenue | BG | Product A Sales |

Your FAGL03 export should include: `posting_date`, `doc_id`, `gl_account`, `amount`, `currency`, `customer_vendor`, `due_date`, `open_amount`

### 2. Run the Pipeline

```bash
# Basic run
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl_dir data/fagl_exports/ \
  --out_dir reports/ \
  --start 2024-01-01 \
  --end 2024-12-31

# With entity filter and dashboard
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl_dir data/fagl_exports/ \
  --out_dir reports/ \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --entity "BG" \
  --generate-dashboard

# Dry run (validation only)
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl_dir data/fagl_exports/ \
  --dry-run

# With config file
python -m fin_review.cli --config config.yaml
```

### 3. Launch Interactive Dashboard

```bash
streamlit run fin_review/dashboard/app.py -- --data-dir reports/latest/
```

## Configuration

Create `config.yaml`:

```yaml
# Input/Output
mapping_file: data/mapping.xlsx
fagl_dir: data/fagl_exports/
output_dir: reports/

# Date range
start_date: "2024-01-01"
end_date: "2024-12-31"

# Filters
entity: null  # null for all entities

# Data processing
amount_sign_convention: "positive_debit"  # or "positive_credit"
default_currency: EUR

# Aging buckets (days)
aging_buckets:
  - [0, 0, "Current"]
  - [1, 30, "0-30 days"]
  - [31, 60, "31-60 days"]
  - [61, 90, "61-90 days"]
  - [91, 999999, ">90 days"]

# Analytics
enable_forecasting: true
forecast_periods: 6
anomaly_threshold_zscore: 3.0
top_n_vendors: 10

# Output formats
generate_excel: true
generate_pptx: true
generate_dashboard: true
```

## Output Structure

```
reports/2025-10-14_financial_review_BG_Q3/
├── mapped_data.parquet          # Cleaned, mapped dataset
├── summary.xlsx                 # Multi-sheet Excel workbook
├── executive_deck.pptx          # PowerPoint presentation
├── unmapped_gls.csv            # List of unmapped GL accounts
├── data_quality_report.json    # Data quality metrics
├── run_manifest.json           # Reproducibility manifest
├── commentary.txt              # NLP-generated insights
├── email_summary.txt           # Short email-ready summary
└── dashboard_data/             # Data for Streamlit app
```

## Project Structure

```
financial-review-pipeline/
├── fin_review/
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── config.py               # Configuration management
│   ├── loaders/                # Data loading modules
│   │   ├── mapping_loader.py
│   │   └── fagl_loader.py
│   ├── transformers/           # Data transformation
│   │   ├── validator.py
│   │   └── normalizer.py
│   ├── analytics/              # Analysis modules
│   │   ├── kpis.py
│   │   ├── trends.py
│   │   ├── aging.py
│   │   ├── anomalies.py
│   │   └── forecasting.py
│   ├── nlp/                    # NLP commentary
│   │   └── commentary.py
│   ├── reporting/              # Report generation
│   │   ├── excel_reporter.py
│   │   ├── pptx_reporter.py
│   │   └── manifest.py
│   └── dashboard/              # Interactive dashboard
│       └── app.py
├── tests/                      # Unit tests
├── data/                       # Sample data
├── requirements.txt
├── config.yaml
└── README.md
```

## CLI Options

```
--mapping PATH              Path to mapping Excel file
--fagl_dir PATH            Directory containing FAGL03 exports
--fagl_file PATH           Single FAGL03 file (alternative to --fagl_dir)
--out_dir PATH             Output directory for reports
--config PATH              YAML configuration file
--start DATE               Start date (YYYY-MM-DD)
--end DATE                 End date (YYYY-MM-DD)
--entity TEXT              Filter by entity code
--generate-dashboard       Generate Streamlit dashboard
--dry-run                  Validate inputs without generating reports
--explain-mode             Include detailed explanations in commentary
--no-forecast              Disable forecasting
--verbose                  Enable verbose logging
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=fin_review --cov-report=html

# Run specific test module
pytest tests/test_analytics.py -v
```

## Advanced Usage

### Custom Column Mapping

If your FAGL03 has different column names, create `column_mapping.json`:

```json
{
  "posting_date": "Posting Date",
  "doc_id": "Document Number",
  "gl_account": "G/L Account",
  "amount": "Amount in LC",
  "currency": "Currency",
  "posting_text": "Document Header Text",
  "customer_vendor": "Partner",
  "due_date": "Due Date",
  "open_amount": "Open Amount"
}
```

Use with: `--column-mapping column_mapping.json`

### Scenario Modeling

```python
from fin_review.analytics.scenarios import ScenarioModeler

modeler = ScenarioModeler(mapped_data)
scenario = modeler.create_scenario("Marketing Cut")
scenario.adjust_bucket("OPEX - Marketing", -0.10)  # 10% reduction
impact = scenario.calculate_impact()
print(impact.margin_improvement)
```

## Example Outputs

### NLP Commentary Sample
```
EXECUTIVE SUMMARY (Confidence: HIGH)

Key Insights for Q3 2024:
• Revenue grew 18.3% YoY driven primarily by Product A (+€2.4M, 67% of growth)
• OPEX - Marketing spiked 78% in August due to VEND-ABC campaign prepayment (€450K one-off)
• Receivables aging deteriorated: 40% now >60 days overdue (vs 18% last quarter)

Top 3 Positive Trends:
1. Product A revenue accelerating (22% MoM growth in Sep)
2. Payroll efficiency improved (14.2% of revenue vs 16.8% target)
3. Interest expenses down 34% YoY due to refinancing

Top 3 Risks:
1. Customer CUST-XYZ accounts for €380K overdue >90 days (28% of AR)
2. Marketing OPEX volatile and 23% above budget YTD
3. Top 5 suppliers represent 67% of payables (concentration risk)

Recommended Actions:
1. Escalate collection for CUST-XYZ (potential cash impact: €380K)
2. Review marketing agency contracts (VEND-ABC) for payment terms
3. Diversify supplier base to reduce concentration risk
```

## Dependencies

- Python 3.10+
- pandas >= 2.0
- numpy >= 1.24
- matplotlib >= 3.7
- plotly >= 5.14
- scikit-learn >= 1.3
- statsmodels >= 0.14
- prophet >= 1.1 (optional)
- pmdarima >= 2.0
- openpyxl >= 3.1
- xlsxwriter >= 3.1
- python-pptx >= 0.6.21
- streamlit >= 1.28
- pyyaml >= 6.0
- structlog >= 23.1
- pytest >= 7.4

## License

MIT License

## Support

For issues and questions, please open an issue on the repository.

## Changelog

### v1.0.0 (2025-10-14)
- Initial release
- Full P&L, AR, AP analytical pipeline
- NLP commentary with confidence levels
- Interactive Streamlit dashboard
- PowerPoint and Excel reporting
- Anomaly detection with explanations
- Actionable recommendations

