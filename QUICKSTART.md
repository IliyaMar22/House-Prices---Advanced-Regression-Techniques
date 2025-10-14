# Quick Start Guide

## Installation

```bash
# Navigate to project directory
cd financial-review-pipeline

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Generate Sample Data (for testing)

```bash
# Generate sample mapping and FAGL03 data
python3 data/generate_sample_data.py
```

This will create:
- `data/mapping.xlsx` - Sample GL account mappings
- `data/sample_fagl03.csv` - Sample FAGL03 transactions (18 months of data)

## Run Your First Analysis

### Option 1: Using Sample Data

```bash
python -m fin_review.cli \
  --mapping data/sample_mapping.csv \
  --fagl-file data/sample_fagl03.csv \
  --out-dir reports/ \
  --generate-dashboard
```

### Option 2: Using Configuration File

```bash
# Edit config.yaml with your paths
python -m fin_review.cli --config config.yaml
```

### Option 3: With Custom Date Range

```bash
python -m fin_review.cli \
  --mapping your_mapping.xlsx \
  --fagl-dir your_fagl_exports/ \
  --out-dir reports/ \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --entity "BG" \
  --generate-dashboard
```

## View Results

After running the pipeline, you'll find in `reports/TIMESTAMP_financial_review/`:

1. **summary.xlsx** - Multi-sheet Excel workbook with all analyses
2. **executive_deck.pptx** - PowerPoint presentation for executives
3. **commentary.txt** - Automated insights and commentary
4. **email_summary.txt** - Short email-ready summary
5. **mapped_data.parquet** - Processed data for further analysis
6. **unmapped_gls.csv** - List of unmapped GL accounts (if any)

## Launch Interactive Dashboard

```bash
streamlit run fin_review/dashboard/app.py -- --data-dir reports/LATEST_REPORT_DIR/
```

Or specify the exact report directory:

```bash
streamlit run fin_review/dashboard/app.py -- --data-dir reports/2025-10-14_123456_financial_review/
```

## Dry Run (Validate Without Processing)

Test your data quality without generating reports:

```bash
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl-file data/fagl03.csv \
  --dry-run
```

## Common Use Cases

### Monthly Financial Review

```bash
python -m fin_review.cli \
  --config config.yaml \
  --start 2024-09-01 \
  --end 2024-09-30 \
  --generate-dashboard
```

### Quarterly Analysis

```bash
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl-dir data/q3_2024/ \
  --start 2024-07-01 \
  --end 2024-09-30 \
  --out-dir reports/q3_2024/
```

### Year-End Review

```bash
python -m fin_review.cli \
  --config config.yaml \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --generate-dashboard \
  --verbose
```

### Multi-Entity Analysis

```bash
# Run for each entity
for entity in BG DE FR; do
  python -m fin_review.cli \
    --config config.yaml \
    --entity $entity \
    --out-dir reports/entity_$entity/
done
```

## Understanding Output

### Excel Report Sheets

- **Summary**: High-level KPIs and metrics
- **Monthly Trends**: Time series of key metrics
- **KPIs**: Detailed growth and ratio metrics
- **AR Aging**: Receivables aging analysis
- **AP Aging**: Payables aging analysis
- **Top Vendors**: Largest suppliers by spend
- **Top Customers**: Largest customers by revenue
- **Anomalies**: Detected anomalies with explanations
- **Forecast**: Time series forecasts (if enabled)

### PowerPoint Deck Slides

1. Title slide
2. Executive summary
3. Key insights (with confidence levels)
4. Financial overview (revenue, OPEX, profit)
5. Trends analysis
6. AR/AP aging
7. Top risks
8. Recommended actions

### Commentary Text

The NLP-generated commentary includes:
- Executive summary
- Top 3 positive insights
- Top 3 risks
- Top 5 recommendations with cash impact
- Confidence levels for each insight

## Tips & Best Practices

### 1. Data Quality

- Ensure your mapping file covers all GL accounts used
- Check unmapped_gls.csv after first run
- Verify date formats (YYYY-MM-DD)
- Ensure amounts have correct sign convention

### 2. Configuration

- Use config.yaml for repeatable runs
- Adjust aging buckets to match your business
- Enable/disable forecasting based on data quality
- Set appropriate anomaly thresholds

### 3. Performance

- For large datasets (>1M rows), use parquet format
- Enable parallel processing in config
- Consider filtering by date range for faster runs

### 4. Interpretation

- High confidence insights are statistically significant
- Medium confidence may need manual review
- Check anomaly explanations for root causes
- Review top contributors when investigating variances

## Troubleshooting

### "Mapping file not found"
- Verify the path to your mapping file
- Ensure it's an Excel file (.xlsx or .xls)
- Check that it has a sheet named 'mapping'

### "No FAGL03 files found"
- Check the directory path
- Ensure files are .csv or .xlsx format
- Verify files have required columns

### "Validation failed"
- Run with --dry-run to see validation issues
- Check unmapped GL accounts
- Verify date ranges are valid
- Ensure currency consistency

### "Quality score too low"
- Review data quality report JSON
- Address unmapped GLs in mapping file
- Check for missing data (dates, amounts)
- Consider adjusting min_data_quality_score in config

### Dashboard won't start
```bash
# Install Streamlit if not already installed
pip install streamlit

# Check that data directory exists
ls reports/YOUR_REPORT_DIR/
```

## Next Steps

1. **Customize Mapping**: Add your specific GL accounts and buckets
2. **Run Historical Analysis**: Process multiple periods to build trends
3. **Schedule Regular Runs**: Automate monthly/quarterly reviews
4. **Integrate with BI**: Export parquet files to your BI tool
5. **Extend Analytics**: Add custom KPIs in the analytics modules

## Support & Documentation

- Full README: `README.md`
- Configuration details: `config.yaml` with inline comments
- API documentation: See docstrings in each module
- Example data: `data/generate_sample_data.py`

## Example Workflow

```bash
# 1. Setup (one time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Prepare your data
# - Export FAGL03 from SAP
# - Create/update mapping.xlsx
# - Customize config.yaml

# 3. Validate
python -m fin_review.cli \
  --mapping data/mapping.xlsx \
  --fagl-dir data/exports/ \
  --dry-run \
  --verbose

# 4. Run full analysis
python -m fin_review.cli --config config.yaml --generate-dashboard

# 5. Review outputs
# - Open summary.xlsx in Excel
# - Open executive_deck.pptx in PowerPoint
# - Read commentary.txt

# 6. Launch dashboard for interactive exploration
streamlit run fin_review/dashboard/app.py -- --data-dir reports/LATEST/

# 7. Share results
# - Email email_summary.txt to stakeholders
# - Present executive_deck.pptx to leadership
# - Share dashboard link for drill-down
```

## Advanced Features

### Scenario Modeling (Coming Soon)
Adjust forecasts with "what-if" scenarios:
```python
from fin_review.analytics.scenarios import ScenarioModeler

modeler = ScenarioModeler(mapped_data)
scenario = modeler.create_scenario("Marketing Cut")
scenario.adjust_bucket("OPEX - Marketing", -0.10)  # 10% reduction
impact = scenario.calculate_impact()
```

### Custom Analytics
Extend the pipeline with custom KPIs:
```python
from fin_review.analytics.kpis import KPICalculator

calculator = KPICalculator(df, config)
custom_kpi = df[df['bucket'] == 'Custom Bucket']['amount'].sum()
```

### Automated Email Reports
Use the email_summary.txt with your email automation:
```bash
# Example with mail command
cat reports/latest/email_summary.txt | mail -s "Monthly Financial Review" team@company.com
```

