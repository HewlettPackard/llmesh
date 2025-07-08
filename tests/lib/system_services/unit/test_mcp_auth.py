#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Authentication functionality

Tests for MCP authentication module including OAuth 2.1, token verification,
and secure token storage implementations.
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock


import httpx
from authlib.jose import jwt

from src.lib.system_services.mcp_auth import (
    AccessToken,
    TokenValidationError,
    AuthSettings,
    IntrospectionTokenVerifier,
    JWTTokenVerifier,
    OAuthClient,
    MemoryTokenStorage,
    SecureTokenStorage,
    generate_key_pair,
    create_jwks,
    validate_mcp_token
)

class TestAuthSettings:
    """Test AuthSettings validation."""

    def test_valid_auth_settings(self):
        """Test creating valid auth settings."""
        settings = AuthSettings(
            issuer_url="https://auth.example.com",
            resource_server_url="https://api.example.com",
            required_scopes=["read", "write"],
            audience="api.example.com",
            algorithms=["RS256", "ES256"],
            validate_resource=True
        )

        assert str(settings.issuer_url) == "https://auth.example.com/"
        assert str(settings.resource_server_url) == "https://api.example.com/"
        assert settings.required_scopes == ["read", "write"]
        assert settings.algorithms == ["RS256", "ES256"]

    def test_invalid_algorithm_raises_error(self):
        """Test that invalid algorithms raise validation error."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            AuthSettings(
                issuer_url="https://auth.example.com",
                resource_server_url="https://api.example.com",
                algorithms=["HS256"]  # Not in SUPPORTED_ALGORITHMS
            )

    def test_none_algorithm_raises_error(self):
        """Test that 'none' algorithm is rejected."""
        with pytest.raises(ValueError, match="Unsupported algorithm: none"):
            AuthSettings(
                issuer_url="https://auth.example.com",
                resource_server_url="https://api.example.com",
                algorithms=["none"]
            )

    def test_default_algorithm(self):
        """Test default algorithm is RS256."""
        settings = AuthSettings(
            issuer_url="https://auth.example.com",
            resource_server_url="https://api.example.com"
        )

        assert settings.algorithms == ["RS256"]


class TestIntrospectionTokenVerifier:
    """Test IntrospectionTokenVerifier functionality."""

    def test_initialization(self):
        """Test verifier initialization."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com",
            client_id="test_client",
            client_secret="test_secret",
            validate_resource=True
        )

        assert verifier.introspection_endpoint == "https://auth.example.com/introspect"
        assert verifier.server_url == "https://api.example.com"
        assert verifier.resource_url == "https://api.example.com"
        assert verifier.client_id == "test_client"
        assert verifier.validate_resource is True

    def test_insecure_endpoint_raises_error(self):
        """Test that insecure endpoints raise error."""
        with pytest.raises(ValueError, match="Insecure introspection endpoint"):
            IntrospectionTokenVerifier(
                introspection_endpoint="http://example.com/introspect",
                server_url="https://api.example.com"
            )

    def test_localhost_endpoint_allowed(self):
        """Test that localhost endpoints are allowed."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="http://localhost:8080/introspect",
            server_url="https://api.example.com"
        )
        assert verifier.introspection_endpoint == "http://localhost:8080/introspect"

    def test_normalize_resource_url(self):
        """Test resource URL normalization."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        # Test various URL formats
        assert verifier._normalize_resource_url("https://API.EXAMPLE.COM") == "https://api.example.com"
        assert verifier._normalize_resource_url("https://api.example.com/") == "https://api.example.com"
        assert verifier._normalize_resource_url("https://api.example.com/path") == "https://api.example.com/path"
        assert verifier._normalize_resource_url("https://api.example.com/path/") == "https://api.example.com/path"

    @pytest.mark.asyncio
    async def test_verify_token_no_token(self):
        """Test verify_token with no token returns None."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        result = await verifier.verify_token("")
        assert result is None

        result = await verifier.verify_token(None)
        assert result is None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_verify_token_success(self, mock_client_class):
        """Test successful token verification."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "active": True,
            "client_id": "test_client",
            "scope": "read write",
            "exp": int(time.time()) + 3600,
            "aud": "https://api.example.com",
            "sub": "user123",
            "user_id": "user123"  # Add user_id to match expected field
        }
        mock_client.post.return_value = mock_response

        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        result = await verifier.verify_token("test_token")

        assert result is not None
        assert result.token == "test_token"
        assert result.client_id == "test_client"
        assert result.scopes == ["read", "write"]
        # user_id is only available in our AccessToken, not AccessToken
        if hasattr(result, 'user_id'):
            assert result.user_id == "user123"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_verify_token_inactive(self, mock_client_class):
        """Test verification of inactive token."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"active": False}
        mock_client.post.return_value = mock_response

        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        result = await verifier.verify_token("test_token")
        assert result is None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_verify_token_with_auth(self, mock_client_class):
        """Test token verification with client credentials."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "active": True,
            "client_id": "test_client",
            "scope": "read"
        }
        mock_client.post.return_value = mock_response

        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com",
            client_id="verifier_client",
            client_secret="verifier_secret"
        )

        await verifier.verify_token("test_token")

        # Verify client credentials were used
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args.kwargs["auth"] is not None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_verify_token_http_error(self, mock_client_class):
        """Test handling of HTTP errors during verification."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")

        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        result = await verifier.verify_token("test_token")
        assert result is None

    def test_validate_resource_exact_match(self):
        """Test resource validation with exact match."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        token_data = {"aud": "https://api.example.com"}
        assert verifier._validate_resource(token_data) is True

    def test_validate_resource_hierarchical_match(self):
        """Test resource validation with hierarchical match."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com/v1/users"
        )

        # Parent resource should validate child
        token_data = {"aud": "https://api.example.com"}
        assert verifier._validate_resource(token_data) is True

    def test_validate_resource_list_audience(self):
        """Test resource validation with audience list."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        token_data = {"aud": ["https://other.com", "https://api.example.com"]}
        assert verifier._validate_resource(token_data) is True

    def test_validate_resource_no_match(self):
        """Test resource validation with no match."""
        verifier = IntrospectionTokenVerifier(
            introspection_endpoint="https://auth.example.com/introspect",
            server_url="https://api.example.com"
        )

        token_data = {"aud": "https://different.com"}
        assert verifier._validate_resource(token_data) is False


class TestJWTTokenVerifier:
    """Test JWTTokenVerifier functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Generate test keys
        self.private_key, self.public_key = generate_key_pair()
        self.jwks = create_jwks(self.public_key, "test-key-1")

    def test_initialization_with_jwks_uri(self):
        """Test verifier initialization with JWKS URI."""
        verifier = JWTTokenVerifier(
            jwks_uri="https://auth.example.com/.well-known/jwks.json",
            issuer="https://auth.example.com",
            audience="api.example.com",
            algorithms=["RS256"],
            validate_resource=True,
            cache_ttl=1800
        )

        assert verifier.jwks_uri == "https://auth.example.com/.well-known/jwks.json"
        assert verifier.issuer == "https://auth.example.com"
        assert verifier.audience == "api.example.com"
        assert verifier.algorithms == ["RS256"]
        assert verifier.cache_ttl == 1800

    def test_initialization_with_static_keys(self):
        """Test verifier initialization with static keys."""
        verifier = JWTTokenVerifier(
            public_keys=self.jwks,
            issuer="https://auth.example.com",
            audience="api.example.com"
        )

        assert verifier._keys is not None
        assert verifier.jwks_uri is None

    def test_invalid_algorithm_raises_error(self):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            JWTTokenVerifier(
                public_keys=self.jwks,
                algorithms=["HS256"]  # Not supported
            )

    @pytest.mark.asyncio
    async def test_verify_token_no_token(self):
        """Test verify_token with no token returns None."""
        verifier = JWTTokenVerifier(
            public_keys=self.jwks,
            issuer="https://auth.example.com"
        )

        result = await verifier.verify_token("")
        assert result is None

        result = await verifier.verify_token(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful JWT token verification."""
        # Create a valid JWT
        claims = {
            "iss": "https://auth.example.com",
            "aud": "api.example.com",
            "sub": "user123",
            "client_id": "test_client",
            "scope": "read write",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "nbf": int(time.time())
        }

        header = {"alg": "RS256", "kid": "test-key-1"}
        token_bytes = jwt.encode(header, claims, self.private_key)
        token = token_bytes.decode('utf-8') if isinstance(token_bytes, bytes) else token_bytes

        verifier = JWTTokenVerifier(
            public_keys=self.jwks,
            issuer="https://auth.example.com",
            audience="api.example.com"
        )

        result = await verifier.verify_token(token)

        assert result is not None
        assert result.token == token
        assert result.client_id == "test_client"
        assert result.scopes == ["read", "write"]

    @pytest.mark.asyncio
    async def test_verify_token_expired(self):
        """Test verification of expired token."""
        # Create an expired JWT
        claims = {
            "iss": "https://auth.example.com",
            "aud": "api.example.com",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200
        }

        header = {"alg": "RS256", "kid": "test-key-1"}
        token = jwt.encode(header, claims, self.private_key)

        verifier = JWTTokenVerifier(
            public_keys=self.jwks,
            issuer="https://auth.example.com",
            audience="api.example.com"
        )

        result = await verifier.verify_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_wrong_issuer(self):
        """Test verification with wrong issuer."""
        claims = {
            "iss": "https://wrong.example.com",
            "aud": "api.example.com",
            "exp": int(time.time()) + 3600
        }

        header = {"alg": "RS256", "kid": "test-key-1"}
        token = jwt.encode(header, claims, self.private_key)

        verifier = JWTTokenVerifier(
            public_keys=self.jwks,
            issuer="https://auth.example.com",
            audience="api.example.com"
        )

        result = await verifier.verify_token(token)
        assert result is None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_keys_success(self, mock_client_class):
        """Test successful JWKS fetching."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.jwks
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        verifier = JWTTokenVerifier(
            jwks_uri="https://auth.example.com/.well-known/jwks.json",
            issuer="https://auth.example.com"
        )

        keys = await verifier._fetch_keys()
        assert keys is not None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_keys_with_cache(self, mock_client_class):
        """Test JWKS caching."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.jwks
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        verifier = JWTTokenVerifier(
            jwks_uri="https://auth.example.com/.well-known/jwks.json",
            issuer="https://auth.example.com",
            cache_ttl=3600
        )

        # First fetch
        await verifier._fetch_keys()
        # Second fetch should use cache
        await verifier._fetch_keys()

        # Should only fetch once due to cache
        mock_client.get.assert_called_once()

    def test_extract_scopes_from_string(self):
        """Test scope extraction from string."""
        claims = {"scope": "read write admin"}
        scopes = JWTTokenVerifier._extract_scopes(claims)
        assert scopes == ["read", "write", "admin"]

    def test_extract_scopes_from_list(self):
        """Test scope extraction from list."""
        claims = {"scopes": ["read", "write", "admin"]}
        scopes = JWTTokenVerifier._extract_scopes(claims)
        assert scopes == ["read", "write", "admin"]

    def test_extract_scopes_empty(self):
        """Test scope extraction with no scopes."""
        claims = {}
        scopes = JWTTokenVerifier._extract_scopes(claims)
        assert scopes == []


class TestOAuthClient:
    """Test OAuthClient functionality."""

    def test_initialization(self):
        """Test OAuth client initialization."""
        client = OAuthClient(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )

        assert client.client_id == "test_client"
        assert client.client_secret == "test_secret"
        assert client.redirect_uri == "http://localhost:8080/callback"
        assert isinstance(client.token_storage, MemoryTokenStorage)

    def test_initialization_with_custom_storage(self):
        """Test OAuth client with custom token storage."""
        custom_storage = Mock()
        client = OAuthClient(
            client_id="test_client",
            token_storage=custom_storage
        )

        assert client.token_storage == custom_storage

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_discover_authorization_unprotected(self, mock_client_class):
        """Test authorization discovery for unprotected resource."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        client = OAuthClient()
        result = await client.discover_authorization("https://api.example.com")

        assert result == {"protected": False}

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_discover_authorization_protected(self, mock_client_class):
        """Test authorization discovery for protected resource."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # First response - resource metadata
        resource_response = Mock()
        resource_response.status_code = 200
        resource_response.json.return_value = {
            "resource": "https://api.example.com",
            "authorization_servers": ["https://auth.example.com"]
        }
        resource_response.raise_for_status = Mock()

        # Second response - auth server metadata
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token"
        }
        auth_response.raise_for_status = Mock()

        mock_client.get.side_effect = [resource_response, auth_response]

        client = OAuthClient()
        result = await client.discover_authorization("https://api.example.com")

        assert result["protected"] is True
        assert result["resource"] == "https://api.example.com"
        assert result["authorization_server"] == "https://auth.example.com"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_register_client_success(self, mock_client_class):
        """Test successful dynamic client registration."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "client_id": "dynamic_client_id",
            "client_secret": "dynamic_secret"
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        client = OAuthClient()
        result = await client.register_client("https://auth.example.com/register")

        assert result["client_id"] == "dynamic_client_id"
        assert result["client_secret"] == "dynamic_secret"
        assert client.client_id == "dynamic_client_id"
        assert client.client_secret == "dynamic_secret"

    @pytest.mark.asyncio
    async def test_get_access_token_cached(self):
        """Test getting cached access token."""
        mock_storage = AsyncMock()
        mock_storage.get_token.return_value = {
            "access_token": "cached_token",
            "expires_in": 3600,
            "issued_at": time.time()
        }

        client = OAuthClient(token_storage=mock_storage)
        token = await client.get_access_token("https://api.example.com")

        assert token == "cached_token"
        mock_storage.get_token.assert_called_once_with("https://api.example.com")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_refresh_token_success(self, mock_client_class):
        """Test successful token refresh."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        mock_storage = AsyncMock()

        client = OAuthClient(
            client_id="test_client",
            client_secret="test_secret",
            token_storage=mock_storage
        )

        # Set server metadata
        client._server_metadata = {
            "token_endpoint": "https://auth.example.com/token"
        }

        result = await client.refresh_token("https://api.example.com", "old_refresh_token")

        assert result["access_token"] == "new_token"
        mock_storage.store_token.assert_called_once()

    def test_is_token_expired_with_expires_at(self):
        """Test token expiration check with expires_at field."""
        # Not expired
        token_data = {"expires_at": time.time() + 3600}
        assert not OAuthClient._is_token_expired(token_data)

        # Expired
        token_data = {"expires_at": time.time() - 3600}
        assert OAuthClient._is_token_expired(token_data)

    def test_is_token_expired_with_expires_in(self):
        """Test token expiration check with expires_in field."""
        token_data = {
            "expires_in": 3600,
            "issued_at": time.time() - 1800  # Issued 30 minutes ago
        }
        assert not OAuthClient._is_token_expired(token_data)

        token_data = {
            "expires_in": 3600,
            "issued_at": time.time() - 7200  # Issued 2 hours ago
        }
        assert OAuthClient._is_token_expired(token_data)


class TestTokenStorage:
    """Test token storage implementations."""

    @pytest.mark.asyncio
    async def test_memory_storage_basic_operations(self):
        """Test basic operations of MemoryTokenStorage."""
        storage = MemoryTokenStorage()

        # Test store and retrieve
        token_data = {"access_token": "test_token", "expires_in": 3600}
        await storage.store_token("resource1", token_data)

        retrieved = await storage.get_token("resource1")
        assert retrieved is not None
        assert retrieved["access_token"] == "test_token"
        assert "issued_at" in retrieved
        assert "expires_at" in retrieved

        # Test remove
        await storage.remove_token("resource1")
        assert await storage.get_token("resource1") is None

    @pytest.mark.asyncio
    async def test_memory_storage_nonexistent(self):
        """Test retrieving nonexistent token from MemoryTokenStorage."""
        storage = MemoryTokenStorage()
        result = await storage.get_token("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_secure_storage_encryption(self):
        """Test SecureTokenStorage encryption functionality."""
        encryption_key = b"test_encryption_key_32_bytes_min"
        storage = SecureTokenStorage(encryption_key)

        # Store token
        token_data = {"access_token": "secret_token", "client_id": "test"}
        await storage.store_token("resource1", token_data)

        # Retrieve and verify
        retrieved = await storage.get_token("resource1")
        assert retrieved is not None
        assert retrieved["access_token"] == "secret_token"
        assert retrieved["client_id"] == "test"

    @pytest.mark.asyncio
    async def test_secure_storage_decryption_failure(self):
        """Test SecureTokenStorage with decryption failure."""
        encryption_key = b"test_encryption_key_32_bytes_min"
        storage = SecureTokenStorage(encryption_key)

        # Manually store corrupted data
        storage._storage._tokens["resource1"] = {"data": "invalid_encrypted_data"}

        # Should return None on decryption failure
        result = await storage.get_token("resource1")
        assert result is None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_generate_key_pair(self):
        """Test RSA key pair generation."""
        private_pem, public_pem = generate_key_pair()

        assert "BEGIN PRIVATE KEY" in private_pem
        assert "END PRIVATE KEY" in private_pem
        assert "BEGIN PUBLIC KEY" in public_pem
        assert "END PUBLIC KEY" in public_pem

    def test_generate_key_pair_custom_size(self):
        """Test RSA key pair generation with custom size."""
        private_pem, public_pem = generate_key_pair(4096)

        assert "BEGIN PRIVATE KEY" in private_pem
        assert "BEGIN PUBLIC KEY" in public_pem

    def test_generate_key_pair_insufficient_size(self):
        """Test key generation with insufficient size raises error."""
        with pytest.raises(ValueError, match="Key size must be at least"):
            generate_key_pair(1024)

    def test_create_jwks(self):
        """Test JWKS creation from public key."""
        _, public_pem = generate_key_pair()
        jwks = create_jwks(public_pem, "test-key-id")

        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
        assert jwks["keys"][0]["kid"] == "test-key-id"
        assert jwks["keys"][0]["use"] == "sig"

    def test_create_jwks_auto_kid(self):
        """Test JWKS creation with auto-generated kid."""
        _, public_pem = generate_key_pair()
        jwks = create_jwks(public_pem)

        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
        assert "kid" in jwks["keys"][0]
        assert len(jwks["keys"][0]["kid"]) == 8  # SHA256 truncated to 8 chars

    @pytest.mark.asyncio
    async def test_validate_mcp_token_success(self):
        """Test successful MCP token validation."""
        mock_verifier = AsyncMock()
        mock_token = AccessToken(
            token="test_token",
            client_id="client",
            scopes=["read", "write"],
            expires_at=int(time.time()) + 3600
        )
        mock_verifier.verify_token.return_value = mock_token

        result = await validate_mcp_token("Bearer test_token", mock_verifier, ["read"])

        assert result == mock_token
        mock_verifier.verify_token.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_validate_mcp_token_invalid(self):
        """Test MCP token validation with invalid token."""
        mock_verifier = AsyncMock()
        mock_verifier.verify_token.return_value = None

        with pytest.raises(TokenValidationError, match="Invalid or expired token"):
            await validate_mcp_token("invalid_token", mock_verifier)

    @pytest.mark.asyncio
    async def test_validate_mcp_token_expired(self):
        """Test MCP token validation with expired token."""
        mock_verifier = AsyncMock()
        mock_token = AccessToken(
            token="test_token",
            client_id="client",
            scopes=["read"],
            expires_at=int(time.time()) - 3600
        )
        mock_verifier.verify_token.return_value = mock_token

        with pytest.raises(TokenValidationError, match="Token has expired"):
            await validate_mcp_token("test_token", mock_verifier)

    @pytest.mark.asyncio
    async def test_validate_mcp_token_missing_scopes(self):
        """Test MCP token validation with missing required scopes."""
        mock_verifier = AsyncMock()
        mock_token = AccessToken(
            token="test_token",
            client_id="client",
            scopes=["read"],
            expires_at=int(time.time()) + 3600
        )
        mock_verifier.verify_token.return_value = mock_token

        with pytest.raises(TokenValidationError, match="Missing required scopes: admin, write"):
            await validate_mcp_token("test_token", mock_verifier, ["read", "write", "admin"])