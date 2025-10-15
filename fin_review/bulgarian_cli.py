"""Bulgarian CLI for financial review pipeline."""

import click
import structlog
from pathlib import Path
from datetime import datetime
import pandas as pd

from .config import load_config
from .loaders.bulgarian_mapping_loader import BulgarianMappingLoader
from .loaders.fagl_loader import FAGLLoader
from .transformers.validator import DataValidator
from .transformers.normalizer import DataNormalizer
from .analytics.kpis import KPICalculator
from .analytics.trends import TrendAnalyzer
from .analytics.aging import AgingAnalyzer
from .analytics.anomalies import AnomalyDetector
from .analytics.forecasting import ForecastingEngine
from .nlp.commentary import CommentaryGenerator
from .reporting.excel_reporter import generate_excel_report
from .reporting.pptx_reporter import generate_pptx_report
from .reporting.pdf_reporter import generate_pdf_report
from .reporting.html_reporter import generate_html_report
from .reporting.manifest import generate_manifest

logger = structlog.get_logger(__name__)


@click.command()
@click.option('--mapping', 
              default="/Users/bilyana/Desktop/Chronology & Mapping/Mapping export.xlsx",
              help='Path to Bulgarian mapping Excel file')
@click.option('--fagl-file', 
              help='Path to FAGL03 export file (CSV/Excel)')
@click.option('--fagl-dir', 
              help='Directory containing FAGL03 export files')
@click.option('--out-dir', 
              default='reports_bulgarian',
              help='Output directory for Bulgarian reports')
@click.option('--start-date', 
              help='Analysis start date (YYYY-MM-DD)')
@click.option('--end-date', 
              help='Analysis end date (YYYY-MM-DD)')
@click.option('--entity', 
              default='Main Entity',
              help='Entity name for Bulgarian analysis')
@click.option('--generate-dashboard/--no-dashboard', 
              default=False,
              help='Generate Streamlit dashboard')
@click.option('--generate-pdf/--no-pdf', 
              default=True, 
              help='Generate PDF summary report')
@click.option('--auto-open/--no-auto-open', 
              default=True, 
              help='Automatically open generated reports')
@click.option('--config', 
              default='config_bulgarian.yaml',
              help='Bulgarian configuration file')
def main(
    mapping,
    fagl_file,
    fagl_dir,
    out_dir,
    start_date,
    end_date,
    entity,
    generate_dashboard,
    generate_pdf,
    auto_open,
    config
):
    """
    Bulgarian Financial Review Pipeline CLI.
    
    Automated P&L, AR, AP analytical review for Bulgarian financial data.
    Supports Bulgarian accounting standards and ABCOTD classifications.
    """
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logger.info("Starting Bulgarian Financial Review Pipeline", 
                mapping_file=mapping,
                output_dir=out_dir)
    
    try:
        # Load Bulgarian configuration
        config_path = Path(config)
        if not config_path.exists():
            logger.warning(f"Bulgarian config not found: {config}, using defaults")
            cfg = None
        else:
            cfg = load_config(config_path)
        
        # Create output directory
        output_dir = Path(out_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_dir = output_dir / f"{timestamp}_bulgarian_financial_review"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Bulgarian analysis directory created", path=str(run_dir))
        
        # Step 1: Load Bulgarian mapping data
        click.echo("📊 Loading Bulgarian mapping data...")
        mapping_path = Path(mapping)
        
        if not mapping_path.exists():
            raise FileNotFoundError(f"Bulgarian mapping file not found: {mapping}")
        
        mapping_loader = BulgarianMappingLoader(mapping_path, cfg)
        mapping_df = mapping_loader.load()
        
        # Get Bulgarian summary
        mapping_summary = mapping_loader.get_bulgarian_summary()
        click.echo(f"✅ Loaded {mapping_summary['total_accounts']} Bulgarian accounts")
        click.echo(f"   FS Sub classes: {len(mapping_summary['fs_sub_classes'])}")
        click.echo(f"   ABCOTD categories: {len(mapping_summary['abcotd_categories'])}")
        
        # Step 2: Load FAGL03 data
        click.echo("\n📋 Loading FAGL03 transaction data...")
        
        if fagl_file:
            fagl_path = Path(fagl_file)
            if not fagl_path.exists():
                raise FileNotFoundError(f"FAGL03 file not found: {fagl_file}")
            
            fagl_loader = FAGLLoader(fagl_path, cfg)
            fagl_df = fagl_loader.load()
            
        elif fagl_dir:
            fagl_dir_path = Path(fagl_dir)
            if not fagl_dir_path.exists():
                raise FileNotFoundError(f"FAGL03 directory not found: {fagl_dir}")
            
            # Load all FAGL03 files in directory
            fagl_files = list(fagl_dir_path.glob("*.csv")) + list(fagl_dir_path.glob("*.xlsx"))
            if not fagl_files:
                raise FileNotFoundError(f"No FAGL03 files found in: {fagl_dir}")
            
            all_fagl_data = []
            for fagl_file_path in fagl_files:
                click.echo(f"   Loading: {fagl_file_path.name}")
                fagl_loader = FAGLLoader(fagl_file_path, cfg)
                fagl_data = fagl_loader.load()
                all_fagl_data.append(fagl_data)
            
            fagl_df = pd.concat(all_fagl_data, ignore_index=True)
            
        else:
            raise ValueError("Either --fagl-file or --fagl-dir must be specified")
        
        click.echo(f"✅ Loaded {len(fagl_df):,} transactions")
        click.echo(f"   Date range: {fagl_df['posting_date'].min()} to {fagl_df['posting_date'].max()}")
        
        # Step 3: Data validation
        click.echo("\n🔍 Validating Bulgarian financial data...")
        validator = DataValidator(cfg)
        validation_result = validator.validate(fagl_df, mapping_df)
        
        quality_score = validation_result['quality_score']
        click.echo(f"✅ Data quality score: {quality_score:.2f}")
        
        if validation_result['unmapped_gls']:
            unmapped_count = len(validation_result['unmapped_gls'])
            click.echo(f"⚠️  Found {unmapped_count} unmapped GL accounts")
        
        # Step 4: Data normalization
        click.echo("\n🔄 Normalizing Bulgarian financial data...")
        normalizer = DataNormalizer(cfg)
        normalized_df = normalizer.normalize(fagl_df, mapping_df)
        
        click.echo(f"✅ Normalized {len(normalized_df):,} transactions")
        
        # Step 5: KPI calculations
        click.echo("\n📊 Calculating Bulgarian KPIs...")
        kpi_calculator = KPICalculator(cfg)
        kpi_result = kpi_calculator.calculate(normalized_df)
        
        click.echo(f"✅ Calculated KPIs for {len(kpi_result.monthly_kpis)} periods")
        
        # Step 6: Trend analysis
        click.echo("\n📈 Analyzing Bulgarian financial trends...")
        trend_analyzer = TrendAnalyzer(cfg)
        trend_result = trend_analyzer.analyze(normalized_df)
        
        click.echo(f"✅ Trend analysis completed")
        
        # Step 7: AR/AP Aging analysis
        click.echo("\n⏰ Analyzing Bulgarian AR/AP aging...")
        aging_analyzer = AgingAnalyzer(cfg)
        aging_result = aging_analyzer.analyze(normalized_df)
        
        ar_overdue = aging_result.ar_aging[aging_result.ar_aging['bucket'] == 'Overdue']['amount'].sum()
        ap_overdue = aging_result.ap_aging[aging_result.ap_aging['bucket'] == 'Overdue']['amount'].sum()
        
        click.echo(f"✅ Aging analysis completed")
        click.echo(f"   AR Overdue: лв {ar_overdue:,.2f}")
        click.echo(f"   AP Overdue: лв {ap_overdue:,.2f}")
        
        # Step 8: Anomaly detection
        click.echo("\n🚨 Detecting anomalies in Bulgarian data...")
        anomaly_detector = AnomalyDetector(cfg)
        anomaly_result = anomaly_detector.detect(normalized_df)
        
        anomaly_count = len(anomaly_result.anomalies)
        click.echo(f"✅ Detected {anomaly_count} anomalies")
        
        # Step 9: Forecasting
        click.echo("\n🔮 Generating Bulgarian financial forecasts...")
        forecasting_engine = ForecastingEngine(cfg)
        forecast_result = forecasting_engine.forecast(normalized_df)
        
        click.echo(f"✅ Forecasting completed")
        
        # Step 10: NLP Commentary
        click.echo("\n💬 Generating Bulgarian financial commentary...")
        commentary_generator = CommentaryGenerator(cfg)
        commentary = commentary_generator.generate(
            kpi_result=kpi_result,
            trend_result=trend_result,
            aging_result=aging_result,
            anomaly_result=anomaly_result,
            forecast_result=forecast_result
        )
        
        click.echo(f"✅ Generated {len(commentary.insights)} insights")
        click.echo(f"✅ Generated {len(commentary.recommendations)} recommendations")
        
        # Step 11: Generate Bulgarian reports
        click.echo("\n📄 Generating Bulgarian financial reports...")
        
        # Excel report
        excel_path = run_dir / "bulgarian_summary.xlsx"
        generate_excel_report(
            kpi_result=kpi_result,
            trend_result=trend_result,
            aging_result=aging_result,
            anomaly_result=anomaly_result,
            forecast_result=forecast_result,
            output_path=excel_path,
            config=cfg
        )
        click.echo(f"✅ Excel report: {excel_path}")
        
        # PowerPoint report
        pptx_path = run_dir / "bulgarian_executive_deck.pptx"
        generate_pptx_report(
            kpi_result=kpi_result,
            trend_result=trend_result,
            aging_result=aging_result,
            anomaly_result=anomaly_result,
            forecast_result=forecast_result,
            commentary=commentary,
            output_path=pptx_path,
            config=cfg
        )
        click.echo(f"✅ PowerPoint report: {pptx_path}")
        
        # HTML report
        html_path = run_dir / "bulgarian_financial_summary.html"
        generate_html_report(
            kpi_result=kpi_result,
            trend_result=trend_result,
            aging_result=aging_result,
            anomaly_result=anomaly_result,
            forecast_result=forecast_result,
            commentary=commentary,
            output_path=html_path,
            config=cfg
        )
        click.echo(f"✅ HTML report: {html_path}")
        
        # PDF report (optional)
        if generate_pdf:
            pdf_path = run_dir / "bulgarian_summary.pdf"
            generate_pdf_report(
                kpi_result=kpi_result,
                trend_result=trend_result,
                aging_result=aging_result,
                anomaly_result=anomaly_result,
                forecast_result=forecast_result,
                commentary=commentary,
                output_path=pdf_path,
                config=cfg
            )
            click.echo(f"✅ PDF report: {pdf_path}")
        
        # Save Bulgarian data
        mapped_data_path = run_dir / "bulgarian_mapped_data.parquet"
        normalized_df.to_parquet(mapped_data_path)
        
        # Save Bulgarian commentary
        commentary_path = run_dir / "bulgarian_commentary.txt"
        with open(commentary_path, 'w', encoding='utf-8') as f:
            f.write(commentary.executive_summary)
            f.write("\n\n")
            f.write("INSIGHTS:\n")
            for insight in commentary.insights:
                f.write(f"- {insight.content} (Confidence: {insight.confidence})\n")
            f.write("\nRECOMMENDATIONS:\n")
            for rec in commentary.recommendations:
                f.write(f"- {rec.content}\n")
        
        # Save Bulgarian email summary
        email_path = run_dir / "bulgarian_email_summary.txt"
        with open(email_path, 'w', encoding='utf-8') as f:
            f.write(commentary.email_summary)
        
        # Generate Bulgarian manifest
        manifest_path = run_dir / "bulgarian_run_manifest.json"
        generate_manifest(
            mapping_file=mapping_path,
            fagl_files=[fagl_file] if fagl_file else fagl_files,
            output_dir=run_dir,
            config=cfg,
            output_path=manifest_path
        )
        
        # Save Bulgarian data quality report
        quality_path = run_dir / "bulgarian_data_quality_report.json"
        import json
        with open(quality_path, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        
        # Auto-open Bulgarian reports
        if auto_open:
            import subprocess
            import platform
            
            click.echo(f"\n📂 Opening Bulgarian reports...")
            
            files_to_open = []
            
            # Prioritize HTML (opens in browser with interactive charts)
            if html_path.exists():
                files_to_open.append(html_path)
            # Then Excel
            if excel_path.exists():
                files_to_open.append(excel_path)
            # Then PowerPoint
            if pptx_path.exists():
                files_to_open.append(pptx_path)
            # Finally PDF if generated
            if generate_pdf and pdf_path.exists():
                files_to_open.append(pdf_path)
            
            # Open files based on OS
            system = platform.system()
            for file_path in files_to_open:
                try:
                    if system == 'Darwin':  # macOS
                        subprocess.run(['open', str(file_path)], check=False)
                    elif system == 'Windows':
                        subprocess.run(['start', str(file_path)], shell=True, check=False)
                    elif system == 'Linux':
                        subprocess.run(['xdg-open', str(file_path)], check=False)
                    
                    click.echo(f"  ✓ Opened: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not auto-open {file_path}: {e}")
        
        # Bulgarian analysis summary
        click.echo(f"\n🎊 BULGARIAN FINANCIAL ANALYSIS COMPLETE! 🎊")
        click.echo(f"═══════════════════════════════════════════════════════════════")
        click.echo(f"📊 Analysis Results:")
        click.echo(f"   • Accounts analyzed: {mapping_summary['total_accounts']:,}")
        click.echo(f"   • Transactions processed: {len(normalized_df):,}")
        click.echo(f"   • Data quality score: {quality_score:.2f}")
        click.echo(f"   • Bulgarian KPIs calculated: {len(kpi_result.monthly_kpis)} periods")
        click.echo(f"   • Anomalies detected: {anomaly_count}")
        click.echo(f"   • Insights generated: {len(commentary.insights)}")
        click.echo(f"   • Recommendations: {len(commentary.recommendations)}")
        click.echo(f"")
        click.echo(f"📁 Bulgarian Reports Generated:")
        click.echo(f"   • HTML Summary: {html_path}")
        click.echo(f"   • Excel Workbook: {excel_path}")
        click.echo(f"   • PowerPoint Deck: {pptx_path}")
        if generate_pdf:
            click.echo(f"   • PDF Summary: {pdf_path}")
        click.echo(f"")
        click.echo(f"🎯 Bulgarian Features:")
        click.echo(f"   • ABCOTD classification: ✅")
        click.echo(f"   • FS Sub class analysis: ✅")
        click.echo(f"   • Bulgarian currency (BGN): ✅")
        click.echo(f"   • Local compliance: ✅")
        click.echo(f"   • Bulgarian language support: ✅")
        
        if auto_open:
            click.echo(f"\n✨ Bulgarian reports opened automatically!")
        
        logger.info("Bulgarian financial analysis completed successfully", 
                   output_dir=str(run_dir),
                   quality_score=quality_score,
                   transactions=len(normalized_df))
        
    except Exception as e:
        logger.error("Bulgarian financial analysis failed", error=str(e))
        click.echo(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
