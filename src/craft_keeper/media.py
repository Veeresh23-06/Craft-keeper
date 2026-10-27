"""Media processing utilities: ffmpeg resolution, validation, audio, and frame extraction."""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("craft_keeper.media")

MAX_DURATION_SECONDS = 300  # 5 minutes
FRAME_SAMPLE_INTERVAL_SECONDS = 10.0


class MediaError(Exception):
    """Base exception for media processing errors."""
    pass


class FFmpegNotFoundError(MediaError):
    """Raised when neither system ffmpeg nor imageio-ffmpeg is available."""
    pass


class MediaValidationError(MediaError):
    """Raised when video duration or stream properties violate constraints."""
    pass


def get_ffmpeg_binary() -> str:
    """Resolve ffmpeg binary path: system PATH first, imageio-ffmpeg fallback.

    Returns:
        String path to the executable.

    Raises:
        FFmpegNotFoundError: If neither system ffmpeg nor imageio-ffmpeg is available.
    """
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except (ImportError, Exception) as e:
        logger.debug("imageio_ffmpeg resolution failed: %s", e)

    raise FFmpegNotFoundError(
        "FFmpeg is not installed or accessible. Please install FFmpeg and add it to your PATH, "
        "or ensure 'imageio-ffmpeg' is installed in your Python environment."
    )


def get_media_duration(video_path: str | Path) -> float:
    """Extract media duration in seconds by parsing 'ffmpeg -i <file>' stderr.

    Works without requiring ffprobe, making it compatible with imageio-ffmpeg.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    resolved_path = str(Path(video_path).resolve())

    # ffmpeg exits with code 1 or 0 when called without output file, but prints metadata to stderr
    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-i", resolved_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    combined_output = (proc.stderr or "") + (proc.stdout or "")

    # Look for Duration: 00:01:23.45 pattern
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", combined_output)
    if not match:
        raise MediaValidationError(
            f"Could not determine video duration for '{video_path}'. Ensure the file is a valid video."
        )

    hours, minutes, seconds = match.groups()
    duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return duration


def validate_media_duration(
    video_path: str | Path,
    max_duration_seconds: float = MAX_DURATION_SECONDS
) -> float:
    """Validate that video duration does not exceed the allowed threshold.

    Returns:
        The validated duration in seconds.
    """
    duration = get_media_duration(video_path)
    if duration > max_duration_seconds:
        raise MediaValidationError(
            f"Video duration ({duration:.1f}s) exceeds maximum allowed limit of {max_duration_seconds:.0f}s (5 minutes)."
        )
    return duration


def has_audio_stream(video_path: str | Path) -> bool:
    """Check if the media file contains at least one audio stream."""
    ffmpeg_exe = get_ffmpeg_binary()
    resolved_path = str(Path(video_path).resolve())

    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-i", resolved_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    combined = (proc.stderr or "") + (proc.stdout or "")
    return "Audio:" in combined


def extract_audio(
    video_path: str | Path,
    output_dir: Optional[str | Path] = None
) -> Optional[str]:
    """Extract mono 16 kHz WAV audio from video.

    Returns:
        Path to extracted WAV file, or None if the video has no audio stream.
    """
    if not has_audio_stream(video_path):
        logger.info("Video '%s' has no audio stream.", video_path)
        return None

    ffmpeg_exe = get_ffmpeg_binary()
    resolved_in = str(Path(video_path).resolve())

    target_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="craft_audio_"))
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / "audio_16k.wav"

    # Command: 16kHz, 1 channel (mono), 16-bit PCM WAV
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", resolved_in,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        str(out_path.resolve())
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if proc.returncode != 0:
        raise MediaError(f"Audio extraction failed: {proc.stderr}")

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise MediaError("Audio extraction produced an empty or missing file.")

    return str(out_path.resolve())


def extract_frames(
    video_path: str | Path,
    output_dir: Optional[str | Path] = None,
    interval_seconds: float = FRAME_SAMPLE_INTERVAL_SECONDS
) -> List[Dict[str, Any]]:
    """Sample visual frames from video approximately once every interval_seconds.

    Frames are scaled to a sensible resolution (max width 640px) while maintaining aspect ratio.
    If video duration is shorter than interval_seconds, at least 1 initial frame is extracted.

    Returns:
        List of dicts: [{"timestamp_seconds": float, "path": str, "frame_index": int}]
    """
    ffmpeg_exe = get_ffmpeg_binary()
    resolved_in = str(Path(video_path).resolve())
    duration = get_media_duration(video_path)

    target_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="craft_frames_"))
    target_dir.mkdir(parents=True, exist_ok=True)

    out_pattern = str((target_dir / "frame_%04d.jpg").resolve())

    # Select initial frame (t=0) and one frame every interval_seconds thereafter
    # Format to yuv420p to ensure standard mjpeg encoder compatibility
    vf_filter = (
        f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{interval_seconds})',"
        "scale='min(640,iw)':-2,"
        "format=yuv420p"
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", resolved_in,
        "-vf", vf_filter,
        "-vsync", "0",
        "-q:v", "3",
        out_pattern
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if proc.returncode != 0:
        raise MediaError(f"Frame extraction failed: {proc.stderr}")

    # Collect extracted frames sorted by filename
    extracted_files = sorted(target_dir.glob("frame_*.jpg"))

    # Fallback if somehow no frames were produced
    if not extracted_files:
        fallback_frame = target_dir / "frame_0001.jpg"
        fallback_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", resolved_in,
            "-vframes", "1",
            "-vf", "scale='min(640,iw)':-2,format=yuv420p",
            "-q:v", "3",
            str(fallback_frame.resolve())
        ]
        subprocess.run(fallback_cmd, capture_output=True, check=True)
        if fallback_frame.exists():
            extracted_files = [fallback_frame]

    frames: List[Dict[str, Any]] = []
    for idx, fpath in enumerate(extracted_files):
        # Timestamp: 0.0s for first frame, then idx * interval_seconds (clamped to duration)
        ts = min(idx * interval_seconds, duration)
        frames.append({
            "frame_index": idx + 1,
            "timestamp_seconds": round(ts, 1),
            "path": str(fpath.resolve())
        })

    return frames


def extract_media(
    video_path: str | Path,
    temp_dir: Optional[str | Path] = None
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """Extract both 16kHz mono audio and sampled visual frames.

    Returns:
        (audio_path, frames)
    """
    base_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="craft_media_"))
    base_dir.mkdir(parents=True, exist_ok=True)

    audio_dir = base_dir / "audio"
    frames_dir = base_dir / "frames"

    audio_path = extract_audio(video_path, output_dir=audio_dir)
    frames = extract_frames(video_path, output_dir=frames_dir)

    return audio_path, frames


def cleanup_temp_dir(path: Optional[str | Path]) -> None:
    """Safely delete temporary media directories and files."""
    if not path:
        return
    p = Path(path)
    if p.exists():
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        except Exception as e:
            logger.warning("Error cleaning up path '%s': %s", path, e)
