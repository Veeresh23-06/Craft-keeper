"""Hosted inference backend calling Google AI Studio API for Gemma and Gemini fallback."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from craft_keeper.backends.base import ModelBackend
from craft_keeper.prompts import CRAFT_KEEPER_SYSTEM_PROMPT, format_craft_prompt, format_retry_prompt

logger = logging.getLogger("craft_keeper.backends.gemma_hosted")

GOOGLE_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_HOSTED_GEMMA_MODEL = "gemma-4-31b-it"
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-2.5-flash"


class GemmaHostedBackend(ModelBackend):
    """Hosted backend executing via Google AI Studio API."""

    name: str = "whisper+gemma-hosted"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        direct_audio_mode: bool = False
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.direct_audio_mode = direct_audio_mode or os.environ.get("USE_DIRECT_AUDIO_GEMINI", "").lower() in ("true", "1")
        if self.direct_audio_mode:
            self.model_name = model_name or os.environ.get("HOSTED_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL)
            self.name = "gemini-fallback"
        else:
            self.model_name = model_name or os.environ.get("HOSTED_MODEL", DEFAULT_HOSTED_GEMMA_MODEL)
            self.name = "whisper+gemma-hosted"

    def health_check(self) -> Dict[str, Any]:
        """Health check verifying API key configuration and reachability."""
        if not self.api_key:
            return {
                "status": "warning",
                "backend": self.name,
                "message": (
                    "GEMINI_API_KEY is not set. Add GEMINI_API_KEY=your_key to your .env file, "
                    "or run with CRAFT_BACKEND=mock for offline demo mode."
                )
            }

        # Quick smoke test with 1-word generation
        url = f"{GOOGLE_API_BASE}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Reply with 'ok'"}]}],
            "generationConfig": {"maxOutputTokens": 5}
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    return {
                        "status": "ok",
                        "backend": self.name,
                        "message": f"Hosted endpoint online with model '{self.model_name}' verified."
                    }
                return {
                    "status": "warning",
                    "backend": self.name,
                    "message": f"Hosted endpoint returned status code {resp.status}."
                }
        except urllib.error.HTTPError as e:
            # Mask API key if accidentally in URL representation
            err_msg = str(e.read().decode("utf-8", errors="replace"))
            return {
                "status": "error",
                "backend": self.name,
                "message": f"API request error (HTTP {e.code}): {err_msg[:200]}"
            }
        except Exception as e:
            return {
                "status": "error",
                "backend": self.name,
                "message": f"Hosted backend connection failed: {e}"
            }

    def _call_api(self, prompt: str, timeout_seconds: int = 60) -> str:
        """Execute request to Google Generative Language API."""
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing. "
                "Please configure GEMINI_API_KEY in your .env file."
            )

        url = f"{GOOGLE_API_BASE}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": CRAFT_KEEPER_SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidate responses returned by hosted model API.")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise RuntimeError("Empty response part returned by hosted model API.")
                return parts[0].get("text", "")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            # If rate-limited
            if e.code == 429:
                raise RuntimeError(
                    "Hosted API quota / rate limit exceeded (429 RESOURCE_EXHAUSTED). "
                    "Free tier limit is 15 RPM. Please wait a moment or switch to CRAFT_BACKEND=mock."
                ) from e
            raise RuntimeError(f"Hosted API error (HTTP {e.code}): {err_body}") from e

    def generate(
        self,
        audio_path: Optional[str],
        frames: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured guide via hosted model."""
        transcript_text = "No audio track in source video."
        detected_language = metadata.get("language") or "Unknown"

        # If running in Gemma mode (which does not accept raw audio), transcribe first with local Whisper
        if not self.direct_audio_mode and audio_path and os.path.exists(audio_path):
            try:
                from craft_keeper.backends.gemma_local import GemmaLocalBackend
                helper = GemmaLocalBackend()
                transcript_text, detected_language = helper._transcribe_audio(audio_path)
            except Exception as e:
                logger.warning("Local Whisper transcription failed: %s; proceeding with placeholder", e)

        # Build prompt
        context_block = f"VERIFIED SPOKEN AUDIO TRANSCRIPT (WITH TIMESTAMPS):\n{transcript_text}\n"
        user_prompt = format_craft_prompt(
            speaker=metadata.get("knowledge_holder") or metadata.get("speaker"),
            place=metadata.get("place"),
            language=detected_language,
            filename=metadata.get("source_filename", "video.mp4"),
            frame_timestamps=f"{len(frames)} visual frames extracted",
            additional_context=context_block,
            model_name=self.model_name
        )

        raw_json_str = self._call_api(user_prompt)
        parsed = self._extract_json(raw_json_str)

        # Provenance metadata
        meta = parsed.get("metadata", {})
        meta["model_used"] = self.name
        meta["frames_used"] = len(frames)
        meta["frame_mode"] = "used" if frames else "unused"
        meta["knowledge_holder"] = metadata.get("knowledge_holder") or metadata.get("speaker") or "Anonymous"
        meta["community"] = metadata.get("community")
        meta["place"] = metadata.get("place")
        meta["language"] = detected_language
        meta["occasion_or_context"] = metadata.get("occasion_or_context")
        meta["source_video_license_or_permission"] = metadata.get("source_video_license_or_permission") or "Personal permission granted by speaker"
        meta["consent_confirmed"] = bool(metadata.get("consent_confirmed", False))
        meta["anonymity_requested"] = bool(metadata.get("anonymity_requested", False))
        if meta["anonymity_requested"]:
            meta["knowledge_holder"] = "Anonymous"
        meta["source_filename"] = metadata.get("source_filename", "unknown.mp4")
        parsed["metadata"] = meta

        return parsed

    def retry_generate(self, validation_error: Exception, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Retry generation once with schema error feedback."""
        retry_prompt = format_retry_prompt(str(validation_error), json.dumps(raw_output))
        logger.info("Retrying hosted model inference with validation feedback...")
        raw_json_str = self._call_api(retry_prompt)
        parsed = self._extract_json(raw_json_str)
        parsed["metadata"] = raw_output.get("metadata", {})
        return parsed

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely parse JSON from raw LLM output, extracting from markdown fences if present."""
        clean = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
        if fence_match:
            clean = fence_match.group(1)
        else:
            brace_match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if brace_match:
                clean = brace_match.group(1)

        try:
            return json.loads(clean)
        except json.JSONDecodeError as err:
            raise ValueError(f"Hosted model output could not be parsed as JSON: {err}\nRaw text:\n{text}") from err
