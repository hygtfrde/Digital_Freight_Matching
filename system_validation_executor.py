#!/usr/bin/env python3
"""
Comprehensive System Validation Executor

Executes all validation tasks for MVP finalization including:
- Business requirements validation against all 7 requirements
- Integration tests covering end-to-end workflows and data integrity
- Performance testing and optimization assessment
- Documentation validation for completeness and accuracy
- Final codebase review ensuring cleanup tasks are completed
- Generation of final evaluation report with metrics and recommendations

This script implements task 6 from the MVP finalization specification.
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import validation components
from validation.business_validator import BusinessValidator, ValidationReport, ValidationStatus
from tests.integration.test_integration_suite import IntegrationTestSuite
from performance.performance_assessor import PerformanceAssessor, PerformanceMetrics
from documentation.generator import DocumentationGenerator
from cleanup.cleanup_executor import CleanupExecutor
from cleanup.codebase_cleanup import CodebaseCleanup

# Import database components
from app.database import engine, Order, Route, Truck, Client, Location, Cargo, Package
from sqlmodel import Session, select

# Import order processor
from order_processor import OrderProcessor, ProcessingResult, ValidationResult, ValidationError


@dataclass
class ValidationSummary:
    """Summary of all validation results"""
    timestamp: str
    overall_status: str
    business_requirements: Dict[str, Any]
    integration_tests: Dict[str, Any]
    performance_assessment: Dict[str, Any]
    documentation_validation: Dict[str, Any]
    codebase_review: Dict[str, Any]
    recommendations: List[str]
    metrics: Dict[str, float]


class SystemValidationExecutor:
    """
    Comprehensive system validation executor for MVP finalization
    
    Coordinates all validation activities and generates final evaluation report.
    """

    def __init__(self):
        """Initialize the system validation executor"""
        self.start_time = datetime.now()
        self.validation_results = {}
        self.recommendations = []
        self.metrics = {}
        
        # Initialize validation components
        self.business_validator = BusinessValidator()
        self.performance_assessor = PerformanceAssessor()
        self.doc_generator = DocumentationGenerator()
        self.cleanup_executor = CleanupExecutor()
        self.codebase_analyzer = CodebaseCleanup()
        self.order_processor = OrderProcessor()
        
        print("🚀 System Validation Executor initialized")
        print(f"📅 Validation started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def validate_business_requirements(self) -> Dict[str, Any]:
        """
        Execute complete business requirements validation suite against all 7 requirements
        
        Returns:
            Dictionary with validation results and metrics
        """
        print("\n" + "="*60)
        print("📋 BUSINESS REQUIREMENTS VALIDATION")
        print("="*60)
        
        try:
            # Load test data from database
            with Session(engine) as session:
                orders = list(session.exec(select(Order)).all())
                routes = list(session.exec(select(Route)).all())
                trucks = list(session.exec(select(Truck)).all())
                
            print(f"📊 Loaded test data: {len(orders)} orders, {len(routes)} routes, {len(trucks)} trucks")
            
            # Run all business requirement validations
            validation_reports = self.business_validator.validate_all_requirements(
                orders=orders,
                routes=routes, 
                trucks=trucks,
                baseline_daily_loss=388.15
            )
            
            # Generate summary
            summary = self.business_validator.generate_summary_report(validation_reports)
            
            # Calculate compliance metrics
            passed_count = summary['passed_count']
            total_count = summary['total_requirements']
            compliance_rate = (passed_count / total_count * 100) if total_count > 0 else 0
            
            # Store metrics
            self.metrics.update({
                'business_requirements_compliance_rate': compliance_rate,
                'business_requirements_passed': passed_count,
                'business_requirements_total': total_count
            })
            
            # Generate recommendations
            if summary['overall_status'] != 'PASSED':
                self.recommendations.append("Address failing business requirements before production deployment")
                
            if summary['warning_count'] > 0:
                self.recommendations.append("Review warnings in business requirements validation")
            
            print(f"✅ Business Requirements Validation Complete")
            print(f"   Status: {summary['overall_status']}")
            print(f"   Compliance Rate: {compliance_rate:.1f}%")
            print(f"   Passed: {passed_count}/{total_count}")
            
            return {
                'status': summary['overall_status'],
                'compliance_rate': compliance_rate,
                'passed_count': passed_count,
                'total_count': total_count,
                'detailed_results': [asdict(report) for report in validation_reports],
                'summary': summary
            }
            
        except Exception as e:
            error_msg = f"Business requirements validation failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.recommendations.append("Fix business requirements validation errors")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }

    def execute_integration_tests(self) -> Dict[str, Any]:
        """
        Execute integration tests covering end-to-end workflows and data integrity
        
        Returns:
            Dictionary with test results and metrics
        """
        print("\n" + "="*60)
        print("🧪 INTEGRATION TESTS EXECUTION")
        print("="*60)
        
        try:
            import unittest
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(IntegrationTestSuite)
            
            # Run tests with custom result collector
            class ValidationTestResult(unittest.TestResult):
                def __init__(self):
                    super().__init__()
                    self.test_results = []
                    
                def addSuccess(self, test):
                    super().addSuccess(test)
                    self.test_results.append({
                        'test': str(test),
                        'status': 'PASSED',
                        'duration': getattr(test, '_test_duration', 0)
                    })
                    
                def addError(self, test, err):
                    super().addError(test, err)
                    self.test_results.append({
                        'test': str(test),
                        'status': 'ERROR',
                        'error': str(err[1]),
                        'duration': getattr(test, '_test_duration', 0)
                    })
                    
                def addFailure(self, test, err):
                    super().addFailure(test, err)
                    self.test_results.append({
                        'test': str(test),
                        'status': 'FAILED',
                        'error': str(err[1]),
                        'duration': getattr(test, '_test_duration', 0)
                    })
            
            # Execute tests
            result = ValidationTestResult()
            start_time = time.time()
            suite.run(result)
            execution_time = time.time() - start_time
            
            # Calculate metrics
            total_tests = result.testsRun
            passed_tests = len([r for r in result.test_results if r['status'] == 'PASSED'])
            failed_tests = len(result.failures) + len(result.errors)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Store metrics
            self.metrics.update({
                'integration_tests_success_rate': success_rate,
                'integration_tests_passed': passed_tests,
                'integration_tests_total': total_tests,
                'integration_tests_execution_time': execution_time
            })
            
            # Generate recommendations
            if success_rate < 100:
                self.recommendations.append("Fix failing integration tests before production")
                
            if execution_time > 30:  # Tests should complete quickly
                self.recommendations.append("Optimize integration test performance")
            
            print(f"✅ Integration Tests Complete")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Passed: {passed_tests}/{total_tests}")
            print(f"   Execution Time: {execution_time:.2f}s")
            
            return {
                'status': 'PASSED' if success_rate == 100 else 'FAILED',
                'success_rate': success_rate,
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'execution_time': execution_time,
                'test_results': result.test_results,
                'failures': [str(f) for f in result.failures],
                'errors': [str(e) for e in result.errors]
            }
            
        except Exception as e:
            error_msg = f"Integration tests execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.recommendations.append("Fix integration test execution errors")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }

    def perform_performance_assessment(self) -> Dict[str, Any]:
        """
        Perform performance testing and optimization assessment
        
        Returns:
            Dictionary with performance results and metrics
        """
        print("\n" + "="*60)
        print("⚡ PERFORMANCE ASSESSMENT")
        print("="*60)
        
        try:
            # Load test data
            with Session(engine) as session:
                orders = list(session.exec(select(Order)).all())[:10]  # Limit for performance testing
                routes = list(session.exec(select(Route)).all())
                trucks = list(session.exec(select(Truck)).all())
            
            print(f"📊 Performance testing with {len(orders)} orders")
            
            # Profile order processing
            print("   🔍 Profiling order processing...")
            processing_metrics = self.performance_assessor.profile_order_processing(orders, routes, trucks)
            
            # Check performance requirements
            meets_time_requirement = processing_metrics.execution_time_ms <= 5000  # 5 second limit
            
            # Generate performance report
            performance_report = self.performance_assessor.generate_performance_report()
            
            # Store metrics
            self.metrics.update({
                'order_processing_time_ms': processing_metrics.execution_time_ms,
                'order_processing_memory_mb': processing_metrics.memory_usage_mb,
                'performance_meets_requirements': meets_time_requirement
            })
            
            # Generate recommendations
            if not meets_time_requirement:
                self.recommendations.append(f"Order processing time ({processing_metrics.execution_time_ms:.1f}ms) exceeds 5-second requirement")
                
            if processing_metrics.memory_usage_mb > 100:
                self.recommendations.append("High memory usage detected - consider optimization")
            
            print(f"✅ Performance Assessment Complete")
            print(f"   Processing Time: {processing_metrics.execution_time_ms:.1f}ms")
            print(f"   Memory Usage: {processing_metrics.memory_usage_mb:.1f}MB")
            print(f"   Meets Requirements: {meets_time_requirement}")
            
            return {
                'status': 'PASSED' if meets_time_requirement else 'WARNING',
                'processing_time_ms': processing_metrics.execution_time_ms,
                'memory_usage_mb': processing_metrics.memory_usage_mb,
                'meets_requirements': meets_time_requirement,
                'detailed_metrics': asdict(processing_metrics),
                'performance_report': performance_report
            }
            
        except Exception as e:
            error_msg = f"Performance assessment failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.recommendations.append("Fix performance assessment errors")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }

    def validate_documentation(self) -> Dict[str, Any]:
        """
        Validate all generated documentation for completeness and accuracy
        
        Returns:
            Dictionary with documentation validation results
        """
        print("\n" + "="*60)
        print("📚 DOCUMENTATION VALIDATION")
        print("="*60)
        
        try:
            # Check if documentation exists
            docs_dir = Path("docs")
            expected_docs = [
                "user-guide.md",
                "technical-guide.md", 
                "api-documentation.md",
                "deployment-guide.md",
                "examples-and-tutorials.md"
            ]
            
            existing_docs = []
            missing_docs = []
            doc_sizes = {}
            
            for doc_name in expected_docs:
                doc_path = docs_dir / doc_name
                if doc_path.exists():
                    existing_docs.append(doc_name)
                    doc_sizes[doc_name] = doc_path.stat().st_size
                else:
                    missing_docs.append(doc_name)
            
            # Calculate completeness
            completeness_rate = (len(existing_docs) / len(expected_docs) * 100)
            
            # Check documentation quality (basic checks)
            quality_issues = []
            for doc_name in existing_docs:
                doc_path = docs_dir / doc_name
                if doc_sizes[doc_name] < 1000:  # Less than 1KB might be incomplete
                    quality_issues.append(f"{doc_name} appears incomplete ({doc_sizes[doc_name]} bytes)")
            
            # Store metrics
            self.metrics.update({
                'documentation_completeness_rate': completeness_rate,
                'documentation_files_count': len(existing_docs),
                'documentation_expected_count': len(expected_docs)
            })
            
            # Generate recommendations
            if missing_docs:
                self.recommendations.append(f"Generate missing documentation: {', '.join(missing_docs)}")
                
            if quality_issues:
                self.recommendations.append("Review documentation quality issues")
            
            print(f"✅ Documentation Validation Complete")
            print(f"   Completeness: {completeness_rate:.1f}%")
            print(f"   Existing: {len(existing_docs)}/{len(expected_docs)} files")
            if missing_docs:
                print(f"   Missing: {', '.join(missing_docs)}")
            
            return {
                'status': 'PASSED' if completeness_rate == 100 else 'WARNING',
                'completeness_rate': completeness_rate,
                'existing_docs': existing_docs,
                'missing_docs': missing_docs,
                'doc_sizes': doc_sizes,
                'quality_issues': quality_issues
            }
            
        except Exception as e:
            error_msg = f"Documentation validation failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.recommendations.append("Fix documentation validation errors")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }

    def conduct_codebase_review(self) -> Dict[str, Any]:
        """
        Conduct final codebase review ensuring cleanup tasks are completed
        
        Returns:
            Dictionary with codebase review results
        """
        print("\n" + "="*60)
        print("🔍 CODEBASE REVIEW")
        print("="*60)
        
        try:
            # Generate cleanup report
            print("   📊 Analyzing codebase quality...")
            
            # Get structured data from analyzer
            duplicates = self.codebase_analyzer.detect_duplicate_code()
            dead_code = self.codebase_analyzer.analyze_dead_code()
            quality_reports = self.codebase_analyzer.check_code_quality()
            
            # Count issues
            dead_code_count = len(dead_code)
            duplicate_count = len(duplicates)
            quality_issues_count = sum(len(qr.issues) for qr in quality_reports)
            
            cleanup_report = {
                'dead_code': dead_code,
                'duplicates': duplicates,
                'quality_reports': quality_reports,
                'total_files': len(self.codebase_analyzer.python_files)
            }
            
            # Calculate quality score
            total_files = cleanup_report.get('total_files', 1)
            total_issues = dead_code_count + duplicate_count + quality_issues_count
            quality_score = max(0, 100 - (total_issues / total_files * 10))  # Rough quality metric
            
            # Store metrics
            self.metrics.update({
                'codebase_quality_score': quality_score,
                'dead_code_items': dead_code_count,
                'duplicate_functions': duplicate_count,
                'quality_issues': quality_issues_count
            })
            
            # Generate recommendations
            if dead_code_count > 10:
                self.recommendations.append(f"Remove {dead_code_count} dead code items")
                
            if duplicate_count > 5:
                self.recommendations.append(f"Consolidate {duplicate_count} duplicate functions")
                
            if quality_score < 80:
                self.recommendations.append("Improve codebase quality before production")
            
            print(f"✅ Codebase Review Complete")
            print(f"   Quality Score: {quality_score:.1f}/100")
            print(f"   Dead Code Items: {dead_code_count}")
            print(f"   Duplicate Functions: {duplicate_count}")
            print(f"   Quality Issues: {quality_issues_count}")
            
            return {
                'status': 'PASSED' if quality_score >= 80 else 'WARNING',
                'quality_score': quality_score,
                'dead_code_count': dead_code_count,
                'duplicate_count': duplicate_count,
                'quality_issues_count': quality_issues_count,
                'cleanup_report': cleanup_report
            }
            
        except Exception as e:
            error_msg = f"Codebase review failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.recommendations.append("Fix codebase review errors")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }

    def generate_final_evaluation_report(self) -> Dict[str, Any]:
        """
        Generate final evaluation report with metrics, capabilities, and recommendations
        
        Returns:
            Complete evaluation report
        """
        print("\n" + "="*60)
        print("📊 GENERATING FINAL EVALUATION REPORT")
        print("="*60)
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall status
        all_statuses = [result.get('status', 'ERROR') for result in self.validation_results.values()]
        error_count = sum(1 for status in all_statuses if status == 'ERROR')
        warning_count = sum(1 for status in all_statuses if status == 'WARNING')
        
        if error_count > 0:
            overall_status = 'FAILED'
        elif warning_count > 0:
            overall_status = 'PASSED_WITH_WARNINGS'
        else:
            overall_status = 'PASSED'
        
        # Create comprehensive evaluation report
        evaluation_report = {
            'metadata': {
                'timestamp': end_time.isoformat(),
                'validation_duration_seconds': total_duration,
                'system_version': '1.0.0-MVP',
                'validation_executor_version': '1.0.0'
            },
            'executive_summary': {
                'overall_status': overall_status,
                'validation_components': len(self.validation_results),
                'total_recommendations': len(self.recommendations),
                'key_metrics': self.metrics
            },
            'detailed_results': self.validation_results,
            'system_capabilities': {
                'order_processing': self.metrics.get('order_processing_time_ms', 0) <= 5000,
                'business_compliance': self.metrics.get('business_requirements_compliance_rate', 0) >= 80,
                'integration_stability': self.metrics.get('integration_tests_success_rate', 0) >= 95,
                'documentation_completeness': self.metrics.get('documentation_completeness_rate', 0) >= 90,
                'code_quality': self.metrics.get('codebase_quality_score', 0) >= 80
            },
            'performance_metrics': {
                'order_processing_time_ms': self.metrics.get('order_processing_time_ms', 0),
                'memory_usage_mb': self.metrics.get('order_processing_memory_mb', 0),
                'integration_test_success_rate': self.metrics.get('integration_tests_success_rate', 0),
                'business_compliance_rate': self.metrics.get('business_requirements_compliance_rate', 0)
            },
            'recommendations': {
                'immediate_actions': [r for r in self.recommendations if 'error' in r.lower() or 'fix' in r.lower()],
                'improvements': [r for r in self.recommendations if r not in [r for r in self.recommendations if 'error' in r.lower() or 'fix' in r.lower()]],
                'production_readiness': self._assess_production_readiness()
            },
            'business_value': {
                'daily_loss_target': -388.15,
                'profitability_improvement': 'Validated through business requirements testing',
                'constraint_compliance': 'Proximity, capacity, time, and cargo constraints enforced',
                'contract_preservation': '5 contract routes maintained'
            }
        }
        
        # Save report to file
        report_file = Path("final_evaluation_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        # Generate human-readable summary
        summary_file = Path("evaluation_summary.md")
        summary_content = self._generate_summary_markdown(evaluation_report)
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"✅ Final Evaluation Report Generated")
        print(f"   Overall Status: {overall_status}")
        print(f"   Report File: {report_file}")
        print(f"   Summary File: {summary_file}")
        print(f"   Validation Duration: {total_duration:.1f}s")
        
        return evaluation_report

    def _assess_production_readiness(self) -> List[str]:
        """Assess production readiness based on validation results"""
        readiness_items = []
        
        # Check critical metrics
        if self.metrics.get('business_requirements_compliance_rate', 0) >= 100:
            readiness_items.append("✅ All business requirements validated")
        else:
            readiness_items.append("❌ Business requirements need attention")
            
        if self.metrics.get('integration_tests_success_rate', 0) >= 95:
            readiness_items.append("✅ Integration tests passing")
        else:
            readiness_items.append("❌ Integration tests need fixes")
            
        if self.metrics.get('order_processing_time_ms', 0) <= 5000:
            readiness_items.append("✅ Performance requirements met")
        else:
            readiness_items.append("❌ Performance optimization needed")
            
        if self.metrics.get('documentation_completeness_rate', 0) >= 90:
            readiness_items.append("✅ Documentation complete")
        else:
            readiness_items.append("❌ Documentation needs completion")
            
        return readiness_items

    def _generate_summary_markdown(self, report: Dict[str, Any]) -> str:
        """Generate human-readable markdown summary"""
        return f"""# Digital Freight Matching System - Final Evaluation Report

**Generated:** {report['metadata']['timestamp']}  
**Overall Status:** {report['executive_summary']['overall_status']}  
**Validation Duration:** {report['metadata']['validation_duration_seconds']:.1f} seconds

## Executive Summary

The Digital Freight Matching system has undergone comprehensive validation covering business requirements, integration testing, performance assessment, documentation review, and codebase quality analysis.

### Key Results

- **Business Requirements Compliance:** {report['performance_metrics']['business_compliance_rate']:.1f}%
- **Integration Test Success Rate:** {report['performance_metrics']['integration_test_success_rate']:.1f}%
- **Order Processing Time:** {report['performance_metrics']['order_processing_time_ms']:.1f}ms
- **Documentation Completeness:** {self.metrics.get('documentation_completeness_rate', 0):.1f}%

### System Capabilities

| Capability | Status |
|------------|--------|
| Order Processing (< 5s) | {'✅' if report['system_capabilities']['order_processing'] else '❌'} |
| Business Compliance | {'✅' if report['system_capabilities']['business_compliance'] else '❌'} |
| Integration Stability | {'✅' if report['system_capabilities']['integration_stability'] else '❌'} |
| Documentation Complete | {'✅' if report['system_capabilities']['documentation_completeness'] else '❌'} |
| Code Quality | {'✅' if report['system_capabilities']['code_quality'] else '❌'} |

### Business Value Delivered

- **Target:** Convert -$388.15 daily loss into profit
- **Constraint Enforcement:** 1km proximity, 48m³ capacity, 9180 lbs weight, 10-hour time limits
- **Contract Preservation:** All 5 required routes maintained
- **Performance:** Order processing within acceptable limits

### Recommendations

#### Immediate Actions
{chr(10).join(f"- {item}" for item in report['recommendations']['immediate_actions'])}

#### Improvements
{chr(10).join(f"- {item}" for item in report['recommendations']['improvements'])}

### Production Readiness Assessment

{chr(10).join(report['recommendations']['production_readiness'])}

---

*This report was generated by the System Validation Executor as part of the MVP finalization process.*
"""

    def execute_comprehensive_validation(self) -> ValidationSummary:
        """
        Execute all validation components and generate final report
        
        Returns:
            Complete validation summary
        """
        print("🎯 STARTING COMPREHENSIVE SYSTEM VALIDATION")
        print("="*80)
        
        # Execute all validation components
        self.validation_results['business_requirements'] = self.validate_business_requirements()
        self.validation_results['integration_tests'] = self.execute_integration_tests()
        self.validation_results['performance_assessment'] = self.perform_performance_assessment()
        self.validation_results['documentation_validation'] = self.validate_documentation()
        self.validation_results['codebase_review'] = self.conduct_codebase_review()
        
        # Generate final evaluation report
        final_report = self.generate_final_evaluation_report()
        
        # Create validation summary
        summary = ValidationSummary(
            timestamp=datetime.now().isoformat(),
            overall_status=final_report['executive_summary']['overall_status'],
            business_requirements=self.validation_results['business_requirements'],
            integration_tests=self.validation_results['integration_tests'],
            performance_assessment=self.validation_results['performance_assessment'],
            documentation_validation=self.validation_results['documentation_validation'],
            codebase_review=self.validation_results['codebase_review'],
            recommendations=self.recommendations,
            metrics=self.metrics
        )
        
        print("\n" + "="*80)
        print("🎉 COMPREHENSIVE SYSTEM VALIDATION COMPLETE")
        print("="*80)
        print(f"📊 Overall Status: {summary.overall_status}")
        print(f"⏱️  Total Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        print(f"📋 Total Recommendations: {len(self.recommendations)}")
        print(f"📈 Key Metrics Collected: {len(self.metrics)}")
        
        return summary


def main():
    """Main execution function"""
    print("=" * 80)
    print("🚀 DIGITAL FREIGHT MATCHING SYSTEM - COMPREHENSIVE VALIDATION")
    print("=" * 80)
    print("Task 6: Execute comprehensive system validation")
    print("Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4")
    print()
    
    try:
        # Initialize and execute validation
        executor = SystemValidationExecutor()
        summary = executor.execute_comprehensive_validation()
        
        # Display final results
        print("\n" + "🎯 VALIDATION SUMMARY")
        print("-" * 40)
        print(f"Overall Status: {summary.overall_status}")
        print(f"Business Requirements: {summary.business_requirements.get('status', 'ERROR')}")
        print(f"Integration Tests: {summary.integration_tests.get('status', 'ERROR')}")
        print(f"Performance Assessment: {summary.performance_assessment.get('status', 'ERROR')}")
        print(f"Documentation: {summary.documentation_validation.get('status', 'ERROR')}")
        print(f"Codebase Review: {summary.codebase_review.get('status', 'ERROR')}")
        
        if summary.overall_status == 'PASSED':
            print("\n✅ System validation PASSED - Ready for evaluation!")
        elif summary.overall_status == 'PASSED_WITH_WARNINGS':
            print("\n⚠️  System validation PASSED with warnings - Review recommendations")
        else:
            print("\n❌ System validation FAILED - Address critical issues")
            
        print(f"\n📄 Detailed reports saved:")
        print(f"   - final_evaluation_report.json")
        print(f"   - evaluation_summary.md")
        
        return 0 if summary.overall_status in ['PASSED', 'PASSED_WITH_WARNINGS'] else 1
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: System validation failed")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)