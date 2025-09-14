#!/bin/bash
# Deploy the BGP Anomaly Detection Lab

set -e

echo "🚀 Deploying BGP Anomaly Detection Lab..."

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

# Create log directories
echo "📁 Creating log directories..."
mkdir -p logs/{spine-01,spine-02,tor-01,tor-02,edge-01,edge-02,server-01,server-02,server-03,server-04,collector,fluent-bit}

# Deploy the lab
echo "🔧 Deploying containerlab topology..."
containerlab deploy --topo topo.clab.yml

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 30

# Check container status
echo "📊 Lab Status:"
containerlab inspect --topo topo.clab.yml

# Show BGP status
echo "🔍 BGP Status:"
echo "Spine-01 BGP neighbors:"
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"

echo "Spine-02 BGP neighbors:"
docker exec clab-bgp-anomaly-lab-spine-02 vtysh -c "show bgp summary"

echo "✅ Lab deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Check BGP status: ./scripts/check-bgp.sh"
echo "2. Inject failures: ./scripts/inject-failures.sh"
echo "3. Monitor logs: ./scripts/monitor-logs.sh"
echo "4. Connect your collector to spine-01:10.0.10.1"
echo "5. Destroy lab: ./scripts/destroy.sh"
