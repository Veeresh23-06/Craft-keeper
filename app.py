"""Craft Keeper - Preserving Living Audiovisual Heritage.

Capturing traditional knowledge, artisan crafts, and heirloom recipes held in people's
voices and hands, recorded on video, and transforming them into structured, verifiable how-to guides.
"""

import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Tuple

# Ensure src is on Python module search path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
import gradio as gr

from craft_keeper.backends import get_backend
from craft_keeper.export import export_to_json, export_to_markdown
from craft_keeper.pipeline import run_pipeline
from craft_keeper.schema import CraftGuide

# Load environment configuration
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("craft_keeper.app")

BACKEND_NAME = os.environ.get("CRAFT_BACKEND", "mock").lower().strip()
logger.info("Initializing Craft Keeper with active backend: '%s'", BACKEND_NAME)

try:
    active_backend = get_backend(BACKEND_NAME)
    health = active_backend.health_check()
    logger.info("Backend health check result: %s", health)
except Exception as e:
    logger.error("Failed to initialize backend '%s': %s", BACKEND_NAME, e)
    health = {"status": "error", "backend": BACKEND_NAME, "message": str(e)}


def get_privacy_notice(backend_mode: str) -> str:
    """Generate honest privacy notice reflecting provider data terms."""
    if backend_mode in ("mock", "gemma_local", "whisper+gemma-local"):
        return """
        <div style="font-size: 0.88rem; color: #1e4620; background: #edf7ed; border-left: 4px solid #2e7d32; padding: 8px 12px; border-radius: 4px; margin-top: 6px;">
            🔒 <strong>Privacy (Local Mode):</strong> Your video stays on this computer. Audio, video frames, and text are processed locally without network access.
        </div>
        """
    else:
        return """
        <div style="font-size: 0.88rem; color: #5c3800; background: #fff8e1; border-left: 4px solid #f57f17; padding: 8px 12px; border-radius: 4px; margin-top: 6px;">
            🌐 <strong>Privacy (Hosted Cloud Mode):</strong> Audio transcript and visual frames are sent to the model provider (Google AI Studio). Under official Google AI Studio Free Tier terms, submitted prompts and media may be reviewed by human annotators and used to train Google products.
        </div>
        """


def get_backend_status_badge() -> str:
    """Generate HTML badge representing active backend health."""
    status = health.get("status", "error")
    msg = health.get("message", "Unknown status")
    backend_id = health.get("backend", BACKEND_NAME)

    if status == "ok":
        return f"""
        <div style="background-color: #e6f4ea; border-left: 4px solid #34a853; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">
            <strong>Active Backend:</strong> <code>{backend_id}</code> &nbsp;|&nbsp; 
            <span style="color: #137333; font-weight: 600;">✓ Ready</span>
            <div style="font-size: 0.85rem; color: #3c4043; margin-top: 2px;">{msg}</div>
        </div>
        """
    elif status == "warning":
        return f"""
        <div style="background-color: #fef7e0; border-left: 4px solid #f9ab00; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">
            <strong>Backend Notice:</strong> <code>{backend_id}</code> &nbsp;|&nbsp; 
            <span style="color: #b06000; font-weight: 600;">⚠️ Notice</span>
            <div style="font-size: 0.85rem; color: #3c4043; margin-top: 2px;">{msg}</div>
        </div>
        """
    else:
        return f"""
        <div style="background-color: #fce8e6; border-left: 4px solid #d93025; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;">
            <strong>Backend Offline:</strong> <code>{backend_id}</code> &nbsp;|&nbsp; 
            <span style="color: #c5221f; font-weight: 600;">⚠️ Unreachable</span>
            <div style="font-size: 0.85rem; color: #3c4043; margin-top: 2px;">{msg}</div>
            <div style="font-size: 0.82rem; color: #5f6368; margin-top: 4px;">Click <em>'Load Sample Result (Demo Mode)'</em> to test the application instantly without a running model.</div>
        </div>
        """


def guide_to_ui_components(guide: CraftGuide) -> Tuple[
    str, str, str, str, str, List[List[str]], List[List[Any]], str, str, str, str
]:
    """Unpack a CraftGuide instance into state and UI fields."""
    # Credit and Heritage badges
    holder = guide.metadata.knowledge_holder or "Anonymous"
    credit_parts = [f"**Knowledge Holder:** {holder}"]
    if guide.metadata.community:
        credit_parts.append(f"**Community/Guild:** {guide.metadata.community}")
    if guide.metadata.place:
        credit_parts.append(f"**Origin:** {guide.metadata.place}")
    if guide.metadata.language:
        credit_parts.append(f"**Language:** {guide.metadata.language}")
    heritage_badge_text = " | ".join(credit_parts)

    # Provenance: How this was made
    how_made_md = f"""
    <div style="background: #f8f9fa; border: 1px solid #dadce0; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.9rem;">
        <strong>How This Was Made (AI Provenance):</strong><br/>
        • <strong>Pipeline Path:</strong> <code>{guide.metadata.model_used}</code><br/>
        • <strong>Visual Frames:</strong> {guide.metadata.frames_used} analyzed ({guide.metadata.frame_mode})<br/>
        • <strong>Source File:</strong> <code>{guide.metadata.source_filename}</code><br/>
        • <strong>Permission/License:</strong> {guide.metadata.source_video_license_or_permission}<br/>
        • <strong>Generated At:</strong> {guide.metadata.generated_at}
    </div>
    """

    # Format ingredients for Dataframe
    ing_rows = []
    for ing in guide.ingredients_or_materials:
        ing_rows.append([ing.name, ing.quantity or "", ing.note or ""])

    # Format steps for Dataframe
    step_rows = []
    for step in guide.steps:
        time_str = f"{step.approx_start_seconds:.1f}s" if step.approx_start_seconds is not None else ""
        step_rows.append([
            step.number,
            time_str,
            step.instruction,
            step.spoken_tip or ""
        ])

    # Format tips and safety
    tips_text = "\n".join(f"- {t}" for t in guide.tips)
    safety_text = "\n".join(f"- {s}" for s in guide.safety_notes)

    # Format uncertain items
    if guide.uncertain_items:
        uncertain_md = """
        <div style="background-color: #fff9e6; border-left: 4px solid #ffb300; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
            <strong>🔍 Please Check These (Model Uncertainties):</strong><br/>
            The following details were unclear in the video or audio and must be verified by a human practitioner before publishing:
            <ul style="margin-top: 4px; margin-bottom: 2px;">
        """
        for item in guide.uncertain_items:
            uncertain_md += f"<li><strong>{item.what}</strong>: {item.reason}</li>"
        uncertain_md += "</ul></div>"
    else:
        uncertain_md = "<div style='color: #555; font-style: italic;'>No uncertain items flagged by the model.</div>"

    raw_json_str = export_to_json(guide)

    return (
        guide.title,
        heritage_badge_text,
        how_made_md,
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
    knowledge_holder: str,
    anonymity: bool,
    community: str,
    place: str,
    language: str,
    occasion: str,
    permission: str,
    consent: bool,
    progress=gr.Progress()
):
    """Handler for the Generate button with multi-stage progress reporting."""
    if not consent:
        raise gr.Error("Consent Required: You must verify permission before generating a guide.")

    if not video_file:
        raise gr.Error("Please upload a video file (.mp4, .mov, or .webm under 100MB).")

    def report_progress(msg: str, val: float):
        progress(val, desc=msg)

    try:
        backend_inst = get_backend()
        guide = run_pipeline(
            video_path=video_file.name if hasattr(video_file, "name") else str(video_file),
            knowledge_holder=knowledge_holder,
            community=community,
            place=place,
            language=language,
            occasion_or_context=occasion,
            source_video_license_or_permission=permission,
            consent_confirmed=consent,
            anonymity_requested=anonymity,
            backend=backend_inst,
            progress_callback=report_progress
        )
        return guide_to_ui_components(guide)
    except Exception as e:
        logger.exception("Pipeline execution failed: %s", e)
        friendly_error = str(e)
        if "Could not connect to Ollama" in friendly_error:
            friendly_error = (
                "Ollama is not running. Please start Ollama ('ollama serve') or set CRAFT_BACKEND=mock "
                "to test with sample data."
            )
        elif "GEMINI_API_KEY" in friendly_error:
            friendly_error = (
                "GEMINI_API_KEY is not configured. Add GEMINI_API_KEY to your .env file or switch "
                "to CRAFT_BACKEND=mock."
            )
        raise gr.Error(friendly_error)


def handle_load_sample():
    """Demo Mode: Load sample result instantly without model or video requirement."""
    try:
        sample_backend = get_backend("mock")
        raw_sample = sample_backend.generate(
            audio_path=None,
            frames=[],
            metadata={
                "source_filename": "sample_mysore_pak_demo.mp4",
                "consent_confirmed": True
            }
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
    
    clean_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).lower() or "heritage_guide"
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
        md_content = f"# {title}\n\n```json\n{raw_json_text}\n```"

    clean_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).lower() or "heritage_guide"
    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, f"{clean_title}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return out_path


# Define Responsive Gradio Blocks UI
custom_css = """
@media (max-width: 768px) {
    .gradio-container { padding: 8px !important; }
    h1 { font-size: 1.6rem !important; }
}
"""

with gr.Blocks(title="Craft Keeper - Preserving Living Audiovisual Heritage", css=custom_css) as demo:
    # Theme Introduction (Audiovisual Heritage)
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 1.2rem;">
        <h1 style="font-size: 2.1rem; margin-bottom: 0.3rem;">🏺 Craft Keeper</h1>
        <p style="font-size: 1.05rem; color: #444; max-width: 820px; margin: 0 auto; line-height: 1.5;">
            Preserving living audiovisual heritage: traditional crafts, heirloom recipes, and artisanal techniques
            held in people's voices and hands, recorded on video, and not written down anywhere.
        </p>
    </div>
    """)

    # Active backend status badge & privacy notice
    gr.HTML(get_backend_status_badge())
    gr.HTML(get_privacy_notice(BACKEND_NAME))

    # Mandatory Human Review Banner
    gr.HTML("""
    <div style="background-color: #fff8e1; border: 1px solid #ffe082; border-left: 5px solid #ffb300; padding: 12px 14px; border-radius: 4px; margin-top: 10px; margin-bottom: 1.2rem; font-size: 0.95rem;">
        <strong>⚠️ AI-Generated Draft:</strong> This how-to guide is an initial draft generated from video and spoken audio. 
        A human practitioner or community archivist must review and verify all measurements and steps before it is published or shared.
    </div>
    """)

    with gr.Row():
        # Input Column
        with gr.Column(scale=4, min_width=320):
            gr.Markdown("### 1. Upload Video Recording")
            video_input = gr.File(
                label="Video File (.mp4, .mov, .webm — max 100 MB, max 5 mins)",
                file_types=[".mp4", ".mov", ".webm"],
                type="filepath"
            )

            gr.Markdown("### 2. Knowledge Holder & Cultural Heritage")
            knowledge_holder_input = gr.Textbox(
                label="Knowledge Holder / Artisan Name",
                placeholder="e.g. Ajji (Grandmother) or Master Chen"
            )
            anonymity_checkbox = gr.Checkbox(
                label="Keep knowledge holder anonymous (display as 'Anonymous')",
                value=False
            )
            community_input = gr.Textbox(
                label="Community / Craft Guild / Lineage",
                placeholder="e.g. Karnataka Traditional Sweet Makers, Zapotec Weavers"
            )
            place_input = gr.Textbox(
                label="Geographic Origin / Place of Practice",
                placeholder="e.g. Mysuru, Karnataka or Oaxaca, Mexico"
            )
            language_input = gr.Dropdown(
                label="Spoken Language",
                choices=["Auto-detect", "Kannada", "Hindi", "Tamil", "Telugu", "Bengali", "Spanish", "English", "Other"],
                value="Auto-detect"
            )
            occasion_input = gr.Textbox(
                label="Occasion or Cultural Context (optional)",
                placeholder="e.g. Deepavali festive preparation, monsoon harvest"
            )
            permission_input = gr.Textbox(
                label="Video Permission / License",
                value="Personal permission granted by knowledge holder",
                placeholder="e.g. Personal permission granted, CC-BY 4.0"
            )

            gr.Markdown("### 3. Consent & Ethics")
            consent_checkbox = gr.Checkbox(
                label="I have permission to use this video, and the person in it agrees.",
                value=False,
                interactive=True
            )

            with gr.Row():
                generate_btn = gr.Button("Generate Guide", variant="primary", interactive=False)
                sample_btn = gr.Button("Load Sample Result (Demo Mode)", variant="secondary")

            status_text = gr.Markdown("Ready.")

        # Result Column
        with gr.Column(scale=6, min_width=360):
            gr.Markdown("### 4. Structured How-To Guide (Review & Edit)")

            # How this was made panel & Heritage provenance badge
            how_made_display = gr.HTML("")
            guide_meta_badge = gr.Markdown("")

            # Title and Summary
            guide_title = gr.Textbox(label="Title", interactive=True)
            guide_summary = gr.Textbox(label="Overview & Summary", lines=2, interactive=True)

            # Uncertain items highlight
            gr.Markdown("#### 🔍 Please Check These (Uncertain Items)")
            uncertain_display = gr.HTML("<div style='color: #666; font-style: italic;'>Load a guide to view items requiring verification.</div>")

            # Editable Ingredients / Materials Table
            gr.Markdown("#### Ingredients / Materials")
            ingredients_table = gr.Dataframe(
                headers=["Item / Material", "Quantity / Measure", "Traditional Note / Gloss"],
                datatype=["str", "str", "str"],
                interactive=True,
                wrap=True
            )

            # Editable Steps Table
            gr.Markdown("#### Numbered Steps & Oral Tips")
            steps_table = gr.Dataframe(
                headers=["#", "Time", "Instruction", "Oral Tip / Sensory Cue"],
                datatype=["number", "str", "str", "str"],
                interactive=True,
                wrap=True
            )

            # Tips and Safety
            with gr.Row():
                tips_box = gr.Textbox(label="Artisan Wisdom & Rules of Thumb", lines=3, interactive=True)
                safety_box = gr.Textbox(label="Safety Precautions", lines=3, interactive=True)

            # Collapsible raw JSON state
            with gr.Accordion("Raw JSON Schema Output", open=False):
                raw_json_state = gr.Code(label="JSON", language="json")

            # Download section
            gr.Markdown("#### 5. Export Verified Guide")
            with gr.Row():
                download_json_btn = gr.Button("⬇️ Download JSON", variant="secondary")
                download_md_btn = gr.Button("⬇️ Download Markdown", variant="secondary")

            download_file_target = gr.File(label="Ready for Download", interactive=False, visible=False)

    # Interactivity bindings
    consent_checkbox.change(
        fn=lambda val: gr.update(interactive=bool(val)),
        inputs=[consent_checkbox],
        outputs=[generate_btn]
    )

    output_components = [
        guide_title,
        guide_meta_badge,
        how_made_display,
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
        inputs=[
            video_input,
            knowledge_holder_input,
            anonymity_checkbox,
            community_input,
            place_input,
            language_input,
            occasion_input,
            permission_input,
            consent_checkbox
        ],
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
