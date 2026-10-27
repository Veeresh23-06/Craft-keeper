"""Intelligent transcript analysis: filters small-talk chatter and extracts actionable craft/recipe steps and ingredients."""

import re
from typing import Any, Dict, List, Optional, Tuple

# Phrases indicating social filler, greetings, and video small-talk (to be filtered out of action steps)
SMALL_TALK_PATTERNS = [
    r"\bwelcome\b",
    r"\bhello\b",
    r"\bhi everyone\b",
    r"\bhi guys\b",
    r"\bhow are you\b",
    r"\bchannel\b",
    r"\bsubscribe\b",
    r"\blike and share\b",
    r"\bcomment down below\b",
    r"\bthank you for watching\b",
    r"\bsee you (in|next)\b",
    r"\bhope you (enjoyed|like)\b",
    r"\bbye bye\b",
    r"\btake care\b",
    r"\btoday('s)? video\b",
    r"\bin this video\b",
    r"\bvanakkam\b",
    r"\bnamaskara\b",
    r"\bnamaste\b",
    r"\bswagatha\b",
    r"\bellarigu\b",
    r"\bdosto\b",
    r"\bnanba\b",
    r"\bnanbargale\b"
]

# Action verbs and craft/culinary terms that signal a real step
ACTION_KEYWORDS = [
    # English culinary & craft actions
    "add", "put", "pour", "mix", "heat", "boil", "fry", "stir", "knead", "sieve",
    "cut", "chop", "slice", "roast", "fold", "bake", "grind", "soak", "dry", "take",
    "place", "keep", "wash", "cook", "shape", "weave", "tie", "cover", "remove",
    "cool", "score", "turn", "blend", "saute", "simmer", "drain", "rub", "whisk",
    "press", "ladle", "spread", "melt", "layer", "knot", "carve", "sand", "stitch",

    # Common terms in Indian / regional cooking demonstrations
    "haaki", "bisi", "kalasi", "kudiso", "thupa", "hittu", "baadi",
    "daale", "milaye", "garam", "ubaale", "pakaaye", "tel", "paani", "kadai",
    "pottu", "sethu", "kalaru", "ennai", "thanni", "maavu", "vango", "choodu"
]

# Common food items, spices, and craft materials
COMMON_INGREDIENTS = [
    "flour", "rice", "wheat", "besan", "sugar", "salt", "oil", "ghee", "water",
    "milk", "butter", "cardamom", "clove", "cinnamon", "turmeric", "chilli",
    "mustard", "cumin", "coriander", "ginger", "garlic", "onion", "tomato",
    "potato", "vegetables", "curry leaves", "dal", "lentils", "gram", "jaggery",
    "coconut", "paneer", "semolina", "rava", "pepper", "sesame", "tamarind",
    # Crafts
    "clay", "mud", "water", "sand", "thread", "wool", "silk", "cotton",
    "bamboo", "reed", "wood", "paint", "dye", "needle", "wire", "leather"
]

QUANTITY_REGEX = re.compile(
    r"\b(\d+(?:\.\d+)?(?:\s*-\s*\d+)?|\bhalf\b|\bone\b|\btwo\b|\bthree\b|\bfour\b|\ba\b|\bone-and-a-half\b)"
    r"\s*(cup|cups|tablespoon|tablespoons|tbsp|teaspoon|teaspoons|tsp|gram|grams|g|kg|ml|litre|litres|pinch|spoon|spoons|handful|glass|glasses|drops)?\b",
    re.IGNORECASE
)


def is_small_talk(text: str) -> bool:
    """Detect if a sentence is conversational chatter, greeting, or channel intro/outro."""
    clean = text.lower().strip()
    if len(clean.split()) < 3 and not any(k in clean for k in ACTION_KEYWORDS):
        return True

    for pat in SMALL_TALK_PATTERNS:
        if re.search(pat, clean):
            # If it also contains a clear cooking instruction, keep it; otherwise discard
            if not any(k in clean for k in ["add", "mix", "pour", "boil", "fry", "heat", "haaki", "daale", "pottu"]):
                return True
    return False


def is_actionable_step(text: str) -> bool:
    """Check if a spoken sentence contains an instruction or craft technique."""
    clean = text.lower()
    return any(k in clean for k in ACTION_KEYWORDS) or any(ing in clean for ing in COMMON_INGREDIENTS)


def extract_ingredients_from_transcript(transcript_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scan transcript for mentioned ingredients, materials, and quantities."""
    found_ingredients = []
    seen_names = set()

    for seg in transcript_segments:
        text = seg["text"].lower()
        for ing in COMMON_INGREDIENTS:
            if ing in text and ing not in seen_names:
                # Look for adjacent quantity
                qty_match = QUANTITY_REGEX.search(text)
                qty = qty_match.group(0).strip() if qty_match else "To taste / As demonstrated"
                
                seen_names.add(ing)
                found_ingredients.append({
                    "name": ing.title(),
                    "quantity": qty,
                    "note": f"Mentioned around [{seg['start']}s]"
                })

    if not found_ingredients:
        found_ingredients = [
            {
                "name": "Ingredients / Materials demonstrated in video",
                "quantity": "As shown",
                "note": "Review video recording to verify exact measurements"
            }
        ]
    return found_ingredients


def structure_transcript_to_steps(transcript_segments: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Filter small talk and convert actionable spoken segments into numbered steps, tips, and safety notes."""
    steps = []
    tips = []
    safety = []

    for seg in transcript_segments:
        text = seg["text"].strip()
        if not text:
            continue

        # Skip social chatter and channel greetings
        if is_small_talk(text):
            continue

        clean_lower = text.lower()

        # Check for safety precautions
        if any(w in clean_lower for w in ["burn", "hot", "careful", "danger", "splash", "smoke", "scald", "caution"]):
            safety.append(text)

        # Check for artisan wisdom / tips
        is_tip = any(w in clean_lower for w in ["tip", "secret", "remember", "never", "always", "important", "trick", "ensure"])
        if is_tip and len(steps) > 0 and steps[-1].get("spoken_tip") is None:
            # Attach as tip to previous step if applicable
            steps[-1]["spoken_tip"] = text
            tips.append(text)
            continue

        # Keep actionable steps
        if is_actionable_step(text) or len(steps) < 3:
            tip_content = text if is_tip else None
            steps.append({
                "number": len(steps) + 1,
                "approx_start_seconds": seg["start"],
                "instruction": text,
                "spoken_tip": tip_content
            })

    # Fallback if overfiltered: if no steps made it through, take non-small-talk segments
    if not steps:
        for seg in transcript_segments:
            t = seg["text"].strip()
            if not is_small_talk(t) and len(t) > 5:
                steps.append({
                    "number": len(steps) + 1,
                    "approx_start_seconds": seg["start"],
                    "instruction": t,
                    "spoken_tip": None
                })

    if not tips:
        tips = ["Observe the artisan's hand movements and sensory cues demonstrated in the video."]
    if not safety:
        safety = ["Handle hot cookware, sharp tools, and heating elements with standard precautions."]

    return steps, tips, safety
