#!/bin/bash
# Start script for Doztra Auth Service with default port 8000

# Default port
PORT=8000

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            echo "Usage: $0 [-p|--port PORT]"
            exit 1
            ;;
    esac
done

# Kill any existing instances
echo "Stopping any existing Doztra Auth Service instances..."
pkill -f "python run.py" || true

# Start the service with the specified port
echo "Starting Doztra Auth Service on port $PORT..."
./start.sh --skip-deps --port $PORT

# Exit with the same status as the start.sh script
exit $?
