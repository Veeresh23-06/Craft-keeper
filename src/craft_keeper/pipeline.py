"""Core processing pipeline for Craft Keeper."""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import ValidationError

from craft_keeper.backends import get_backend
from craft_keeper.backends.base import ModelBackend
from craft_keeper.media import extract_media, validate_media_duration, cleanup_temp_dir
from craft_keeper.schema import CraftGuide
import tempfile

logger = logging.getLogger("craft_keeper.pipeline")

# Limits specified in product requirements (default: 1 GB / 1024 MB and 30 minutes)
MAX_FILE_SIZE_BYTES = int(os.environ.get("MAX_FILE_SIZE_BYTES", 1024 * 1024 * 1024))  # 1 GB
MAX_DURATION_SECONDS = int(os.environ.get("MAX_DURATION_SECONDS", 1800))  # 30 minutes
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}


class PipelineError(Exception):
    """Base exception for pipeline validation and processing failures."""
    pass


class InputValidationError(PipelineError):
    """Raised when an uploaded file violates format, size, or consent constraints."""
    pass


def validate_file_input(
    video_path: str | Path,
    consent_confirmed: bool
) -> Path:
    """Validate user input constraints.

    Rules:
    - Consent checkbox must be confirmed.
    - File must exist and have extension .mp4, .mov, or .webm.
    - File size must not exceed 100 MB.
    """
    if not consent_confirmed:
        raise InputValidationError(
            "Consent confirmation is required: You must confirm you have permission to use this video."
        )

    path = Path(video_path)
    if not path.is_file():
        raise InputValidationError(f"File not found: {video_path}")

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InputValidationError(
            f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        mb = size / (1024 * 1024)
        limit_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise InputValidationError(
            f"File size ({mb:.1f} MB) exceeds maximum allowed limit of {limit_mb:.0f} MB."
        )

    return path


def run_pipeline(
    video_path: Optional[str | Path],
    knowledge_holder: Optional[str] = None,
    community: Optional[str] = None,
    place: Optional[str] = None,
    language: Optional[str] = None,
    occasion_or_context: Optional[str] = None,
    source_video_license_or_permission: Optional[str] = None,
    consent_confirmed: bool = False,
    anonymity_requested: bool = False,
    backend: Optional[ModelBackend] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    speaker: Optional[str] = None
) -> CraftGuide:
    """Execute the end-to-end Craft Keeper extraction pipeline.

    1. Validates file and consent.
    2. Extracts audio (16kHz WAV) and frames (~1 every 10s) using ffmpeg.
    3. Calls backend.generate(...).
    4. Validates output with Pydantic, retrying once if schema fails.
    5. Returns validated CraftGuide.
    """
    if progress_callback:
        progress_callback("Validating input video and permissions...", 0.1)

    filename = "sample.mp4"
    audio_path = None
    frames: List[Dict[str, Any]] = []
    temp_dir = None

    # Handle backward-compatibility for speaker argument
    effective_holder = knowledge_holder or speaker or "Anonymous"
    if anonymity_requested:
        effective_holder = "Anonymous"

    try:
        if video_path:
            valid_path = validate_file_input(video_path, consent_confirmed)
            filename = valid_path.name

            if progress_callback:
                progress_callback("Checking video duration and audio tracks...", 0.2)
            validate_media_duration(valid_path, max_duration_seconds=MAX_DURATION_SECONDS)

            if progress_callback:
                progress_callback("Extracting 16kHz audio and sampled visual frames...", 0.4)
            temp_dir = tempfile.mkdtemp(prefix="craft_media_")
            audio_path, frames = extract_media(valid_path, temp_dir=temp_dir)

        if not backend:
            backend = get_backend()

        metadata = {
            "knowledge_holder": effective_holder,
            "speaker": effective_holder,
            "community": community,
            "place": place,
            "language": language or "Auto-detect",
            "occasion_or_context": occasion_or_context,
            "source_video_license_or_permission": source_video_license_or_permission or "Personal permission granted by speaker",
            "consent_confirmed": consent_confirmed,
            "anonymity_requested": anonymity_requested,
            "source_filename": filename
        }

        if progress_callback:
            progress_callback(f"Analyzing content with backend '{backend.name}'...", 0.7)

        # First attempt
        raw_output = backend.generate(audio_path=audio_path, frames=frames, metadata=metadata)

        if progress_callback:
            progress_callback("Validating generated guide structure...", 0.9)

        # Validate output schema
        try:
            guide = CraftGuide.model_validate(raw_output)
            if progress_callback:
                progress_callback("Guide generated successfully!", 1.0)
            return guide
        except ValidationError as first_err:
            logger.warning("First schema validation failed: %s. Attempting retry...", first_err)

            # Retry once if backend supports correction or if raw_output has errors
            if hasattr(backend, "retry_generate"):
                try:
                    corrected_output = backend.retry_generate(first_err, raw_output, metadata)
                    guide = CraftGuide.model_validate(corrected_output)
                    if progress_callback:
                        progress_callback("Guide generated successfully after correction!", 1.0)
                    return guide
                except Exception as retry_err:
                    raise PipelineError(
                        f"Schema validation failed after retry: {retry_err}\nRaw output: {raw_output}"
                    ) from retry_err
            else:
                raise PipelineError(
                    f"Generated guide failed schema validation: {first_err}\nRaw output: {raw_output}"
                ) from first_err
    finally:
        if temp_dir:
            cleanup_temp_dir(temp_dir)
