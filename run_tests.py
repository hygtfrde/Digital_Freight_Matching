#!/usr/bin/env python3
"""
Test runner script for Digital Freight Matching project

Usage:
    python run_tests.py                    # Run core tests (fast)
    python run_tests.py --all             # Run all tests (slow)
    python run_tests.py --core            # Run core tests only
    python run_tests.py --integration     # Run integration tests only
    python run_tests.py --performance     # Run performance tests only
    python run_tests.py test_business_validator  # Run specific test
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test categories
CORE_TESTS = [
    "tests/test_business_validator.py",
    "tests/test_db_manager.py", 
    "tests/test_network_cache.py",
    "tests/test_simple.py"
]

INTEGRATION_TESTS = [
    "tests/integration/",
]

PERFORMANCE_TESTS = [
    "tests/performance/",
]

SLOW_TESTS = [
    "tests/test_route_calculation_service.py",
    "tests/test_osmnx_basic.py"
]

def run_tests(category="core"):
    """Run tests by category"""
    
    if category == "core":
        cmd = [sys.executable, "-m", "pytest"] + CORE_TESTS + ["-v", "--maxfail=5"]
        print("🚀 Running core tests (fast)...")
        
    elif category == "integration":
        cmd = [sys.executable, "-m", "pytest"] + INTEGRATION_TESTS + ["-v", "--maxfail=3", "--timeout=600"]
        print("🔗 Running integration tests...")
        
    elif category == "performance":
        cmd = [sys.executable, "-m", "pytest"] + PERFORMANCE_TESTS + ["-v", "--maxfail=2", "--timeout=900"]
        print("⚡ Running performance tests...")
        
    elif category == "all":
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--maxfail=10", "--timeout=1200"]
        print("🌍 Running ALL tests (this may take a while)...")
        
    elif category == "safe":
        # Run everything except the problematic slow tests
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--maxfail=5", "--timeout=600"]
        for slow_test in SLOW_TESTS:
            cmd.extend(["--ignore", slow_test])
        print("🛡️  Running safe test suite (excluding slow tests)...")
        
    else:
        # Specific test file
        cmd = [sys.executable, "-m", "pytest", f"tests/{category}.py", "-v"]
        print(f"🎯 Running specific test: {category}")
    
    result = subprocess.run(cmd)
    return result.returncode

def main():
    if len(sys.argv) == 1:
        # Default to core tests
        return run_tests("core")
    
    arg = sys.argv[1]
    
    if arg == "--all":
        return run_tests("all")
    elif arg == "--core":
        return run_tests("core")
    elif arg == "--integration":
        return run_tests("integration")
    elif arg == "--performance":
        return run_tests("performance")
    elif arg == "--safe":
        return run_tests("safe")
    elif arg == "--help":
        print(__doc__)
        return 0
    else:
        # Assume it's a specific test name
        return run_tests(arg)

if __name__ == "__main__":
    sys.exit(main())