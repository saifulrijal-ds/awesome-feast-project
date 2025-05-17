#!/bin/bash
set -e

# Function to wait for a service to be available using a timeout approach
wait_for_service() {
  local host=$1
  local port=$2
  local service=$3
  local timeout=30
  local count=0
  
  echo "Waiting for $service to be available at $host:$port..."
  
  while [ $count -lt $timeout ]; do
    # Try to connect to the host:port using /dev/tcp
    (echo > /dev/tcp/$host/$port) >/dev/null 2>&1
    result=$?
    
    if [ $result -eq 0 ]; then
      echo "$service is available!"
      return 0
    fi
    
    count=$((count+1))
    sleep 1
  done
  
  echo "Timed out waiting for $service at $host:$port"
  return 1
}

# Wait for PostgreSQL and Redis to be available
wait_for_service $POSTGRES_HOST $POSTGRES_PORT "PostgreSQL"
wait_for_service $REDIS_HOST $REDIS_PORT "Redis"

# Create a data directory if it doesn't exist
mkdir -p /feature_repo/data

# Start supervisord
echo "Starting all Feast services..."
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf