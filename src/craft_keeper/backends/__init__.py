"""Backends module with factory get_backend()."""

import os
from craft_keeper.backends.base import ModelBackend
from craft_keeper.backends.mock import MockBackend


def get_backend(backend_name: str | None = None) -> ModelBackend:
    """Instantiate and return the configured ModelBackend.

    Defaults to reading CRAFT_BACKEND environment variable, falling back to 'mock'.
    Allowed values:
      - 'mock': offline sample data (default)
      - 'gemma_local': local faster-whisper + local Gemma (Ollama/GGUF)
      - 'gemma_hosted': hosted Gemma-4 via Google AI Studio API
      - 'gemini_fallback': hosted Gemini direct multimodal fallback
    """
    selected = (backend_name or os.environ.get("CRAFT_BACKEND", "mock")).lower().strip()

    if selected == "mock":
        return MockBackend()
    elif selected in ("gemma_local", "whisper+gemma-local"):
        from craft_keeper.backends.gemma_local import GemmaLocalBackend
        return GemmaLocalBackend()
    elif selected in ("gemma_hosted", "whisper+gemma-hosted"):
        from craft_keeper.backends.gemma_hosted import GemmaHostedBackend
        return GemmaHostedBackend()
    elif selected in ("gemini_fallback", "gemini-fallback"):
        from craft_keeper.backends.gemma_hosted import GemmaHostedBackend
        return GemmaHostedBackend(direct_audio_mode=True)
    else:
        raise ValueError(
            f"Unknown backend '{selected}'. Allowed values: 'mock', 'gemma_local', 'gemma_hosted', 'gemini_fallback'."
        )
