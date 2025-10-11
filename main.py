import json
import logging
import os
import sys
from typing import Any

import httpx
from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pyrad.client import Client
from pyrad.dictionary import Dictionary

app = FastAPI(
    # root_path="/synauthproxy"
)
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure logging with simple format
# Allow LOG_LEVEL environment variable to control logging level (default: INFO)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# RADIUS config from environment
RADIUS_SERVER = os.getenv("RADIUS_SERVER")
RADIUS_SECRET = os.getenv("RADIUS_SECRET")
RADIUS_PORT = int(os.getenv("RADIUS_PORT", "1812"))
RADIUS_NAS_IDENTIFIER = os.getenv("RADIUS_NAS_IDENTIFIER", "synauthproxy")
LOGIN_DOMAIN = os.getenv("LOGIN_DOMAIN")
ADMIN_USERS = (
    os.getenv("SYNAUTHPROXY_ADMIN_USERS", "").split(",")
    if os.getenv("SYNAUTHPROXY_ADMIN_USERS")
    else []
)

# Validate required environment variables
missing_vars = []
if not RADIUS_SERVER:
    missing_vars.append("RADIUS_SERVER")
if not RADIUS_SECRET:
    missing_vars.append("RADIUS_SECRET")

if missing_vars:
    error_msg = f"""
================================================================================
CONFIGURATION ERROR: Missing Required Environment Variables
================================================================================

The following required environment variables are not set:
  {", ".join(missing_vars)}

Please configure these variables in your container environment:

Required Variables:
  - RADIUS_SERVER: IP address of your RADIUS server (e.g., 192.168.1.10)
  - RADIUS_SECRET: RADIUS shared secret

For setup instructions, see:
  https://github.com/okigan/synauthproxy#readme

Container cannot start without these variables.
================================================================================
"""
    print(error_msg, file=sys.stderr, flush=True)
    logging.error(
        "Configuration error: Missing required environment variables: %s",
        ", ".join(missing_vars),
    )
    sys.exit(1)

# Print startup information
git_commit = "unknown"
try:
    with open("/app/git_commit.txt") as f:
        git_commit = f.read().strip()
except Exception:
    pass

startup_msg = f"""
================================================================================
SynAuthProxy Starting
================================================================================
Git Commit:    {git_commit}
RADIUS Server: {RADIUS_SERVER}:{RADIUS_PORT}
NAS ID:        {RADIUS_NAS_IDENTIFIER}
Login Domain:  {LOGIN_DOMAIN if LOGIN_DOMAIN else "(not set)"}
Admin Users:   {", ".join(ADMIN_USERS) if ADMIN_USERS else "(all authenticated users)"}
================================================================================
"""
print(startup_msg, flush=True)

# Initialize RADIUS client and dictionary
radius_dict = Dictionary("/app/dictionary")
client = Client(
    server=RADIUS_SERVER,
    secret=RADIUS_SECRET.encode(),
    authport=RADIUS_PORT,
    dict=radius_dict,
)

# Load config from /app/config/synauthproxy.json


def load_config() -> dict[str, Any]:
    try:
        with open("/app/config/synauthproxy.json") as f:
            config = json.load(f)
            # Validate version
            if config.get("version") != "1.0":
                logging.warning(f"Unknown config version: {config.get('version')}")
            return config
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return {"version": "1.0", "mappings": []}


def load_mappings():
    config = load_config()
    return config.get("mappings", [])


def save_mappings(mappings):
    try:
        config = {"version": "1.0", "mappings": mappings}
        with open("/app/config/synauthproxy.json", "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save mappings: {str(e)}") from None


class AuthRequestModel(BaseModel):
    username: str
    password: str


class MappingModel(BaseModel):
    match_url: str  # Combined host/path like "app.mysynology.me/path"
    http_dest: str
    flags: list  # Array of flags: "strip_path", "disabled", etc.


def is_admin_user(username: str) -> bool:
    """Check if the given username is in the admin users list."""
    if not ADMIN_USERS:
        # If no admin users configured, all authenticated users can modify mappings
        return True
    return username.strip().lower() in [u.strip().lower() for u in ADMIN_USERS]


def get_login_url(request: Request, next_path: str):
    domain = LOGIN_DOMAIN if LOGIN_DOMAIN else request.headers.get("host", "localhost")
    # Check if domain already includes protocol
    if domain and (domain.startswith("http://") or domain.startswith("https://")):
        return f"{domain}/login?next={next_path}"
    else:
        # Use http for local testing (change to https in production)
        return f"http://{domain}/login?next={next_path}"


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next, "unrestricted_access": not ADMIN_USERS},
    )


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    try:
        logging.info(f"Login attempt for user: {username}")
        logging.debug(f"RADIUS Server: {RADIUS_SERVER}:{RADIUS_PORT}")

        # Create RADIUS auth request (code 1 = Access-Request)
        logging.debug("Creating RADIUS auth packet")
        req = client.CreateAuthPacket(code=1, User_Name=username.encode())

        # Set password - pyrad will encrypt it properly
        req["User-Password"] = req.PwCrypt(password.encode())

        # Add NAS-Identifier attribute
        req["NAS-Identifier"] = RADIUS_NAS_IDENTIFIER.encode()

        # Send request and get response
        logging.debug(f"Sending RADIUS packet to {RADIUS_SERVER}:{RADIUS_PORT}")
        reply = client.SendPacket(req)
        logging.debug(f"Received RADIUS reply with code: {reply.code}")

        if reply.code == 2:  # Access-Accept
            response = RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)
            # Set secure=False for local HTTP testing (change to True in production with HTTPS)
            response.set_cookie(
                key="auth",
                value="authenticated",
                httponly=True,
                secure=False,
                max_age=3600,
            )
            response.set_cookie(
                key="username",
                value=username,
                httponly=True,
                secure=False,
                max_age=3600,
            )
            return response
        else:  # Access-Reject
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "next": next,
                    "error": "Invalid username or password",
                    "unrestricted_access": not ADMIN_USERS,
                },
            )

    except Exception as e:
        logging.error(f"Login error for user '{username}': {type(e).__name__}: {str(e)}")
        logging.error(f"RADIUS connection details - Server: {RADIUS_SERVER}, Port: {RADIUS_PORT}")
        logging.exception("Full traceback:")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "next": next,
                "error": str(e),
                "unrestricted_access": not ADMIN_USERS,
            },
        )


@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="auth")
    response.delete_cookie(key="username")
    return response


def get_username_from_cookie(request: Request) -> str:
    """Extract username from cookie."""
    cookies = request.headers.get("cookie", "")
    for cookie in cookies.split(";"):
        if "username=" in cookie:
            return cookie.split("username=")[1].strip()
    return ""


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.svg", media_type="image/svg+xml")


@app.get("/synauthproxy", response_class=HTMLResponse)
async def mappings_page(request: Request):
    if "auth=authenticated" not in request.headers.get("cookie", ""):
        login_url = get_login_url(request, "/synauthproxy")
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

    username = get_username_from_cookie(request)
    is_admin = is_admin_user(username)

    return templates.TemplateResponse(
        "mappings.html",
        {
            "request": request,
            "mappings": load_mappings(),
            "is_admin": is_admin,
            "username": username,
            "unrestricted_access": not ADMIN_USERS,
        },
    )


@app.post("/synauthproxy/add")
async def add_mapping(
    request: Request,
    match_url: str = Form(...),
    http_dest: str = Form(...),
    flags: str = Form(""),
):
    if "auth=authenticated" not in request.headers.get("cookie", ""):
        raise HTTPException(status_code=401, detail="Authentication required")

    username = get_username_from_cookie(request)
    if not is_admin_user(username):
        raise HTTPException(status_code=403, detail="Admin access required")

    mappings = load_mappings()
    # Parse flags from comma-separated string
    flags_list = [f.strip() for f in flags.split(",") if f.strip()]
    new_mapping: dict[str, Any] = {
        "match_url": match_url,
        "http_dest": http_dest,
        "flags": flags_list,
    }
    mappings.append(new_mapping)
    save_mappings(mappings)
    return RedirectResponse(url="/synauthproxy", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/synauthproxy/update/{index}")
async def update_mapping(
    request: Request,
    index: int,
    match_url: str = Form(...),
    http_dest: str = Form(...),
    flags: str = Form(""),
):
    if "auth=authenticated" not in request.headers.get("cookie", ""):
        raise HTTPException(status_code=401, detail="Authentication required")

    username = get_username_from_cookie(request)
    if not is_admin_user(username):
        raise HTTPException(status_code=403, detail="Admin access required")

    mappings = load_mappings()
    if 0 <= index < len(mappings):
        # Parse flags from comma-separated string
        flags_list = [f.strip() for f in flags.split(",") if f.strip()]
        mappings[index] = {
            "match_url": match_url,
            "http_dest": http_dest,
            "flags": flags_list,
        }
        save_mappings(mappings)
    return RedirectResponse(url="/synauthproxy", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/synauthproxy/move/{index}")
async def move_mapping(request: Request, index: int, direction: int = Form(...)):
    if "auth=authenticated" not in request.headers.get("cookie", ""):
        raise HTTPException(status_code=401, detail="Authentication required")

    username = get_username_from_cookie(request)
    if not is_admin_user(username):
        raise HTTPException(status_code=403, detail="Admin access required")

    mappings = load_mappings()
    if 0 <= index < len(mappings):
        new_index = index + direction
        if 0 <= new_index < len(mappings):
            # Swap the mappings
            mappings[index], mappings[new_index] = mappings[new_index], mappings[index]
            save_mappings(mappings)
    return RedirectResponse(url="/synauthproxy", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/synauthproxy/delete/{index}")
async def delete_mapping(request: Request, index: int):
    if "auth=authenticated" not in request.headers.get("cookie", ""):
        raise HTTPException(status_code=401, detail="Authentication required")

    username = get_username_from_cookie(request)
    if not is_admin_user(username):
        raise HTTPException(status_code=403, detail="Admin access required")

    mappings = load_mappings()
    if 0 <= index < len(mappings):
        mappings.pop(index)
        save_mappings(mappings)
    return RedirectResponse(url="/synauthproxy", status_code=status.HTTP_303_SEE_OTHER)


# HTTP proxy handler with WebSocket upgrade support
async def proxy_request(request: Request, dest_url: str, path: str):
    # Check if this is a WebSocket upgrade request
    upgrade_header = request.headers.get("upgrade", "").lower()
    connection_header = request.headers.get("connection", "").lower()

    if upgrade_header == "websocket" and "upgrade" in connection_header:
        # Handle WebSocket upgrade
        return await handle_websocket_upgrade(request, dest_url, path)

    # Regular HTTP proxy
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "connection", "upgrade")
    }
    headers["Host"] = dest_url.split("://")[1].split("/")[0]

    full_url = dest_url.rstrip("/") + "/" + path.lstrip("/")
    try:
        logging.debug(f"Proxying {request.method} request to: {full_url}")

        # Create a client that will stay open during streaming
        client = httpx.AsyncClient(timeout=300.0)

        # Prepare request based on method
        if request.method == "GET":
            req = client.build_request(
                "GET", full_url, headers=headers, params=request.query_params
            )
        elif request.method == "POST":
            body = await request.body()
            req = client.build_request(
                "POST",
                full_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
        else:
            await client.aclose()
            raise HTTPException(status_code=405, detail="Method not allowed")

        # Send request with streaming enabled
        resp = await client.send(req, stream=True)

        # Filter out headers that can cause decoding issues
        response_headers = {
            k: v
            for k, v in resp.headers.items()
            if k.lower()
            not in (
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            )
        }

        # Stream the response - keep client and response alive until streaming is done
        async def generate():
            try:
                async for chunk in resp.aiter_bytes(chunk_size=8192):
                    yield chunk
            finally:
                await resp.aclose()
                await client.aclose()

        return StreamingResponse(
            generate(),
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type"),
        )
    except Exception as e:
        logging.error(f"Proxy error for {request.method} {full_url}: {type(e).__name__}: {str(e)}")
        logging.exception("Full proxy error traceback:")
        raise HTTPException(status_code=500, detail=str(e)) from e


# WebSocket upgrade handler using httpx for upgrade
async def handle_websocket_upgrade(request: Request, dest_url: str, path: str):
    import asyncio

    from starlette.responses import Response
    from starlette.types import Receive, Scope, Send

    # Build WebSocket URL from HTTP URL
    full_url = dest_url.rstrip("/") + "/" + path.lstrip("/")
    ws_url = full_url.replace("http://", "ws://").replace("https://", "wss://")
    logging.info(f"WebSocket upgrade request to: {ws_url}")

    # Forward all WebSocket-related headers
    headers = {}
    for k, v in request.headers.items():
        if k.lower() not in ("host",):
            headers[k] = v
    headers["Host"] = dest_url.split("://")[1].split("/")[0]

    async def websocket_proxy(scope: Scope, receive: Receive, send: Send):
        import websockets

        try:
            # Connect to backend WebSocket
            async with websockets.connect(ws_url, extra_headers=headers) as backend_ws:
                # Accept the client connection
                await send(
                    {
                        "type": "websocket.accept",
                    }
                )

                # Create tasks for bidirectional forwarding
                async def client_to_backend():
                    try:
                        while True:
                            message = await receive()
                            if message["type"] == "websocket.disconnect":
                                break
                            elif message["type"] == "websocket.receive":
                                if "text" in message:
                                    await backend_ws.send(message["text"])
                                elif "bytes" in message:
                                    await backend_ws.send(message["bytes"])
                    except Exception as e:
                        logging.error(f"Client to backend error: {str(e)}")

                async def backend_to_client():
                    try:
                        async for message in backend_ws:
                            if isinstance(message, str):
                                await send(
                                    {
                                        "type": "websocket.send",
                                        "text": message,
                                    }
                                )
                            else:
                                await send(
                                    {
                                        "type": "websocket.send",
                                        "bytes": message,
                                    }
                                )
                    except Exception as e:
                        logging.error(f"Backend to client error: {str(e)}")

                # Run both tasks concurrently
                await asyncio.gather(
                    client_to_backend(), backend_to_client(), return_exceptions=True
                )

        except Exception as e:
            logging.error(f"WebSocket upgrade error for {ws_url}: {type(e).__name__}: {str(e)}")
            logging.exception("Full WebSocket error traceback:")
            await send({"type": "websocket.close", "code": 1011, "reason": str(e)})

    # Return a custom response that handles WebSocket at ASGI level
    class WebSocketProxyResponse(Response):
        def __init__(self):
            super().__init__()

        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            await websocket_proxy(scope, receive, send)

    return WebSocketProxyResponse()


# Catch-all route for proxying (handles both HTTP and WebSocket upgrades)
@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def handle_request(request: Request, full_path: str = ""):
    host_header = request.headers.get("host", "").lower()
    # Strip port number from host header for matching
    host_without_port = host_header.split(":")[0] if ":" in host_header else host_header
    request_path = f"/{full_path}".rstrip("/") if full_path else "/"
    logging.debug(f"Handling request: {request.method} {host_without_port}{request_path}")

    # Check mappings (reload on each request to pick up changes)
    for mapping in load_mappings():
        flags = mapping.get("flags", [])

        # Skip disabled mappings
        if "disabled" in flags:
            continue

        match_url = mapping.get("match_url", "")
        http_dest = mapping.get("http_dest", "")
        strip_path = "strip_path" in flags

        if not http_dest or not match_url:
            continue

        # Parse match_url into host and path components
        # Format can be: "host.com" or "host.com/path" or "/path"
        if "/" in match_url:
            parts = match_url.split("/", 1)
            host = parts[0] if parts[0] else ""
            path = parts[1] if len(parts) > 1 else ""
        else:
            host = match_url
            path = ""

        # Match host and path
        host_matches = (not host) or (host == host_without_port)
        path_matches = (not path) or request_path.startswith(f"/{path}")

        if host_matches and path_matches:
            # Check authentication
            if "auth=authenticated" not in request.headers.get("cookie", ""):
                # Use full_path (without root_path prefix) for the next parameter
                next_url = f"/{full_path}" if full_path else "/"
                login_url = get_login_url(request, next_url)
                return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

            # Determine target path
            target_path = f"/{full_path}" if full_path else "/"

            # Strip the path portion if configured
            if strip_path and path:
                prefix_to_strip = f"/{path}"
                if target_path.startswith(prefix_to_strip):
                    target_path = target_path[len(prefix_to_strip) :] or "/"

            # Proxy HTTP or WebSocket upgrade - pass the modified path
            return await proxy_request(request, http_dest, target_path)

    raise HTTPException(status_code=404, detail="App not found")
