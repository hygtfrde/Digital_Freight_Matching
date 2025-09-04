"""
Integration tests package for Digital Freight Matching System

This package contains comprehensive integration tests that validate
end-to-end functionality, database consistency, API integration,
and performance requirements.
"""

from .test_integration_suite import IntegrationTestSuite, run_integration_tests

__all__ = ['IntegrationTestSuite', 'run_integration_tests']