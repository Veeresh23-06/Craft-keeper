# Craft Keeper Roadmap & Good-First-Issues

This document tracks upcoming planned improvements and beginner-friendly tasks for hackathon contributors.

---

## Good-First-Issue Tasks (Open for Contributions)

### 1. `good-first-issue`: Add Audio Waveform Preview to the Gradio UI
- **Context:** Currently, the upload area accepts video files, but does not display a visual waveform or audio player of the extracted 16 kHz audio track.
- **Task:** In `app.py`, add a `gr.Audio` component below the video upload that automatically renders the extracted audio stream, allowing users to listen to specific speech snippets directly.
- **Skills:** Python, Gradio.

### 2. `good-first-issue`: Printable Recipe Card & PDF Export
- **Context:** Traditional knowledge holders and community kitchens often need physical printouts of the verified guide.
- **Task:** Create an export utility in `src/craft_keeper/export.py` that formats the verified guide into a clean HTML/PDF printable index card with large legible fonts, checkbox steps, and artisan credits.
- **Skills:** Python, HTML/CSS.

### 3. `good-first-issue`: Regional Culinary & Craft Terminology Glossary Builder
- **Context:** When a video contains non-English regional terms (e.g. *kadai*, *oru kambi padam*, *besan*), the model extracts them in the `note` field.
- **Task:** Automatically aggregate all non-English terms and their English glosses into a dedicated "Regional Glossary" table at the bottom of the exported Markdown document.
- **Skills:** Python, Pydantic, Markdown.

---

## Future Architecture Milestones
- **Whisper Fine-Tuning on Indic Dialects:** Benchmark and fine-tune open Whisper models on regional Indian culinary demonstration corpora to improve Kannada and Hindi speech recognition accuracy.
- **Local Vision Token Optimization:** Support quantized multimodal vision projection for local Gemma E2B to analyze keyframes on CPU with low token budgets (70-140 visual tokens).
- **Offline Desktop Packaging:** Package Craft Keeper with PyInstaller and bundled FFmpeg for one-click offline execution by community fieldworkers.
