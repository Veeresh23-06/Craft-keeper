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

    # Metadata badges
    speaker_info = f"**Speaker/Maker:** {guide.metadata.speaker}" if guide.metadata.speaker else ""
    place_info = f"**Place:** {guide.metadata.place}" if guide.metadata.place else ""
    lang_info = f"**Language:** {guide.detected_language}"
    cat_info = f"**Category:** {guide.category.title()}"
    meta_parts = [p for p in [cat_info, lang_info, speaker_info, place_info] if p]
    if meta_parts:
        lines.append(" | ".join(meta_parts) + "\n")

    # Summary
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
        lines.append("## Tools & Equipment\n")
        for tool in guide.tools:
            lines.append(f"- {tool}")
        lines.append("")

    # Steps
    if guide.steps:
        lines.append("## Instructions\n")
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
        lines.append("## Tips & Cultural Context\n")
        for tip in guide.tips:
            lines.append(f"- {tip}")
        lines.append("")

    # Safety notes
    if guide.safety_notes:
        lines.append("## ⚠️ Safety Precautions\n")
        for note in guide.safety_notes:
            lines.append(f"- {note}")
        lines.append("")

    # Footer provenance
    lines.append("---\n")
    lines.append(f"*Archived by Craft Keeper using `{guide.metadata.model_used}` on {guide.metadata.generated_at}*")
    if guide.metadata.source_filename:
        lines.append(f"  \n*Source File: `{guide.metadata.source_filename}`*")

    return "\n".join(lines)
