# Craft Keeper Demo Checklist (Hackathon Preparation)

Follow this checklist 30 minutes before your live hackathon presentation or judging session to guarantee a smooth, flawless demonstration.

---

## 1. Environment & Hardware Preparation
- [ ] **Close Background Applications**: On an 8 GB RAM laptop, close memory-heavy apps (browser tabs, Slack, Spotify, IDE extensions) to keep at least 2 GB of free physical memory available for Python and Whisper.
- [ ] **Verify Virtual Environment**: Ensure `.venv` is active:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- [ ] **Run Test Suite**: Confirm all 20 tests pass:
  ```powershell
  $env:PYTHONPATH="src"
  .venv\Scripts\python.exe -m pytest tests/ -v
  ```

---

## 2. Default Demo Mode Verification (Zero-Fail Safety Net)
- [ ] **Verify Default Mock Backend**: Launch the app:
  ```powershell
  $env:PYTHONPATH="src"
  .venv\Scripts\python.exe app.py
  ```
- [ ] Open `http://127.0.0.1:7860` in your browser.
- [ ] Click **"Load Sample Result (Demo Mode)"**:
  - Confirms instant loading of the sample Mysuru Paak heritage guide.
  - Verifies that ingredients table, steps table, credit line, and "Please check these" uncertain items populate immediately.
- [ ] Click **"⬇️ Download Markdown"** and verify that a structured `.md` file is generated with the credit line:
  `Knowledge shared by: Sample Artisan (Maintainer Demonstration), South Indian Traditional Confectionery, Mysuru, Karnataka`.

---

## 3. Real Inference Demo Preparation (If Demonstrating Real Video)
- [ ] **Verify Video Clip**: Ensure `samples/demo_craft_1min.mp4` is present (69 seconds, ~1 MB, with clean spoken audio).
- [ ] **If using Hosted Gemma (`CRAFT_BACKEND=gemma_hosted`)**:
  - Verify `GEMINI_API_KEY` is present in `.env`.
  - Check that the UI top badge displays: `Active Backend: whisper+gemma-hosted | ✓ Ready`.
  - Perform one test run on the 1-minute video before the judges arrive.
- [ ] **If using Local Gemma (`CRAFT_BACKEND=gemma_local`)**:
  - Start Ollama server in a background terminal: `ollama serve`.
  - Ensure model is pulled: `ollama pull gemma4:e2b` (or your local model).
  - Note: Local transcription takes ~33s on CPU; tell the audience what is happening during the progress bar!

---

## 4. Emergency Backup
- [ ] **Screen Recording Backup**: Keep a 30-second screen recording video of the full workflow on your desktop ready to play if conference Wi-Fi drops or a model quota error occurs.
- [ ] **Quick Reset**: If the UI hangs or network disconnects, simply refresh the browser tab or click **"Load Sample Result (Demo Mode)"**. The demo never depends on external internet!
