"""Tests for schema validation and mock backend integration."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from craft_keeper.backends.mock import MockBackend
from craft_keeper.export import export_to_json, export_to_markdown
from craft_keeper.pipeline import run_pipeline, InputValidationError
from craft_keeper.schema import CraftGuide


def test_sample_json_matches_schema():
    """Verify that samples/sample_guide.json conforms strictly to CraftGuide schema."""
    sample_path = Path("samples") / "sample_guide.json"
    assert sample_path.exists(), "sample_guide.json does not exist"
    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guide = CraftGuide.model_validate(data)
    assert guide.title == "Traditional Mysore Pak"
    assert guide.category == "recipe"
    assert len(guide.steps) == 6
    assert len(guide.uncertain_items) == 2
    assert guide.metadata.consent_confirmed is True


def test_schema_missing_required_fields_fails():
    """Verify pydantic raises ValidationError when required fields are missing."""
    invalid_data = {
        "title": "Incomplete Guide",
        # missing detected_language, category, summary, metadata
    }
    with pytest.raises(ValidationError):
        CraftGuide.model_validate(invalid_data)


def test_mock_backend_generation():
    """Verify MockBackend loads sample data and populates custom user metadata."""
    backend = MockBackend()
    health = backend.health_check()
    assert health["status"] == "ok"

    result = backend.generate(
        audio_path=None,
        frames=[],
        metadata={
            "speaker": "Asha",
            "place": "Bengaluru",
            "source_filename": "test.mp4",
            "consent_confirmed": True
        }
    )
    guide = CraftGuide.model_validate(result)
    assert guide.metadata.speaker == "Asha"
    assert guide.metadata.place == "Bengaluru"
    assert guide.metadata.source_filename == "test.mp4"
    assert guide.metadata.model_used == "mock"


def test_pipeline_with_mock_backend():
    """Verify the pipeline executes end-to-end with the mock backend."""
    backend = MockBackend()
    guide = run_pipeline(
        video_path=None,
        speaker="Test Artisan",
        place="Jaipur",
        consent_confirmed=True,
        backend=backend
    )
    assert isinstance(guide, CraftGuide)
    assert guide.metadata.speaker == "Test Artisan"
    assert guide.metadata.place == "Jaipur"


def test_pipeline_consent_validation():
    """Verify pipeline rejects execution if consent is not confirmed."""
    backend = MockBackend()
    # If video_path is provided with consent=False, validate_file_input must raise error
    with pytest.raises(InputValidationError):
        from craft_keeper.pipeline import validate_file_input
        validate_file_input("nonexistent.mp4", consent_confirmed=False)


def test_export_utilities():
    """Verify JSON and Markdown export functions."""
    backend = MockBackend()
    guide_dict = backend.generate(None, [], {"consent_confirmed": True})
    guide = CraftGuide.model_validate(guide_dict)

    # Test JSON export
    json_out = export_to_json(guide)
    assert "Traditional Mysore Pak" in json_out
    parsed = json.loads(json_out)
    assert parsed["category"] == "recipe"

    # Test Markdown export
    md_out = export_to_markdown(guide)
    assert "# Traditional Mysore Pak" in md_out
    assert "AI-generated draft" in md_out
    assert "Please Check These (Uncertain Items)" in md_out
    assert "Sieve the gram flour twice" in md_out
    assert "Spoken Tip:" in md_out
