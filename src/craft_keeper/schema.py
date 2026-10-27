"""Pydantic schema definitions for Craft Keeper structured how-to guides."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class IngredientOrMaterial(BaseModel):
    name: str = Field(description="Name of the ingredient or craft material")
    quantity: Optional[str] = Field(default=None, description="Measured quantity or amount, if mentioned")
    note: Optional[str] = Field(default=None, description="Notes, preparations, or English gloss for regional terms")


class Step(BaseModel):
    number: int = Field(description="Step sequence number (1-indexed)")
    approx_start_seconds: Optional[float] = Field(
        default=None,
        description="Approximate start time in seconds relative to the video"
    )
    instruction: str = Field(description="Actionable instruction observed or described")
    spoken_tip: Optional[str] = Field(
        default=None,
        description="Key verbal tip, rationale, or technique shared by the speaker"
    )


class UncertainItem(BaseModel):
    what: str = Field(description="The ambiguous item, quantity, or step")
    reason: str = Field(description="Why this item is uncertain (e.g., muffled speech, obscured view)")


class GuideMetadata(BaseModel):
    speaker: Optional[str] = Field(default=None, description="Name or identifier of the speaker/maker")
    place: Optional[str] = Field(default=None, description="Geographic location or cultural origin")
    consent_confirmed: bool = Field(description="Whether user verified consent for using the media")
    source_filename: str = Field(description="Original filename of the submitted video")
    model_used: str = Field(description="Backend or model name that produced this guide")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of generation"
    )


class CraftGuide(BaseModel):
    title: str = Field(description="Descriptive title of the recipe or craft")
    detected_language: str = Field(description="Primary language spoken or detected")
    category: Literal["recipe", "craft", "other"] = Field(
        description="Category: recipe, craft, or other traditional practice"
    )
    summary: str = Field(description="One or two sentences summarizing the craft or recipe")
    ingredients_or_materials: List[IngredientOrMaterial] = Field(
        default_factory=list,
        description="List of ingredients or materials required"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tools, cookware, or equipment used"
    )
    steps: List[Step] = Field(
        default_factory=list,
        description="Ordered sequence of steps"
    )
    tips: List[str] = Field(
        default_factory=list,
        description="General tips, cultural context, or best practices mentioned"
    )
    safety_notes: List[str] = Field(
        default_factory=list,
        description="Safety precautions or warnings"
    )
    uncertain_items: List[UncertainItem] = Field(
        default_factory=list,
        description="Uncertain or ambiguous details that need human verification"
    )
    metadata: GuideMetadata = Field(description="Provenance and operational metadata")
