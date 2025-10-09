#!/usr/bin/env python3
"""
Redirect Server for Doztra Auth Service

This script runs a simple HTTP server on port 8000 that redirects all requests to port 8001.
This is useful when users try to access the default port (8000) but the service is running on port 8001.
"""

import http.server
import socketserver
import argparse
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("doztra-redirect-server")

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Redirect all GET requests to the target port."""
        target_host = f"http://{self.server.target_host}:{self.server.target_port}"
        target_url = f"{target_host}{self.path}"
        
        self.send_response(302)  # Temporary redirect
        self.send_header('Location', target_url)
        self.end_headers()
        
        logger.info(f"Redirected: {self.path} -> {target_url}")

    def do_POST(self):
        """Redirect all POST requests to the target port."""
        target_host = f"http://{self.server.target_host}:{self.server.target_port}"
        target_url = f"{target_host}{self.path}"
        
        self.send_response(307)  # Temporary redirect that preserves the method
        self.send_header('Location', target_url)
        self.end_headers()
        
        logger.info(f"Redirected POST: {self.path} -> {target_url}")
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger."""
        logger.info(format % args)

def main():
    """Main function to run the redirect server."""
    parser = argparse.ArgumentParser(description="Run a redirect server for Doztra Auth Service")
    parser.add_argument("--source-port", type=int, default=8000, help="Source port to listen on")
    parser.add_argument("--target-host", type=str, default="localhost", help="Target host to redirect to")
    parser.add_argument("--target-port", type=int, default=8001, help="Target port to redirect to")
    
    args = parser.parse_args()
    
    # Create the server
    handler = RedirectHandler
    
    try:
        with socketserver.TCPServer(("", args.source_port), handler) as httpd:
            # Add target information to the server
            httpd.target_host = args.target_host
            httpd.target_port = args.target_port
            
            logger.info(f"Starting redirect server on port {args.source_port}")
            logger.info(f"Redirecting all requests to {args.target_host}:{args.target_port}")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
            finally:
                httpd.server_close()
                logger.info("Server closed")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"Port {args.source_port} is already in use. Cannot start redirect server.")
            return 1
        else:
            logger.error(f"Error starting server: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
