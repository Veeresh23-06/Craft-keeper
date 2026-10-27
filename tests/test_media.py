"""Unit and integration tests for media validation, ffmpeg resolution, audio/frame extraction."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import pytest

from craft_keeper.media import (
    FFmpegNotFoundError,
    MediaValidationError,
    cleanup_temp_dir,
    extract_audio,
    extract_frames,
    extract_media,
    get_ffmpeg_binary,
    get_media_duration,
    has_audio_stream,
    validate_media_duration,
)
from craft_keeper.pipeline import (
    InputValidationError,
    validate_file_input,
    run_pipeline,
    MAX_FILE_SIZE_BYTES
)
from craft_keeper.backends.mock import MockBackend


@pytest.fixture(scope="session")
def ffmpeg_bin():
    """Ensure ffmpeg executable is available for test suite."""
    return get_ffmpeg_binary()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory that is cleaned up after test."""
    td = tempfile.mkdtemp(prefix="craft_test_workspace_")
    yield Path(td)
    shutil.rmtree(td, ignore_errors=True)


def create_synthetic_video(
    output_path: Path,
    duration_seconds: int = 2,
    has_audio: bool = True
) -> Path:
    """Dynamically generate a tiny test video using ffmpeg without committing video files."""
    ffmpeg_exe = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration_seconds}:size=320x240:rate=10"
    ]
    if has_audio:
        cmd.extend([
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration_seconds}"
        ])
        cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
    else:
        cmd.extend(["-c:v", "libx264", "-an"])

    cmd.append(str(output_path.resolve()))
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Synthetic video creation failed: {res.stderr}"
    assert output_path.exists()
    return output_path


def test_ffmpeg_resolution_and_fallback(monkeypatch):
    """Test get_ffmpeg_binary locates either system or imageio-ffmpeg binary, or raises clear error."""
    bin_path = get_ffmpeg_binary()
    assert os.path.isfile(bin_path)

    # Test error when neither is available
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    import imageio_ffmpeg
    monkeypatch.setattr(imageio_ffmpeg, "get_ffmpeg_exe", lambda: None)
    with pytest.raises(FFmpegNotFoundError) as exc_info:
        get_ffmpeg_binary()
    assert "FFmpeg is not installed or accessible" in str(exc_info.value)


def test_file_format_and_consent_validation(temp_workspace):
    """Verify input file format and consent validation rules."""
    valid_file = temp_workspace / "valid_sample.mp4"
    valid_file.write_bytes(b"dummy mp4 data")

    # Consent missing
    with pytest.raises(InputValidationError, match="Consent confirmation is required"):
        validate_file_input(valid_file, consent_confirmed=False)

    # Valid file and consent
    res = validate_file_input(valid_file, consent_confirmed=True)
    assert res == valid_file

    # Unsupported format
    invalid_ext = temp_workspace / "sample.avi"
    invalid_ext.write_bytes(b"dummy avi data")
    with pytest.raises(InputValidationError, match="Unsupported file format"):
        validate_file_input(invalid_ext, consent_confirmed=True)

    # Non-existent file
    with pytest.raises(InputValidationError, match="File not found"):
        validate_file_input(temp_workspace / "nonexistent.webm", consent_confirmed=True)


def test_file_size_validation(temp_workspace, monkeypatch):
    """Verify files larger than allowed limit are rejected."""
    large_file = temp_workspace / "huge_video.mp4"
    large_file.write_bytes(b"small content")

    orig_stat = Path.stat

    def fake_stat(self, *args, **kwargs):
        if self == large_file:
            class FakeStat:
                st_size = MAX_FILE_SIZE_BYTES + (10 * 1024 * 1024)
                st_mode = 0o100644
            return FakeStat()
        return orig_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", fake_stat)

    with pytest.raises(InputValidationError, match="exceeds maximum allowed limit"):
        validate_file_input(large_file, consent_confirmed=True)


def test_media_duration_and_limit(temp_workspace):
    """Verify duration parsing and max duration threshold enforcement."""
    short_vid = temp_workspace / "short.mp4"
    create_synthetic_video(short_vid, duration_seconds=2)

    dur = get_media_duration(short_vid)
    assert 1.8 <= dur <= 2.5
    validated = validate_media_duration(short_vid, max_duration_seconds=300)
    assert validated == dur

    # Verify exceeding duration threshold raises MediaValidationError
    with pytest.raises(MediaValidationError, match="exceeds maximum allowed limit"):
        validate_media_duration(short_vid, max_duration_seconds=1.0)


def test_audio_and_frame_extraction(temp_workspace):
    """Verify audio and frame extraction on a synthetic video."""
    video = temp_workspace / "test_craft.mp4"
    create_synthetic_video(video, duration_seconds=3, has_audio=True)

    assert has_audio_stream(video) is True

    # Test audio extraction
    audio_dir = temp_workspace / "audio_out"
    audio_path = extract_audio(video, output_dir=audio_dir)
    assert audio_path is not None
    assert Path(audio_path).exists()
    assert audio_path.endswith(".wav")
    assert Path(audio_path).stat().st_size > 0

    # Test frame extraction
    frames_dir = temp_workspace / "frames_out"
    frames = extract_frames(video, output_dir=frames_dir, interval_seconds=1.0)
    assert len(frames) >= 1
    for frame in frames:
        assert Path(frame["path"]).exists()
        assert "timestamp_seconds" in frame
        assert frame["timestamp_seconds"] >= 0.0


def test_audio_extraction_video_without_audio(temp_workspace):
    """Verify silent video returns None for audio without crashing."""
    video_silent = temp_workspace / "silent.mp4"
    create_synthetic_video(video_silent, duration_seconds=1, has_audio=False)

    assert has_audio_stream(video_silent) is False
    audio_path = extract_audio(video_silent)
    assert audio_path is None


def test_windows_paths_with_spaces(temp_workspace):
    """Verify video extraction works when directory and filenames contain spaces."""
    dir_with_spaces = temp_workspace / "Folder With Spaces And Symbols #1"
    video_with_spaces = dir_with_spaces / "My Traditional Craft Demo.mp4"
    create_synthetic_video(video_with_spaces, duration_seconds=2, has_audio=True)

    out_dir = dir_with_spaces / "Extracted Outputs"
    audio_path, frames = extract_media(video_with_spaces, temp_dir=out_dir)

    assert audio_path is not None
    assert Path(audio_path).exists()
    assert len(frames) >= 1
    assert Path(frames[0]["path"]).exists()


def test_temp_cleanup(temp_workspace):
    """Verify cleanup_temp_dir deletes directories and files cleanly."""
    temp_folder = temp_workspace / "dir_to_delete"
    temp_folder.mkdir()
    (temp_folder / "file.txt").write_text("temporary")
    assert temp_folder.exists()

    cleanup_temp_dir(temp_folder)
    assert not temp_folder.exists()


def test_end_to_end_pipeline_with_real_video(temp_workspace):
    """Verify the entire pipeline runs with an actual video file and mock backend."""
    video = temp_workspace / "pipeline_test.mp4"
    create_synthetic_video(video, duration_seconds=2, has_audio=True)

    mock_backend = MockBackend()
    guide = run_pipeline(
        video_path=video,
        speaker="Master Carpenter",
        place="Kyoto",
        language="Japanese",
        consent_confirmed=True,
        backend=mock_backend
    )
    assert "Mysuru Paak" in guide.title  # from sample
    assert guide.metadata.knowledge_holder == "Master Carpenter"
    assert guide.metadata.place == "Kyoto"
    assert guide.metadata.source_filename == "pipeline_test.mp4"
    assert guide.metadata.consent_confirmed is True
