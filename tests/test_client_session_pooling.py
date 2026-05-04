"""Tests for NetBoxApiClient session pooling and lifecycle."""

import asyncio

import pytest

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config


@pytest.fixture
def config():
    return Config(
        base_url="https://netbox.example.com",
        token_secret="test-token",
    )


class TestSessionPooling:
    """Test session creation and reuse."""

    @pytest.mark.asyncio
    async def test_single_request_creates_one_session(self, config):
        """A single request should create exactly one session."""
        client = NetBoxApiClient(config)
        try:
            assert client._session is None

            session1 = await client._get_session()
            assert client._session is not None
            assert not client._session.closed

            session2 = await client._get_session()
            assert session1 is session2
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_concurrent_get_session_no_race(self, config):
        """Concurrent calls to _get_session should not create duplicate sessions."""
        client = NetBoxApiClient(config)
        try:
            tasks = [client._get_session() for _ in range(10)]
            sessions = await asyncio.gather(*tasks)

            first_session = sessions[0]
            for session in sessions:
                assert session is first_session

            assert client._session is first_session
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self, config):
        """Using client as context manager should close session on exit."""
        async with NetBoxApiClient(config) as client:
            session = await client._get_session()
            assert session is not None
            assert not session.closed

        assert client._session is None

    @pytest.mark.asyncio
    async def test_nested_context_manager(self, config):
        """Nested context managers should not close session prematurely."""
        client = NetBoxApiClient(config)
        try:
            async with client:
                session = await client._get_session()
                assert not session.closed

                async with client:
                    assert not session.closed

                assert not session.closed

            assert client._session is None
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, config):
        """Calling close multiple times should not raise."""
        client = NetBoxApiClient(config)
        await client._get_session()

        await client.close()
        await client.close()

        assert client._session is None

    @pytest.mark.asyncio
    async def test_session_recreated_after_close(self, config):
        """After close, a new session should be created on next request."""
        client = NetBoxApiClient(config)
        try:
            session1 = await client._get_session()
            await client.close()

            session2 = await client._get_session()
            assert session2 is not session1
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_loop_detection(self, config):
        """Using client from different loops should create new session."""
        client = NetBoxApiClient(config)

        async def use_in_loop1():
            session1 = await client._get_session()
            loop1_id = id(asyncio.get_running_loop())
            return session1, loop1_id

        session1, loop1_id = await use_in_loop1()

        client._session_loop_id = 0

        await client._get_session()
        assert client._session is not None

        await client.close()

    @pytest.mark.asyncio
    async def test_session_active_property(self, config):
        """session_active property should correctly report session state."""
        client = NetBoxApiClient(config)
        try:
            assert not client.session_active

            await client._get_session()
            assert client.session_active

            await client.close()
            assert not client.session_active
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_reset_session(self, config):
        """reset_session should close session and allow recreation."""
        client = NetBoxApiClient(config)
        try:
            session1 = await client._get_session()
            assert client.session_active

            await client.reset_session()
            assert not client.session_active
            assert client._session is None

            session2 = await client._get_session()
            assert session2 is not session1
            assert client.session_active
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_lock_created_lazily(self, config):
        """Lock should be created lazily when first needed."""
        client = NetBoxApiClient(config)
        try:
            assert client._session_lock is None

            lock1 = client._get_lock()
            assert client._session_lock is not None

            lock2 = client._get_lock()
            assert lock1 is lock2
        finally:
            await client.close()
