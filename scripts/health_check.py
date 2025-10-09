#!/usr/bin/env python3
"""
Health Check Script for Doztra Auth Service

This script performs a health check on the Doztra Auth Service API.
It can be used in monitoring systems or as a Kubernetes liveness probe.

Usage:
    python health_check.py [--url URL] [--timeout TIMEOUT]

Example:
    python health_check.py --url http://localhost:8000/health --timeout 5
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional
import urllib.request
import urllib.error


def check_health(url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Check the health of the service.

    Args:
        url: The URL of the health check endpoint
        timeout: Timeout in seconds

    Returns:
        Dict containing the health check response

    Raises:
        urllib.error.URLError: If the request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def main() -> int:
    """
    Main function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Health check for Doztra Auth Service")
    parser.add_argument("--url", default="http://localhost:8000/health", help="Health check URL")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        start_time = time.time()
        health_data = check_health(args.url, args.timeout)
        elapsed_time = time.time() - start_time
        
        if health_data.get("status") == "healthy":
            if args.verbose:
                print(f"Health check passed in {elapsed_time:.2f}s")
                print(f"Service: {health_data.get('service')}")
                print(f"Version: {health_data.get('version')}")
                print(f"Timestamp: {health_data.get('timestamp')}")
            return 0
        else:
            if args.verbose:
                print(f"Health check failed: Service status is {health_data.get('status')}")
            return 1
    
    except urllib.error.URLError as e:
        if args.verbose:
            print(f"Health check failed: {e}")
        return 1
    
    except json.JSONDecodeError as e:
        if args.verbose:
            print(f"Health check failed: Invalid JSON response: {e}")
        return 1
    
    except Exception as e:
        if args.verbose:
            print(f"Health check failed: Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
