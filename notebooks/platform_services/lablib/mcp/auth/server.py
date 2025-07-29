#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP server with Auth0 authentication support.

This script demonstrates how to set up a FastMCP server with OAuth authentication
via Auth0, using streamable HTTP transport. It includes token verification and
protected endpoints that require authentication.
"""

import os
import sys
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse
import uvicorn
import jwt
from jwt import PyJWKClient
import httpx

# Import your custom modules (adjust path as needed)
try:
    from notebooks.platform_services.lablib.mcp.definitions import (
        register_tools,
        register_resources,
        register_prompts
    )
except ImportError:
    print("Warning: Could not import custom MCP definitions")
    # Define dummy functions if imports fail
    def register_tools(mcp): pass
    def register_resources(mcp): pass
    def register_prompts(mcp): pass

class Auth0TokenVerifier(TokenVerifier):
    """Token verifier that validates tokens against Auth0."""

    def __init__(self, auth0_domain: str, auth0_audience: str):
        self.auth0_domain = auth0_domain
        self.auth0_audience = auth0_audience
        self.issuer = f"https://{auth0_domain}/"
        self.jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
        # Initialize JWKS client with caching
        self.jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify the token with Auth0 using proper JWT validation."""
        try:
            # Get the signing key from Auth0 JWKS endpoint
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify the JWT
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.auth0_audience,
                issuer=self.issuer,
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )

            # Extract relevant information from the token
            sub = payload.get("sub", "")
            exp = payload.get("exp")
            client_id = payload.get("azp") or payload.get("client_id", "")

            # Extract scopes from token
            scope_string = payload.get("scope", "")
            scopes = scope_string.split() if scope_string else []

            # If no scopes in 'scope' claim, check 'permissions' claim (for Auth0 RBAC)
            if not scopes:
                permissions = payload.get("permissions", [])
                if isinstance(permissions, list):
                    scopes = permissions

            # Ensure MCP scopes are present
            if not any(scope.startswith("mcp:") for scope in scopes):
                # Add default MCP scopes if none present
                scopes.extend(["mcp:read", "mcp:write"])

            return AccessToken(
                token=token,
                client_id=client_id,
                scopes=scopes,
                expires_at=exp
            )

        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidAudienceError:
            print("Invalid audience")
            return None
        except jwt.InvalidIssuerError:
            print("Invalid issuer")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

from dotenv import load_dotenv
from pathlib import Path
current_dir = Path(__file__).parent
project_root = Path(__file__).parent.parent.parent.parent.parent.parent

dotenv_path = current_dir / '.env'
if not load_dotenv(dotenv_path):
    dotenv_path = project_root / '.env'
    if not load_dotenv(dotenv_path):
        print(f"No .env file found in {project_root / '.env'} or {current_dir / '.env'}.")
    else:
        print(f"Environment variables loaded from: {dotenv_path}")
else:
    print(f"Environment variables loaded from: {dotenv_path}")

# Get Auth0 configuration from environment
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL", "")

# Validate configuration
if not all([AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_CLIENT_ID, AUTH0_CALLBACK_URL]):
    print("❌ Error: Missing Auth0 configuration!")
    print("Please set the following environment variables:")
    print("  - AUTH0_DOMAIN (e.g., 'dev-xxx.us.auth0.com')")
    print("  - AUTH0_AUDIENCE (e.g., 'https://your-api-identifier')")
    print("  - AUTH0_CLIENT_ID (your Auth0 application Client ID)")
    print("  - AUTH0_CLIENT_SECRET (optional, for confidential clients)")
    print("  - AUTH0_CALLBACK_URL (e.g., 'http://localhost:8003/secure/callback')")
    sys.exit(1)



# Create MCP server with authentication
mcp = FastMCP(
    name="AuthenticatedMathServer",
    stateless_http=True,
    token_verifier=Auth0TokenVerifier(AUTH0_DOMAIN, AUTH0_AUDIENCE),
    auth=AuthSettings(
        issuer_url=f"https://{AUTH0_DOMAIN}/",
        resource_server_url="http://localhost:8003",
        required_scopes=["mcp:read", "mcp:write"]
    )
)

# Tool specific to authenticated server
@mcp.tool(description="A secure calculation tool")
def secure_multiply(a: float, b: float) -> str:
    """Multiply two numbers securely (requires authentication)"""
    return f"{a} × {b} = {a * b}"

# Register common components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

# Create FastAPI app with MCP's lifespan
app = FastAPI(lifespan=lambda app: mcp.session_manager.run())
app.mount("/secure", mcp.streamable_http_app())

# Add Auth0 discovery endpoints for RFC 9728 compliance
@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """OAuth 2.0 protected resource discovery endpoint"""
    return {
        "resource": "http://localhost:8003",
        "authorization_servers": [f"https://{AUTH0_DOMAIN}/"]
    }

@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 authorization server metadata endpoint"""
    return {
        "issuer": f"https://{AUTH0_DOMAIN}/",
        "authorization_endpoint": f"https://{AUTH0_DOMAIN}/authorize",
        "token_endpoint": "http://localhost:8003/token",  # Point to our proxy endpoint
        "jwks_uri": f"https://{AUTH0_DOMAIN}/.well-known/jwks.json",
        "registration_endpoint": "http://localhost:8003/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": ["openid", "profile", "email", "mcp:read", "mcp:write", "offline_access"],
        "code_challenge_methods_supported": ["S256"]
    }

@app.get("/auth/config")
async def get_auth_config():
    """Endpoint to get Auth0 configuration for clients"""
    return {
        "domain": AUTH0_DOMAIN,
        "clientId": AUTH0_CLIENT_ID,
        "clientSecret": AUTH0_CLIENT_SECRET if AUTH0_CLIENT_SECRET else None,
        "audience": AUTH0_AUDIENCE,
        "scope": "openid profile email mcp:read mcp:write offline_access",
        "redirectUri": AUTH0_CALLBACK_URL
    }

@app.post("/token")
async def token_proxy(
    grant_type: str = Form(...),
    code: str = Form(None),
    redirect_uri: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    refresh_token: str = Form(None),
    code_verifier: str = Form(None)
):
    """Proxy token requests to Auth0 with proper PKCE handling."""

    auth0_token_url = f"https://{AUTH0_DOMAIN}/oauth/token"

    # Build the request data
    data = {
        "grant_type": grant_type,
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": redirect_uri or AUTH0_CALLBACK_URL,
    }

    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        data["code"] = code
        data["audience"] = AUTH0_AUDIENCE
        if code_verifier:
            data["code_verifier"] = code_verifier
            # For public clients with PKCE, don't include client_secret
            print(f"Using PKCE flow with code_verifier")
        elif AUTH0_CLIENT_SECRET:
            data["client_secret"] = AUTH0_CLIENT_SECRET

    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")
        data["refresh_token"] = refresh_token

        # Include client_secret if available
        if AUTH0_CLIENT_SECRET:
            data["client_secret"] = AUTH0_CLIENT_SECRET

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant type: {grant_type}")

    # Make request to Auth0
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(auth0_token_url, data=data)

            if response.status_code != 200:
                print(f"Auth0 error: {response.status_code} - {response.text}")
                # Return Auth0's error response
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json()
                )

            return response.json()

        except Exception as e:
            print(f"Token exchange error: {e}")
            raise HTTPException(status_code=500, detail="Token exchange failed")

@app.get("/authorize")
async def authorize_redirect(request: Request):
    """Redirect authorization requests to Auth0 with all parameters."""
    # Get all query parameters from the request
    params = dict(request.query_params)

    # Force re-authentication by adding prompt=login
    params['prompt'] = 'login'  # This forces Auth0 to show login page

    # Ensure we have the audience parameter for Auth0
    if 'audience' not in params:
        params['audience'] = AUTH0_AUDIENCE

    # Build the Auth0 authorization URL
    auth0_authorize_url = f"https://{AUTH0_DOMAIN}/authorize"
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    redirect_url = f"{auth0_authorize_url}?{query_string}"

    print(f"Redirecting to Auth0: {redirect_url}")

    # Redirect to Auth0
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url, status_code=302)

@app.post("/register")
async def register_client(request: Request):
    """Mock client registration endpoint for MCP OAuth flow.

    Since we're using Auth0, clients are pre-registered there.
    This endpoint just returns the client info back with the Auth0 client ID.
    """
    from mcp.shared.auth import OAuthClientInformationFull

    # Get the request body
    body = await request.json()

    # Return the registration with our Auth0 client ID
    return OAuthClientInformationFull(
        client_id=AUTH0_CLIENT_ID,
        client_name=body.get("client_name", "MCP Client"),
        redirect_uris=[AUTH0_CALLBACK_URL],  # Use fixed callback URL
        grant_types=body.get("grant_types", ["authorization_code", "refresh_token"]),
        response_types=body.get("response_types", ["code"]),
        scope=body.get("scope", "openid profile email mcp:read mcp:write offline_access")
    ).model_dump()

if __name__ == "__main__":
    print(f"📌 Auth0 Domain: {AUTH0_DOMAIN}")
    print(f"📌 Auth0 Audience: {AUTH0_AUDIENCE}")
    print(f"📌 Auth0 Client ID: {AUTH0_CLIENT_ID}")
    print(f"📌 Callback URL: {AUTH0_CALLBACK_URL}")
    print(f"📌 Server URL: http://localhost:8003/secure/mcp")
    print(f"📌 Token endpoint: http://localhost:8003/token")
    print(f"📌 Discovery endpoint: http://localhost:8003/.well-known/oauth-protected-resource")
    print("\n⚠️  Make sure your Auth0 application has the following callback URL configured:")
    print(f"   {AUTH0_CALLBACK_URL}")
    print("\n⚠️  Note: This server requires PyJWT for token verification.")
    print("Install with: pip install PyJWT cryptography python-multipart")
    uvicorn.run(app, host="0.0.0.0", port=8003)