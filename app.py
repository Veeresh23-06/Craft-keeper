"""Craft Keeper - AI-Powered Preservation of Traditional Crafts & Recipes.

Single-file Gradio entry point.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure src is on Python module search path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
import gradio as gr

from craft_keeper.backends import get_backend
from craft_keeper.export import export_to_json, export_to_markdown
from craft_keeper.pipeline import run_pipeline
from craft_keeper.schema import CraftGuide, IngredientOrMaterial, Step, UncertainItem

# Load environment configuration
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("craft_keeper.app")

# Determine active backend and perform initial health check
BACKEND_NAME = os.environ.get("CRAFT_BACKEND", "mock").lower()
logger.info("Initializing Craft Keeper with active backend: '%s'", BACKEND_NAME)

try:
    active_backend = get_backend(BACKEND_NAME)
    health = active_backend.health_check()
    logger.info("Backend health check result: %s", health)
except Exception as e:
    logger.error("Failed to initialize backend '%s': %s", BACKEND_NAME, e)
    health = {"status": "error", "backend": BACKEND_NAME, "message": str(e)}


def get_backend_status_badge() -> str:
    """Generate HTML badge representing active backend health."""
    if health.get("status") == "ok":
        return f"""
        <div style="background-color: #e6f4ea; border-left: 4px solid #34a853; padding: 10px; border-radius: 4px; margin-bottom: 12px;">
            <strong>Backend Active:</strong> <code>{BACKEND_NAME}</code> &nbsp;|&nbsp; 
            <span style="color: #137333;">✓ Ready ({health.get('message', 'Online')})</span>
        </div>
        """
    else:
        return f"""
        <div style="background-color: #fce8e6; border-left: 4px solid #d93025; padding: 10px; border-radius: 4px; margin-bottom: 12px;">
            <strong>Backend Notice:</strong> <code>{BACKEND_NAME}</code> is unreachable or misconfigured. &nbsp;|&nbsp; 
            <span style="color: #c5221f;">⚠️ {health.get('message', 'Initialization error')}</span>
            <br/><small>You can still click <em>'Load Sample Result'</em> or run in <code>mock</code> mode.</small>
        </div>
        """


def guide_to_ui_components(guide: CraftGuide) -> Tuple[
    str, str, str, str, List[List[str]], List[List[Any]], str, str, str, str
]:
    """Unpack a CraftGuide instance into state and UI fields."""
    # Format ingredients for Dataframe
    ing_rows = []
    for ing in guide.ingredients_or_materials:
        ing_rows.append([ing.name, ing.quantity or "", ing.note or ""])

    # Format steps for Dataframe
    step_rows = []
    for step in guide.steps:
        step_rows.append([
            step.number,
            f"{step.approx_start_seconds:.1f}s" if step.approx_start_seconds is not None else "",
            step.instruction,
            step.spoken_tip or ""
        ])

    # Format tips and safety
    tips_text = "\n".join(f"- {t}" for t in guide.tips)
    safety_text = "\n".join(f"- {s}" for s in guide.safety_notes)

    # Format uncertain items
    if guide.uncertain_items:
        uncertain_md = "### 🔍 Items to Verify with Speaker / Source\n"
        for item in guide.uncertain_items:
            uncertain_md += f"- **{item.what}**: {item.reason}\n"
    else:
        uncertain_md = "*No uncertain items flagged by the model.*"

    raw_json_str = export_to_json(guide)

    return (
        guide.title,
        f"{guide.category.title()} | Language: {guide.detected_language}",
        guide.summary,
        uncertain_md,
        ing_rows,
        step_rows,
        tips_text,
        safety_text,
        raw_json_str,
        "Guide loaded successfully."
    )


def handle_generate(
    video_file,
    speaker: str,
    place: str,
    language: str,
    consent: bool,
    progress=gr.Progress()
):
    """Handler for the Generate button."""
    if not consent:
        raise gr.Error("Consent required: Please check the consent verification box before proceeding.")

    if not video_file:
        raise gr.Error("Please upload a video file (.mp4, .mov, .webm under 100MB).")

    def report_progress(msg: str, val: float):
        progress(val, desc=msg)

    try:
        backend_inst = get_backend()
        guide = run_pipeline(
            video_path=video_file.name if hasattr(video_file, "name") else str(video_file),
            speaker=speaker,
            place=place,
            language=language,
            consent_confirmed=consent,
            backend=backend_inst,
            progress_callback=report_progress
        )
        return guide_to_ui_components(guide)
    except Exception as e:
        logger.exception("Pipeline execution failed: %s", e)
        raise gr.Error(f"Generation failed: {e}")


def handle_load_sample():
    """Load sample result without requiring any video upload or model inference."""
    try:
        sample_backend = get_backend("mock")
        raw_sample = sample_backend.generate(
            audio_path=None,
            frames=[],
            metadata={"source_filename": "mysore_pak_demo.mp4", "consent_confirmed": True}
        )
        guide = CraftGuide.model_validate(raw_sample)
        return guide_to_ui_components(guide)
    except Exception as e:
        logger.exception("Failed loading sample guide: %s", e)
        raise gr.Error(f"Could not load sample guide: {e}")


def handle_export_json(raw_json_text: str, title: str) -> str:
    """Prepare edited JSON file for download."""
    if not raw_json_text.strip():
        raise gr.Error("No guide to download.")
    
    clean_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).lower() or "craft_guide"
    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, f"{clean_title}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw_json_text)
    return out_path


def handle_export_markdown(raw_json_text: str, title: str) -> str:
    """Prepare edited Markdown file for download."""
    if not raw_json_text.strip():
        raise gr.Error("No guide to download.")
    try:
        data = json.loads(raw_json_text)
        md_content = export_to_markdown(data)
    except Exception:
        # Fallback to direct text if JSON parsing fails
        md_content = f"# {title}\n\n```json\n{raw_json_text}\n```"

    clean_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).lower() or "craft_guide"
    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, f"{clean_title}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return out_path


# Define Gradio Blocks UI
with gr.Blocks(title="Craft Keeper - Preserve Traditional Crafts & Recipes") as demo:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.2rem;">🏺 Craft Keeper</h1>
        <p style="font-size: 1.05rem; color: #555; max-width: 780px; margin: 0 auto;">
            Capturing traditional skills, recipes, and artisan wisdom from spoken demonstrations 
            into structured, verifiable how-to guides.
        </p>
    </div>
    """)

    # Active backend status badge
    gr.HTML(get_backend_status_badge())

    # Mandatory Review Banner
    gr.HTML("""
    <div style="background-color: #fff8e1; border: 1px solid #ffe082; border-left: 5px solid #ffb300; padding: 12px; border-radius: 4px; margin-bottom: 1.5rem;">
        <strong>⚠️ AI-Generated Draft:</strong> This guide was generated by AI from video and audio. 
        A human practitioner or archivist must review and verify all steps and measurements before sharing.
    </div>
    """)

    with gr.Row():
        # Input column
        with gr.Column(scale=4):
            gr.Markdown("### 1. Upload Spoken Video")
            video_input = gr.File(
                label="Video File (.mp4, .mov, .webm — max 100 MB, max 5 mins)",
                file_types=[".mp4", ".mov", ".webm"],
                type="filepath"
            )

            gr.Markdown("### 2. Context & Provenance")
            speaker_input = gr.Textbox(
                label="Speaker / Artisan Name (optional)",
                placeholder="e.g. Ajji (Grandmother) or Master Chen"
            )
            place_input = gr.Textbox(
                label="Place / Cultural Origin (optional)",
                placeholder="e.g. Mysuru, Karnataka or Oaxaca, Mexico"
            )
            language_input = gr.Dropdown(
                label="Language",
                choices=["Auto-detect", "Kannada", "Hindi", "Tamil", "Telugu", "Bengali", "Spanish", "English", "Other"],
                value="Auto-detect"
            )

            consent_checkbox = gr.Checkbox(
                label="I have permission to use this video and the person in it agrees to its use.",
                value=False,
                interactive=True
            )

            with gr.Row():
                generate_btn = gr.Button("Generate Guide", variant="primary", interactive=False)
                sample_btn = gr.Button("Load Sample Result", variant="secondary")

            status_text = gr.Markdown("Ready.")

        # Result column
        with gr.Column(scale=6):
            gr.Markdown("### 3. Structured Guide (Review & Edit)")

            # Editable Title & Summary
            guide_title = gr.Textbox(label="Title", interactive=True)
            guide_meta_badge = gr.Markdown("")
            guide_summary = gr.Textbox(label="Summary", lines=2, interactive=True)

            # Uncertain items highlight
            with gr.Group():
                gr.Markdown("#### ⚠️ Review Items (Model Uncertainties)")
                uncertain_display = gr.Markdown("*No uncertain items loaded.*")

            # Editable Ingredients/Materials Table
            gr.Markdown("#### Ingredients / Materials")
            ingredients_table = gr.Dataframe(
                headers=["Item / Material", "Quantity", "Note / Gloss"],
                datatype=["str", "str", "str"],
                interactive=True,
                wrap=True
            )

            # Editable Steps Table
            gr.Markdown("#### Numbered Steps")
            steps_table = gr.Dataframe(
                headers=["#", "Time", "Instruction", "Spoken Tip"],
                datatype=["number", "str", "str", "str"],
                interactive=True,
                wrap=True
            )

            # Tips and Safety
            with gr.Row():
                tips_box = gr.Textbox(label="Spoken Tips & Context", lines=3, interactive=True)
                safety_box = gr.Textbox(label="Safety Precautions", lines=3, interactive=True)

            # Hidden or collapsible raw JSON state
            with gr.Accordion("Raw JSON Output", open=False):
                raw_json_state = gr.Code(label="JSON", language="json")

            # Download buttons
            with gr.Row():
                download_json_btn = gr.Button("⬇️ Download JSON", variant="secondary")
                download_md_btn = gr.Button("⬇️ Download Markdown", variant="secondary")

            download_file_target = gr.File(label="Download File", interactive=False, visible=False)

    # UI Interactivity Event Bindings
    def update_btn_state(consent_val):
        return gr.update(interactive=bool(consent_val))

    consent_checkbox.change(
        fn=update_btn_state,
        inputs=[consent_checkbox],
        outputs=[generate_btn]
    )

    output_components = [
        guide_title,
        guide_meta_badge,
        guide_summary,
        uncertain_display,
        ingredients_table,
        steps_table,
        tips_box,
        safety_box,
        raw_json_state,
        status_text
    ]

    generate_btn.click(
        fn=handle_generate,
        inputs=[video_input, speaker_input, place_input, language_input, consent_checkbox],
        outputs=output_components
    )

    sample_btn.click(
        fn=handle_load_sample,
        inputs=[],
        outputs=output_components
    )

    # Downloads
    def on_download_json(raw_json, title):
        filepath = handle_export_json(raw_json, title)
        return gr.update(value=filepath, visible=True)

    def on_download_md(raw_json, title):
        filepath = handle_export_markdown(raw_json, title)
        return gr.update(value=filepath, visible=True)

    download_json_btn.click(
        fn=on_download_json,
        inputs=[raw_json_state, guide_title],
        outputs=[download_file_target]
    )

    download_md_btn.click(
        fn=on_download_md,
        inputs=[raw_json_state, guide_title],
        outputs=[download_file_target]
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
