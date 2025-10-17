# SynAuthProxy Stack

This is the **original SynAuthProxy solution** - a Python FastAPI application that provides RADIUS-based authentication with a beautiful management UI.

## Features

- ✅ All-in-one solution (proxy + auth + management UI)
- ✅ Beautiful web UI for managing mappings
- ✅ Role-based access control
- ✅ WebSocket support with automatic upgrades
- ✅ Path stripping and URL rewriting
- ✅ User/group-based access control per mapping
- ✅ Inline editing with auto-save
- ✅ Real-time metrics and monitoring
- ✅ Server-Sent Events (SSE) support

## Architecture

```
Client → SynAuthProxy → RADIUS → Backend App
         (FastAPI)
```

All functionality is in a single service:
- HTTP/WebSocket reverse proxy
- RADIUS authentication
- Session management
- Mapping management UI
- Metrics dashboard

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RADIUS_SERVER` | ✅ Yes | - | RADIUS server IP/hostname |
| `RADIUS_SECRET` | ✅ Yes | - | RADIUS shared secret |
| `RADIUS_PORT` | No | `1812` | RADIUS server port |
| `RADIUS_NAS_IDENTIFIER` | No | `synauthproxy` | NAS identifier |
| `LOGIN_DOMAIN` | No | - | Domain for login redirects |
| `SYNAUTHPROXY_ADMIN_USERS` | No | - | Comma-separated admin usernames |

### Mappings Configuration

Edit `config/synauthproxy.json` or use the web UI at `/synauthproxy`:

```json
{
  "version": "1.0",
  "mappings": [
    {
      "match_url": "app.example.com",
      "http_dest": "http://backend:8080",
      "flags": [],
      "allowed_users": ["alice", "bob"],
      "allowed_groups": ["admins"]
    }
  ]
}
```

**Available Flags:**
- `strip_path` - Remove path prefix before forwarding
- `disabled` - Temporarily disable this mapping

## Running

From the project root:

```bash
docker-compose -f docker-compose.synauthproxy.yml up
```

Or run just this stack (with external RADIUS):

```bash
cd apps/synauthproxy
docker build -t synauthproxy .
docker run -p 9000:9000 \
  -e RADIUS_SERVER=your-radius-server \
  -e RADIUS_SECRET=your-secret \
  synauthproxy
```

## Access

- **Main proxy:** http://localhost:9000
- **Management UI:** http://localhost:9000/synauthproxy
- **Metrics:** http://localhost:9000/synauthproxy/metrics
- **Login:** http://localhost:9000/login

## Development

```bash
# Install dependencies
uv sync

# Run locally
uvicorn main:app --reload --port 9000

# Run tests
make lint
```

## Management UI Features

### Mappings Management
- ✏️ Inline editing with auto-save
- 🔼🔽 Reorder mappings (priority matters!)
- ✅ Enable/disable toggles
- 🗑️ Delete mappings
- ➕ Add new mappings

### Metrics Dashboard
- 📊 Requests per mapping/user
- 📈 Bytes sent/received
- ⏰ First/last access times
- 👥 Active users count

## Security

- **Authentication:** RADIUS-based with session cookies
- **Admin Access:** Configurable via `SYNAUTHPROXY_ADMIN_USERS`
- **Authorization:** Per-mapping user/group restrictions via JWT tokens
- **Sessions:** Stateless JWT with expiration

## Use Cases

Perfect for:
- Self-hosted applications on Synology NAS
- Home lab environments
- Small-scale deployments
- Scenarios requiring dynamic configuration
- WebSocket-heavy applications
