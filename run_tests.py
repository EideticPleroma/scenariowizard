#!/usr/bin/env python3
"""
Test runner script for ScenarioWizard
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True

def main():
    """Main test runner"""
    print("🧪 ScenarioWizard Test Suite Runner")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Test commands
    commands = [
        ("python -m pytest tests/ -v --tb=short", "Unit Tests"),
        ("python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing", "Coverage Report"),
        ("python -m black app/ tests/ --check", "Code Formatting Check"),
        ("python -m isort app/ tests/ --check-only", "Import Sorting Check"),
        ("python -m flake8 app/ tests/", "Linting Check"),
    ]
    
    # Run all commands
    success_count = 0
    total_count = len(commands)
    
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary: {success_count}/{total_count} checks passed")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
