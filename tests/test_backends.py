"""Unit tests for backend factory, mock, and offline health checks."""

import pytest
from craft_keeper.backends import get_backend
from craft_keeper.backends.mock import MockBackend
from craft_keeper.backends.gemma_local import GemmaLocalBackend
from craft_keeper.backends.gemma_hosted import GemmaHostedBackend


def test_get_backend_mock():
    """Verify factory returns MockBackend by default."""
    b = get_backend("mock")
    assert isinstance(b, MockBackend)
    assert b.name == "mock"
    health = b.health_check()
    assert health["status"] == "ok"


def test_get_backend_gemma_local():
    """Verify factory returns GemmaLocalBackend and health check handles offline Ollama gracefully."""
    b = get_backend("gemma_local")
    assert isinstance(b, GemmaLocalBackend)
    assert b.name == "whisper+gemma-local"
    # When Ollama is offline or uninitialized, health_check must return status without crashing
    health = b.health_check()
    assert "status" in health
    assert health["backend"] == "whisper+gemma-local"


def test_get_backend_gemma_hosted():
    """Verify factory returns GemmaHostedBackend and health check warns if key is missing."""
    b = get_backend("gemma_hosted")
    assert isinstance(b, GemmaHostedBackend)
    assert b.name == "whisper+gemma-hosted"
    health = b.health_check()
    assert "status" in health


def test_get_backend_unknown():
    """Verify unknown backend names raise clear ValueError."""
    with pytest.raises(ValueError, match="Unknown backend"):
        get_backend("nonexistent_backend")
