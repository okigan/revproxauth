#!/usr/bin/env python3
"""
Unified RADIUS authentication backend for reverse proxy forward auth using FastAPI.
Supports nginx, Traefik, and Caddy with configurable behavior.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pyrad.client import Client
from pyrad.dictionary import Dictionary

# Configuration
RADIUS_SERVER = os.getenv("RADIUS_SERVER", "radius")
RADIUS_SECRET = os.getenv("RADIUS_SECRET", "testing123")
RADIUS_PORT = int(os.getenv("RADIUS_PORT", "1812"))
RADIUS_NAS_IDENTIFIER = os.getenv("RADIUS_NAS_IDENTIFIER", "auth-backend")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))
# nginx auth_request module only accepts 2xx (auth ok) or 401/403 (auth fail)
# Traefik/Caddy forward_auth can handle 302 redirects directly
PROXY_TYPE = os.getenv("PROXY_TYPE", "generic")  # nginx | generic
PROXY_NAME = os.getenv("PROXY_NAME", "Auth")  # Display name for branding

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Initialize FastAPI app
app = FastAPI(title=f"{PROXY_NAME} RADIUS Auth Backend")

# Initialize RADIUS client
radius_dict = Dictionary("/app/dictionary")
radius_client = Client(
    server=RADIUS_SERVER,
    secret=RADIUS_SECRET.encode(),
    authport=RADIUS_PORT,
    dict=radius_dict,
)

# In-memory session store (use Redis in production)
sessions = {}


def validate_session(session_id):
    """Validate session ID and check expiration."""
    if not session_id or session_id not in sessions:
        return None

    session = sessions[session_id]
    if datetime.now() > session["expires"]:
        del sessions[session_id]
        return None

    return session["username"]


def create_session(username):
    """Create a new session for the user."""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "expires": datetime.now() + timedelta(seconds=SESSION_TIMEOUT),
    }
    return session_id


@app.get("/auth")
async def auth(request: Request):
    """
    Authentication endpoint for reverse proxy forward auth.

    nginx's auth_request module limitation:
    - Only accepts 2xx (authenticated) or 401/403 (not authenticated)
    - Cannot handle 302 redirects from subrequests
    - nginx config uses error_page 401 = @error401 to redirect

    Traefik/Caddy forward_auth:
    - Can handle 302 redirects directly from auth backend
    - More flexible and cleaner approach
    """
    session_id = request.cookies.get("session_id")
    username = validate_session(session_id)

    if username:
        logging.info(f"Authenticated request for user: {username}")
        return Response(
            content="OK",
            status_code=200,
            headers={"X-Auth-User": username},
        )

    # nginx: Return 401, let nginx config handle redirect via @error401
    if PROXY_TYPE == "nginx":
        logging.info("Unauthenticated request (nginx auth_request)")
        return Response(content="Unauthorized", status_code=401)

    # Traefik/Caddy: Return 302 redirect directly
    original_uri = request.headers.get("X-Forwarded-Uri", request.url.path)
    forwarded_host = request.headers.get(
        "X-Forwarded-Host", request.headers.get("Host", "localhost")
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")

    login_url = f"{forwarded_proto}://{forwarded_host}/login?next={original_uri}"
    logging.info(f"Unauthenticated request, redirecting to {login_url}")
    return RedirectResponse(url=login_url, status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, next: str = "/", error: str = ""):
    """Display login form."""
    # Get the host from request
    forwarded_host = request.headers.get(
        "X-Forwarded-Host", request.headers.get("Host", "localhost")
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
    base_url = f"{forwarded_proto}://{forwarded_host}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - {PROXY_NAME} RADIUS Auth</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f0f0f0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .login-box {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 300px;
            }}
            h1 {{
                margin: 0 0 20px 0;
                color: #333;
                text-align: center;
                font-size: 24px;
            }}
            .subtitle {{
                color: #666;
                font-size: 14px;
                text-align: center;
                margin-bottom: 20px;
            }}
            input {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{
                background: #0056b3;
            }}
            .error {{
                color: red;
                margin: 10px 0;
                text-align: center;
                font-size: 14px;
            }}
            .info {{
                color: #666;
                font-size: 12px;
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🔐 Login</h1>
            <div class="subtitle">{PROXY_NAME} + RADIUS Authentication</div>
            {f'<div class="error">{error}</div>' if error else ""}
            <form method="post" action="{base_url}/do-login">
                <input type="text" name="username" placeholder="Username" required autofocus>
                <input type="password" name="password" placeholder="Password" required>
                <input type="hidden" name="next" value="{next}">
                <button type="submit">Login</button>
            </form>
            <div class="info">
                Test credentials: testuser/testpass
            </div>
        </div>
    </body>
    </html>
    """
    return html


@app.post("/do-login")
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    """Handle login form submission."""
    # Get the host from request
    forwarded_host = request.headers.get(
        "X-Forwarded-Host", request.headers.get("Host", "localhost")
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
    base_url = f"{forwarded_proto}://{forwarded_host}"

    if not username or not password:
        return RedirectResponse(
            url=f"{base_url}/login?next={next}&error=Username and password required",
            status_code=303,
        )

    try:
        # Authenticate with RADIUS
        logging.info(f"Attempting RADIUS authentication for user: {username}")
        req = radius_client.CreateAuthPacket(code=1, User_Name=username.encode())
        req["User-Password"] = req.PwCrypt(password.encode())
        req["NAS-Identifier"] = RADIUS_NAS_IDENTIFIER.encode()

        # Enable Message-Authenticator for security (required by Synology RADIUS)
        req.add_message_authenticator()

        reply = radius_client.SendPacket(req)

        if reply.code == 2:  # Access-Accept
            logging.info(f"Login successful for user: {username}")
            session_id = create_session(username)

            response = RedirectResponse(
                url=next if next.startswith("/") else f"{base_url}{next}",
                status_code=303,
            )
            response.set_cookie(
                "session_id",
                session_id,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                max_age=SESSION_TIMEOUT,
            )
            return response
        else:
            logging.warning(f"Login failed for user: {username}")
            return RedirectResponse(
                url=f"{base_url}/login?next={next}&error=Invalid credentials",
                status_code=303,
            )

    except Exception as e:
        logging.error(f"Login error: {type(e).__name__}: {str(e)}")
        logging.exception("Full traceback:")
        return RedirectResponse(
            url=f"{base_url}/login?next={next}&error=Authentication service error",
            status_code=303,
        )


@app.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        username = sessions[session_id].get("username", "unknown")
        del sessions[session_id]
        logging.info(f"User logged out: {username}")

    # Get the host from request
    forwarded_host = request.headers.get(
        "X-Forwarded-Host", request.headers.get("Host", "localhost")
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
    base_url = f"{forwarded_proto}://{forwarded_host}"

    response = RedirectResponse(url=f"{base_url}/login", status_code=303)
    response.delete_cookie("session_id")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8999)
