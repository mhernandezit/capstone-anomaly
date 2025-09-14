#!/bin/bash
# Test BMP Collector

echo "🧪 Testing BMP Collector"
echo "======================="

# Check if BMP collector container is running
if docker ps --format "table {{.Names}}" | grep -q "bmp-collector"; then
    echo "✅ BMP collector container is running"
else
    echo "❌ BMP collector container is not running"
    echo "Run: ./scripts/deploy.sh to start the lab"
    exit 1
fi

# Check BMP collector logs
echo ""
echo "📋 BMP Collector Logs (last 20 lines):"
echo "--------------------------------------"
docker logs --tail 20 clab-bgp-anomaly-lab-bmp-collector

# Check NATS connection
echo ""
echo "🔌 Testing NATS connection:"
echo "---------------------------"
if docker exec clab-bgp-anomaly-lab-bmp-collector nc -z nats 4222; then
    echo "✅ NATS connection successful"
else
    echo "❌ NATS connection failed"
fi

# Check BMP port
echo ""
echo "🌐 Testing BMP port:"
echo "--------------------"
if docker exec clab-bgp-anomaly-lab-bmp-collector nc -z localhost 1790; then
    echo "✅ BMP port 1790 is listening"
else
    echo "❌ BMP port 1790 is not listening"
fi

echo ""
echo "✅ BMP collector test complete!"
