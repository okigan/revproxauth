# Traefik + RADIUS Authentication Stack

This stack uses **Traefik** with ForwardAuth middleware to provide RADIUS-based authentication.

## Architecture

```
Client → Traefik → ForwardAuth Middleware (RADIUS validation) → upstream app
```

## How It Works

1. Client makes request to Traefik
2. For protected routes, Traefik forwards authentication to the **py-radius-auth** service
3. **py-radius-auth** validates session or RADIUS credentials
4. If authenticated, request proceeds to upstream
5. If not authenticated, py-radius-auth returns a redirect to the login page

## Features

- ✅ Modern, cloud-native reverse proxy
- ✅ Dynamic configuration (no restarts needed)
- ✅ Built-in Let's Encrypt support
- ✅ ForwardAuth middleware for authentication
- ✅ Excellent WebSocket support
- ✅ Automatic service discovery

## Limitations

- ⚠️ Requires separate auth backend service
- ⚠️ More complex initial configuration
- ⚠️ Higher resource usage than nginx

## Configuration

Edit `traefik.yml` for static configuration:
- Entry points (HTTP/HTTPS ports)
- API/Dashboard settings
- Certificate resolvers

Edit `dynamic/radius-auth.yml` for dynamic configuration:
- Routers and services
- Middleware configuration
- ForwardAuth settings

Edit `radius-auth/auth.py` to configure:
- RADIUS server settings
- Session timeout
- Authentication logic

## Running

From the project root:

```bash
docker-compose -f docker-compose.traefik.yml up
```

Or run just this stack:

```bash
cd apps/traefik
docker-compose up
```

## Testing

Access your application at:
- http://localhost:8080 (redirects to login if not authenticated)
- http://localhost:8080/login (login page)
- http://localhost:8080/dashboard/ (Traefik dashboard)
