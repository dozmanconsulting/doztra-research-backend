import uvicorn
import argparse
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("doztra-auth-service")

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description="Run the Doztra Auth Service")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set log level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Check if the port is available
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((args.host, args.port))
    except OSError:
        logger.warning(f"Port {args.port} is already in use. Try a different port.")
        return 1
    except Exception as e:
        logger.error(f"Error checking port availability: {e}")
    
    # Log startup information
    logger.info(f"Starting Doztra Auth Service on {args.host}:{args.port}")
    logger.info(f"Auto-reload: {'enabled' if args.reload else 'disabled'}")
    logger.info(f"Workers: {args.workers}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level="debug" if args.debug else "info"
        )
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
