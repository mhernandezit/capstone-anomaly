#!/bin/bash
# BGP Collector for the lab environment

echo "📡 Starting BGP Collector for Lab Environment"
echo "============================================="

# Check if GoBGP is available
if ! command -v gobgp &> /dev/null; then
    echo "❌ GoBGP is not installed. Installing..."
    apk add --no-cache gobgp
fi

# Create collector configuration
cat > /tmp/gobgp.conf << EOF
[global.config]
  as = 65000
  router-id = "10.0.10.100"

[[neighbors]]
  [neighbors.config]
    neighbor-address = "10.0.10.1"
    peer-as = 65001
    [neighbors.transport.config]
      local-address = "10.0.10.2"
      [neighbors.transport.config.tcp]
        mss = 1460
        [neighbors.transport.config.tcp.auth-password]
          password = ""

[[neighbors]]
  [neighbors.config]
    neighbor-address = "10.0.10.5"
    peer-as = 65001
    [neighbors.transport.config]
      local-address = "10.0.10.6"
      [neighbors.transport.config.tcp]
        mss = 1460
        [neighbors.transport.config.tcp.auth-password]
          password = ""

[zebra]
  [zebra.config]
    enabled = true
    url = "unix:/var/run/frr/zserv.api"
    version = 6
EOF

echo "🔧 Starting GoBGP collector..."
echo "Collecting BGP updates from:"
echo "  - spine-01 (10.0.10.1)"
echo "  - spine-02 (10.0.10.5)"
echo ""

# Start GoBGP with monitoring
gobgp -f /tmp/gobgp.conf monitor global rib -j | while read line; do
    echo "$(date): $line" >> /var/log/collector.log
    echo "$line"
done
