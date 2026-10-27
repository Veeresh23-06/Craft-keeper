"""Backend abstractions and factory for Craft Keeper."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelBackend(ABC):
    """Abstract base class for Craft Keeper model inference backends."""

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        audio_path: Optional[str],
        frames: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured guide JSON from audio, frames, and user metadata.

        Args:
            audio_path: Path to extracted WAV audio file, or None if no audio.
            frames: List of dicts, e.g. [{"timestamp_seconds": float, "path": str}].
            metadata: User-provided metadata dict (speaker, place, filename, consent).

        Returns:
            Dict matching the CraftGuide schema.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform a quick health check or smoke test.

        Returns:
            Dict with status ("ok" or "error"), backend name, and detail message.
        """
        pass
