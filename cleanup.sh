#!/bin/bash

# Stop all running containers
echo "Stopping running containers..."
docker stop $(docker ps -aq)

# Remove all containers
echo "Removing containers..."
docker rm $(docker ps -aq)

# Remove all images
echo "Removing images..."
docker rmi $(docker images -q)

# Remove all volumes
echo "Removing volumes..."
docker volume rm $(docker volume ls -q)

# Optional: Remove all networks
# echo "Removing networks..."
# docker network rm $(docker network ls -q)

# Your Docker environment is now clean
echo "Docker environment has been cleaned up."
