#!/bin/bash
# Enhanced Failure Injection for Testing

set -e

echo "💥 Injecting Test Failures"
echo "========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to inject interface failure
inject_interface_failure() {
    local device=$1
    local interface=$2
    local duration=${3:-30}
    
    print_warning "Injecting interface failure: $device $interface (${duration}s)"
    
    # Bring interface down
    docker exec clab-bgp-anomaly-lab-$device ip link set $interface down
    
    # Wait for duration
    sleep $duration
    
    # Bring interface back up
    docker exec clab-bgp-anomaly-lab-$device ip link set $interface up
    
    print_success "Interface $interface restored on $device"
}

# Function to inject BGP session reset
inject_bgp_reset() {
    local device=$1
    local neighbor=$2
    
    print_warning "Injecting BGP session reset: $device -> $neighbor"
    
    # Clear BGP session
    docker exec clab-bgp-anomaly-lab-$device vtysh -c "clear bgp $neighbor"
    
    print_success "BGP session reset: $device -> $neighbor"
}

# Function to inject route withdrawal
inject_route_withdrawal() {
    local device=$1
    local prefix=$2
    
    print_warning "Injecting route withdrawal: $device withdraws $prefix"
    
    # Withdraw route
    docker exec clab-bgp-anomaly-lab-$device vtysh -c "no network $prefix"
    
    sleep 10
    
    # Re-advertise route
    docker exec clab-bgp-anomaly-lab-$device vtysh -c "network $prefix"
    
    print_success "Route $prefix re-advertised on $device"
}

# Function to inject container restart
inject_container_restart() {
    local device=$1
    local duration=${2:-60}
    
    print_warning "Injecting container restart: $device (${duration}s down)"
    
    # Stop container
    docker stop clab-bgp-anomaly-lab-$device
    
    # Wait
    sleep $duration
    
    # Start container
    docker start clab-bgp-anomaly-lab-$device
    
    # Wait for BGP to re-establish
    sleep 30
    
    print_success "Container $device restarted and BGP re-established"
}

# Function to inject high CPU load
inject_cpu_load() {
    local device=$1
    local duration=${2:-60}
    
    print_warning "Injecting CPU load: $device (${duration}s)"
    
    # Start CPU intensive process
    docker exec -d clab-bgp-anomaly-lab-$device sh -c "
        for i in \$(seq 1 4); do
            while true; do
                : 
            done &
        done
    "
    
    # Wait
    sleep $duration
    
    # Kill CPU intensive processes
    docker exec clab-bgp-anomaly-lab-$device pkill -f "while true"
    
    print_success "CPU load removed from $device"
}

# Main failure injection scenarios
print_status "Starting failure injection scenarios..."

# Scenario 1: Interface flapping
print_status "=== Scenario 1: Interface Flapping ==="
inject_interface_failure "spine-01" "eth2" 15
sleep 5
inject_interface_failure "spine-02" "eth2" 15
sleep 10

# Scenario 2: BGP session resets
print_status "=== Scenario 2: BGP Session Resets ==="
inject_bgp_reset "spine-01" "10.0.1.2"
sleep 5
inject_bgp_reset "spine-02" "10.0.1.1"
sleep 10

# Scenario 3: Route withdrawals
print_status "=== Scenario 3: Route Withdrawals ==="
inject_route_withdrawal "server-01" "192.168.1.0/24"
sleep 5
inject_route_withdrawal "server-02" "192.168.2.0/24"
sleep 10

# Scenario 4: Container restart
print_status "=== Scenario 4: Container Restart ==="
inject_container_restart "tor-01" 30
sleep 10

# Scenario 5: CPU load
print_status "=== Scenario 5: CPU Load ==="
inject_cpu_load "spine-01" 30
sleep 10

# Scenario 6: Multiple simultaneous failures
print_status "=== Scenario 6: Multiple Failures ==="
inject_interface_failure "edge-01" "eth1" 20 &
inject_bgp_reset "spine-01" "10.0.2.1" &
inject_route_withdrawal "server-03" "192.168.3.0/24" &
wait

print_success "All failure scenarios completed!"
print_status "Check the dashboard for anomaly detection results"
