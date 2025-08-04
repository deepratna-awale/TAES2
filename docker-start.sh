#!/bin/bash

# TAES 2 Docker Start Script
# This script uses Docker Compose to manage the application stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 TAES 2 Docker Stack Management${NC}"
echo -e "${BLUE}=================================${NC}"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker and Docker Compose are available
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_status "✅ Docker and Docker Compose are available"
}

# Get Docker Compose command
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Start the full application stack
start_stack() {
    print_status "Starting TAES 2 application stack..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    # Start all services
    $COMPOSE_CMD up -d
    
    print_status "Waiting for services to be ready..."
    
    # Wait for database health check
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if $COMPOSE_CMD ps | grep -q "healthy"; then
            print_status "✅ Database is ready and healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Services failed to start after $max_attempts attempts"
            $COMPOSE_CMD logs
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo
    
    # Wait a bit more for the app to be fully ready
    sleep 5
}

# Start only the database
start_database() {
    print_status "Starting PostgreSQL database only..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    # Start only the database service
    $COMPOSE_CMD up -d database
    
    print_status "Waiting for database to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker inspect taes2-database --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            print_status "✅ Database is ready and healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Database failed to start after $max_attempts attempts"
            $COMPOSE_CMD logs database
            exit 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo
}

# Display connection information
show_connection_info() {
    echo -e "${GREEN}"
    echo "🎉 TAES 2 services are running!"
    echo "==============================="
    echo ""
    echo "🌐 Application:"
    echo "   URL: http://localhost:7860"
    echo ""
    echo "🔗 Database Connection:"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: taes2_db"
    echo "   Username: taes2_db_user"
    echo "   Password: postgres_admin_pass"
    echo ""
    echo "📊 Database URL:"
    echo "   postgresql://taes2_db_user:postgres_admin_pass@localhost:5432/taes2_db"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   • Start full stack: $0 start"
    echo "   • Start database only: $0 database"
    echo "   • Start pgAdmin: $0 admin"
    echo "   • Stop services: $0 stop"
    echo "   • View logs: $0 logs"
    echo "   • Check status: $0 status"
    echo -e "${NC}"
}

# Handle script arguments
case "${1:-start}" in
    "start")
        check_docker
        start_stack
        show_connection_info
        ;;
    "database")
        check_docker
        start_database
        show_connection_info
        ;;
    "stop")
        print_status "Stopping all services..."
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD down
        print_status "✅ All services stopped"
        ;;
    "restart")
        print_status "Restarting services..."
        $0 stop
        sleep 2
        $0 start
        ;;
    "logs")
        COMPOSE_CMD=$(get_compose_cmd)
        if [ -n "$2" ]; then
            $COMPOSE_CMD logs -f "$2"
        else
            $COMPOSE_CMD logs -f
        fi
        ;;
    "status")
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD ps
        ;;
    "admin")
        print_status "Starting pgAdmin for database management..."
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD --profile admin up -d pgadmin
        echo -e "${GREEN}🌐 pgAdmin available at: http://localhost:8080${NC}"
        echo -e "${GREEN}📧 Email: admin@example.com${NC}"
        echo -e "${GREEN}🔑 Password: admin123${NC}"
        ;;
    *)
        echo "Usage: $0 {start|database|stop|restart|logs|status|admin}"
        echo ""
        echo "Commands:"
        echo "  start     - Start full application stack (default)"
        echo "  database  - Start database only"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart services"
        echo "  logs      - Show service logs (optional: specify service name)"
        echo "  status    - Show service status"
        echo "  admin     - Start pgAdmin web interface"
        exit 1
        ;;
esac
