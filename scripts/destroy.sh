#!/bin/bash
# Destroy the BGP Anomaly Detection Lab

set -e

echo "🗑️ Destroying BGP Anomaly Detection Lab..."

# Check if containerlab is installed
if ! command -v containerlab &> /dev/null; then
    echo "❌ containerlab is not installed."
    exit 1
fi

# Destroy the lab
echo "🔧 Destroying containerlab topology..."
containerlab destroy --topo topo.clab.yml

# Clean up log files (optional)
read -p "🗑️ Do you want to clean up log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up log files..."
    rm -rf logs/*
    echo "✅ Log files cleaned up."
fi

echo "✅ Lab destroyed successfully!"
