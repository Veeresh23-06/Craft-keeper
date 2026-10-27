"""Pydantic schema definitions for Craft Keeper structured audiovisual heritage guides."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class IngredientOrMaterial(BaseModel):
    name: str = Field(description="Name of the ingredient, plant, metal, clay, or craft material")
    quantity: Optional[str] = Field(default=None, description="Measured quantity or traditional proportion, if mentioned")
    note: Optional[str] = Field(
        default=None,
        description="Preparation notes, regional terminology, or English gloss for regional terms"
    )


class Step(BaseModel):
    number: int = Field(description="Step sequence number (1-indexed)")
    approx_start_seconds: Optional[float] = Field(
        default=None,
        description="Approximate start time in seconds relative to the video recording"
    )
    instruction: str = Field(description="Observed manual action or instruction")
    spoken_tip: Optional[str] = Field(
        default=None,
        description="Direct oral tip, sensory cue (sound, smell, feel), or technique passed down by the speaker"
    )


class UncertainItem(BaseModel):
    what: str = Field(description="The ambiguous element, unstated quantity, or partly occluded step")
    reason: str = Field(description="Why this item is uncertain (e.g., muffled audio, off-camera motion, regional dialect term)")


class GuideMetadata(BaseModel):
    knowledge_holder: str = Field(
        default="Anonymous",
        description="Name of the artisan, elder, or maker sharing the knowledge (or 'Anonymous')"
    )
    community: Optional[str] = Field(
        default=None,
        description="Cultural tradition, craft guild, indigenous lineage, or community origin"
    )
    place: Optional[str] = Field(
        default=None,
        description="Geographic region, village, town, or place of practice"
    )
    language: str = Field(
        default="Unknown",
        description="Language or dialect spoken in the demonstration"
    )
    occasion_or_context: Optional[str] = Field(
        default=None,
        description="Cultural occasion, ritual, season, or household context (e.g., harvest, wedding, daily staple)"
    )
    source_video_license_or_permission: str = Field(
        default="Personal permission granted by speaker",
        description="Permission or open-license terms governing the source video recording"
    )
    consent_confirmed: bool = Field(
        description="Confirmation that explicit permission was granted by the recorded person"
    )
    anonymity_requested: bool = Field(
        default=False,
        description="Flag indicating whether knowledge holder requested to remain anonymous"
    )
    source_filename: str = Field(
        default="unknown_source.mp4",
        description="Original filename of the submitted video recording"
    )
    model_used: str = Field(
        description="Backend identifier used for generation (e.g. 'mock', 'whisper+gemma-local', 'whisper+gemma-hosted', 'gemini-fallback')"
    )
    frames_used: int = Field(
        default=0,
        description="Number of visual frames analyzed by the model"
    )
    frame_mode: str = Field(
        default="unused",
        description="Visual frame analysis status: 'used', 'unused_in_local', or 'transcript_only'"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of generation"
    )


class CraftGuide(BaseModel):
    title: str = Field(description="Descriptive title of the heritage craft or culinary practice")
    detected_language: str = Field(description="Primary language or dialect spoken")
    category: Literal["recipe", "craft", "other"] = Field(
        description="Category: culinary recipe, artisan craft, or other living heritage practice"
    )
    summary: str = Field(description="One or two sentences summarizing the technique, craft, or recipe")
    ingredients_or_materials: List[IngredientOrMaterial] = Field(
        default_factory=list,
        description="List of ingredients or raw materials required"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Traditional tools, cookware, hearths, or equipment used"
    )
    steps: List[Step] = Field(
        default_factory=list,
        description="Ordered sequence of steps with approximate timestamps and oral tips"
    )
    tips: List[str] = Field(
        default_factory=list,
        description="Sensory cues, rules of thumb, and oral wisdom shared by the maker"
    )
    safety_notes: List[str] = Field(
        default_factory=list,
        description="Safety precautions, heat handling, or sharp tool guidelines"
    )
    uncertain_items: List[UncertainItem] = Field(
        default_factory=list,
        description="Uncertain details requiring human review before sharing"
    )
    metadata: GuideMetadata = Field(description="Provenance, cultural credit, and technical metadata")
