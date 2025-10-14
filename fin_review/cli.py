"""Command-line interface for the financial review pipeline."""

import click
import structlog
import sys
import json
from pathlib import Path
from datetime import datetime

from fin_review.config import load_config, Config
from fin_review.loaders import load_mapping, load_fagl_data
from fin_review.transformers import validate_data, normalize_data
from fin_review.analytics import calculate_kpis, analyze_trends, calculate_aging, detect_anomalies, generate_forecasts
from fin_review.nlp import generate_commentary
from fin_review.reporting import generate_excel_report, generate_pptx_report, generate_pdf_report, generate_html_report, generate_manifest

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@click.command()
@click.option('--config', type=click.Path(exists=True), help='Path to YAML configuration file')
@click.option('--mapping', type=click.Path(exists=True), help='Path to mapping Excel file')
@click.option('--fagl-dir', type=click.Path(exists=True), help='Directory containing FAGL03 files')
@click.option('--fagl-file', type=click.Path(exists=True), help='Single FAGL03 file')
@click.option('--out-dir', type=click.Path(), default='reports', help='Output directory')
@click.option('--start', type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end', type=str, help='End date (YYYY-MM-DD)')
@click.option('--entity', type=str, help='Entity filter')
@click.option('--generate-dashboard/--no-dashboard', default=False, help='Generate Streamlit dashboard')
@click.option('--generate-pdf/--no-pdf', default=True, help='Generate PDF summary report')
@click.option('--auto-open/--no-auto-open', default=True, help='Automatically open generated reports')
@click.option('--dry-run', is_flag=True, help='Validate inputs without generating reports')
@click.option('--explain-mode', is_flag=True, help='Include detailed explanations in commentary')
@click.option('--no-forecast', is_flag=True, help='Disable forecasting')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def main(
    config,
    mapping,
    fagl_dir,
    fagl_file,
    out_dir,
    start,
    end,
    entity,
    generate_dashboard,
    generate_pdf,
    auto_open,
    dry_run,
    explain_mode,
    no_forecast,
    verbose
):
    """
    Financial Review Pipeline - Automated P&L, AR, AP Analysis
    
    Generate comprehensive financial analytical reviews from FAGL03 exports
    with automated insights, anomaly detection, and interactive dashboards.
    """
    
    # Configure logging level
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    
    logger.info(
        "Starting financial review pipeline",
        version="1.0.0",
        dry_run=dry_run
    )
    
    try:
        # Load configuration
        cfg = load_config(
            config_path=config,
            mapping_file=mapping,
            fagl_dir=fagl_dir,
            fagl_file=fagl_file,
            output_dir=out_dir,
            start_date=start,
            end_date=end,
            entity=entity,
            generate_dashboard=generate_dashboard,
            dry_run=dry_run,
            explain_mode=explain_mode,
            enable_forecasting=not no_forecast,
            verbose=verbose,
            log_level=log_level
        )
        
        logger.info("Configuration loaded", config=cfg.to_dict())
        
        # Step 1: Load mapping
        logger.info("=" * 60)
        logger.info("STEP 1: Loading Mapping File")
        logger.info("=" * 60)
        
        mapping_df = load_mapping(cfg.mapping_file)
        logger.info(f"Loaded {len(mapping_df)} GL account mappings")
        
        # Step 2: Load FAGL data
        logger.info("=" * 60)
        logger.info("STEP 2: Loading FAGL03 Data")
        logger.info("=" * 60)
        
        fagl_df = load_fagl_data(
            fagl_dir=cfg.fagl_dir,
            fagl_file=cfg.fagl_file,
            column_mapping=cfg.column_mapping,
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            entity=cfg.entity
        )
        
        logger.info(
            f"Loaded {len(fagl_df)} transactions",
            date_range=f"{fagl_df['posting_date'].min()} to {fagl_df['posting_date'].max()}"
        )
        
        # Step 3: Validate data
        logger.info("=" * 60)
        logger.info("STEP 3: Validating Data")
        logger.info("=" * 60)
        
        validation_result = validate_data(
            fagl_df,
            mapping_df,
            cfg.__dict__
        )
        
        logger.info(
            "Validation complete",
            quality_score=validation_result.quality_score,
            warnings=len(validation_result.warnings),
            errors=len(validation_result.errors)
        )
        
        # Print warnings and errors
        for warning in validation_result.warnings:
            logger.warning(warning)
        
        for error in validation_result.errors:
            logger.error(error)
        
        if not validation_result.is_valid:
            logger.error(
                "Data validation failed",
                quality_score=validation_result.quality_score,
                min_required=cfg.min_data_quality_score
            )
            if not cfg.dry_run:
                click.echo(f"❌ Validation failed. Quality score: {validation_result.quality_score:.2f}")
                sys.exit(1)
        
        click.echo(f"✓ Validation passed. Quality score: {validation_result.quality_score:.2f}")
        
        # If dry-run, stop here
        if cfg.dry_run:
            click.echo("\n✓ Dry run completed successfully")
            click.echo(f"  Total transactions: {len(fagl_df)}")
            click.echo(f"  Mapped accounts: {len(mapping_df)}")
            click.echo(f"  Unmapped GLs: {len(validation_result.unmapped_gls)}")
            click.echo(f"  Quality score: {validation_result.quality_score:.2f}")
            return
        
        # Step 4: Normalize data
        logger.info("=" * 60)
        logger.info("STEP 4: Normalizing Data")
        logger.info("=" * 60)
        
        normalized_df = normalize_data(fagl_df, mapping_df, cfg.__dict__)
        
        logger.info(
            "Data normalized",
            mapped_rows=normalized_df['is_mapped'].sum(),
            unmapped_rows=(~normalized_df['is_mapped']).sum()
        )
        
        # Step 5: Create output directory
        output_path = cfg.create_output_dir()
        logger.info(f"Output directory: {output_path}")
        
        # Step 6: Calculate KPIs
        logger.info("=" * 60)
        logger.info("STEP 5: Calculating KPIs")
        logger.info("=" * 60)
        
        kpi_result = calculate_kpis(normalized_df, cfg.__dict__)
        logger.info("KPIs calculated")
        
        # Step 7: Analyze trends
        logger.info("=" * 60)
        logger.info("STEP 6: Analyzing Trends")
        logger.info("=" * 60)
        
        trend_result = analyze_trends(normalized_df, cfg.__dict__)
        logger.info("Trends analyzed")
        
        # Step 8: Calculate aging
        logger.info("=" * 60)
        logger.info("STEP 7: Calculating AR/AP Aging")
        logger.info("=" * 60)
        
        aging_result = calculate_aging(normalized_df, cfg.__dict__)
        logger.info(
            "Aging calculated",
            ar_overdue_pct=aging_result.ar_summary.get('overdue_pct', 0),
            ap_overdue_pct=aging_result.ap_summary.get('overdue_pct', 0)
        )
        
        # Step 9: Detect anomalies
        logger.info("=" * 60)
        logger.info("STEP 8: Detecting Anomalies")
        logger.info("=" * 60)
        
        anomaly_result = detect_anomalies(normalized_df, cfg.__dict__)
        logger.info(
            "Anomalies detected",
            total=len(anomaly_result.anomalies),
            high_severity=anomaly_result.summary.get('high_severity_count', 0)
        )
        
        # Step 10: Generate forecasts
        forecast_result = None
        if cfg.enable_forecasting:
            logger.info("=" * 60)
            logger.info("STEP 9: Generating Forecasts")
            logger.info("=" * 60)
            
            forecast_result = generate_forecasts(normalized_df, cfg.__dict__)
            logger.info(f"Forecasts generated using {forecast_result.method_used}")
        
        # Step 11: Generate NLP commentary
        logger.info("=" * 60)
        logger.info("STEP 10: Generating NLP Commentary")
        logger.info("=" * 60)
        
        commentary_result = generate_commentary(
            normalized_df,
            kpi_result.to_dict(),
            trend_result.to_dict(),
            aging_result.to_dict(),
            anomaly_result.to_dict(),
            cfg.__dict__
        )
        
        logger.info(
            "Commentary generated",
            insights=len(commentary_result.insights),
            risks=len(commentary_result.risks),
            recommendations=len(commentary_result.recommendations)
        )
        
        # Step 12: Save outputs
        logger.info("=" * 60)
        logger.info("STEP 11: Generating Reports")
        logger.info("=" * 60)
        
        # Save mapped data
        if cfg.generate_parquet:
            parquet_path = output_path / "mapped_data.parquet"
            normalized_df.to_parquet(parquet_path, index=False)
            logger.info(f"Saved mapped data: {parquet_path}")
        
        # Save unmapped GLs
        if validation_result.unmapped_gls:
            from fin_review.transformers.normalizer import DataNormalizer
            normalizer = DataNormalizer(fagl_df, mapping_df, cfg.__dict__)
            normalizer.fagl_df = normalized_df
            normalizer.normalized_df = normalized_df
            unmapped_summary = normalizer.get_unmapped_summary()
            unmapped_path = output_path / "unmapped_gls.csv"
            unmapped_summary.to_csv(unmapped_path, index=False)
            logger.info(f"Saved unmapped GLs: {unmapped_path}")
        
        # Generate Excel report
        excel_path = None
        if cfg.generate_excel:
            excel_path = output_path / "summary.xlsx"
            generate_excel_report(
                excel_path,
                normalized_df,
                kpi_result.to_dict(),
                trend_result.to_dict(),
                aging_result.to_dict(),
                anomaly_result.to_dict(),
                forecast_result.to_dict() if forecast_result else None,
                cfg.__dict__
            )
            logger.info(f"Generated Excel report: {excel_path}")
            click.echo(f"✓ Excel report: {excel_path}")
        
        # Generate PowerPoint report
        pptx_path = None
        if cfg.generate_pptx:
            pptx_path = output_path / "executive_deck.pptx"
            generate_pptx_report(
                pptx_path,
                commentary_result.to_dict(),
                kpi_result.to_dict(),
                trend_result.to_dict(),
                aging_result.to_dict(),
                anomaly_result.to_dict(),
                cfg.__dict__
            )
            logger.info(f"Generated PowerPoint report: {pptx_path}")
            click.echo(f"✓ PowerPoint deck: {pptx_path}")
        
        # Generate PDF report
        pdf_path = None
        if generate_pdf:
            pdf_path = output_path / "financial_summary.pdf"
            try:
                generate_pdf_report(
                    pdf_path,
                    commentary_result.to_dict(),
                    kpi_result.to_dict(),
                    aging_result.to_dict(),
                    anomaly_result.to_dict(),
                    normalized_df,
                    cfg.__dict__
                )
                logger.info(f"Generated PDF report: {pdf_path}")
                click.echo(f"✓ PDF summary: {pdf_path}")
            except Exception as e:
                logger.warning(f"PDF generation failed: {e}")
                click.echo(f"⚠ PDF generation skipped (reportlab may not be installed)")
        
        # Generate HTML summary (always, it's lightweight and useful)
        html_path = output_path / "financial_summary.html"
        try:
            generate_html_report(
                html_path,
                commentary_result.to_dict(),
                kpi_result.to_dict(),
                trend_result.to_dict(),
                aging_result.to_dict(),
                anomaly_result.to_dict(),
                normalized_df,
                cfg.__dict__
            )
            logger.info(f"Generated HTML report: {html_path}")
            click.echo(f"✓ HTML summary: {html_path}")
        except Exception as e:
            logger.warning(f"HTML generation failed: {e}")
            html_path = None
        
        # Save commentary
        commentary_path = output_path / "commentary.txt"
        with open(commentary_path, 'w') as f:
            f.write(commentary_result.executive_summary)
        logger.info(f"Saved commentary: {commentary_path}")
        
        # Save email summary
        email_path = output_path / "email_summary.txt"
        with open(email_path, 'w') as f:
            f.write(commentary_result.email_summary)
        logger.info(f"Saved email summary: {email_path}")
        
        # Save data quality report
        quality_path = output_path / "data_quality_report.json"
        with open(quality_path, 'w') as f:
            json.dump(validation_result.to_dict(), f, indent=2)
        logger.info(f"Saved data quality report: {quality_path}")
        
        # Generate manifest
        if cfg.generate_manifest:
            manifest_path = output_path / "run_manifest.json"
            input_files = {
                'mapping': Path(cfg.mapping_file)
            }
            if cfg.fagl_file:
                input_files['fagl'] = Path(cfg.fagl_file)
            
            processing_stats = {
                'total_transactions': len(normalized_df),
                'mapped_transactions': int(normalized_df['is_mapped'].sum()),
                'unmapped_transactions': int((~normalized_df['is_mapped']).sum()),
                'date_range': {
                    'start': str(normalized_df['posting_date'].min()),
                    'end': str(normalized_df['posting_date'].max())
                },
                'processing_time_seconds': None  # Could track this
            }
            
            generate_manifest(
                manifest_path,
                input_files,
                validation_result.to_dict(),
                processing_stats,
                cfg.to_dict(),
                cfg.__dict__
            )
            logger.info(f"Generated manifest: {manifest_path}")
        
        # Success message
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        click.echo("\n" + "=" * 60)
        click.echo("✅ PIPELINE COMPLETED SUCCESSFULLY")
        click.echo("=" * 60)
        click.echo(f"\nOutput directory: {output_path}")
        click.echo(f"\nKey Metrics:")
        summary_kpis = kpi_result.summary_kpis
        click.echo(f"  • Total Revenue: €{summary_kpis.get('total_revenue', 0)/1000:.1f}K")
        click.echo(f"  • Total OPEX: €{summary_kpis.get('total_opex', 0)/1000:.1f}K")
        click.echo(f"  • Net Profit: €{summary_kpis.get('net_profit', 0)/1000:.1f}K")
        click.echo(f"  • Anomalies detected: {len(anomaly_result.anomalies)}")
        click.echo(f"  • AR overdue: {aging_result.ar_summary.get('overdue_pct', 0):.1f}%")
        
        if cfg.generate_dashboard:
            click.echo(f"\n💡 To launch the dashboard, run:")
            click.echo(f"   streamlit run fin_review/dashboard/app.py -- --data-dir {output_path}")
        
        # Auto-open generated files
        if auto_open:
            import subprocess
            import platform
            
            click.echo(f"\n📂 Opening generated reports...")
            
            files_to_open = []
            
            # Prioritize HTML (opens in browser with interactive charts)
            if html_path and html_path.exists():
                files_to_open.append(html_path)
            # Then Excel
            if excel_path and excel_path.exists():
                files_to_open.append(excel_path)
            # Then PowerPoint
            if pptx_path and pptx_path.exists():
                files_to_open.append(pptx_path)
            # Finally PDF if generated
            if pdf_path and pdf_path.exists():
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
        
    except Exception as e:
        logger.error("Pipeline failed", error=str(e), exc_info=True)
        click.echo(f"\n❌ Pipeline failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

