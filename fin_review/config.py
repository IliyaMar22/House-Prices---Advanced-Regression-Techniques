"""Configuration management for the financial review pipeline."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class Config:
    """Main configuration class for the pipeline."""
    
    # Paths
    mapping_file: str
    fagl_dir: Optional[str] = None
    fagl_file: Optional[str] = None
    output_dir: str = "reports"
    
    # Date range
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Filters
    entity: Optional[str] = None
    
    # Data processing
    amount_sign_convention: str = "positive_debit"
    default_currency: str = "EUR"
    column_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Aging buckets
    aging_buckets: List[List] = field(default_factory=lambda: [
        [0, 0, "Current"],
        [1, 30, "0-30 days"],
        [31, 60, "31-60 days"],
        [61, 90, "61-90 days"],
        [91, 999999, ">90 days"],
    ])
    
    # Analytics configuration
    enable_growth_metrics: bool = True
    enable_ratios: bool = True
    rolling_windows: List[int] = field(default_factory=lambda: [3, 6, 12])
    enable_seasonality: bool = True
    enable_anomaly_detection: bool = True
    anomaly_threshold_zscore: float = 3.0
    anomaly_threshold_mad: float = 3.5
    use_isolation_forest: bool = True
    enable_forecasting: bool = True
    forecast_periods: int = 6
    forecast_confidence_level: float = 0.95
    top_n_vendors: int = 10
    top_n_customers: int = 10
    top_n_expenses: int = 15
    pareto_threshold: float = 0.80
    
    # AR/AP
    calculate_dso: bool = True
    calculate_dpo: bool = True
    flag_overdue: bool = True
    overdue_threshold_days: int = 30
    
    # Output
    generate_excel: bool = True
    generate_pptx: bool = True
    generate_dashboard: bool = True
    generate_parquet: bool = True
    excel_sheets: List[str] = field(default_factory=lambda: [
        "summary", "monthly_trends", "kpis", "ar_aging", "ap_aging",
        "top_vendors", "top_customers", "anomalies", "forecast"
    ])
    pptx_template: Optional[str] = None
    include_speaker_notes: bool = True
    
    # NLP
    enable_commentary: bool = True
    confidence_levels: bool = True
    top_insights: int = 3
    top_risks: int = 3
    max_recommendations: int = 5
    explain_mode: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/pipeline.log"
    structured_logging: bool = True
    
    # Validation
    warn_unmapped_gls: bool = True
    check_date_continuity: bool = True
    check_currency_consistency: bool = True
    min_data_quality_score: float = 0.7
    
    # Performance
    parallel_processing: bool = True
    max_workers: int = 4
    chunk_size: int = 10000
    
    # Reproducibility
    generate_manifest: bool = True
    calculate_checksums: bool = True
    save_config_snapshot: bool = True
    
    # Special modes
    dry_run: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.fagl_dir and not self.fagl_file:
            raise ValueError("Either fagl_dir or fagl_file must be provided")
        
        if self.fagl_dir and self.fagl_file:
            logger.warning("Both fagl_dir and fagl_file provided, using fagl_file")
            self.fagl_dir = None
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Flatten nested dicts
        flat_config = cls._flatten_config(config_dict)
        
        return cls(**flat_config)
    
    @staticmethod
    def _flatten_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested configuration dictionary."""
        flat = {}
        
        # Top-level keys
        for key in ['mapping_file', 'fagl_dir', 'fagl_file', 'output_dir', 
                    'start_date', 'end_date', 'entity', 'amount_sign_convention',
                    'default_currency', 'column_mapping', 'aging_buckets']:
            if key in config_dict:
                flat[key] = config_dict[key]
        
        # Analytics section
        if 'analytics' in config_dict:
            analytics = config_dict['analytics']
            for key in ['enable_growth_metrics', 'enable_ratios', 'rolling_windows',
                       'enable_seasonality', 'enable_anomaly_detection',
                       'anomaly_threshold_zscore', 'anomaly_threshold_mad',
                       'use_isolation_forest', 'enable_forecasting',
                       'forecast_periods', 'forecast_confidence_level',
                       'top_n_vendors', 'top_n_customers', 'top_n_expenses',
                       'pareto_threshold']:
                if key in analytics:
                    flat[key] = analytics[key]
        
        # AR/AP section
        if 'ar_ap' in config_dict:
            ar_ap = config_dict['ar_ap']
            for key in ['calculate_dso', 'calculate_dpo', 'flag_overdue',
                       'overdue_threshold_days']:
                if key in ar_ap:
                    flat[key] = ar_ap[key]
        
        # Output section
        if 'output' in config_dict:
            output = config_dict['output']
            for key in ['generate_excel', 'generate_pptx', 'generate_dashboard',
                       'generate_parquet', 'excel_sheets', 'pptx_template',
                       'include_speaker_notes']:
                if key in output:
                    flat[key] = output[key]
        
        # NLP section
        if 'nlp' in config_dict:
            nlp = config_dict['nlp']
            for key in ['enable_commentary', 'confidence_levels', 'top_insights',
                       'top_risks', 'max_recommendations', 'explain_mode']:
                if key in nlp:
                    flat[key] = nlp[key]
        
        # Logging section
        if 'logging' in config_dict:
            logging_cfg = config_dict['logging']
            if 'level' in logging_cfg:
                flat['log_level'] = logging_cfg['level']
            if 'log_file' in logging_cfg:
                flat['log_file'] = logging_cfg['log_file']
            if 'structured' in logging_cfg:
                flat['structured_logging'] = logging_cfg['structured']
        
        # Validation section
        if 'validation' in config_dict:
            validation = config_dict['validation']
            for key in ['warn_unmapped_gls', 'check_date_continuity',
                       'check_currency_consistency', 'min_data_quality_score']:
                if key in validation:
                    flat[key] = validation[key]
        
        # Performance section
        if 'performance' in config_dict:
            perf = config_dict['performance']
            for key in ['parallel_processing', 'max_workers', 'chunk_size']:
                if key in perf:
                    flat[key] = perf[key]
        
        # Reproducibility section
        if 'reproducibility' in config_dict:
            repro = config_dict['reproducibility']
            for key in ['generate_manifest', 'calculate_checksums',
                       'save_config_snapshot']:
                if key in repro:
                    flat[key] = repro[key]
        
        return flat
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'mapping_file': self.mapping_file,
            'fagl_dir': self.fagl_dir,
            'fagl_file': self.fagl_file,
            'output_dir': self.output_dir,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'entity': self.entity,
            'amount_sign_convention': self.amount_sign_convention,
            'default_currency': self.default_currency,
            'aging_buckets': self.aging_buckets,
            'analytics': {
                'enable_growth_metrics': self.enable_growth_metrics,
                'enable_ratios': self.enable_ratios,
                'rolling_windows': self.rolling_windows,
                'enable_seasonality': self.enable_seasonality,
                'enable_anomaly_detection': self.enable_anomaly_detection,
                'anomaly_threshold_zscore': self.anomaly_threshold_zscore,
                'anomaly_threshold_mad': self.anomaly_threshold_mad,
                'use_isolation_forest': self.use_isolation_forest,
                'enable_forecasting': self.enable_forecasting,
                'forecast_periods': self.forecast_periods,
                'top_n_vendors': self.top_n_vendors,
                'top_n_customers': self.top_n_customers,
                'top_n_expenses': self.top_n_expenses,
                'pareto_threshold': self.pareto_threshold,
            },
            'ar_ap': {
                'calculate_dso': self.calculate_dso,
                'calculate_dpo': self.calculate_dpo,
                'flag_overdue': self.flag_overdue,
                'overdue_threshold_days': self.overdue_threshold_days,
            },
            'output': {
                'generate_excel': self.generate_excel,
                'generate_pptx': self.generate_pptx,
                'generate_dashboard': self.generate_dashboard,
            },
            'nlp': {
                'enable_commentary': self.enable_commentary,
                'explain_mode': self.explain_mode,
            }
        }
    
    def create_output_dir(self) -> Path:
        """Create output directory with timestamp."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        entity_str = f"_{self.entity}" if self.entity else ""
        dir_name = f"{timestamp}_financial_review{entity_str}"
        
        output_path = Path(self.output_dir) / dir_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (output_path / "dashboard_data").mkdir(exist_ok=True)
        (output_path / "logs").mkdir(exist_ok=True)
        
        return output_path


def load_config(
    config_path: Optional[str] = None,
    **kwargs
) -> Config:
    """
    Load configuration from file and override with kwargs.
    
    Args:
        config_path: Path to YAML configuration file
        **kwargs: Override configuration parameters
    
    Returns:
        Config object
    """
    if config_path and os.path.exists(config_path):
        logger.info(f"Loading configuration from {config_path}")
        config = Config.from_yaml(config_path)
        
        # Override with kwargs
        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        
        return config
    else:
        # Create from kwargs only
        logger.info("Creating configuration from parameters")
        return Config(**{k: v for k, v in kwargs.items() if v is not None})

