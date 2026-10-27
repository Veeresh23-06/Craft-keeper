# Craft Keeper Architecture & Pipeline Design

Craft Keeper transforms short video demonstrations of traditional crafts and recipes into structured, verifiable how-to guides. It is architected for strict grounding, privacy preservation, and offline resilience.

---

## High-Level Pipeline Diagram

```
+-----------------------------------------------------------------------------------+
|                              1. User Input & Ethics                               |
|   - Video Upload (.mp4 / .mov / .webm, <= 100 MB, <= 5 minutes)                   |
|   - Heritage Metadata: Knowledge Holder, Community, Place, Occasion, Permission   |
|   - Consent Checkbox: Mandatory confirmation & Optional Anonymity toggle          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        2. Media Processing Engine (FFmpeg)                         |
|   - Binary Resolution: System PATH ffmpeg -> bundled imageio-ffmpeg fallback       |
|   - Duration Extraction: Regex parsing of `ffmpeg -i` stderr (no ffprobe needed)   |
|   - Audio Track: Extract 16 kHz mono 16-bit PCM WAV (`audio_16k.wav`)              |
|   - Frame Sampling: 1 frame every 10s starting at t=0 (`select` filter, max 640px) |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           3. Backend Inference Dispatch                            |
|                                                                                   |
|   [Mode A: mock]           -> Instant offline verified sample (samples/)          |
|                                                                                   |
|   [Mode B: gemma_local]    -> faster-whisper (CPU, int8) transcribes audio        |
|                               -> explicit garbage collection frees RAM            |
|                               -> prompt sent to local Gemma (Ollama: gemma4:e2b)  |
|                                                                                   |
|   [Mode C: gemma_hosted]   -> Whisper STT transcript + visual frames sent via     |
|                               Google AI Studio API to `gemma-4-31b-it`            |
|                                                                                   |
|   [Mode D: gemini_fallback]-> Direct raw multimodal audio sent to `gemini-2.5`    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       4. Pydantic v2 Schema & Retry Loop                          |
|   - Validates JSON output strictly against CraftGuide schema                      |
|   - If invalid: Automatic 1x retry prompt passing exact validation error to LLM    |
|   - If still invalid: Raises clear error with raw output preserved                |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        5. Interactive Review & Stewardship                        |
|   - AI-Generated Draft Review Banner                                              |
|   - Highlighted "Please Check These" section for model uncertainties              |
|   - Editable Dataframe tables for ingredients and numbered steps                  |
|   - How This Was Made (AI Provenance) panel showing path, models, and frame status|
|   - Clean 1-click Export: Formatted JSON and Markdown with credit attribution      |
+-----------------------------------------------------------------------------------+
```

---

## Plain-English Explanation of Each Stage

### 1. User Input & Cultural Consent
Users submit a short video recording along with cultural metadata: the artisan or elder's name, cultural community, geographic origin, and context (e.g. holiday tradition, heirloom practice). To honor personal privacy and cultural agency, users can check *"Keep knowledge holder anonymous"*, and generation is gated behind an explicit consent checkbox verifying permission.

### 2. Media Extraction (Subprocess FFmpeg)
The app checks if FFmpeg is installed globally in the system `PATH`. If not, it falls back seamlessly to the bundled `imageio-ffmpeg` static binary.
- Because `imageio-ffmpeg` contains only the `ffmpeg` executable and no `ffprobe`, video duration is extracted by running `ffmpeg -hide_banner -i` and parsing the `Duration:` header with regular expressions.
- The audio track is converted to 16 kHz mono WAV, which is the standard format required by speech recognition encoders.
- Visual frames are sampled at approximately 1 frame every 10 seconds starting from $t=0$, scaled to 640px maximum width.
- Extracted files are stored in an isolated temporary directory and automatically deleted when processing completes.

### 3. Model Backends & Memory Management
The user selects a backend via the `CRAFT_BACKEND` environment variable:
- **`mock`**: Instantly loads a verified sample guide from `samples/sample_guide.json`. Requires no model, GPU, or internet connection.
- **`gemma_local`**: Designed to run safely on entry-level hardware (such as laptops with 8 GB RAM and no dedicated GPU). It transcribes the 16 kHz audio using `faster-whisper` with INT8 quantization on CPU (~150 MB peak RAM increase). It immediately frees the Whisper model from memory (`del model; gc.collect()`), and then passes the timestamped transcript to local Gemma (`gemma4:e2b` via Ollama) to structure the guide.
- **`gemma_hosted`**: Sends the timestamped transcript and visual frames to Google AI Studio's hosted `gemma-4-31b-it` model via HTTPS. Keys are loaded exclusively from `.env`.
- **`gemini_fallback`**: Used if direct raw audio streaming is requested on Google AI Studio without local Whisper transcription.

### 4. Pydantic Schema Validation & Retry
The model's output is parsed into a Pydantic v2 `CraftGuide` model. If any required field is missing or malformed, the pipeline automatically sends a single retry prompt containing the exact Pydantic validation error back to the model.

### 5. Review & Export
The generated guide is displayed in a clean Gradio web interface. A visible banner reminds the user that AI drafts must be verified by a human before sharing. Items the model was unsure about are highlighted in a dedicated *"Please Check These"* review box. Ingredients and steps can be edited directly in interactive tables, and the finished guide can be downloaded as JSON or Markdown with complete credit attribution lines.
