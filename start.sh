#!/bin/bash

# TAES 2 Startup Script
# This script provides easy ways to start the application in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "TAES 2 Startup Script"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [main|minimal|simple]  Start the application with specified interface"
    echo "  test                         Run application tests"
    echo "  docker                       Start with Docker Compose"
    echo "  docker-build                 Rebuild and start with Docker Compose"
    echo "  clean                        Clean up Docker containers and volumes"
    echo "  help                         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start simple              Start with simple interface"
    echo "  $0 start                     Start with main interface (default)"
    echo "  $0 test                      Run tests"
    echo "  $0 docker                    Start with Docker"
}

# Function to check if dependencies are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check if requirements are installed
    if ! python3 -c "import gradio" &> /dev/null; then
        print_warning "Python dependencies may not be installed"
        print_status "Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    print_success "Dependencies check completed"
}

# Function to start the application
start_app() {
    local interface_mode=${1:-main}
    
    print_status "Starting TAES 2 with '$interface_mode' interface..."
    
    # Set environment variable
    export TAES_INTERFACE_MODE=$interface_mode
    
    # Check dependencies
    check_dependencies
    
    # Start the application
    python3 app.py $interface_mode
}

# Function to run tests
run_tests() {
    print_status "Running TAES 2 tests..."
    
    # Check dependencies
    check_dependencies
    
    # Run the test suite
    pip install -q -r requirements-dev.txt
    python3 -m pytest -q tests
}

# Function to start with Docker
start_docker() {
    local rebuild=${1:-false}
    
    print_status "Starting TAES 2 with Docker Compose..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    if [ "$rebuild" = "true" ]; then
        print_status "Rebuilding Docker images..."
        docker compose down --volumes --remove-orphans
        docker compose build --no-cache
    fi
    
    # Start the services
    docker compose up -d
    
    print_success "TAES 2 started with Docker!"
    print_status "Application will be available at: http://localhost:7860"
    print_status "Database admin: docker compose --profile admin up -d pgadmin (http://localhost:8080)"
    print_status ""
    print_status "To view logs: docker compose logs -f app"
    print_status "To stop: docker compose down"
}

# Function to clean up Docker
clean_docker() {
    print_status "Cleaning up Docker containers and volumes..."
    
    docker compose down --volumes --remove-orphans
    docker system prune -f
    
    print_success "Docker cleanup completed"
}

# Main script logic
case "${1:-help}" in
    start)
        start_app "${2:-main}"
        ;;
    test)
        run_tests
        ;;
    docker)
        start_docker false
        ;;
    docker-build)
        start_docker true
        ;;
    clean)
        clean_docker
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
