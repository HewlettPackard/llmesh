#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example Streamable-http MCP client with Auth0 authentication.
"""

import asyncio
import webbrowser
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from typing import Optional, Tuple
import httpx
from aiohttp import web

# Import demo utility
try:
    from notebooks.platform_services.lablib.mcp.client_util import run_demo
except ImportError:
    async def run_demo(session):
        print("\n🔧 Available tools:")
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")

        if tools.tools:
            print(f"\n📊 Calling {tools.tools[0].name}...")
            result = await session.call_tool(
                tools.tools[0].name,
                arguments={"a": 5, "b": 3}
            )
            print(f"Result: {result}")

class InMemoryTokenStorage(TokenStorage):
    """Simple in-memory token storage."""

    def __init__(self):
        self.tokens: Optional[OAuthToken] = None
        self.client_info: Optional[OAuthClientInformationFull] = None

    async def get_tokens(self) -> Optional[OAuthToken]:
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens

    async def get_client_info(self) -> Optional[OAuthClientInformationFull]:
        return self.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_info = client_info

class Auth0OAuthProvider(OAuthClientProvider):
    """OAuth provider for Auth0 that properly integrates with MCP framework."""

    def __init__(self, server_url: str, auth0_domain: str, client_id: str,
                 client_secret: Optional[str], audience: str, redirect_uri: str):
        self.auth0_domain = auth0_domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience
        self.redirect_uri = redirect_uri
        self.server_runner: Optional[web.AppRunner] = None
        self.callback_event = asyncio.Event()
        self.callback_params: dict = {}

        # Create storage instance
        self._storage = InMemoryTokenStorage()

        # Initialize parent with required handlers
        super().__init__(
            server_url=server_url,
            client_metadata=OAuthClientMetadata(
                client_name="MCP Lab Client",
                redirect_uris=[redirect_uri],
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                scope="openid profile email mcp:read mcp:write offline_access"
            ),
            storage=self._storage,
            redirect_handler=self._handle_redirect,
            callback_handler=self._handle_callback
        )

    async def _start_callback_server(self) -> None:
        """Start a local web server to capture the OAuth callback."""
        async def handle_callback(request):
            # Capture all query parameters
            self.callback_params = dict(request.query)
            self.callback_event.set()

            if 'code' in self.callback_params:
                html = """
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>✅ Authentication Successful!</h1>
                    <p>You can now close this window and return to the terminal.</p>
                    <script>
                        setTimeout(() => {
                            window.close();
                            setTimeout(() => {
                                document.body.innerHTML += '<p style="margin-top: 20px; color: #666;">If this window doesn\'t close automatically, you can close it manually.</p>';
                            }, 1000);
                        }, 2000);
                    </script>
                </body>
                </html>
                """
            else:
                error = self.callback_params.get('error_description', self.callback_params.get('error', 'Unknown error'))
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>❌ Authentication Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
                """

            return web.Response(text=html, content_type='text/html')

        app = web.Application()
        app.router.add_get('/callback', handle_callback)

        self.server_runner = web.AppRunner(app)
        await self.server_runner.setup()
        site = web.TCPSite(self.server_runner, 'localhost', 8080)
        await site.start()
        print(f"📡 Started callback server on {self.redirect_uri}")

    async def _stop_callback_server(self):
        """Stop the callback server."""
        if self.server_runner:
            await self.server_runner.cleanup()

    async def _handle_redirect(self, auth_url: str) -> None:
        """Handle the authorization redirect by opening browser."""
        # Start callback server first
        await self._start_callback_server()

        print("\n🔐 Opening browser for authentication...")
        print(f"If browser doesn't open, please visit:\n{auth_url}\n")

        # Open browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("Please open the URL manually in your browser.")

    async def _handle_callback(self) -> Tuple[str, Optional[str]]:
        """Handle OAuth callback - return code and state for framework to process."""
        print("⏳ Waiting for authentication callback...")

        try:
            # Wait for callback with timeout
            await asyncio.wait_for(self.callback_event.wait(), timeout=300)

            # Stop callback server
            await self._stop_callback_server()

            if 'error' in self.callback_params:
                raise ValueError(f"Authentication failed: {self.callback_params.get('error_description', self.callback_params['error'])}")

            if 'code' not in self.callback_params:
                raise ValueError("No authorization code received")

            print("✅ Authorization code received")

            # Return the code and state for the framework to handle token exchange
            code = self.callback_params['code']
            state = self.callback_params.get('state')

            return (code, state)

        except asyncio.TimeoutError:
            await self._stop_callback_server()
            raise ValueError("Authentication timeout - no callback received within 5 minutes")
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            await self._stop_callback_server()
            raise

async def main():
    # Get Auth0 configuration from server
    config_url = "http://localhost:8003/auth/config"

    print("🔐 Auth0 MCP Client Demo")
    print("=" * 50)
    print(f"Fetching Auth0 configuration from {config_url}...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(config_url)
            if response.status_code != 200:
                print(f"❌ Failed to fetch Auth0 config: {response.status_code}")
                print("Make sure the Auth0-enabled server is running on port 8003")
                return

            config = response.json()
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("Make sure the Auth0-enabled server is running on port 8003")
        return

    # Validate configuration
    if not config.get('domain') or config['domain'] == '<domain>':
        print("\n❌ Server returned invalid Auth0 configuration!")
        print("Please ensure the server has the following environment variables set:")
        print("  - AUTH0_DOMAIN")
        print("  - AUTH0_AUDIENCE")
        print("  - AUTH0_CLIENT_ID")
        print("  - AUTH0_CLIENT_SECRET (optional)")
        return

    print(f"✅ Auth0 Domain: {config['domain']}")
    print(f"✅ Client ID: {config['clientId']}")
    print(f"✅ Audience: {config['audience']}")
    print(f"✅ Callback URL: {config['redirectUri']}")

    # Set up OAuth authentication
    oauth_provider = Auth0OAuthProvider(
        server_url="http://localhost:8003",  # Base server URL
        auth0_domain=config['domain'],
        client_id=config['clientId'],
        client_secret=config.get('clientSecret'),
        audience=config['audience'],
        redirect_uri=config['redirectUri']
    )

    server_url = "http://localhost:8003/secure/mcp"
    print(f"\n📡 Connecting to authenticated MCP server at {server_url}...")

    try:
        # Connect with authentication
        async with streamablehttp_client(server_url, auth=oauth_provider) as (reader, writer, _):
            print("✅ Successfully authenticated and connected!")

            async with ClientSession(reader, writer) as session:
                await run_demo(session)

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Make sure the Auth0-enabled server is running on port 8003")
        print("2. Check that Auth0 credentials are configured correctly")
        print("3. Ensure Auth0 application has http://localhost:8080/callback as allowed callback URL")
        print("4. Check that PyJWT is installed: pip install PyJWT cryptography")

if __name__ == "__main__":
    asyncio.run(main())