#!/bin/bash
# Failure injection scripts for BGP Anomaly Detection Lab

set -e

echo "💥 BGP Anomaly Detection Lab - Failure Injection"
echo "================================================"

# Function to show available failure scenarios
show_scenarios() {
    echo ""
    echo "Available failure scenarios:"
    echo "1.  Link failure (spine-01 to tor-01)"
    echo "2.  Link failure (spine-02 to tor-02)"
    echo "3.  Router crash (spine-01)"
    echo "4.  Router crash (tor-01)"
    echo "5.  Router crash (edge-01)"
    echo "6.  Server crash (server-01)"
    echo "7.  BGP session reset (spine-01 to tor-01)"
    echo "8.  BGP session reset (edge-01 to server-01)"
    echo "9.  Interface down (spine-01 eth2)"
    echo "10. Interface down (tor-01 eth1)"
    echo "11. Restore all failures"
    echo "12. Show current status"
    echo "0.  Exit"
}

# Function to inject link failure
inject_link_failure() {
    local from=$1
    local to=$2
    local interface=$3
    
    echo "💥 Injecting link failure: $from -> $to ($interface)"
    docker exec clab-bgp-anomaly-lab-$from ip link set $interface down
    echo "✅ Link failure injected. Interface $interface on $from is down."
}

# Function to inject router crash
inject_router_crash() {
    local router=$1
    
    echo "💥 Injecting router crash: $router"
    docker stop clab-bgp-anomaly-lab-$router
    echo "✅ Router $router crashed."
}

# Function to inject BGP session reset
inject_bgp_reset() {
    local router=$1
    local neighbor=$2
    
    echo "💥 Injecting BGP session reset: $router -> $neighbor"
    docker exec clab-bgp-anomaly-lab-$router vtysh -c "clear bgp $neighbor"
    echo "✅ BGP session reset injected."
}

# Function to inject interface down
inject_interface_down() {
    local router=$1
    local interface=$2
    
    echo "💥 Injecting interface down: $router $interface"
    docker exec clab-bgp-anomaly-lab-$router ip link set $interface down
    echo "✅ Interface $interface on $router is down."
}

# Function to restore all failures
restore_all() {
    echo "🔧 Restoring all failures..."
    
    # Restart all containers
    docker start clab-bgp-anomaly-lab-spine-01 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-spine-02 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-tor-01 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-tor-02 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-edge-01 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-edge-02 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-server-01 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-server-02 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-server-03 2>/dev/null || true
    docker start clab-bgp-anomaly-lab-server-04 2>/dev/null || true
    
    # Wait for containers to start
    sleep 10
    
    # Bring up all interfaces
    docker exec clab-bgp-anomaly-lab-spine-01 ip link set eth2 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-spine-02 ip link set eth3 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-tor-01 ip link set eth1 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-tor-02 ip link set eth2 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-edge-01 ip link set eth1 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-edge-02 ip link set eth2 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-server-01 ip link set eth1 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-server-02 ip link set eth1 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-server-03 ip link set eth1 up 2>/dev/null || true
    docker exec clab-bgp-anomaly-lab-server-04 ip link set eth1 up 2>/dev/null || true
    
    echo "✅ All failures restored."
}

# Function to show current status
show_status() {
    echo "📊 Current Lab Status:"
    echo "====================="
    
    # Check container status
    echo "Container Status:"
    docker ps --filter "name=clab-bgp-anomaly-lab" --format "table {{.Names}}\t{{.Status}}"
    
    echo ""
    echo "Interface Status:"
    echo "spine-01 eth2 (to tor-01):"
    docker exec clab-bgp-anomaly-lab-spine-01 ip link show eth2 2>/dev/null || echo "  ❌ Container not running"
    
    echo "spine-02 eth3 (to tor-02):"
    docker exec clab-bgp-anomaly-lab-spine-02 ip link show eth3 2>/dev/null || echo "  ❌ Container not running"
    
    echo "tor-01 eth1 (to spine-01):"
    docker exec clab-bgp-anomaly-lab-tor-01 ip link show eth1 2>/dev/null || echo "  ❌ Container not running"
    
    echo "tor-02 eth2 (to spine-02):"
    docker exec clab-bgp-anomaly-lab-tor-02 ip link show eth2 2>/dev/null || echo "  ❌ Container not running"
}

# Main menu
while true; do
    show_scenarios
    echo ""
    read -p "Select scenario (0-12): " choice
    
    case $choice in
        1)
            inject_link_failure "spine-01" "tor-01" "eth2"
            ;;
        2)
            inject_link_failure "spine-02" "tor-02" "eth3"
            ;;
        3)
            inject_router_crash "spine-01"
            ;;
        4)
            inject_router_crash "tor-01"
            ;;
        5)
            inject_router_crash "edge-01"
            ;;
        6)
            inject_router_crash "server-01"
            ;;
        7)
            inject_bgp_reset "spine-01" "10.0.2.2"
            ;;
        8)
            inject_bgp_reset "edge-01" "10.0.4.2"
            ;;
        9)
            inject_interface_down "spine-01" "eth2"
            ;;
        10)
            inject_interface_down "tor-01" "eth1"
            ;;
        11)
            restore_all
            ;;
        12)
            show_status
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please select 0-12."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
