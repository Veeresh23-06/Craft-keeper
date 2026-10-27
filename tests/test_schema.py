"""Tests for schema validation, heritage fields, and mock backend integration."""

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
    assert "Mysuru Paak" in guide.title
    assert guide.category == "recipe"
    assert len(guide.steps) == 6
    assert len(guide.uncertain_items) == 2
    assert guide.metadata.consent_confirmed is True
    assert guide.metadata.knowledge_holder != ""
    assert guide.metadata.community == "South Indian Traditional Confectionery"
    assert guide.metadata.place == "Mysuru, Karnataka"


def test_schema_missing_required_fields_fails():
    """Verify pydantic raises ValidationError when required fields are missing."""
    invalid_data = {
        "title": "Incomplete Guide",
        # missing detected_language, category, summary, metadata
    }
    with pytest.raises(ValidationError):
        CraftGuide.model_validate(invalid_data)


def test_mock_backend_generation_and_heritage_fields():
    """Verify MockBackend loads sample data and populates custom heritage metadata."""
    backend = MockBackend()
    health = backend.health_check()
    assert health["status"] == "ok"

    result = backend.generate(
        audio_path=None,
        frames=[],
        metadata={
            "knowledge_holder": "Asha Amma",
            "community": "Karnataka Culinary Guild",
            "place": "Bengaluru",
            "occasion_or_context": "Family festive harvest",
            "source_filename": "test.mp4",
            "consent_confirmed": True,
            "anonymity_requested": False
        }
    )
    guide = CraftGuide.model_validate(result)
    assert guide.metadata.knowledge_holder == "Asha Amma"
    assert guide.metadata.community == "Karnataka Culinary Guild"
    assert guide.metadata.place == "Bengaluru"
    assert guide.metadata.occasion_or_context == "Family festive harvest"
    assert guide.metadata.source_filename == "test.mp4"
    assert guide.metadata.model_used == "mock"


def test_anonymity_preference():
    """Verify knowledge holder name is replaced with 'Anonymous' when anonymity is requested."""
    backend = MockBackend()
    result = backend.generate(
        audio_path=None,
        frames=[],
        metadata={
            "knowledge_holder": "Private Elder",
            "anonymity_requested": True,
            "consent_confirmed": True
        }
    )
    guide = CraftGuide.model_validate(result)
    assert guide.metadata.knowledge_holder == "Anonymous"
    assert guide.metadata.anonymity_requested is True


def test_pipeline_with_mock_backend():
    """Verify the pipeline executes end-to-end with the mock backend and heritage arguments."""
    backend = MockBackend()
    guide = run_pipeline(
        video_path=None,
        knowledge_holder="Master Weaver Chen",
        community="Bamboo Craft Guild",
        place="Kyoto",
        consent_confirmed=True,
        backend=backend
    )
    assert isinstance(guide, CraftGuide)
    assert guide.metadata.knowledge_holder == "Master Weaver Chen"
    assert guide.metadata.community == "Bamboo Craft Guild"
    assert guide.metadata.place == "Kyoto"


def test_pipeline_consent_validation():
    """Verify pipeline rejects execution if consent is not confirmed."""
    with pytest.raises(InputValidationError):
        from craft_keeper.pipeline import validate_file_input
        validate_file_input("nonexistent.mp4", consent_confirmed=False)


def test_export_utilities_with_credit_line():
    """Verify JSON and Markdown export functions include theme credit lines and AI provenance."""
    backend = MockBackend()
    guide_dict = backend.generate(
        None,
        [],
        {
            "knowledge_holder": "Ajji",
            "community": "Mysuru Heritage Artisans",
            "place": "Karnataka",
            "consent_confirmed": True
        }
    )
    guide = CraftGuide.model_validate(guide_dict)

    # Test JSON export
    json_out = export_to_json(guide)
    assert "Mysuru Paak" in json_out
    parsed = json.loads(json_out)
    assert parsed["category"] == "recipe"
    assert parsed["metadata"]["community"] == "Mysuru Heritage Artisans"

    # Test Markdown export
    md_out = export_to_markdown(guide)
    assert "# Traditional Mysuru Paak" in md_out
    assert "AI-generated draft" in md_out
    assert "**Knowledge shared by:** Ajji, Mysuru Heritage Artisans, Karnataka" in md_out
    assert "## 🔍 Please Check These (Uncertain Items)" in md_out
    assert "### How This Was Made (AI Provenance)" in md_out
