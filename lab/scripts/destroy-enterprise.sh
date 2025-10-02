#!/bin/bash
# Destroy Enterprise BGP Anomaly Detection Lab

set -e

echo "🗑️ Destroying Enterprise BGP Anomaly Detection Lab..."

# Check if containerlab is installed
if ! command -v containerlab &> /dev/null; then
    echo "❌ containerlab is not installed."
    exit 1
fi

# Destroy the lab
echo "🔧 Destroying enterprise containerlab topology..."
cd /mnt/c/Users/PC/Documents/GitHub/capstone-anomaly/lab
containerlab destroy --topo topo-enterprise.clab.yml

# Clean up any remaining containers
echo "🧹 Cleaning up remaining containers..."
docker container prune -f

# Clean up networks
echo "🌐 Cleaning up networks..."
docker network prune -f

# Show system resources after cleanup
echo "💻 System Resources After Cleanup:"
echo "Memory usage:"
free -h
echo ""
echo "Docker container count:"
docker ps --format "table {{.Names}}\t{{.Status}}" | wc -l
echo ""
echo "Docker system usage:"
docker system df

echo "✅ Enterprise lab destroyed successfully!"
echo ""
echo "📋 Cleanup completed:"
echo "- All containers removed"
echo "- Networks cleaned up"
echo "- System resources freed"
