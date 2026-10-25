"""Name parsing and model-output clean-up: the parts every count depends on."""

import pytest

import ghosts


@pytest.mark.parametrize("full, first, last", [
    ("Elias Thorne", "Elias", "Thorne"),
    ("Elias", "Elias", ""),
    ("Inspector Miller", "Miller", ""),        # titles are not names
    ("Master Kaelen", "Kaelen", ""),
    ("Mrs. Gable", "Gable", ""),
    ("Dr. Aris Vance", "Aris", "Vance"),
    ("the boy", "", ""),                       # unnamed characters are dropped
    ("unknown woman", "", ""),
    ("Narrator", "", ""),
    ("", "", ""),
])
def test_first_name_and_surname(full, first, last):
    assert ghosts.first_name(full) == first
    assert ghosts.surname(full) == last


def test_strip_thinking_removes_reasoning_blocks():
    assert ghosts.strip_thinking("<think>plan the story</think>Once upon a time") == "Once upon a time"
    # Gemma 4's (empty) thought channel
    assert ghosts.strip_thinking("<|channel>thought\n<channel|>Elias lit the lamp.") == "Elias lit the lamp."


def test_parse_json_tolerates_fences_and_chatter():
    assert ghosts.parse_json('```json\n{"genre": "fantasy"}\n```') == {"genre": "fantasy"}
    assert ghosts.parse_json('Here you go: {"genre": "mystery"} Hope that helps!') == {"genre": "mystery"}
    with pytest.raises(ValueError):
        ghosts.parse_json("no json here")


def test_cosine_of_trait_profiles():
    from collections import Counter
    a = Counter({"quiet": 2, "observant": 1})
    assert ghosts._cos(a, a) == pytest.approx(1.0)
    assert ghosts._cos(a, Counter({"loud": 3})) == 0
