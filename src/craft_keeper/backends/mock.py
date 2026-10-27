"""Mock backend for Craft Keeper. Works offline with zero dependencies or GPU."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from craft_keeper.backends.base import ModelBackend


class MockBackend(ModelBackend):
    """Mock backend returning verified sample data from samples/."""

    name: str = "mock"

    def __init__(self, sample_path: Optional[str] = None):
        if sample_path:
            self.sample_path = Path(sample_path)
        else:
            # Locate sample_guide.json in repository samples/
            curr = Path(__file__).resolve()
            # Climb up until we find samples/ or reach root
            candidate = curr.parent.parent.parent.parent / "samples" / "sample_guide.json"
            if not candidate.exists():
                candidate = Path("samples") / "sample_guide.json"
            self.sample_path = candidate

    def health_check(self) -> Dict[str, Any]:
        """Health check verifying the sample guide file exists and is valid JSON."""
        if not self.sample_path.exists():
            return {
                "status": "error",
                "backend": self.name,
                "message": f"Sample file not found at {self.sample_path}"
            }
        try:
            with open(self.sample_path, "r", encoding="utf-8") as f:
                json.load(f)
            return {
                "status": "ok",
                "backend": self.name,
                "message": f"Mock backend ready. Sample guide loaded from {self.sample_path.name}"
            }
        except Exception as e:
            return {
                "status": "error",
                "backend": self.name,
                "message": f"Failed reading sample guide: {e}"
            }

    def generate(
        self,
        audio_path: Optional[str],
        frames: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return the pre-recorded sample guide populated with the given metadata."""
        if not self.sample_path.exists():
            raise FileNotFoundError(f"Mock sample guide file not found: {self.sample_path}")

        with open(self.sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Merge supplied user metadata while preserving sample fields
        guide_meta = data.get("metadata", {})
        if metadata.get("speaker"):
            guide_meta["speaker"] = metadata["speaker"]
        if metadata.get("place"):
            guide_meta["place"] = metadata["place"]
        if "consent_confirmed" in metadata:
            guide_meta["consent_confirmed"] = bool(metadata["consent_confirmed"])
        if metadata.get("source_filename"):
            guide_meta["source_filename"] = metadata["source_filename"]
        guide_meta["model_used"] = "mock"
        guide_meta["generated_at"] = datetime.now(timezone.utc).isoformat()
        data["metadata"] = guide_meta

        return data
