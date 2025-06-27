#!/bin/bash
# Safe mode, exit on error
set -e

# Color definitions
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
BOLD="\033[1m"
RESET="\033[0m"

# Source environment variables
source .env

# Function to print colored headers
print_header() {
    echo -e "${BOLD}${BLUE}================================${RESET}"
    echo -e "${BOLD}${BLUE} $1${RESET}"
    echo -e "${BOLD}${BLUE}================================${RESET}"
}

# Function to print status messages
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[INFO] ${message}${RESET}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR] $1${RESET}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}[WARNING] $1${RESET}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS] $1${RESET}"
}

# Function to check the status of the containers
check_containers() {
    print_status "${CYAN}" "Checking container health status..."

    # Verify every container is running
    FAILED_CONTAINERS=$(docker-compose -f docker-compose.yml -f labels/labels-${1}.yml ps -q | xargs docker inspect --format='{{.Name}}: {{.State.Status}}' | grep -v "running" || true)

    if [ -n "$FAILED_CONTAINERS" ]; then
        print_error "Some containers are not running:"
        echo "$FAILED_CONTAINERS"
        return 1
    fi

    print_success "All containers are running properly"
    return 0
}

# Function to check odoo service health
check_service_health() {
    local max_attempts=10
    local attempt=1
    local wait_time=1

    print_status "${CYAN}" "Verifying Odoo service health..."

    while [ $attempt -le $max_attempts ]; do
        print_status "${YELLOW}" "Health check attempt $attempt of $max_attempts"

        # Verify service health via HTTP request
        if [ -n "${1}" ]; then
            STATUS=$(curl -Is "${1}${DNS}" 2>/dev/null | head -n 1 | cut -d' ' -f2 || echo "")
        else
            STATUS=$(curl -Is "${DNS}" 2>/dev/null | head -n 1 | cut -d' ' -f2 || echo "")
        fi

        if [ "$STATUS" = "303" ]; then
            print_success "Odoo service is healthy (HTTP $STATUS)"
            return 0
        elif [ -n "$STATUS" ]; then
            print_warning "Service responding with status $STATUS, waiting..."
        else
            print_warning "No response from service, retrying..."
        fi

        sleep $wait_time
        attempt=$((attempt + 1))
    done

    print_error "Service unavailable after $((max_attempts * wait_time)) seconds"
    return 1
}

# Show logs on error
show_logs_on_error() {
    print_header "FAILURE LOGS"

    # Show docker logs
    print_status "${BLUE}" "Displaying Docker container logs:"
    docker-compose -f docker-compose.yml -f labels/labels-${1}.yml logs --tail=30

    echo ""

    # Odoo logs
    if [ -f "log/odoo-server.log" ]; then
        print_status "${BLUE}" "Displaying Odoo server logs:"
        tail -n 30 log/odoo-server.log
    else
        print_warning "Odoo log file not found at path: log/odoo-server.log"
    fi
}

# Determine environment mode
LABEL_FILE=labels/labels-prod.yml
TEST_URL=""
MODE=""

print_header "Checking environment variables"
if [ "$ENVIRONMENT" = "dev" ]; then
    MODE="DEVELOPMENT"
    LABEL_FILE=labels/labels-dev.yml
    TEST_URL="test."
elif [ "$ENVIRONMENT" = "prod" ]; then
    MODE="PRODUCTION"
else
    print_error "Unknown environment mode. ENVIRONMENT variable in .env should be 'dev' or 'prod'"
    exit 1
fi

URL="${TEST_URL}${DNS}"
print_success "Environment variables verified"
print_status "${CYAN}" "Project name: $COMPOSE_PROJECT_NAME"
print_status "${CYAN}" "Odoo version: $ODOO_VERSION"
print_status "${CYAN}" "Deploying in $MODE mode"
print_status "${CYAN}" "On URL: $URL"
print_status "${CYAN}" "Using label file: $LABEL_FILE"
print_status "${CYAN}" "Optional parameters:"
print_status "${CYAN}" "Install whisper speech recognition: $OPTIONAL_WHISPER"

# Start containers
print_header "STARTING CONTAINERS"
print_status "${CYAN}" "Building containers"
docker-compose -f docker-compose.yml -f $LABEL_FILE build
echo ""

print_status "${CYAN}" "Spinning up containers"
docker-compose -f docker-compose.yml -f $LABEL_FILE up -d
echo ""

# Check containers and service health
if check_containers $ENVIRONMENT; then
    echo ""
    if check_service_health $TEST_URL; then
        echo ""
        print_header "DEPLOYMENT SUCCESSFUL"
        print_success "Odoo environment started successfully"
    else
        echo ""
        show_logs_on_error $ENVIRONMENT
        exit 1
    fi
else
    echo ""
    print_header "DEPLOYMENT FAILED"
    print_error "Failed to start Odoo environment"
    show_logs_on_error $ENVIRONMENT
    exit 1
fi