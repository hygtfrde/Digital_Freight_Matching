"""
Business Requirements Validation Framework

This module provides comprehensive validation of the Digital Freight Matching
system against all business requirements from the engineering lab specification.

Key Components:
- BusinessValidator: Main validation class
- ValidationReport: Individual requirement validation results
- PerformanceReport: System performance metrics
- ValidationStatus: Validation result status enumeration

Usage:
    from validation.business_validator import BusinessValidator, ValidationReport

    validator = BusinessValidator()
    reports = validator.validate_all_requirements(orders, routes, trucks)
    summary = validator.generate_summary_report(reports)
"""

from .business_validator import (
    BusinessValidator,
    ValidationReport,
    PerformanceReport,
    ValidationStatus
)

__all__ = [
    'BusinessValidator',
    'ValidationReport',
    'PerformanceReport',
    'ValidationStatus'
]
