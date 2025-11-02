#!/bin/bash
# Reconnect forge-face-detection to ix-forge_default network
# Run this after TrueNAS restarts containers

echo "Connecting forge-face-detection to Forge network..."
docker network connect ix-forge_default ix-forge-face-detection-forge-face-detection-1 2>/dev/null || echo "Already connected or error occurred"

echo "Testing connection..."
docker exec ix-forge-forge-1 wget -qO- http://ix-forge-face-detection-forge-face-detection-1:5000/health

if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
else
    echo "❌ Connection failed!"
fi
