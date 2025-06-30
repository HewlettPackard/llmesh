#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration test suite for the Tool API service.

This test suite verifies:
- That tool calling works correctly with the temperature_finder function.
- That the service can handle various valid and extreme coordinates.
- That the service can be configured with SSL certificates and still function correctly.

Run with: pytest tests/platform/test_tool_api_integration.py -vv
"""

import os
import pytest
import re
import tempfile
import asyncio
from src.platform.tool_api.main import temperature_finder


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_finder_returns_valid_response():
    """Test that temperature_finder returns a properly formatted temperature string."""
    # Test with real coordinates (New York City)
    result = await temperature_finder(latitude=40.7128, longitude=-74.0060)

    # Verify the response format
    assert isinstance(result, str)
    assert "The current temperature is" in result
    assert "°C" in result
    print(result)

    # Extract temperature value to ensure it's a valid number
    temp_match = re.search(r'([-+]?\d+(?:\.\d+)?)\s*°C', result)
    assert temp_match is not None, "Temperature value not found in response"

    temperature = float(temp_match.group(1))
    # Reasonable temperature range check (-50 to +50 Celsius)
    assert -50 <= temperature <= 50, f"Temperature {temperature}°C seems unrealistic"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_finder_different_locations():
    """Test temperature_finder with different valid locations."""
    locations = [
        (40.7128, -74.0060),   # New York
        (51.5074, -0.1278),    # London
        (-33.8688, 151.2093),  # Sydney
    ]

    for lat, lon in locations:
        result = await temperature_finder(latitude=lat, longitude=lon)
        assert isinstance(result, str)
        print(result)
        assert "The current temperature is" in result
        assert "°C" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_finder_extreme_coordinates():
    """Test temperature_finder with extreme but valid coordinates."""
    # Test North Pole area
    result = await temperature_finder(latitude=89.9, longitude=0.0)
    assert isinstance(result, str)
    assert "The current temperature is" in result

    # Test South Pole area
    result = await temperature_finder(latitude=-89.9, longitude=0.0)
    assert isinstance(result, str)
    print(result)
    assert "The current temperature is" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temperature_finder_equator():
    """Test temperature_finder at the equator."""
    # Test equator location (Quito, Ecuador)
    result = await temperature_finder(latitude=0.0, longitude=-78.5)
    assert isinstance(result, str)
    print(result)
    assert "The current temperature is" in result
    assert "°C" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_api_with_ssl_certificate():
    """Test that tool_api service works with SSL certificates enabled."""
    # Create temporary SSL certificate files
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_file = os.path.join(temp_dir, "test_cert.pem")
        key_file = os.path.join(temp_dir, "test_key.pem")

        # Generate self-signed certificate
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        import ipaddress

        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256())

        # Write private key
        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Test the MCP server with SSL configuration
        from src.platform.mcp.main import PlatformRegistry

        # Create a test registry instance
        test_registry = PlatformRegistry()

        # Configure the tool with SSL
        ssl_config = {
            "host": "localhost",
            "port": 5558,  # Use a different port for testing
            "ssh_cert": {
                "certfile": cert_file,
                "keyfile": key_file
            }
        }

        # Register the tool with SSL configuration
        await test_registry.register_platform_tool(
            name="test_ssl_tool",
            func=temperature_finder,
            config=ssl_config,
            description="Temperature finder with SSL for testing"
        )

        # Verify the SSL configuration was processed correctly
        registry_entry = test_registry.registry.servers["test_ssl_tool"]
        assert registry_entry.config["ssl_certfile"] == cert_file
        assert registry_entry.config["ssl_keyfile"] == key_file
        assert "ssh_cert" not in registry_entry.config  # Original key should be removed

        # Start the server using the registry which will pass SSL parameters
        await test_registry.registry.start_server("test_ssl_tool")

        # Give the server time to start
        await asyncio.sleep(2)

        # Get the server instance for cleanup later
        server = registry_entry.server

        # Verify the uvicorn server has SSL configured
        assert server._uvicorn_server is not None, "Uvicorn server should be initialized"
        uvicorn_config = server._uvicorn_server.config
        assert uvicorn_config.ssl_certfile == cert_file
        assert uvicorn_config.ssl_keyfile == key_file

        try:
            # Test HTTPS connection to the health endpoint
            import aiohttp
            import ssl

            # Create SSL context that accepts self-signed certificates
            # Note: We disable verification because it's a self-signed cert for testing
            # In production, you would use proper certificate verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Accept self-signed cert for testing

            async with aiohttp.ClientSession() as session:
                # Make HTTPS request to health endpoint
                async with session.get(
                    'https://localhost:5558/health',
                    ssl=ssl_context
                ) as response:
                    assert response.status == 200
                    # Verify we're actually using HTTPS
                    assert response.url.scheme == 'https'

                    data = await response.json()
                    assert data["status"] == "healthy"
                    assert data["server"] == "test_ssl_tool"
                    assert data["transport"] == "streamable"

                # Also verify that HTTP (non-SSL) connections fail
                try:
                    async with session.get('http://localhost:5558/health') as response:
                        # This should not succeed - if it does, SSL is not enforced
                        assert False, "HTTP request should fail when SSL is configured"
                except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError):
                    # Expected - connection should be refused or disconnected for non-SSL
                    pass

            # Also verify the tool function still works
            result = await temperature_finder(latitude=40.7128, longitude=-74.0060)
            assert isinstance(result, str)
            assert "The current temperature is" in result
            assert "°C" in result

        finally:
            # Stop the server properly
            if server and server._running:
                await server.stop()

            # Clean up registry entry
            if "test_ssl_tool" in test_registry.registry.servers:
                del test_registry.registry.servers["test_ssl_tool"]

            # Give asyncio event loop time to clean up
            await asyncio.sleep(0.5)

            # Clean up any remaining tasks from our test
            tasks = asyncio.all_tasks()
            current_task = asyncio.current_task()
            pending_tasks = [t for t in tasks if t != current_task and not t.done()]

            # Log what tasks are still pending
            if pending_tasks:
                for task in pending_tasks:
                    # Only cancel tasks that are related to our test
                    if "uvicorn" in str(task) or "lifespan" in str(task):
                        task.cancel()

                # Wait briefly for cancellation
                await asyncio.sleep(0.1)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, "-vv", "-m", "integration"])
