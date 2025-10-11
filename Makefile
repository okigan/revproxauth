# Makefile for Synology authentication proxy Docker operations

.PHONY: all up down build logs restart clean

all: build up

# Build the Docker image
build:
	docker-compose build

# Start the service in detached mode
up:
	docker-compose up -d
# Stop and remove the service
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f
# Restart the service
restart:
	docker-compose restart

# Clean up: stop and remove containers, images, and volumes
clean:
	docker-compose down --rmi all --volumes --remove-orphans