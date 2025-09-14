#!/bin/bash
# Full System Test - Containerlab + BMP + NATS + Frontend + Failures

set -e

echo "🚀 Full System Test - BGP Anomaly Detection"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LAB_NAME="bgp-anomaly-lab"
TEST_DURATION=300  # 5 minutes
FAILURE_INTERVAL=60  # Inject failures every minute

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    if [ -f /tmp/test_pid ]; then
        kill $(cat /tmp/test_pid) 2>/dev/null || true
        rm -f /tmp/test_pid
    fi
    docker stop $(docker ps -q --filter "name=clab-$LAB_NAME") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=clab-$LAB_NAME") 2>/dev/null || true
}

# Set up cleanup trap
trap cleanup EXIT

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command_exists clab; then
    print_error "Containerlab is not installed"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python3 is not installed"
    exit 1
fi

print_success "All prerequisites found"

# Step 1: Check BMP collector binary
print_status "Checking BMP collector binary..."
if [ ! -f "../cmd/bmp-collector/bmp-collector" ]; then
    print_error "BMP collector binary not found. Please build it first:"
    print_error "cd ../cmd/bmp-collector && go build -o bmp-collector ."
    exit 1
fi
print_success "BMP collector binary found"

# Step 2: Deploy Containerlab environment
print_status "Deploying Containerlab environment..."
clab deploy -t topo.clab.yml
if [ $? -ne 0 ]; then
    print_error "Failed to deploy Containerlab"
    exit 1
fi

# Step 3: Wait for services to be ready
print_status "Waiting for services to start..."

# Wait for NATS
wait_for_service "NATS" "docker exec clab-$LAB_NAME-nats nc -z localhost 4222"

# Wait for BMP collector
wait_for_service "BMP Collector" "docker logs clab-$LAB_NAME-bmp-collector 2>&1 | grep -q 'Starting BMP collector'"

# Wait for BGP sessions to establish
print_status "Waiting for BGP sessions to establish..."
sleep 30

# Check BGP status
print_status "Checking BGP status..."
./scripts/check-bgp.sh

# Step 4: Start monitoring dashboard
print_status "Starting Streamlit dashboard..."
cd ../src
streamlit run dash/enhanced_dashboard.py --server.port 8501 --server.headless true &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > /tmp/test_pid
cd ../lab

# Step 5: Start ML integration
print_status "Starting ML integration..."
python3 scripts/integrate-with-ml.py &
ML_PID=$!
echo $ML_PID >> /tmp/test_pid

# Step 6: Start failure injection
print_status "Starting automated failure injection..."
(
    sleep 30  # Wait for system to stabilize
    
    # Run comprehensive failure scenarios
    ./scripts/inject-test-failures.sh
    
    # Additional periodic failures
    for i in {1..3}; do
        print_warning "Injecting additional failure #$i"
        ./scripts/inject-failures.sh
        sleep $FAILURE_INTERVAL
    done
) &
FAILURE_PID=$!
echo $FAILURE_PID >> /tmp/test_pid

# Step 7: Monitor system
print_status "Monitoring system for $TEST_DURATION seconds..."
print_status "Dashboard available at: http://localhost:8501"
print_status "Press Ctrl+C to stop early"

# Monitor logs and status
(
    while true; do
        echo ""
        print_status "=== System Status ==="
        
        # Check container status
        print_status "Containers:"
        docker ps --filter "name=clab-$LAB_NAME" --format "table {{.Names}}\t{{.Status}}"
        
        # Check BGP status
        print_status "BGP Sessions:"
        docker exec clab-$LAB_NAME-spine-01 vtysh -c "show bgp summary" 2>/dev/null | grep -E "(Neighbor|Established)" || true
        
        # Check BMP collector
        print_status "BMP Collector:"
        docker logs --tail 5 clab-$LAB_NAME-bmp-collector 2>&1 | tail -3
        
        # Check NATS messages
        print_status "NATS Messages:"
        docker exec clab-$LAB_NAME-nats nats sub "bgp.updates" --count 1 --timeout 2s 2>/dev/null || echo "No recent messages"
        
        sleep 30
    done
) &
MONITOR_PID=$!
echo $MONITOR_PID >> /tmp/test_pid

# Wait for test duration
sleep $TEST_DURATION

# Step 8: Generate test report
print_status "Generating test report..."

REPORT_FILE="test-report-$(date +%Y%m%d-%H%M%S).txt"
{
    echo "BGP Anomaly Detection System Test Report"
    echo "========================================"
    echo "Test Date: $(date)"
    echo "Test Duration: $TEST_DURATION seconds"
    echo ""
    
    echo "Container Status:"
    docker ps --filter "name=clab-$LAB_NAME" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    
    echo "BGP Status:"
    ./scripts/check-bgp.sh
    echo ""
    
    echo "BMP Collector Logs (last 20 lines):"
    docker logs --tail 20 clab-$LAB_NAME-bmp-collector
    echo ""
    
    echo "ML Integration Logs (last 20 lines):"
    docker logs --tail 20 clab-$LAB_NAME-ml-integration 2>/dev/null || echo "ML integration not containerized"
    echo ""
    
    echo "Test completed successfully!"
} > "$REPORT_FILE"

print_success "Test completed! Report saved to: $REPORT_FILE"
print_status "Dashboard: http://localhost:8501"
print_status "To stop all services: ./scripts/destroy.sh"
