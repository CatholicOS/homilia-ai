#!/usr/bin/env python3
"""
Test runner script for document processing tests.

This script runs all tests and provides detailed output.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def run_tests(test_pattern=None, verbose=False, coverage=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent
    cmd.append(str(test_dir))
    
    # Add pattern if specified
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add verbose flag
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=services", "--cov=routes", "--cov-report=html", "--cov-report=term"])
    
    # Add other useful flags
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=backend_dir)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest and other test dependencies.")
        print("Run: pip install pytest pytest-cov pytest-asyncio")
        return 1


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run document processing tests")
    parser.add_argument(
        "-k", "--pattern", 
        help="Test pattern to match (pytest -k option)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage report"
    )
    parser.add_argument(
        "--routes-only", 
        action="store_true", 
        help="Run only document routes tests"
    )
    parser.add_argument(
        "--service-only", 
        action="store_true", 
        help="Run only document service tests"
    )
    
    args = parser.parse_args()
    
    # Determine test pattern
    test_pattern = args.pattern
    if args.routes_only:
        test_pattern = "test_document_routes"
    elif args.service_only:
        test_pattern = "test_document_processing_service"
    
    # Run tests
    exit_code = run_tests(
        test_pattern=test_pattern,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
