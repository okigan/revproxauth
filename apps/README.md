# Test Apps

Simple backend applications for testing the authentication stacks.

## whoami

A simple HTTP service that returns information about the request (headers, IP, etc.).  
Uses the `traefik/whoami` Docker image.

## websocket-echo

A WebSocket echo server for testing WebSocket support.  
Echoes back any message it receives.

## Running

These apps are included in the main docker-compose files. Access them through the authentication proxy.

## Manual Testing

Run standalone:

```bash
# whoami
docker run -d -p 8081:80 traefik/whoami

# Test
curl http://localhost:8081
```
