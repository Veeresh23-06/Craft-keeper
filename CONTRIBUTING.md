# Contributing to Craft Keeper

Thank you for your interest in contributing to Craft Keeper! We are committed to building an open, respectful, and reliable tool for safeguarding living audiovisual heritage.

---

## 1. Running the Test Suite
Before submitting any changes, verify that the complete test suite passes:

```bash
# Set PYTHONPATH to include src/
export PYTHONPATH=src          # On Linux/macOS
$env:PYTHONPATH="src"          # On Windows PowerShell

# Run pytest
pytest tests/ -v
```

All 20+ tests should pass, covering media extraction, duration limit checks, format validation, Pydantic schemas, and backend health checks.

---

## 2. How to Add a New Language
Craft Keeper supports multilingual craft and recipe preservation. To add support or prompt tuning for a new language (e.g., Kannada, Marathi, Quechua, Yoruba):

1. **Update Language Choices in UI**:
   Open `app.py` and add the language name to the `language_input` dropdown list:
   ```python
   choices=["Auto-detect", "Kannada", "Hindi", "Tamil", "Marathi", "YourLanguage", ...]
   ```
2. **Tune Prompt Glossing Rules**:
   Open `src/craft_keeper/prompts.py` to add specific transliteration or cultural glossing instructions for your language's dialects.
3. **Add a Multilingual Test**:
   In `tests/test_schema.py`, add a test case validating that non-English terms in `ingredients_or_materials[].note` are preserved alongside an English gloss.

---

## 3. How to Add a New Backend Adapter
Craft Keeper uses a clean plugin architecture where all inference providers inherit from `ModelBackend`.

To add a new backend (e.g., vLLM, llama.cpp server, Groq, or AWS Bedrock):
1. **Create an Adapter File**:
   Create `src/craft_keeper/backends/my_new_backend.py`:
   ```python
   from typing import Any, Dict, List, Optional
   from craft_keeper.backends.base import ModelBackend

   class MyNewBackend(ModelBackend):
       name = "my-new-backend"

       def health_check(self) -> Dict[str, Any]:
           # Return {"status": "ok" | "error" | "warning", "backend": self.name, "message": "..."}
           pass

       def generate(self, audio_path: Optional[str], frames: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
           # Return a dictionary adhering to CraftGuide schema
           pass
   ```
2. **Register the Backend**:
   In `src/craft_keeper/backends/__init__.py`, update `get_backend()` to instantiate your backend when `CRAFT_BACKEND=my_new_backend`.
3. **Add a Health Check Test**:
   In `tests/test_backends.py`, add a test verifying your backend initializes and handles offline status gracefully.

---

## 4. How to Add New Heritage Fields
Traditional crafts often involve specialized cultural categories (e.g., sacred vs secular, seasonal harvesting rules, heirloom seed varieties).

To extend the schema with new heritage fields:
1. **Update Pydantic Schema**:
   Open `src/craft_keeper/schema.py` and add the new field to `GuideMetadata` with a default value and documentation string.
2. **Update Prompts**:
   Open `src/craft_keeper/prompts.py` and add the new field to `TARGET_JSON_SCHEMA` so models extract it accurately.
3. **Update Markdown Export**:
   Open `src/craft_keeper/export.py` to format the new field in human-readable output.
4. **Update UI**:
   In `app.py`, add an input widget in Section 2 ("Knowledge Holder & Cultural Heritage") and wire it into the `handle_generate` handler.

---

## 5. Development Principles & Code Style
- **Zero Secrets in Code**: Never commit API keys or personal credentials. Use `.env` exclusively.
- **Maintain Test Integrity**: Tests must create synthetic video test fixtures dynamically using FFmpeg rather than committing binary video files.
- **Preserve Grounding**: We never allow hallucinated or invented steps in model prompts.
