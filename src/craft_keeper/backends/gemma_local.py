"""Local inference backend using faster-whisper and local Gemma via Ollama or Hugging Face."""

import gc
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from craft_keeper.backends.base import ModelBackend
from craft_keeper.prompts import CRAFT_KEEPER_SYSTEM_PROMPT, format_craft_prompt, format_retry_prompt

logger = logging.getLogger("craft_keeper.backends.gemma_local")

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e2b"


class GemmaLocalBackend(ModelBackend):
    """Local offline backend combining CPU-optimized Whisper transcription and local Gemma inference."""

    name: str = "whisper+gemma-local"

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        model_tag: Optional[str] = None,
        whisper_size: str = "base"
    ):
        self.ollama_host = (ollama_host or os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")
        self.model_tag = model_tag or os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.whisper_size = whisper_size

    def health_check(self) -> Dict[str, Any]:
        """Health check verifying Ollama server connectivity and model availability."""
        tags_url = f"{self.ollama_host}/api/tags"
        try:
            req = urllib.request.Request(tags_url, headers={"User-Agent": "CraftKeeper/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            models = [m.get("name", "") for m in data.get("models", [])]
            # Check if target model or tag is present
            has_model = any(self.model_tag in m for m in models)
            
            if has_model:
                return {
                    "status": "ok",
                    "backend": self.name,
                    "message": f"Ollama online with model '{self.model_tag}' ready."
                }
            else:
                available_str = ", ".join(models) if models else "none"
                return {
                    "status": "warning",
                    "backend": self.name,
                    "message": (
                        f"Ollama is running, but model '{self.model_tag}' is not downloaded yet. "
                        f"Available: [{available_str}]. Run 'ollama pull {self.model_tag}'."
                    )
                }
        except urllib.error.URLError:
            return {
                "status": "error",
                "backend": self.name,
                "message": (
                    f"Ollama server is not responding at {self.ollama_host}. "
                    "Start Ollama with 'ollama serve' or set CRAFT_BACKEND=mock for offline demo mode."
                )
            }
        except Exception as e:
            return {
                "status": "error",
                "backend": self.name,
                "message": f"Local backend health check error: {e}"
            }

    def _transcribe_audio(self, audio_path: str) -> Tuple[str, str]:
        """Transcribe audio using faster-whisper on CPU with INT8 quantization, then immediately free RAM."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper is not installed. Run 'pip install faster-whisper' to use local audio transcription."
            )

        logger.info("Loading Whisper '%s' model on CPU (int8)...", self.whisper_size)
        model = WhisperModel(self.whisper_size, device="cpu", compute_type="int8")
        try:
            segments, info = model.transcribe(audio_path, beam_size=1)
            formatted_segments = []
            full_text_parts = []
            for s in segments:
                ts_str = f"[{s.start:.1f}s -> {s.end:.1f}s]"
                formatted_segments.append(f"{ts_str} {s.text.strip()}")
                full_text_parts.append(s.text.strip())

            transcript_str = "\n".join(formatted_segments)
            detected_lang = info.language
            return transcript_str, detected_lang
        finally:
            # Force explicit garbage collection to reclaim memory for Gemma
            del model
            gc.collect()
            logger.info("Whisper model freed from memory.")

    def _query_ollama(self, prompt: str, timeout_seconds: int = 120) -> str:
        """Send prompt to local Ollama API."""
        generate_url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model_tag,
            "system": CRAFT_KEEPER_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            generate_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.ollama_host}: {e}. "
                "Ensure Ollama is running ('ollama serve') or switch to CRAFT_BACKEND=mock."
            ) from e

    def generate(
        self,
        audio_path: Optional[str],
        frames: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute local pipeline: Whisper STT -> Memory cleanup -> Gemma structuring."""
        transcript_text = "No audio track detected in source video."
        detected_language = metadata.get("language") or "Unknown"

        if audio_path and os.path.exists(audio_path):
            logger.info("Beginning audio transcription with Whisper...")
            transcript_text, detected_language = self._transcribe_audio(audio_path)
            logger.info("Transcription complete. Language: %s", detected_language)

        # Build grounded prompt
        context_block = f"VERIFIED SPOKEN AUDIO TRANSCRIPT (WITH TIMESTAMPS):\n{transcript_text}\n"
        user_prompt = format_craft_prompt(
            speaker=metadata.get("knowledge_holder") or metadata.get("speaker"),
            place=metadata.get("place"),
            language=detected_language,
            filename=metadata.get("source_filename", "video.mp4"),
            frame_timestamps=f"{len(frames)} frames available (marked unused in CPU mode)",
            additional_context=context_block,
            model_name=self.name
        )

        logger.info("Sending transcript to local model '%s' via Ollama...", self.model_tag)
        raw_response = self._query_ollama(user_prompt)

        # Parse JSON
        parsed = self._extract_json(raw_response)

        # Attach accurate execution provenance
        meta = parsed.get("metadata", {})
        meta["model_used"] = self.name
        meta["frames_used"] = 0
        meta["frame_mode"] = "transcript_only"
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
        logger.info("Retrying local Gemma inference with validation feedback...")
        raw_response = self._query_ollama(retry_prompt)
        parsed = self._extract_json(raw_response)
        parsed["metadata"] = raw_output.get("metadata", {})
        return parsed

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely parse JSON from raw LLM output, extracting from markdown fences if present."""
        clean = text.strip()
        # Remove markdown code fences if wrapped
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
        if fence_match:
            clean = fence_match.group(1)
        else:
            # Look for outer braces
            brace_match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if brace_match:
                clean = brace_match.group(1)

        try:
            return json.loads(clean)
        except json.JSONDecodeError as err:
            raise ValueError(f"Model output could not be parsed as JSON: {err}\nRaw text:\n{text}") from err


Tuple_Transcript = Any
