"""Backends module with factory get_backend()."""

import os
from craft_keeper.backends.base import ModelBackend
from craft_keeper.backends.mock import MockBackend


def get_backend(backend_name: str | None = None) -> ModelBackend:
    """Instantiate and return the configured ModelBackend.

    Defaults to reading CRAFT_BACKEND environment variable, falling back to 'mock'.
    """
    selected = backend_name or os.environ.get("CRAFT_BACKEND", "mock").lower()

    if selected == "mock":
        return MockBackend()
    elif selected == "gemma_local":
        from craft_keeper.backends.gemma_local import GemmaLocalBackend
        return GemmaLocalBackend()
    elif selected == "gemma_hosted":
        from craft_keeper.backends.gemma_hosted import GemmaHostedBackend
        return GemmaHostedBackend()
    else:
        raise ValueError(
            f"Unknown backend '{selected}'. Allowed values: 'mock', 'gemma_local', 'gemma_hosted'."
        )
