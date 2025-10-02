#!/bin/bash
# Deploy Enterprise-Scale BGP Anomaly Detection Lab

set -e

echo "🚀 Deploying Enterprise BGP Anomaly Detection Lab..."

# Check if containerlab is installed
if ! command -v containerlab &> /dev/null; then
    echo "❌ containerlab is not installed. Please install it first:"
    echo "   https://containerlab.dev/install/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Generate configurations
echo "📝 Generating enterprise configurations..."
cd /mnt/c/Users/PC/Documents/GitHub/capstone-anomaly/lab
python3 scripts/generate-enterprise-configs.py

# Create log directories for all devices
echo "📁 Creating log directories..."
mkdir -p logs/{core-01,core-02,core-03,core-04,dist-01,dist-02,dist-03,dist-04,dist-05,dist-06,dist-07,dist-08,access-01,access-02,access-03,access-04,access-05,access-06,access-07,access-08,access-09,access-10,access-11,access-12,access-13,access-14,access-15,access-16,access-17,access-18,access-19,access-20,edge-01,edge-02,edge-03,edge-04,server-01,server-02,server-03,server-04,server-05,server-06,server-07,server-08,server-09,server-10,collector,fluent-bit,nats}

# Deploy the enterprise lab
echo "🔧 Deploying enterprise containerlab topology..."
containerlab deploy --topo topo-enterprise.clab.yml

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 60

# Check container status
echo "📊 Enterprise Lab Status:"
containerlab inspect --topo topo-enterprise.clab.yml

# Configure BGP sessions
echo "🔧 Configuring BGP sessions..."

# Configure core routers
for i in {1..4}; do
    echo "Configuring core-0$i BGP..."
    docker exec clab-bgp-enterprise-lab-core-0$i vtysh -c "configure terminal" -c "router bgp 65000" -c "address-family ipv4 unicast" -c "exit-address-family" -c "exit"
done

# Configure distribution switches
for i in {1..8}; do
    echo "Configuring dist-0$i BGP..."
    docker exec clab-bgp-enterprise-lab-dist-0$i vtysh -c "configure terminal" -c "router bgp 65100" -c "address-family ipv4 unicast" -c "exit-address-family" -c "exit"
done

# Configure access switches (first 10)
for i in {1..10}; do
    echo "Configuring access-0$i BGP..."
    docker exec clab-bgp-enterprise-lab-access-0$i vtysh -c "configure terminal" -c "router bgp 65200" -c "address-family ipv4 unicast" -c "exit-address-family" -c "exit"
done

# Configure edge routers
for i in {1..4}; do
    echo "Configuring edge-0$i BGP..."
    docker exec clab-bgp-enterprise-lab-edge-0$i vtysh -c "configure terminal" -c "router bgp 65300" -c "address-family ipv4 unicast" -c "exit-address-family" -c "exit"
done

# Configure servers (first 10)
for i in {1..10}; do
    echo "Configuring server-0$i BGP..."
    docker exec clab-bgp-enterprise-lab-server-0$i vtysh -c "configure terminal" -c "router bgp 65400" -c "address-family ipv4 unicast" -c "exit-address-family" -c "exit"
done

# Wait for BGP sessions to establish
echo "⏳ Waiting for BGP sessions to establish..."
sleep 30

# Show BGP status for core routers
echo "🔍 Core Router BGP Status:"
for i in {1..4}; do
    echo "Core-0$i BGP neighbors:"
    docker exec clab-bgp-enterprise-lab-core-0$i vtysh -c "show bgp summary" | head -10
    echo "---"
done

# Check system resources
echo "💻 System Resource Usage:"
echo "Memory usage:"
free -h
echo ""
echo "Docker container count:"
docker ps --format "table {{.Names}}\t{{.Status}}" | wc -l
echo ""
echo "Total containers:"
docker ps --format "table {{.Names}}" | tail -n +2

echo "✅ Enterprise lab deployed successfully!"
echo ""
echo "📋 Lab Statistics:"
echo "- Core Routers: 4"
echo "- Distribution Switches: 8"
echo "- Access Switches: 20"
echo "- Edge Routers: 4"
echo "- Servers: 10"
echo "- Total Devices: 46+"
echo ""
echo "📋 Next steps:"
echo "1. Check BGP status: docker exec clab-bgp-enterprise-lab-core-01 vtysh -c 'show bgp summary'"
echo "2. Monitor logs: tail -f logs/core-01/frr.log"
echo "3. Start ML pipeline: cd ../src && python run_enhanced_pipeline.py"
echo "4. Access dashboard: http://localhost:8501"
echo "5. Destroy lab: ./scripts/destroy-enterprise.sh"
