# Nginx + RADIUS Authentication Stack

This stack uses **nginx** with the `auth_request` module to provide RADIUS-based authentication.

## Architecture

```
Client → nginx → radius-auth (RADIUS validation) → upstream app
```

## How It Works

1. **nginx** receives all requests
2. For each request, nginx makes a subrequest to the **radius-auth** service (`/auth` endpoint)
3. **radius-auth** checks for valid session cookie or validates credentials against RADIUS
4. If authenticated, nginx proxies the request to the upstream application
5. If not authenticated, nginx redirects to the login page

## Features

- ✅ Mature, battle-tested reverse proxy
- ✅ High performance with minimal overhead
- ✅ `auth_request` module for authentication
- ✅ WebSocket support
- ✅ Simple configuration

## Limitations

- ⚠️ Requires separate auth backend service
- ⚠️ Less dynamic configuration (requires reload for changes)
- ⚠️ Session management in separate service

## Configuration

Edit `nginx.conf` to configure:
- Upstream services
- Authentication endpoints
- SSL/TLS settings
- Proxy headers

Edit `radius-auth/auth.py` to configure:
- RADIUS server settings
- Session timeout
- Authentication logic

## Running

From the project root:

```bash
docker-compose -f docker-compose.nginx.yml up
```

Or run just this stack:

```bash
cd apps/nginx
docker-compose up
```

## Testing

Access your application at:
- http://localhost:8080 (redirects to login if not authenticated)
- http://localhost:8080/login (login page)
