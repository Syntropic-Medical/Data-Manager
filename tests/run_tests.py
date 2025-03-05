#!/usr/bin/env python
"""
Script to run all tests for the Data-Manager application.
"""
import os
import sys
import subprocess
import importlib.metadata

def check_dependencies():
    """Check if dependencies are correctly installed."""
    try:
        flask_version = importlib.metadata.version('flask')
        pytest_flask_version = importlib.metadata.version('pytest-flask')
        
        print(f"Flask version: {flask_version}")
        print(f"pytest-flask version: {pytest_flask_version}")
        
        # Check if Flask version is compatible with pytest-flask
        if flask_version.startswith('2.3') or flask_version.startswith('3.'):
            print("\nWARNING: You're using Flask version >= 2.3, which may not be compatible with pytest-flask.")
            print("Consider downgrading Flask to version 2.2.x or earlier:")
            print("pip install flask<=2.2.5\n")
            return False
        
        return True
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False

def run_tests_with_subprocess():
    """Run tests using subprocess to avoid import issues."""
    print("Running tests with subprocess...")
    command = [
        "pytest",
        "-xvs",
        "--cov=src",
        "--cov-report=term",
        "--cov-report=html",
        "tests/"
    ]
    subprocess.run(command)

if __name__ == "__main__":
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, 'src'))
    
    if check_dependencies():
        run_tests_with_subprocess()
    else:
        print("Please fix dependency issues before running tests.")
        sys.exit(1) 