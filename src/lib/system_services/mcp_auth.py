#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Authentication module for Model Context Protocol servers and clients.

This module provides OAuth 2.1 compliant authentication for MCP implementations,
including token verification, OAuth flows, and security utilities. It follows
the MCP authentication specification and implements RFC 9728, RFC 8707, and
other relevant standards.

Security features:
- OAuth 2.1 with PKCE support
- Token introspection (RFC 7662)
- Resource indicators (RFC 8707)
- Protected resource metadata (RFC 9728)
- JWT validation with proper claim verification
- Secure token storage recommendations

Example:
    Server-side token verification:

    .. code-block:: python

        from src.lib.system_services.mcp_auth import IntrospectionTokenVerifier

        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://mcp.example.com"
        )

        token_info = await verifier.verify_token(bearer_token)
"""

import time
import secrets
import hashlib
import base64
from typing import Optional, List, Dict, Any, Protocol
from mcp.server.auth.provider import AccessToken
from urllib.parse import urlparse, urljoin
import json

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from authlib.jose import jwt, JsonWebKey, KeySet
from authlib.jose.errors import JoseError, ExpiredTokenError, InvalidClaimError
from pydantic import BaseModel, HttpUrl, Field, field_validator
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from src.lib.core.log import Logger

logger = Logger().get_logger()


# Security Constants
DEFAULT_ALGORITHM = "RS256"
DEFAULT_TOKEN_EXPIRY = 3600  # 1 hour
MIN_KEY_SIZE = 2048
SUPPORTED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
OAUTH_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
MAX_CLOCK_SKEW = 300  # 5 minutes


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class TokenValidationError(AuthenticationError):
    """Token validation failed."""
    pass


class OAuthFlowError(AuthenticationError):
    """OAuth flow error."""
    pass


class TokenVerifier(Protocol):
    """Protocol for token verification implementations."""

    async def verify_token(self, token: str) -> Optional["AccessToken"]:
        """
        Verify an access token.

        :param token: Bearer token to verify
        :return: MCP AccessToken if valid, None otherwise
        """
        ...


class AuthSettings(BaseModel):
    """
    Authentication settings for MCP servers.

    These settings configure OAuth 2.1 authentication for protected MCP servers
    following the MCP authentication specification.
    """
    issuer_url: HttpUrl
    resource_server_url: HttpUrl
    required_scopes: List[str] = Field(default_factory=list)
    audience: Optional[str] = None
    algorithms: List[str] = Field(default_factory=lambda: ["RS256"])
    validate_resource: bool = True  # RFC 8707 resource validation

    @field_validator('algorithms')
    def validate_algorithms(cls, v):
        """Ensure only secure algorithms are used."""
        for algo in v:
            if algo not in SUPPORTED_ALGORITHMS:
                raise ValueError(f"Unsupported algorithm: {algo}")
            if algo == "none":
                raise ValueError("The 'none' algorithm is not allowed")
        return v


class IntrospectionTokenVerifier(TokenVerifier):
    """
    Token verifier using OAuth 2.0 Token Introspection (RFC 7662).

    This implementation validates tokens by calling an introspection endpoint
    on the authorization server. It includes RFC 8707 resource validation
    and secure HTTP client configuration.
    """

    def __init__(
        self,
        introspection_endpoint: str,
        server_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        validate_resource: bool = True,
        timeout: Optional[httpx.Timeout] = None
    ):
        """
        Initialize introspection-based token verifier.

        :param introspection_endpoint: Authorization server introspection URL
        :param server_url: This MCP server's URL (for resource validation)
        :param client_id: Optional client ID for authenticated introspection
        :param client_secret: Optional client secret for authenticated introspection
        :param validate_resource: Enable RFC 8707 resource validation
        :param timeout: HTTP timeout configuration
        """
        self.introspection_endpoint = introspection_endpoint
        self.server_url = server_url
        self.resource_url = self._normalize_resource_url(server_url)
        self.client_id = client_id
        self.client_secret = client_secret
        self.validate_resource = validate_resource
        self.timeout = timeout or OAUTH_TIMEOUT

        # Validate introspection endpoint
        if not self._is_secure_endpoint(introspection_endpoint):
            raise ValueError(f"Insecure introspection endpoint: {introspection_endpoint}")

    @staticmethod
    def _normalize_resource_url(url: str) -> str:
        """Normalize resource URL per RFC 8707."""
        parsed = urlparse(url)
        # Remove fragment, lowercase scheme/host
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        if parsed.path and parsed.path != "/":
            normalized += parsed.path.rstrip("/")
        return normalized

    @staticmethod
    def _is_secure_endpoint(url: str) -> bool:
        """Validate endpoint security."""
        return url.startswith(("https://", "http://localhost", "http://127.0.0.1"))

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify token via introspection endpoint.

        :param token: Bearer token to verify
        :return: AccessToken if valid, None otherwise
        """
        if not token:
            logger.debug("No token provided for verification")
            return None

        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            verify=True,
            follow_redirects=False
        ) as client:
            try:
                # Prepare introspection request
                data = {"token": token}
                auth = None

                if self.client_id and self.client_secret:
                    # Use HTTP Basic auth for client credentials
                    auth = httpx.BasicAuth(self.client_id, self.client_secret)

                response = await client.post(
                    self.introspection_endpoint,
                    data=data,
                    auth=auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code != 200:
                    logger.warning(f"Introspection failed with status {response.status_code}")
                    return None

                result = response.json()

                # Token must be active
                if not result.get("active", False):
                    logger.debug("Token is not active")
                    return None

                # RFC 8707 resource validation
                if self.validate_resource and not self._validate_resource(result):
                    logger.warning("Token resource validation failed")
                    return None

                # Return AccessToken if available, otherwise return None
                return AccessToken(
                    token=token,
                    client_id=result.get("client_id", "unknown"),
                    scopes=result.get("scope", "").split() if result.get("scope") else [],
                    expires_at=result.get("exp"),
                    resource=result.get("aud")
                )

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during introspection: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error during introspection: {e}")
                return None

    async def load_access_token(self, token: str) -> Optional["AccessToken"]:
        """
        Load/verify an access token - called by MCP's auth middleware.
        This method exists to match MCP's expected auth interface.

        :param token: Bearer token to verify
        :return: MCP AccessToken if valid, None otherwise
        """
        return await self.verify_token(token)

    def _validate_resource(self, token_data: dict) -> bool:
        """
        Validate token was issued for this resource server (RFC 8707).

        :param token_data: Introspection response data
        :return: True if resource is valid
        """
        if not self.resource_url:
            return False

        # Check 'aud' (audience) claim
        aud = token_data.get("aud")

        if isinstance(aud, list):
            return any(self._check_resource_match(a) for a in aud)
        elif aud:
            return self._check_resource_match(aud)

        # Also check 'resource' claim if present
        resource = token_data.get("resource")
        if resource:
            return self._check_resource_match(resource)

        return False

    def _check_resource_match(self, resource: str) -> bool:
        """Check if resource matches using hierarchical matching."""
        normalized_resource = self._normalize_resource_url(resource)

        # Exact match
        if self.resource_url == normalized_resource:
            return True

        # Hierarchical match: token for parent resource is valid for child
        if self.resource_url.startswith(normalized_resource + "/"):
            return True

        return False


class JWTTokenVerifier(TokenVerifier):
    """
    Local JWT token verifier using public key validation.

    This implementation validates JWT tokens locally using public keys fetched
    from a JWKS endpoint or provided directly. Suitable for high-performance
    scenarios where introspection overhead should be avoided.
    """

    def __init__(
        self,
        jwks_uri: Optional[str] = None,
        public_keys: Optional[Dict[str, Any]] = None,
        issuer: str = None,
        audience: str = None,
        algorithms: Optional[List[str]] = None,
        validate_resource: bool = True,
        cache_ttl: int = 3600
    ):
        """
        Initialize JWT token verifier.

        :param jwks_uri: JWKS endpoint URL for dynamic key discovery
        :param public_keys: Static public keys (if not using JWKS)
        :param issuer: Expected token issuer
        :param audience: Expected token audience
        :param algorithms: Allowed signing algorithms
        :param validate_resource: Enable audience validation
        :param cache_ttl: JWKS cache duration in seconds
        """
        self.jwks_uri = jwks_uri
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self.validate_resource = validate_resource
        self.cache_ttl = cache_ttl

        # Validate algorithms
        for algo in self.algorithms:
            if algo not in SUPPORTED_ALGORITHMS:
                raise ValueError(f"Unsupported algorithm: {algo}")

        # Key management
        self._keys: Optional[KeySet] = None
        self._keys_cached_at: Optional[float] = None

        if public_keys:
            self._keys = self._load_static_keys(public_keys)

    def _load_static_keys(self, keys_data: Dict[str, Any]) -> KeySet:
        """Load static public keys."""
        if "keys" in keys_data:
            # JWK Set format
            return JsonWebKey.import_key_set(keys_data)
        else:
            # Single key
            key = JsonWebKey.import_key(keys_data)
            return KeySet([key])

    async def _fetch_keys(self) -> KeySet:
        """Fetch public keys from JWKS endpoint."""
        if not self.jwks_uri:
            raise ValueError("No JWKS URI configured")

        # Check cache
        if self._keys and self._keys_cached_at:
            if time.time() - self._keys_cached_at < self.cache_ttl:
                return self._keys

        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            try:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()

                jwks_data = response.json()
                self._keys = JsonWebKey.import_key_set(jwks_data)
                self._keys_cached_at = time.time()

                return self._keys

            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                # Return cached keys if available
                if self._keys:
                    return self._keys
                raise

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify JWT token using public key validation.

        :param token: JWT token to verify
        :return: AccessToken if valid, None otherwise
        """
        if not token:
            return None

        try:
            # Get signing keys
            if self.jwks_uri:
                keys = await self._fetch_keys()
            elif self._keys:
                keys = self._keys
            else:
                logger.error("No keys available for JWT verification")
                return None

            # Decode and validate token
            claims_options = {
                "iss": {"essential": True, "value": self.issuer} if self.issuer else None,
                "aud": {"essential": True, "value": self.audience} if self.audience else None,
                "exp": {"essential": True},
                "nbf": {"essential": False},
            }

            # Remove None values
            claims_options = {k: v for k, v in claims_options.items() if v is not None}

            # Decode with validation
            claims = jwt.decode(
                token,
                keys,
                claims_options=claims_options,
                claims_cls=None  # Use default claims class
            )

            # Additional validation
            claims.validate()

            return AccessToken(
                token=token,
                client_id=claims.get("client_id", claims.get("azp", "unknown")),
                scopes=self._extract_scopes(claims),
                expires_at=claims.get("exp"),
                resource=claims.get("aud")
            )

        except ExpiredTokenError:
            logger.debug("Token has expired")
            return None
        except InvalidClaimError as e:
            logger.debug(f"Invalid token claim: {e}")
            return None
        except JoseError as e:
            logger.debug(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JWT verification: {e}")
            return None

    async def load_access_token(self, token: str) -> Optional["AccessToken"]:
        """
        Load/verify an access token - called by MCP's auth middleware.
        This method exists to match MCP's expected auth interface.

        :param token: Bearer token to verify
        :return: MCP AccessToken if valid, None otherwise
        """
        return await self.verify_token(token)

    @staticmethod
    def _extract_scopes(claims: dict) -> List[str]:
        """Extract scopes from various claim formats."""
        scope = claims.get("scope", claims.get("scopes", ""))

        if isinstance(scope, list):
            return scope
        elif isinstance(scope, str):
            return scope.split() if scope else []
        else:
            return []


class OAuthClient:
    """
    OAuth 2.1 client for MCP client authentication.

    Implements OAuth 2.1 authorization code flow with PKCE, dynamic client
    registration, and token management. Follows MCP authentication spec
    requirements including RFC 8707 resource indicators.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://localhost:8080/callback",
        token_storage: Optional["TokenStorage"] = None
    ):
        """
        Initialize OAuth client.

        :param client_id: OAuth client ID (optional for dynamic registration)
        :param client_secret: OAuth client secret
        :param redirect_uri: OAuth redirect URI
        :param token_storage: Token storage implementation
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_storage = token_storage or MemoryTokenStorage()

        self._oauth_client: Optional[AsyncOAuth2Client] = None
        self._server_metadata: Optional[Dict[str, Any]] = None
        self._resource_metadata: Optional[Dict[str, Any]] = None

    async def discover_authorization(self, resource_url: str) -> Dict[str, Any]:
        """
        Discover authorization requirements using RFC 9728.

        :param resource_url: MCP server URL
        :return: Authorization configuration
        """
        metadata_url = urljoin(resource_url, "/.well-known/oauth-protected-resource")

        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            try:
                response = await client.get(metadata_url)

                if response.status_code == 404:
                    # No authentication required
                    return {"protected": False}

                response.raise_for_status()
                self._resource_metadata = response.json()

                # Get authorization server metadata
                auth_servers = self._resource_metadata.get("authorization_servers", [])
                if not auth_servers:
                    raise OAuthFlowError("No authorization servers found")

                # Use first authorization server (could be enhanced with selection logic)
                auth_server = auth_servers[0]

                # Fetch authorization server metadata
                as_metadata_url = urljoin(auth_server, "/.well-known/oauth-authorization-server")
                as_response = await client.get(as_metadata_url)
                as_response.raise_for_status()

                self._server_metadata = as_response.json()

                return {
                    "protected": True,
                    "resource": self._resource_metadata.get("resource", resource_url),
                    "authorization_server": auth_server,
                    "metadata": self._server_metadata
                }

            except httpx.HTTPError as e:
                logger.error(f"Failed to discover authorization: {e}")
                raise OAuthFlowError(f"Authorization discovery failed: {e}")

    async def register_client(self, registration_endpoint: str) -> Dict[str, str]:
        """
        Dynamically register OAuth client (RFC 7591).

        :param registration_endpoint: Dynamic registration endpoint
        :return: Client credentials
        """
        registration_data = {
            "client_name": "MCP Client",
            "redirect_uris": [self.redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_basic",
            "application_type": "native"
        }

        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            try:
                response = await client.post(
                    registration_endpoint,
                    json=registration_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                result = response.json()
                self.client_id = result["client_id"]
                self.client_secret = result.get("client_secret")

                logger.info(f"Dynamically registered client: {self.client_id}")

                return {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }

            except httpx.HTTPError as e:
                logger.error(f"Client registration failed: {e}")
                raise OAuthFlowError(f"Dynamic registration failed: {e}")

    async def get_access_token(self, resource_url: str, scopes: Optional[List[str]] = None) -> str:
        """
        Get access token for resource, handling full OAuth flow if needed.

        :param resource_url: Target MCP server URL
        :param scopes: Required scopes
        :return: Access token
        """
        # Check for existing valid token
        cached_token = await self.token_storage.get_token(resource_url)
        if cached_token and not self._is_token_expired(cached_token):
            return cached_token["access_token"]

        # Try refresh if available
        if cached_token and "refresh_token" in cached_token:
            try:
                new_token = await self.refresh_token(resource_url, cached_token["refresh_token"])
                return new_token["access_token"]
            except Exception as e:
                logger.debug(f"Refresh failed, starting new flow: {e}")

        # Start new authorization flow
        return await self._authorization_flow(resource_url, scopes)

    async def _authorization_flow(self, resource_url: str, scopes: Optional[List[str]] = None) -> str:
        """
        Execute OAuth 2.1 authorization code flow with PKCE.

        :param resource_url: Target resource
        :param scopes: Required scopes
        :return: Access token
        """
        if not self._server_metadata:
            await self.discover_authorization(resource_url)

        # Dynamic registration if needed
        if not self.client_id and self._server_metadata.get("registration_endpoint"):
            await self.register_client(self._server_metadata["registration_endpoint"])

        if not self.client_id:
            raise OAuthFlowError("No client_id available and dynamic registration not supported")

        # Create OAuth client
        self._oauth_client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            authorization_endpoint=self._server_metadata["authorization_endpoint"],
            token_endpoint=self._server_metadata["token_endpoint"],
            code_challenge_method="S256"  # PKCE
        )

        # Generate PKCE challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = create_s256_code_challenge(code_verifier)

        # Build authorization URL with resource parameter (RFC 8707)
        auth_url, state = self._oauth_client.create_authorization_url(
            self._server_metadata["authorization_endpoint"],
            code_challenge=code_challenge,
            code_challenge_method="S256",
            resource=resource_url,  # RFC 8707
            scope=" ".join(scopes) if scopes else None
        )

        # TODO: Implement browser interaction to redirect user to auth_url
        raise NotImplementedError(
            "Full OAuth flow requires browser interaction. "
            f"Please visit: {auth_url} and implement callback handling."
        )

    async def refresh_token(self, resource_url: str, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.

        :param resource_url: Target resource
        :param refresh_token: Refresh token
        :return: New token data
        """
        if not self._server_metadata:
            await self.discover_authorization(resource_url)

        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            try:
                response = await client.post(
                    self._server_metadata["token_endpoint"],
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "resource": resource_url  # RFC 8707
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()

                token_data = response.json()
                await self.token_storage.store_token(resource_url, token_data)

                return token_data

            except httpx.HTTPError as e:
                logger.error(f"Token refresh failed: {e}")
                raise OAuthFlowError(f"Token refresh failed: {e}")

    @staticmethod
    def _is_token_expired(token_data: Dict[str, Any]) -> bool:
        """Check if token is expired."""
        expires_at = token_data.get("expires_at")
        if not expires_at:
            # Calculate from expires_in if available
            if "expires_in" in token_data and "issued_at" in token_data:
                expires_at = token_data["issued_at"] + token_data["expires_in"]
            else:
                return True  # Assume expired if no expiration info

        return time.time() > (expires_at - 60)  # 60 second buffer


class TokenStorage(Protocol):
    """Protocol for token storage implementations."""

    async def get_token(self, resource: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored token for resource."""
        ...

    async def store_token(self, resource: str, token_data: Dict[str, Any]) -> None:
        """Store token for resource."""
        ...

    async def remove_token(self, resource: str) -> None:
        """Remove token for resource."""
        ...


class MemoryTokenStorage(TokenStorage):
    """In-memory token storage (not for production use)."""

    def __init__(self):
        self._tokens: Dict[str, Dict[str, Any]] = {}

    async def get_token(self, resource: str) -> Optional[Dict[str, Any]]:
        return self._tokens.get(resource)

    async def store_token(self, resource: str, token_data: Dict[str, Any]) -> None:
        # Add metadata
        token_data["issued_at"] = time.time()
        if "expires_in" in token_data and "expires_at" not in token_data:
            token_data["expires_at"] = time.time() + token_data["expires_in"]

        self._tokens[resource] = token_data

    async def remove_token(self, resource: str) -> None:
        self._tokens.pop(resource, None)


class SecureTokenStorage(TokenStorage):
    """
    Secure token storage with encryption.

    This is a simplified example. In production, use proper key management
    (HSM, KMS, etc.) and secure storage (encrypted database, secure vault).
    """

    def __init__(self, encryption_key: bytes):
        """
        Initialize secure storage.

        :param encryption_key: 32-byte encryption key
        """
        from cryptography.fernet import Fernet

        # Derive Fernet key from provided key
        key = base64.urlsafe_b64encode(encryption_key[:32].ljust(32, b'\0'))
        self._cipher = Fernet(key)
        self._storage = MemoryTokenStorage()  # TODO: Replace with persistent storage

    async def get_token(self, resource: str) -> Optional[Dict[str, Any]]:
        encrypted_data = await self._storage.get_token(resource)
        if not encrypted_data:
            return None

        try:
            decrypted = self._cipher.decrypt(encrypted_data["data"].encode())
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            return None

    async def store_token(self, resource: str, token_data: Dict[str, Any]) -> None:
        encrypted = self._cipher.encrypt(json.dumps(token_data).encode())
        await self._storage.store_token(resource, {"data": encrypted.decode()})

    async def remove_token(self, resource: str) -> None:
        await self._storage.remove_token(resource)


# Utility functions

def generate_key_pair(key_size: int = 2048) -> tuple[str, str]:
    """
    Generate RSA key pair for JWT signing.

    :param key_size: RSA key size (minimum 2048)
    :return: Tuple of (private_key_pem, public_key_pem)
    """
    if key_size < MIN_KEY_SIZE:
        raise ValueError(f"Key size must be at least {MIN_KEY_SIZE} bits")

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem.decode(), public_pem.decode()


def create_jwks(public_key_pem: str, kid: str = None) -> Dict[str, Any]:
    """
    Create JWKS from public key.

    :param public_key_pem: PEM-encoded public key
    :param kid: Key ID
    :return: JWKS dictionary
    """
    if not kid:
        kid = hashlib.sha256(public_key_pem.encode()).hexdigest()[:8]

    key = JsonWebKey.import_key(public_key_pem)
    key_data = key.as_dict()
    key_data["kid"] = kid
    key_data["use"] = "sig"

    return {"keys": [key_data]}


async def validate_mcp_token(
    token: str,
    verifier: TokenVerifier,
    required_scopes: Optional[List[str]] = None
) -> AccessToken:
    """
    Validate MCP access token with scope checking.

    :param token: Bearer token
    :param verifier: Token verifier implementation
    :param required_scopes: Required scopes
    :return: Validated AccessToken
    :raises: TokenValidationError if validation fails
    """
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    # Verify token
    access_token = await verifier.verify_token(token)
    if not access_token:
        raise TokenValidationError("Invalid or expired token")

    # Check expiration
    if access_token.expires_at and int(time.time()) > access_token.expires_at:
        raise TokenValidationError("Token has expired")

    # Check required scopes
    if required_scopes:
        missing_scopes = set(required_scopes) - set(access_token.scopes)
        if missing_scopes:
            raise TokenValidationError(
                f"Missing required scopes: {', '.join(sorted(missing_scopes))}"
            )

    return access_token
