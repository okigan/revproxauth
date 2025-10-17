#!/usr/bin/env python3
"""
Simple RADIUS authentication backend for Traefik ForwardAuth middleware using FastAPI.
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
RADIUS_NAS_IDENTIFIER = os.getenv("RADIUS_NAS_IDENTIFIER", "traefik-auth")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Initialize FastAPI app
app = FastAPI(title="Traefik RADIUS Auth Backend")

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
    Authentication endpoint for Traefik ForwardAuth.
    Returns 200 if authenticated, 302 redirect if not.
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

    # Get original URI and host from Traefik headers
    original_uri = request.headers.get("X-Forwarded-Uri", "/")
    forwarded_host = request.headers.get(
        "X-Forwarded-Host", request.headers.get("Host", "localhost")
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")

    logging.info(f"Unauthenticated request, redirecting to login (next={original_uri})")

    # Redirect to login with next parameter using the original host
    redirect_url = f"{forwarded_proto}://{forwarded_host}/login?next={original_uri}"
    return RedirectResponse(
        url=redirect_url,
        status_code=302,
    )


@app.get("/login", response_class=HTMLResponse)
async def login(next: str = "/", error: str = ""):
    """Display login form."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Traefik RADIUS Auth</title>
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
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 300px;
            }}
            h1 {{ margin: 0 0 20px 0; font-size: 24px; color: #333; }}
            input {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                padding: 10px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{ background: #0056b3; }}
            .error {{ color: red; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🔐 Login</h1>
            <p style="color: #666; margin-bottom: 20px;">Traefik + RADIUS Authentication</p>
            {"<div class='error'>" + error + "</div>" if error else ""}
            <form method="POST" action="/do-login">
                <input type="hidden" name="next" value="{next}">
                <input type="text" name="username" placeholder="Username" required autofocus>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/do-login")
async def do_login(
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    """Handle login form submission."""
    if not username or not password:
        return RedirectResponse(
            url=f"/login?next={next}&error=Username and password required",
            status_code=303,
        )

    try:
        # Authenticate with RADIUS
        logging.info(f"Attempting RADIUS authentication for user: {username}")
        req = radius_client.CreateAuthPacket(code=1, User_Name=username.encode())
        req["User-Password"] = req.PwCrypt(password.encode())
        req["NAS-Identifier"] = RADIUS_NAS_IDENTIFIER.encode()

        reply = radius_client.SendPacket(req)

        if reply.code == 2:  # Access-Accept
            logging.info(f"Login successful for user: {username}")
            session_id = create_session(username)

            response = RedirectResponse(url=next, status_code=303)
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
                url=f"/login?next={next}&error=Invalid credentials",
                status_code=303,
            )

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return RedirectResponse(
            url=f"/login?next={next}&error=Authentication service error",
            status_code=303,
        )


@app.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response
