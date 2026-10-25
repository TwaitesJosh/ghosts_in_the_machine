"""End-to-end check of `ghosts.py report` on a tiny synthetic dataset (no model needed)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def character(name, role="protagonist", traits=("quiet", "observant"), occupation="clockmaker"):
    return {"name": name, "gender": "male", "age": "elderly", "role": role, "occupation": occupation,
            "setting": "Oakhaven", "traits": list(traits), "goal": "to mend the clock",
            "wound": "his late wife", "flaw": "pride", "arc": "lets go", "fate": "finds peace",
            "relationships": []}


def write_dataset(folder: Path):
    stories, extracts = [], []
    for i in range(6):
        sid = f"s{i}"
        stories.append({"id": sid, "prompt": "Write a story.", "text": "..."})
        cast = [character("Elias Thorne" if i % 2 else "Elias")]
        if i < 4:
            cast.append({**character("Clara", role="love interest", traits=("vibrant", "warm")),
                         "gender": "female"})
        cast.append(character("the shadow"))          # unnamed: must be ignored
        extracts.append({"story_id": sid, "prompt": "Write a story.", "genre": "fantasy",
                         "ending_tone": "hopeful", "characters": cast})
    (folder / "stories.jsonl").write_text("\n".join(json.dumps(s) for s in stories) + "\n")
    (folder / "characters.jsonl").write_text("\n".join(json.dumps(e) for e in extracts) + "\n")


def test_report_counts_names_and_surnames(tmp_path):
    write_dataset(tmp_path)
    subprocess.run([sys.executable, str(ROOT / "ghosts.py"), "report", "--data", str(tmp_path),
                    "--min-stories", "1"], check=True, cwd=tmp_path, capture_output=True)
    report = (tmp_path / "report.md").read_text()
    stats = json.loads((tmp_path / "stats.json").read_text())

    assert "Stories analysed: **6**" in report
    assert stats["Elias"]["stories"] == 6
    assert stats["Clara"]["stories"] == 4
    assert "Shadow" not in stats and "The" not in stats
    assert "| 1 | Thorne | 3 |" in report                # surname table: 3 stories, all Elias
