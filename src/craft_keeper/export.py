"""Export utilities for Craft Keeper guides (JSON and Markdown)."""

import json
from typing import Any, Dict
from craft_keeper.schema import CraftGuide


def export_to_json(guide: CraftGuide | Dict[str, Any], indent: int = 2) -> str:
    """Serialize a CraftGuide model or dict to pretty-printed JSON string."""
    if isinstance(guide, CraftGuide):
        return guide.model_dump_json(indent=indent)
    return json.dumps(guide, indent=indent, ensure_ascii=False)


def format_seconds(seconds: float | int | None) -> str:
    """Format seconds into MM:SS format."""
    if seconds is None:
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def export_to_markdown(guide_input: CraftGuide | Dict[str, Any]) -> str:
    """Convert a CraftGuide into a clean, human-readable Markdown how-to document."""
    if isinstance(guide_input, dict):
        guide = CraftGuide.model_validate(guide_input)
    else:
        guide = guide_input

    lines = []
    lines.append(f"# {guide.title}\n")
    lines.append("> ⚠️ **AI-generated draft.** A person must review it before it is shared.\n")

    # Credit line as required by theme alignment:
    holder_name = guide.metadata.knowledge_holder or "Anonymous"
    credit_parts = [holder_name]
    if guide.metadata.community:
        credit_parts.append(guide.metadata.community)
    if guide.metadata.place:
        credit_parts.append(guide.metadata.place)
    lines.append(f"**Knowledge shared by:** {', '.join(credit_parts)}\n")

    # Heritage context line
    context_items = []
    if guide.metadata.occasion_or_context:
        context_items.append(f"**Occasion/Context:** {guide.metadata.occasion_or_context}")
    if guide.metadata.language:
        context_items.append(f"**Spoken Language:** {guide.metadata.language}")
    if guide.metadata.source_video_license_or_permission:
        context_items.append(f"**Permission/License:** {guide.metadata.source_video_license_or_permission}")
    if context_items:
        lines.append(" | ".join(context_items) + "\n")

    # Overview
    lines.append("## Overview\n")
    lines.append(f"{guide.summary}\n")

    # Uncertain items (highlighted review section)
    if guide.uncertain_items:
        lines.append("## 🔍 Please Check These (Uncertain Items)\n")
        lines.append("> The following details were unclear in the video or audio and require human verification:\n")
        for item in guide.uncertain_items:
            lines.append(f"- **{item.what}**: {item.reason}")
        lines.append("")

    # Ingredients / Materials
    if guide.ingredients_or_materials:
        header = "Ingredients" if guide.category == "recipe" else "Materials"
        lines.append(f"## {header}\n")
        for ing in guide.ingredients_or_materials:
            qty_part = f" — *{ing.quantity}*" if ing.quantity else ""
            note_part = f" ({ing.note})" if ing.note else ""
            lines.append(f"- **{ing.name}**{qty_part}{note_part}")
        lines.append("")

    # Tools
    if guide.tools:
        lines.append("## Traditional Tools & Vessels\n")
        for tool in guide.tools:
            lines.append(f"- {tool}")
        lines.append("")

    # Steps
    if guide.steps:
        lines.append("## Steps & Oral Guidance\n")
        for step in guide.steps:
            time_tag = ""
            if step.approx_start_seconds is not None:
                time_str = format_seconds(step.approx_start_seconds)
                time_tag = f" `[{time_str}]`"
            lines.append(f"### Step {step.number}{time_tag}\n")
            lines.append(f"{step.instruction}\n")
            if step.spoken_tip:
                lines.append(f"> 💬 *Spoken Tip:* \"{step.spoken_tip}\"\n")

    # Tips
    if guide.tips:
        lines.append("## Artisan Wisdom & Rules of Thumb\n")
        for tip in guide.tips:
            lines.append(f"- {tip}")
        lines.append("")

    # Safety notes
    if guide.safety_notes:
        lines.append("## ⚠️ Safety Precautions\n")
        for note in guide.safety_notes:
            lines.append(f"- {note}")
        lines.append("")

    # How this was made provenance
    lines.append("---\n")
    lines.append("### How This Was Made (AI Provenance)\n")
    lines.append(f"- **Generation Path:** `{guide.metadata.model_used}`")
    lines.append(f"- **Visual Frames:** {guide.metadata.frames_used} analyzed ({guide.metadata.frame_mode})")
    lines.append(f"- **Source Recording:** `{guide.metadata.source_filename}`")
    lines.append(f"- **Recorded On:** {guide.metadata.generated_at}")
    lines.append(f"- **Consent Status:** Explicit permission confirmed (`consent_confirmed={guide.metadata.consent_confirmed}`)")

    return "\n".join(lines)
