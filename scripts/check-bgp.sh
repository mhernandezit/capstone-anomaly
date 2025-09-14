#!/bin/bash
# Check BGP status across all lab devices

echo "🔍 BGP Status Check"
echo "=================="

# Function to check BGP status for a device
check_bgp() {
    local device=$1
    echo ""
    echo "📡 $device BGP Status:"
    echo "----------------------"
    docker exec clab-bgp-anomaly-lab-$device vtysh -c "show bgp summary" 2>/dev/null || echo "❌ Could not connect to $device"
}

# Check all devices
check_bgp "spine-01"
check_bgp "spine-02"
check_bgp "tor-01"
check_bgp "tor-02"
check_bgp "edge-01"
check_bgp "edge-02"
check_bgp "server-01"
check_bgp "server-02"
check_bgp "server-03"
check_bgp "server-04"

echo ""
echo "✅ BGP status check complete!"
