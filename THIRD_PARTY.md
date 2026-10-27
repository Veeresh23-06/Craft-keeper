# Third-Party Open-Source Software & Model Attributions

Craft Keeper is built entirely upon open-source software and open-weights models. Below is the comprehensive bill of materials and licenses.

---

## 1. Machine Learning Models & Frameworks

### Google Gemma 4 (E2B / E4B / 31B)
- **Role:** Open-weights foundation models for multimodal structuring and instruction following.
- **Developer:** Google DeepMind / Google AI
- **License:** **Apache 2.0** [VERIFIED]
- **Verification Source:** [Google Gemma Terms & License](https://ai.google.dev/gemma/terms) | [Hugging Face Gemma 4 Model Card](https://huggingface.co/google/gemma-4-E2B-it)
- **Notes:** Unlike Gemma 1 & 2 (which had custom Google Terms of Use), Gemma 4 is distributed under standard permissive Apache-2.0.

### Faster-Whisper (OpenAI Whisper via CTranslate2)
- **Role:** Local Automatic Speech Recognition (ASR) with millisecond timestamp extraction.
- **Developers:** SYSTRAN / OpenAI
- **License:** **MIT License** [VERIFIED]
- **Verification Source:** [faster-whisper GitHub Repository](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE)

---

## 2. Media Processing

### FFmpeg
- **Role:** Audio track extraction (16 kHz mono WAV) and video keyframe sampling.
- **Developers:** FFmpeg Team
- **License:** **LGPL v2.1+ / GPL v2+** (depending on build configuration) [VERIFIED]
- **Verification Source:** [FFmpeg Official Legal & Licensing](https://ffmpeg.org/legal.html)

### imageio-ffmpeg
- **Role:** Standalone bundled FFmpeg binary fallback for cross-platform execution without global PATH configuration.
- **Developers:** ImageIO Team
- **License:** **BSD 2-Clause License** [VERIFIED]
- **Verification Source:** [imageio-ffmpeg PyPI / GitHub](https://github.com/imageio/imageio-ffmpeg/blob/master/LICENSE)

---

## 3. Web UI & Application Framework

### Gradio
- **Role:** Web interface, interactive components (dataframes, sliders, markdown blocks), and audio/video input handlers.
- **Developer:** Hugging Face, Inc.
- **License:** **Apache 2.0** [VERIFIED]
- **Verification Source:** [Gradio GitHub Repository](https://github.com/gradio-app/gradio/blob/main/LICENSE)

### Pydantic (v2)
- **Role:** Data validation, strict JSON schema enforcement, and serialization for CraftGuide data structures.
- **Developer:** Samuel Colvin & Pydantic Contributors
- **License:** **MIT License** [VERIFIED]
- **Verification Source:** [Pydantic GitHub Repository](https://github.com/pydantic/pydantic/blob/main/LICENSE)

### python-dotenv
- **Role:** Secure environment variable management (.env parsing for API keys and configurations).
- **Developer:** Saurabh Kumar & Contributors
- **License:** **BSD 3-Clause License** [VERIFIED]
- **Verification Source:** [python-dotenv GitHub Repository](https://github.com/theskumar/python-dotenv/blob/master/LICENSE)

### pytest
- **Role:** Automated testing framework for unit, integration, and media pipeline tests.
- **Developers:** pytest Development Team
- **License:** **MIT License** [VERIFIED]
- **Verification Source:** [pytest GitHub Repository](https://github.com/pytest-dev/pytest/blob/main/LICENSE)

### psutil
- **Role:** Process memory profiling and hardware utilization monitoring.
- **Developers:** Giampaolo Rodola & psutil contributors
- **License:** **BSD 3-Clause License** [VERIFIED]
- **Verification Source:** [psutil GitHub Repository](https://github.com/giampaolo/psutil/blob/master/LICENSE)

### audioop-lts
- **Role:** Compatibility shim providing the legacy audioop module on Python 3.13+.
- **Developers:** Joshua Root & Contributors
- **License:** **Python Software Foundation (PSF) License 2.0** [VERIFIED]
- **Verification Source:** [audioop-lts GitHub Repository](https://github.com/joshuaprince/audioop-lts/blob/main/LICENSE)
