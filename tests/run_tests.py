#!/usr/bin/env python3
"""
Test runner script for Doztra Auth Service.

This script runs all unit tests and API tests for the Doztra Auth Service.
"""

import argparse
import subprocess
import sys
import os

def run_unit_tests(verbose=False):
    """Run unit tests using pytest."""
    print("Running unit tests...")
    
    cmd = ["pytest", "tests/unit"]
    if verbose:
        cmd.append("-v")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_api_tests(host="localhost", port=8000, verbose=False):
    """Run API tests."""
    print(f"Running API tests against {host}:{port}...")
    
    cmd = ["python", "tests/api_tests.py", "--host", host, "--port", str(port)]
    if verbose:
        cmd.append("--verbose")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for Doztra Auth Service")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--host", default="localhost", help="Host for API tests")
    parser.add_argument("--port", type=int, default=8000, help="Port for API tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # If neither --unit nor --api is specified, run both
    run_all = not (args.unit or args.api)
    
    success = True
    
    # Run unit tests
    if args.unit or run_all:
        unit_success = run_unit_tests(args.verbose)
        if not unit_success:
            success = False
            print("Unit tests failed!")
        else:
            print("Unit tests passed!")
    
    # Run API tests
    if args.api or run_all:
        # Check if the server is running
        try:
            import requests
            response = requests.get(f"http://{args.host}:{args.port}/health", timeout=2)
            if response.status_code != 200:
                print(f"Warning: Server at {args.host}:{args.port} is not responding correctly.")
                print("Make sure the server is running before running API tests.")
                if not args.api:  # Only skip if not explicitly requested
                    print("Skipping API tests.")
                    return success
        except requests.RequestException:
            print(f"Warning: Could not connect to server at {args.host}:{args.port}.")
            print("Make sure the server is running before running API tests.")
            if not args.api:  # Only skip if not explicitly requested
                print("Skipping API tests.")
                return success
        
        api_success = run_api_tests(args.host, args.port, args.verbose)
        if not api_success:
            success = False
            print("API tests failed!")
        else:
            print("API tests passed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
