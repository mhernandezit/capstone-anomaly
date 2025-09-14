#!/bin/bash
# System Validation Script

echo "🔍 Validating System Components"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if containers are running
check_containers() {
    print_status "Checking containers..."
    
    local containers=("nats" "bmp-collector" "spine-01" "spine-02" "tor-01" "tor-02" "edge-01" "edge-02")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "clab-bgp-anomaly-lab-$container"; then
            print_success "Container $container is running"
        else
            print_error "Container $container is not running"
            all_running=false
        fi
    done
    
    if [ "$all_running" = true ]; then
        print_success "All containers are running"
        return 0
    else
        print_error "Some containers are not running"
        return 1
    fi
}

# Check NATS connectivity
check_nats() {
    print_status "Checking NATS connectivity..."
    
    if docker exec clab-bgp-anomaly-lab-nats nc -z localhost 4222; then
        print_success "NATS is listening on port 4222"
    else
        print_error "NATS is not accessible"
        return 1
    fi
    
    # Test NATS publish/subscribe
    if docker exec clab-bgp-anomaly-lab-nats nats pub "test" "hello" >/dev/null 2>&1; then
        print_success "NATS publish/subscribe working"
    else
        print_warning "NATS publish/subscribe test failed"
    fi
}

# Check BMP collector
check_bmp_collector() {
    print_status "Checking BMP collector..."
    
    if docker logs clab-bgp-anomaly-lab-bmp-collector 2>&1 | grep -q "Starting BMP collector"; then
        print_success "BMP collector is running"
    else
        print_error "BMP collector is not running properly"
        return 1
    fi
    
    # Check if BMP collector is listening
    if docker exec clab-bgp-anomaly-lab-bmp-collector nc -z localhost 1790; then
        print_success "BMP collector is listening on port 1790"
    else
        print_warning "BMP collector port 1790 not accessible"
    fi
}

# Check BGP sessions
check_bgp_sessions() {
    print_status "Checking BGP sessions..."
    
    local devices=("spine-01" "spine-02" "tor-01" "tor-02" "edge-01" "edge-02")
    local established_sessions=0
    local total_sessions=0
    
    for device in "${devices[@]}"; do
        print_status "Checking BGP on $device..."
        local bgp_output=$(docker exec clab-bgp-anomaly-lab-$device vtysh -c "show bgp summary" 2>/dev/null || echo "")
        
        if [ -n "$bgp_output" ]; then
            local established=$(echo "$bgp_output" | grep -c "Established" || echo "0")
            local total=$(echo "$bgp_output" | grep -c "Neighbor" || echo "0")
            
            established_sessions=$((established_sessions + established))
            total_sessions=$((total_sessions + total))
            
            print_success "$device: $established/$total BGP sessions established"
        else
            print_warning "$device: Could not get BGP status"
        fi
    done
    
    if [ $total_sessions -gt 0 ]; then
        local percentage=$((established_sessions * 100 / total_sessions))
        print_status "Overall BGP status: $established_sessions/$total_sessions sessions ($percentage%)"
        
        if [ $percentage -ge 80 ]; then
            print_success "BGP sessions are healthy"
            return 0
        else
            print_warning "Some BGP sessions are not established"
            return 1
        fi
    else
        print_error "No BGP sessions found"
        return 1
    fi
}

# Check dashboard accessibility
check_dashboard() {
    print_status "Checking dashboard accessibility..."
    
    if curl -s http://localhost:8501 >/dev/null 2>&1; then
        print_success "Dashboard is accessible at http://localhost:8501"
        return 0
    else
        print_warning "Dashboard is not accessible (may not be started yet)"
        return 1
    fi
}

# Check ML integration
check_ml_integration() {
    print_status "Checking ML integration..."
    
    # Check if Python process is running
    if pgrep -f "integrate-with-ml.py" >/dev/null; then
        print_success "ML integration process is running"
    else
        print_warning "ML integration process is not running"
    fi
    
    # Check for recent BGP updates in NATS
    local recent_updates=$(docker exec clab-bgp-anomaly-lab-nats nats sub "bgp.updates" --count 5 --timeout 5s 2>/dev/null | wc -l)
    
    if [ "$recent_updates" -gt 0 ]; then
        print_success "BGP updates are flowing through NATS ($recent_updates recent messages)"
    else
        print_warning "No recent BGP updates in NATS"
    fi
}

# Main validation
main() {
    print_status "Starting system validation..."
    
    local exit_code=0
    
    check_containers || exit_code=1
    echo ""
    
    check_nats || exit_code=1
    echo ""
    
    check_bmp_collector || exit_code=1
    echo ""
    
    check_bgp_sessions || exit_code=1
    echo ""
    
    check_dashboard || exit_code=1
    echo ""
    
    check_ml_integration || exit_code=1
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        print_success "All system components are working correctly!"
    else
        print_error "Some system components have issues"
    fi
    
    return $exit_code
}

# Run validation
main
