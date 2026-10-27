"""Unit tests for transcript small-talk filtering and step/ingredient extraction."""

from craft_keeper.extractor import (
    extract_ingredients_from_transcript,
    is_actionable_step,
    is_small_talk,
    structure_transcript_to_steps,
)


def test_is_small_talk():
    assert is_small_talk("Hello everyone, welcome back to my channel!")
    assert is_small_talk("Please subscribe, like and share.")
    assert is_small_talk("Namaskara dosto!")
    assert is_small_talk("Hi")

    # Actionable instructions should NOT be classified as small talk
    assert not is_small_talk("Add 2 cups of water and boil on medium heat.")
    assert not is_small_talk("Mix the rice flour with a pinch of salt.")


def test_is_actionable_step():
    assert is_actionable_step("Pour 100ml oil into the pan.")
    assert is_actionable_step("Knead the dough until soft.")
    assert is_actionable_step("Chop onions and tomatoes finely.")
    assert not is_actionable_step("I think the weather is very nice outside today.")


def test_extract_ingredients_from_transcript():
    segments = [
        {"start": 10.0, "end": 14.0, "text": "Take 2 cups of rice flour and one teaspoon of salt."},
        {"start": 20.0, "end": 25.0, "text": "Heat 2 tablespoons ghee in a kadai."},
    ]
    ingredients = extract_ingredients_from_transcript(segments)
    names = [i["name"] for i in ingredients]

    assert "Rice" in names
    assert "Flour" in names
    assert "Salt" in names
    assert "Ghee" in names


def test_structure_transcript_to_steps():
    segments = [
        {"start": 0.0, "end": 4.0, "text": "Hello friends, welcome to our traditional recipe series."},
        {"start": 5.0, "end": 9.0, "text": "Today I will show you how to make this special item."},
        {"start": 10.0, "end": 15.0, "text": "First, take 2 cups of rice flour and add warm water."},
        {"start": 16.0, "end": 20.0, "text": "Remember, the secret is to knead slowly so no lumps form."},
        {"start": 21.0, "end": 26.0, "text": "Be careful as the hot pan can cause severe burns."},
        {"start": 27.0, "end": 30.0, "text": "Thank you for watching, please subscribe to our channel!"},
    ]

    steps, tips, safety = structure_transcript_to_steps(segments)

    # Small talk at start and end should be eliminated
    instructions = [s["instruction"] for s in steps]
    assert not any("welcome" in inst.lower() for inst in instructions)
    assert not any("subscribe" in inst.lower() for inst in instructions)

    # Meaningful steps kept
    assert any("rice flour" in inst.lower() for inst in instructions)

    # Safety captured
    assert any("burn" in s.lower() for s in safety)

    # Tips captured
    assert any("secret" in t.lower() or "lump" in t.lower() for t in tips)
