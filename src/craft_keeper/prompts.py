"""Model prompt definitions and system instructions for Craft Keeper.

All rules governing inference, JSON formatting, grounding, and retry behavior
are consolidated here.
"""

from typing import Optional

CRAFT_KEEPER_SYSTEM_PROMPT = """You are Craft Keeper, an expert archivist dedicated to preserving traditional recipes and artisan crafts.
Your task is to transform visual and spoken demonstrations of traditional knowledge into a structured, faithful, and editable how-to guide.

STRICT GROUNDING RULES:
1. Grounding: Use ONLY what is explicitly spoken or visibly shown in the video inputs. Never invent steps, quantities, brands, ingredients, tools, or facts.
2. Handling Ambiguity: If something is unclear, partly heard, occluded, or only guessed, DO NOT state it as fact. Add it to `uncertain_items` with a clear explanation of what is ambiguous and why.
3. Speaker's Voice: Preserve the speaker's own words and phrasing for tips and instructions wherever possible to honor their authentic teaching style.
4. Multilingual Terms: If the speech is in a language other than English (or contains indigenous, regional, or dialect terms), keep the original-language term (in its native script or transliteration) and provide a concise English gloss/translation in the `note` field.
5. Approximate Timestamps: Timestamps for steps (`approx_start_seconds`) must be derived strictly from the timestamps provided on input frames or chunk markers. Do not hallucinate exact second marks.
6. JSON Output: Return strictly valid JSON matching the target schema. Do NOT include markdown code fences, greetings, preambles, or conversational sign-offs.
"""

CRAFT_KEEPER_USER_TEMPLATE = """Please extract a structured guide from the provided multimedia inputs for this traditional craft or recipe.

INPUT CONTEXT:
- Speaker Name: {speaker}
- Geographic/Cultural Origin: {place}
- Preferred/Detected Language: {language}
- Source File: {filename}
- Available Timestamps / Frame Markers: {frame_timestamps}

{additional_context}

TARGET JSON SCHEMA:
{{
  "title": "string (name of the craft or recipe)",
  "detected_language": "string (language detected or spoken)",
  "category": "recipe" | "craft" | "other",
  "summary": "string (1-2 sentences summarizing the technique or dish)",
  "ingredients_or_materials": [
    {{
      "name": "string (name of item)",
      "quantity": "string or null",
      "note": "string or null (include English gloss if regional name)"
    }}
  ],
  "tools": ["string (equipment/vessels/tools used)"],
  "steps": [
    {{
      "number": 1,
      "approx_start_seconds": 0.0,
      "instruction": "string (clear action observed)",
      "spoken_tip": "string or null (authentic words/tips spoken during this step)"
    }}
  ],
  "tips": ["string (general tips/rules of thumb mentioned)"],
  "safety_notes": ["string (burn/cut/hot liquid precautions observed)"],
  "uncertain_items": [
    {{
      "what": "string (unclear quantity, missing step, or ambiguous ingredient)",
      "reason": "string (why it is uncertain, e.g., camera pointed away, faint speech)"
    }}
  ],
  "metadata": {{
    "speaker": {speaker_repr},
    "place": {place_repr},
    "consent_confirmed": true,
    "source_filename": {filename_repr},
    "model_used": "{model_name}",
    "generated_at": "{generated_at}"
  }}
}}

Remember: Return JSON ONLY. No markdown ticks, no commentary.
"""

CRAFT_KEEPER_RETRY_TEMPLATE = """Your previous response did not validate against the required Pydantic schema.

VALIDATION ERRORS ENCOUNTERED:
{validation_error}

ORIGINAL RAW OUTPUT:
{raw_output}

Please fix the errors above and return the corrected JSON.
Ensure:
1. Strict adherence to the schema and types.
2. Every required key is present.
3. No extraneous text or formatting outside the JSON object.
"""


def format_craft_prompt(
    speaker: Optional[str] = None,
    place: Optional[str] = None,
    language: Optional[str] = None,
    filename: Optional[str] = "video.mp4",
    frame_timestamps: Optional[str] = "None provided",
    additional_context: Optional[str] = "",
    model_name: str = "gemma",
    generated_at: str = ""
) -> str:
    """Format user prompt for the model backend."""
    import json
    return CRAFT_KEEPER_USER_TEMPLATE.format(
        speaker=speaker or "Not specified",
        place=place or "Not specified",
        language=language or "Auto-detect",
        filename=filename,
        frame_timestamps=frame_timestamps,
        additional_context=additional_context or "",
        speaker_repr=json.dumps(speaker),
        place_repr=json.dumps(place),
        filename_repr=json.dumps(filename),
        model_name=model_name,
        generated_at=generated_at
    )


def format_retry_prompt(validation_error: str, raw_output: str) -> str:
    """Format retry prompt when JSON validation fails."""
    return CRAFT_KEEPER_RETRY_TEMPLATE.format(
        validation_error=validation_error,
        raw_output=raw_output
    )
