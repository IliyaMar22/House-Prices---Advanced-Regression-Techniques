"""
Financial Review Pipeline - Automated P&L, AR, AP Analytical Review System

A comprehensive pipeline for financial analysis with mapping-driven approach,
interactive dashboards, and automated insights generation.
"""

__version__ = "1.0.0"
__author__ = "Financial Analytics Team"

from typing import Dict, Any

# Package metadata
PACKAGE_NAME = "financial-review-pipeline"
PACKAGE_VERSION = __version__

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "amount_sign_convention": "positive_debit",
    "default_currency": "EUR",
    "aging_buckets": [
        [0, 0, "Current"],
        [1, 30, "0-30 days"],
        [31, 60, "31-60 days"],
        [61, 90, "61-90 days"],
        [91, 999999, ">90 days"],
    ],
}

