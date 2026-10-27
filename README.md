# 🏺 Craft Keeper

> **Preserving living audiovisual heritage by turning short video demonstrations of traditional crafts and heirloom recipes into structured, verified how-to guides.**

[![CI Test Suite](https://github.com/owner/craft-keeper/actions/workflows/ci.yml/badge.svg)](https://github.com/owner/craft-keeper)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-brightgreen.svg)](requirements.txt)
[![Gemma 4](https://img.shields.io/badge/Model-Gemma_4-red.svg)](THIRD_PARTY.md)

---

## ⚡ 20-Second Pitch for Hackathon Judges

Thousands of traditional recipes, weaving techniques, and artisanal skills exist only in spoken memory and the hands of elders—captured on family phone videos, but never written down. **Craft Keeper** transforms a 2–3 minute video into a clean, editable guide: extracting ingredients and tools, timestamped steps with the artisan's own spoken tips, and an explicit **"Please Check These"** review box highlighting details the AI was unsure about.

```
[ Video Demonstration (.mp4) ]
              │
              ▼
   FFmpeg (Audio & Frames)
              │
              ▼
Speech-to-Text (Whisper) ──► Structuring (Gemma 4) ──► Pydantic v2 Schema
                                                              │
                                                              ▼
               [ Editable Heritage Guide + Attribution Export ]
```

---

## 📸 Demo Preview

```
+----------------------------------------------------------------------------------------------------+
| 🏺 Craft Keeper - Preserving Living Audiovisual Heritage                                          |
| Active Backend: mock | ✓ Ready (Mock backend ready. Sample heritage guide loaded)                 |
| 🔒 Privacy: Your video stays on this computer. Local processing without network access.           |
| ⚠️ AI-Generated Draft: Review and verify all measurements and steps before sharing.                |
+-------------------------------------------------+--------------------------------------------------+
| 1. Upload Video & Cultural Provenance           | 3. Structured Guide (Review & Edit)             |
|    - Video: mysore_pak_demo.mp4                 |    Title: Traditional Mysuru Paak                |
|    - Knowledge Holder: Ajji                     |    Knowledge shared by: Ajji, Mysuru, Karnataka  |
|    - [x] Keep anonymous                         |                                                  |
|    - Community: South Indian Confectionery      |    🔍 Please Check These (Uncertain Items):      |
|    - Place: Mysuru, Karnataka                   |    - Cardamom addition: mentioned but not shown  |
|    - Language: Kannada                          |                                                  |
| 2. Consent                                      |    Ingredients:                                  |
|    [x] I have permission to use this video,     |    - Besan (Gram flour): 1 cup (Sieved twice)    |
|        and the person in it agrees.             |    - Pure Desi Ghee: 2 cups (Warm)               |
|                                                 |    - Sugar: 2 cups (One-string consistency)      |
|    [ Generate Guide ]   [ Load Sample Result ]  |                                                  |
|                                                 |    [ ⬇️ Download JSON ]  [ ⬇️ Download Markdown ]  |
+-------------------------------------------------+--------------------------------------------------+
```

---

## 🚀 Try It in 2 Minutes (Mock Mode — Zero Setup & Zero Internet)

No API key, GPU, or Ollama download is needed to evaluate Craft Keeper:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/craft-keeper.git
cd craft-keeper

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.venv\Scripts\Activate.ps1       # On Windows PowerShell

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Run the app (defaults to mock backend)
python app.py
```

Open `http://127.0.0.1:7860` and click **"Load Sample Result (Demo Mode)"** to inspect an interactive heritage guide loaded instantly.

---

## 🛠️ Complete Installation & System Requirements

### Prerequisites
- Python 3.11, 3.12, or 3.13
- FFmpeg (System `PATH` preferred; if not present, Craft Keeper automatically falls back to bundled `imageio-ffmpeg` binary)

### Optional: Installing System FFmpeg
If you prefer a global system FFmpeg installation:
- **Windows**: `winget install Gyan.FFmpeg.Essentials` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt update && sudo apt install -y ffmpeg`

---

## 🎛️ How to Switch Backends

Craft Keeper supports three primary execution adapters via the `CRAFT_BACKEND` environment variable:

```bash
# Option A: Offline Sample Mode (Default — No GPU/Network needed)
CRAFT_BACKEND=mock python app.py

# Option B: Local Private Mode (Whisper STT + Local Gemma 4 E2B via Ollama)
CRAFT_BACKEND=gemma_local python app.py

# Option C: Hosted Gemma 4 Mode (Google AI Studio hosted gemma-4-31b-it)
CRAFT_BACKEND=gemma_hosted python app.py

# Option D: Direct Audio Gemini Fallback Mode
CRAFT_BACKEND=gemini_fallback python app.py
```

### Environment Variables (.env)
Create your `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Key variables:
- `CRAFT_BACKEND`: `mock` | `gemma_local` | `gemma_hosted` | `gemini_fallback`
- `GEMINI_API_KEY`: Required only for `gemma_hosted` or `gemini_fallback` (Get free at [aistudio.google.com](https://aistudio.google.com/))
- `OLLAMA_HOST`: URL of local Ollama server (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL`: Target local model tag (default: `gemma4:e2b`)

---

## 💻 Hardware Notes for Running Gemma Locally

We profiled memory consumption on an entry-level test machine (Windows 11, Intel HD Graphics 610, 8.0 GB RAM total):
- **Sequential Execution**: Whisper speech-to-text transcribes the audio on CPU (INT8). It uses **~151 MB peak RAM** and is immediately freed (`del model; gc.collect()`) before local Gemma loads.
- **Model Sizing**:
  - `gemma4:e2b` (~1.5–3.5 GB quantized): **Runs on 8 GB RAM machines.**
  - `gemma4:e4b` (~2.8–8 GB): Requires at least 12–16 GB RAM for smooth execution.
  - `gemma 12B / 31B`: Requires 16–32 GB RAM or dedicated NVIDIA VRAM; use `gemma_hosted` on laptops.

---

## 📜 Model License & Verification
- **Gemma 4 License**: **Apache 2.0 License** [VERIFIED]
- **Verification Source**: Verified from official Google DeepMind documentation and the [Google AI for Developers Gemma Terms](https://ai.google.dev/gemma/terms). Unlike Gemma 1 and Gemma 2 which had custom Google Terms of Use and commercial revenue restrictions, Gemma 4 is distributed under standard permissive Apache 2.0.

---

## ⚠️ Known Limitations & Responsible AI Notice
- **Regional Dialect Accuracy (Untested)**: Speech-to-text accuracy on regional Indian languages (Kannada, Tamil, Telugu, Hindi) and accented English has **not been formally benchmarked** on this project. In our tests on culinary terms, Whisper `base` transcribed *"kadai"* as *"cadet"* and *"sieved"* as *"sived"*.
- **Mandatory Human Review**: AI output can omit steps or misinterpret quantities. A human practitioner or archivist must review every draft before sharing.
- **Acoustic Noise**: Workshop clatter and kitchen noise can reduce transcription quality.
- See full documentation in [docs/RESPONSIBLE_AI.md](docs/RESPONSIBLE_AI.md).

---

## 🔒 Privacy Notice: What Happens to Uploaded Videos?
- **Local Mode (`mock` or `gemma_local`)**: Your video, audio track, and keyframes **stay 100% on your computer**. Nothing is transmitted over the network.
- **Hosted Cloud Mode (`gemma_hosted`)**: Transcripts and sampled frames are transmitted over HTTPS to Google AI Studio. Under the **Google AI Studio Free Tier terms**, submitted prompts, responses, and media may be reviewed by human annotators and used to train Google products. If processing confidential cultural knowledge, use `gemma_local` or a paid Google Cloud Vertex AI account with data logging disabled.

---

## 🧪 Running Automated Tests

Run the comprehensive 20-test automated suite (validating schemas, media extraction, Windows paths with spaces, duration thresholds, and backend health checks):

```bash
$env:PYTHONPATH="src"          # On Windows PowerShell
export PYTHONPATH=src          # On Linux/macOS
pytest tests/ -v
```

---

## 🤝 Contributing
Contributions are warmly welcomed! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for step-by-step guides on:
- Adding a new spoken language
- Adding a new backend adapter
- Extending cultural heritage fields
- Picking up a task from [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 📄 License
This project is licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.
All third-party tools and models are documented in [THIRD_PARTY.md](THIRD_PARTY.md).
