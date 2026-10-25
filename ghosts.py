#!/usr/bin/env python3
"""
ghosts.py - who are the default characters LLMs keep writing?

Pipeline against a local llama.cpp server (llama-server, OpenAI-compatible API):

  1. generate   ask the model for lots of stories          -> data/stories.jsonl
  2. extract    pull every named character into a schema   -> data/characters.jsonl
  3. report     aggregate by first name, compute stats     -> data/report.md + data/stats.json
  4. profile    LLM writes a composite character sheet     -> data/sheets/<Name>.md
  5. probe      name x trait association, straight from     -> data/probe.csv, probe.md,
                the model's next-word probabilities            probe_heatmap.html
  6. bio        ask for biographies of each bare name,      -> data/bios.jsonl, bio_report.md
                compare with who they are in the stories
  7. roulette   name probabilities at the moment a name is  -> data/roulette_<label>.json,
                due; compare models with --label               roulette.md, roulette.html
  8. swap       force or swap the name and see whether the  -> data/swap_open.md, swap_cut.md
                lighthouse comes with it
  9. genre      same name across genres: one persona, or    -> data/genre.md
                does the genre make the character?

Every step is resumable: re-run it and it picks up where it left off.
Python 3.9+. Only optional dependency: `pip install tqdm` for progress bars
(without it you get a plain text counter).

Quick start (model paths and llama-server flags live in ghosts_config.py):
  python ghosts.py generate --n 50          # starts llama-server on the default model, stops it after
  python ghosts.py extract
  python ghosts.py report                   # no model needed
  python ghosts.py profile --top 12
  python ghosts.py --model base roulette    # another model by name; base gets bare text automatically
  python ghosts.py probe --invented     # also scores made-up names (sound-symbolism test)
  python ghosts.py bio --n 10           # 10 biographies per name per prompt
  python ghosts.py roulette --label instruct   # name probabilities at the naming moment
  python ghosts.py swap --mode open     # stories forced to start with each name
  python ghosts.py swap --mode cut      # Elias's stories re-continued as David, Thomas, Vorrak
  python ghosts.py genre                # is sci-fi Mara the same person as romance Mara?

Each run starts llama-server itself (and stops it at the end) unless the same model is already
running on the configured port, which it then reuses. --url points at a server you run yourself.
"""

import argparse
import atexit
import csv
import html
import json
import math
import shutil
import random
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import ghosts_config as CFG
except ImportError:
    CFG = None

try:
    from tqdm import tqdm as _tqdm
except ImportError:  # fall back to a minimal text counter
    _tqdm = None


class _Plain:
    """Tiny stand-in for tqdm so the script still shows progress without it."""
    def __init__(self, total=None, desc="", unit="it", **_):
        self.n, self.total, self.desc, self.unit, self.post = 0, total, desc, unit, ""
        self.t0 = time.time()

    def update(self, k=1):
        self.n += k
        el = time.time() - self.t0
        eta = (self.total - self.n) * el / self.n if self.total and self.n else 0
        print(f"\r{self.desc}: {self.n}/{self.total} {self.unit} "
              f"[{el:,.0f}s elapsed, ~{eta:,.0f}s left] {self.post}   ", end="", flush=True)

    def set_postfix_str(self, s, refresh=True):
        self.post = s

    def close(self):
        print()

    @staticmethod
    def write(s):
        print("\n" + s, file=sys.stderr)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def bar(total, desc, unit="it"):
    if _tqdm:
        return _tqdm(total=total, desc=desc, unit=unit, dynamic_ncols=True, smoothing=0.1)
    return _Plain(total=total, desc=desc, unit=unit)


def say(msg):
    (_tqdm.write if _tqdm else print)(msg)

# --------------------------------------------------------------------------- prompts

# Plain prompts (the Cornell study used ones like these) plus genre prompts,
# because fantasy names (Kaelen, Seraphina) mostly appear when asked for fantasy.
STORY_PROMPTS = [
    "Write a story.",
    "Tell me a story.",
    "Write a short story.",
    "Write a fantasy story.",
    "Write a science fiction story.",
    "Write a mystery story.",
    "Write a romance story.",
    "Write a story about a family.",
    "Write a dark story.",
    "Write an adventure story.",
]

EXTRACT_SYSTEM = """You are a literary analyst. Read the story and describe every NAMED character in it.
Only include characters who have a proper name (skip "the old man", "the keeper" unless named).
Be faithful to the text. If something is not stated or clearly implied, write "unknown".
Keep traits to at most 6 single adjectives each. Keep free-text fields to one short sentence.

Fill the descriptive fields first; the labels come last so you can base them on what you wrote:
- role: protagonist = the main character whose story it is (usually the point-of-view character).
  antagonist = a NAMED person who actively opposes the protagonist (a villain or rival).
  A monster, darkness, curse or force of nature is never a character's role. Most stories have
  no named antagonist. mentor / love interest / companion / family / minor otherwise.
- relationships: relation = what the OTHER person is to this character
  (if Clara is Elias's wife, Elias's entry says {"name": "Clara", "relation": "wife"}).
- ending_tone (for the whole story, judged by what happens to the protagonist):
  happy = they get what they want and are well; hopeful = things look up but aren't resolved;
  bittersweet = real gain with real loss; tragic = they die, are destroyed, consumed or lose;
  ambiguous = genuinely unclear."""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "genre": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "gender": {"type": "string", "enum": ["male", "female", "nonbinary", "unknown"]},
                    "age": {"type": "string", "enum": ["child", "teen", "young adult", "adult", "middle-aged", "elderly", "unknown"]},
                    "occupation": {"type": "string"},
                    "setting": {"type": "string"},
                    "traits": {"type": "array", "items": {"type": "string"}},
                    "goal": {"type": "string", "description": "what they want"},
                    "wound": {"type": "string", "description": "past hurt, fear or loss that haunts them"},
                    "flaw": {"type": "string"},
                    "arc": {"type": "string", "description": "how they change over the story"},
                    "fate": {"type": "string", "description": "where they end up at the end"},
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"name": {"type": "string"},
                                           "relation": {"type": "string",
                                                        "description": "what this other person is TO the character"}},
                            "required": ["name", "relation"],
                        },
                    },
                    "role": {"type": "string", "enum": ["protagonist", "antagonist", "mentor", "love interest", "companion", "family", "minor"]},
                },
                "required": ["name", "gender", "age", "occupation", "setting", "traits",
                             "goal", "wound", "flaw", "arc", "fate", "relationships", "role"],
            },
        },
    },
    "required": ["genre", "characters", "ending_tone"],
}
# ending_tone goes after the characters so the model judges it having described them
EXTRACT_SCHEMA["properties"]["ending_tone"] = {
    "type": "string", "enum": ["happy", "hopeful", "bittersweet", "tragic", "ambiguous"]}

PROFILE_SYSTEM = """You are writing a character sheet for a "field guide to the ghosts in the machine":
the stock characters that language models keep reinventing in their stories.
You are given aggregate statistics and a sample of individual appearances of one recurring name.
Write a composite profile of who this character *usually* is. Ground every claim in the data;
when appearances disagree, say so and give rough proportions. Be vivid but honest. Markdown, no preamble."""

PROFILE_TEMPLATE = """Character: {name}

Aggregate statistics (from {n} appearances across {total} stories):
{stats}

Sample of individual appearances:
{samples}

Write the sheet with these sections:
# {name}
*One-line summary in the style of a dramatis personae entry.*
## At a glance   (typical age, gender, job, setting, role - with proportions)
## Personality
## What they want
## What haunts them
## Their usual story   (the arc and how it typically ends)
## Who they keep company with
## Variants and outliers
## Field notes   (2-3 observations about what this character reveals about the model)"""

# capitalised words that come where a name would but aren't names
NOT_NAMES = {"the", "a", "an", "he", "she", "it", "they", "his", "her", "its", "this", "that", "and", "but",
             "after", "simply", "only", "just", "not", "because", "for", "by", "in", "on", "at", "as", "so",
             "one", "no", "nobody", "none", "something", "nothing", "everyone", "mister", "madam", "saint", "st",
             "aunt", "uncle", "granny", "grandma", "grandpa"}
TITLES = {"dr", "doctor", "captain", "capt", "lord", "lady", "sir", "dame", "professor", "prof",
          "commander", "old", "young", "mr", "mrs", "ms", "miss", "master", "mistress", "king",
          "queen", "prince", "princess", "father", "mother", "brother", "sister", "general",
          "detective", "inspector", "agent", "officer", "sergeant", "lieutenant", "elder", "aunt", "uncle"}

# --------------------------------------------------------------------------- helpers

_lock = threading.Lock()


def append_jsonl(path: Path, record: dict):
    with _lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # a half-written line from an interrupted run
    return out


def strip_thinking(text: str) -> str:
    # Some chat templates leak reasoning into content; drop it.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"<\|channel\|>.*?<\|message\|>", "", text, flags=re.S)
    text = re.sub(r"<\|channel>.*?<channel\|>", "", text, flags=re.S)   # Gemma 4 thought block
    return text.strip()


def chat(args, messages, temperature, max_tokens, response_format=None, retries=3):
    body = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens,
            # Thinking off: llama-server switches Gemma 4's thinking on by default for chat requests,
            # which spends the token budget thinking (empty answers) and isn't plain chat behaviour.
            "chat_template_kwargs": {"enable_thinking": False}}
    if temperature > 0:
        body["top_p"] = args.top_p
        body["seed"] = random.randint(0, 2**31 - 1)  # make sure parallel slots don't share a seed
    if response_format:
        body["response_format"] = response_format
    url = args.url.rstrip("/") + "/v1/chat/completions"
    data = json.dumps(body).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=args.timeout) as r:
                resp = json.load(r)
            msg = resp["choices"][0]["message"]
            content = strip_thinking(msg.get("content") or "")
            if not content.strip():
                why = ("the model put everything into its thinking and never answered"
                       if (msg.get("reasoning_content") or "").strip() else "empty reply")
                finish = resp["choices"][0].get("finish_reason")
                raise RuntimeError(f"{why} (finish_reason={finish}, max_tokens={max_tokens})")
            return content, resp
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
            if e.code == 400:
                break  # bad request won't fix itself
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(last)


def parse_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise


UNNAMED = {"unknown", "unnamed", "none", "n/a", "na", "narrator", "nobody"}


def _words(full: str):
    full = (full or "").strip()
    low = full.lower()
    if low in UNNAMED or low.startswith(("the ", "a ", "an ", "unknown", "unnamed")):
        return []  # "the boy", "the shadow", "unknown woman" are not names
    words = re.findall(r"[A-Za-zÀ-ÿ0-9'\-]+", full)
    return [w for w in words if w.lower().strip(".") not in TITLES]


def first_name(full: str) -> str:
    w = _words(full)
    return w[0].capitalize() if w else ""


def surname(full: str) -> str:
    w = _words(full)
    return w[-1].capitalize() if len(w) > 1 else ""


def run_pool(args, jobs, fn, label, unit="it"):
    """Run fn over jobs in parallel with a progress bar. Returns {job_index: result}."""
    results, failed = {}, 0
    if not jobs:
        say(f"{label}: nothing to do.")
        return results
    with bar(len(jobs), label, unit) as pb, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fn, j): i for i, j in enumerate(jobs)}
        for f in as_completed(futs):
            try:
                results[futs[f]] = f.result()
            except Exception as e:  # noqa: BLE001
                failed += 1
                pb.write(f"  ! {str(e)[:300]}")
            pb.update(1)
            if failed:
                pb.set_postfix_str(f"{failed} failed")
    if failed:
        say(f"{label}: {failed} of {len(jobs)} failed (re-run the command to retry them)")
        FAILURES.append((label, failed, len(jobs)))
    return results


FAILURES = []   # (label, failed, total) for every parallel batch with failures in this run


def exit_code_for_failures():
    """0 if (nearly) everything worked; 3 if more than 10% of any batch failed, so overnight.py
    reports the step instead of calling it ok."""
    bad = [(l, f, t) for l, f, t in FAILURES if f > max(1, 0.1 * t)]
    if bad:
        say("MOSTLY FAILED: " + "; ".join(f"{l} {f}/{t}" for l, f, t in bad))
        return 3
    return 0


# --------------------------------------------------------------------------- 1. generate

def cmd_generate(args):
    path = args.data / "stories.jsonl"
    existing = Counter(r["prompt"] for r in read_jsonl(path))
    jobs = []
    for p in STORY_PROMPTS:
        jobs += [p] * max(0, args.n - existing[p])
    random.shuffle(jobs)
    print(f"{sum(existing.values())} stories already saved; generating {len(jobs)} more "
          f"(temperature {args.temperature}, {args.workers} parallel).")

    def one(prompt):
        text, resp = chat(args, [{"role": "user", "content": prompt}], args.temperature, args.max_tokens)
        if len(text) < 200:
            raise RuntimeError(f"suspiciously short story ({len(text)} chars)")
        append_jsonl(path, {
            "id": f"s{time.time_ns()}{random.randint(0, 999):03d}",
            "prompt": prompt,
            "temperature": args.temperature,
            "model": resp.get("model", args.model or "unknown"),
            "text": text,
        })

    run_pool(args, jobs, one, "Writing stories", "story")


# --------------------------------------------------------------------------- 2. extract

def cmd_extract(args):
    stories = read_jsonl(args.data / "stories.jsonl")
    out = args.data / "characters.jsonl"
    seen = {r["story_id"] for r in read_jsonl(out)}
    jobs = [s for s in stories if s["id"] not in seen]
    print(f"{len(seen)} stories already extracted; extracting {len(jobs)}.")
    use_schema = {"ok": not args.no_schema}

    def one(story):
        messages = [{"role": "system", "content": EXTRACT_SYSTEM},
                    {"role": "user", "content": "Story:\n\n" + story["text"] +
                     "\n\nReturn JSON with keys genre, characters, ending_tone."}]
        fmt = {"type": "json_schema", "json_schema": {"name": "characters", "schema": EXTRACT_SCHEMA}}
        try:
            text, _ = chat(args, messages, 0.0, 2500, fmt if use_schema["ok"] else None)
        except RuntimeError as e:
            if use_schema["ok"] and "HTTP 400" in str(e):
                use_schema["ok"] = False  # older llama.cpp: fall back to prompt-only JSON
                say("  (server rejected json_schema; falling back to plain JSON prompting)")
                messages[0]["content"] += "\nRespond with JSON only, matching:\n" + json.dumps(EXTRACT_SCHEMA)
                text, _ = chat(args, messages, 0.0, 2500)
            else:
                raise
        data = parse_json(text)
        append_jsonl(out, {"story_id": story["id"], "prompt": story["prompt"], **data})

    run_pool(args, jobs, one, "Extracting characters", "story")


# --------------------------------------------------------------------------- 3. report

def build_index(args):
    stories = {s["id"]: s for s in read_jsonl(args.data / "stories.jsonl")}
    extracts = read_jsonl(args.data / "characters.jsonl")
    by_name = defaultdict(list)
    by_surname = defaultdict(list)
    for ex in extracts:
        chars = ex.get("characters") or []
        names_here = {first_name(c.get("name", "")) for c in chars} - {""}
        for c in chars:
            fn = first_name(c.get("name", ""))
            if not fn:
                continue
            rec = {
                **c,
                "_story": ex["story_id"],
                "_prompt": ex.get("prompt") or stories.get(ex["story_id"], {}).get("prompt"),
                "_genre": (ex.get("genre") or "unknown").lower(),
                "_ending": ex.get("ending_tone", "unknown"),
                "_with": sorted(names_here - {fn}),
            }
            by_name[fn].append(rec)
            sn = surname(c.get("name", ""))
            if sn:
                by_surname[sn].append(rec)
    return stories, extracts, by_name, by_surname


def pct(counter: Counter, n: int, k: int = 5):
    return ", ".join(f"{v} {round(100 * c / n)}%" for v, c in counter.most_common(k)) or "-"


def name_stats(apps, total_stories):
    n_stories = len({a["_story"] for a in apps})
    low = lambda key: Counter((a.get(key) or "unknown").strip().lower() for a in apps)
    traits = Counter(t.strip().lower() for a in apps for t in (a.get("traits") or []) if t.strip())
    return {
        "appearances": len(apps),
        "stories": n_stories,
        "share_of_all_stories": round(100 * n_stories / max(total_stories, 1), 1),
        "full_names": Counter(a.get("name", "").strip() for a in apps).most_common(8),
        "gender": low("gender").most_common(),
        "age": low("age").most_common(),
        "role": low("role").most_common(),
        "occupation": low("occupation").most_common(10),
        "setting": low("setting").most_common(8),
        "traits": traits.most_common(15),
        "genre": Counter(a["_genre"] for a in apps).most_common(6),
        "prompt": Counter(a["_prompt"] for a in apps).most_common(),
        "ending_tone": Counter(a["_ending"] for a in apps).most_common(),
        "keeps_company_with": Counter(w for a in apps for w in a["_with"]).most_common(8),
    }


def cmd_report(args):
    stories, extracts, by_name, by_surname = build_index(args)
    total = len(extracts)
    if not total:
        sys.exit("Nothing extracted yet - run `extract` first.")
    ranked = sorted(by_name.items(), key=lambda kv: -len({a["_story"] for a in kv[1]}))
    ranked = [(n, a) for n, a in ranked if len({x["_story"] for x in a}) >= args.min_stories]

    stats = {n: name_stats(a, total) for n, a in ranked}
    (args.data / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    all_names = sum(len(a) for a in by_name.values())
    top10 = {n for n, _ in ranked[:10]}
    stories_with_top10 = sum(1 for ex in extracts
                             if top10 & {first_name(c.get("name", "")) for c in ex.get("characters") or []})
    endings = Counter(ex.get("ending_tone", "unknown") for ex in extracts)

    L = ["# Ghosts in the machine - story report",
         "",
         f"- Stories analysed: **{total}**  (generated: {len(stories)})",
         f"- Named character appearances: **{all_names}**, distinct first names: **{len(by_name)}**",
         f"- Stories containing at least one of the top 10 names: **{stories_with_top10} "
         f"({round(100 * stories_with_top10 / total)}%)**",
         f"- Ending tone across all stories: {pct(endings, total, 6)}",
         "",
         f"## Leaderboard (names in >= {args.min_stories} stories)",
         "",
         "| # | Name | Stories | % of all | Usual role | Usual job | Top traits |",
         "|---|------|---------|----------|------------|-----------|------------|"]
    for i, (n, _) in enumerate(ranked, 1):
        s = stats[n]
        L.append(f"| {i} | {n} | {s['stories']} | {s['share_of_all_stories']}% | "
                 f"{s['role'][0][0]} | {s['occupation'][0][0]} | "
                 f"{', '.join(t for t, _ in s['traits'][:4])} |")

    sur = sorted(by_surname.items(), key=lambda kv: -len({a["_story"] for a in kv[1]}))
    sur = [(n, a) for n, a in sur if len({x["_story"] for x in a}) >= args.min_stories]
    L += ["", "## Surname leaderboard", "", "| # | Surname | Stories | First names it attaches to |",
          "|---|---------|---------|----------------------------|"]
    for i, (n, apps) in enumerate(sur[:20], 1):
        firsts = Counter(first_name(a.get("name", "")) for a in apps).most_common(5)
        L.append(f"| {i} | {n} | {len({a['_story'] for a in apps})} | "
                 f"{', '.join(f'{f} ({c_})' for f, c_ in firsts)} |")

    for n, apps in (_tqdm(ranked[:args.top], desc="Building report", unit="name")
                    if _tqdm else ranked[:args.top]):
        s = stats[n]
        k = s["appearances"]
        c = lambda pairs: pct(Counter(dict(pairs)), k)
        L += ["", f"## {n}", "",
              f"- In **{s['stories']}** stories ({s['share_of_all_stories']}% of all)",
              f"- Full names: {', '.join(f'{x} ({c_})' for x, c_ in s['full_names'])}",
              f"- Gender: {c(s['gender'])}  |  Age: {c(s['age'])}",
              f"- Role: {c(s['role'])}",
              f"- Occupation: {c(s['occupation'])}",
              f"- Setting: {c(s['setting'])}",
              f"- Traits: {', '.join(f'{t} ({x})' for t, x in s['traits'])}",
              f"- Ending tone of their stories: {c(s['ending_tone'])}",
              f"- Keeps company with: {', '.join(f'{x} ({c_})' for x, c_ in s['keeps_company_with']) or '-'}",
              f"- Shows up for prompts: {', '.join(f'{p!r} ({c_})' for p, c_ in s['prompt'])}",
              "", "Sample goals / wounds / fates:"]
        for a in random.sample(apps, min(4, len(apps))):
            L.append(f"  - wants *{a.get('goal', '?')}*; haunted by *{a.get('wound', '?')}*; ends *{a.get('fate', '?')}*")

    out = args.data / "report.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {out} and stats.json  ({len(ranked)} names in >= {args.min_stories} stories)")
    for i, (n, _) in enumerate(ranked[:15], 1):
        print(f"  {i:2}. {n:<14} {stats[n]['stories']:>4} stories  {stats[n]['share_of_all_stories']:>5}%")


# --------------------------------------------------------------------------- 4. profile

def cmd_profile(args):
    _, extracts, by_name, by_surname = build_index(args)
    total = len(extracts)
    ranked = sorted(by_name.items(), key=lambda kv: -len({a["_story"] for a in kv[1]}))
    if args.names:
        # a name can be a first name (Elara) or a surname (Voss); first names win
        ranked = []
        for x in args.names.split(","):
            x = x.strip().capitalize()
            apps = by_name.get(x) or by_surname.get(x)
            if apps:
                ranked.append((x, apps))
            else:
                print(f"  (no appearances of {x})")
    else:
        ranked = ranked[:args.top]
    sheets = args.data / "sheets"
    sheets.mkdir(exist_ok=True)

    def one(item):
        name, apps = item
        stats = name_stats(apps, total)
        fields = ("name", "gender", "age", "role", "occupation", "setting", "traits",
                  "goal", "wound", "flaw", "arc", "fate", "relationships")
        sample = random.sample(apps, min(args.samples, len(apps)))
        samples = "\n".join(json.dumps({**{k: a.get(k) for k in fields}, "ending": a["_ending"]},
                                       ensure_ascii=False) for a in sample)
        prompt = PROFILE_TEMPLATE.format(name=name, n=len(apps), total=total,
                                         stats=json.dumps(stats, indent=1, ensure_ascii=False),
                                         samples=samples)
        text, _ = chat(args, [{"role": "system", "content": PROFILE_SYSTEM},
                              {"role": "user", "content": prompt}], 0.4, 2500)
        (sheets / f"{name}.md").write_text(text + "\n", encoding="utf-8")

    run_pool(args, ranked, one, "Writing character sheets", "sheet")
    print(f"Character sheets in {sheets}/")


# --------------------------------------------------------------------------- 5. probe
#
# For each name, fill a few neutral sentence frames ("{name} was the kind of person who was")
# and read the model's probability for each trait word coming next. Compare with the same
# frames filled with plain baseline names (David, Sarah...). The difference, in bits, is the
# name's pull towards that trait: +1 = twice as likely as for a plain name, -1 = half as likely.

# Frames end on words that almost force an adjective next ("very ___"), so the traits
# get a real share of the probability instead of living in the far tail.
# Check what the model wants to say with:  ghosts.py probe --check-frames
PROBE_TEMPLATES = [
    "{name} was very",
    "{name} was extremely",
    "Everyone who knew {name} said {name} was very",
    "Above all else, {name} was incredibly",
    "{name} seemed so",
    "People often described {name} as very",
]

# By default each frame is put in the model's own chat format: the user asks for a sentence
# about the name, and the model's answer starts with the frame. Chat-tuned (and especially
# "uncensored" fine-tuned) models can be badly broken at continuing raw text, but answer
# normally in chat. Use --raw to send the bare frame instead.
PROBE_INSTRUCTION = "Write one sentence describing the personality of a character named {name}."

PROBE_NAMES = ["Kaelen", "Elara", "Lyra", "Soren", "Voss", "Elias", "Marcus", "Elena",
               "Seraphina", "Thorne", "Silas", "Mara", "Kira", "Aris", "Vance", "Vex"]

BASELINE_NAMES = ["David", "Sarah", "Michael", "Emily", "James", "Laura",
                  "John", "Anna", "Robert", "Mary", "Daniel", "Rachel"]

# Made-up names: harsh-sounding vs soft-sounding. If the model sorts them into
# villains and sweethearts, that's sound symbolism (bouba/kiki), not memory of books.
INVENTED_NAMES = ["Vorrak", "Grishnak", "Kragthul", "Zorvex",
                  "Lumie", "Miwela", "Oona", "Liloa"]

PROBE_TRAITS = ["grumpy", "kind", "gentle", "cold", "cruel", "brave", "shy", "wise", "naive",
                "lonely", "ambitious", "loyal", "arrogant", "mysterious", "cheerful", "stern",
                "curious", "brilliant", "reckless", "patient", "bitter", "warm", "proud", "quiet",
                "charming", "cunning", "honest", "stubborn", "fierce", "calm", "sad", "angry",
                "funny", "beautiful", "strong", "clever", "lazy", "generous", "greedy", "dangerous"]


def post(args, path, body):
    req = urllib.request.Request(args.url.rstrip("/") + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{path}: HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
        except Exception as e:  # noqa: BLE001
            last = repr(e)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{path}: {last}")


def tokenize(args, text):
    toks = post(args, "/tokenize", {"content": text, "add_special": False}).get("tokens", [])
    return [t["id"] if isinstance(t, dict) else t for t in toks]


_template_cache = {}
_template_lock = threading.Lock()


def probe_prompt(args, name, frame, instruction=None):
    """The text sent to /completion for one name + frame (the model's answer starts with the frame)."""
    text = frame.format(name=name)
    if args.raw:
        return text
    instr = (instruction or PROBE_INSTRUCTION).format(name=name)
    with _template_lock:
        cached = _template_cache.get(instr)
    if cached is None:
        msg = [{"role": "user", "content": instr}]
        try:
            r = post(args, "/apply-template", {"messages": msg, "add_generation_prompt": True,
                                                "chat_template_kwargs": {"enable_thinking": False}})
            cached = r["prompt"]
        except Exception as e:  # noqa: BLE001
            sys.exit(f"Couldn't get the chat template from the server ({e}). "
                     "Update llama.cpp, or run the probe with --raw.")
        # If the template opens a thinking block, close it so the answer starts straight away.
        if re.search(r"<think>\s*$", cached):
            cached += "\n</think>\n\n"
        # Some models (Gemma 4) open every answer with a thought block, empty when thinking is off.
        # Let the model write that opening itself, so our frame starts where its answer really starts.
        opening = answer_opening(args, cached)
        if opening:
            cached += opening
        with _template_lock:
            if opening and not _template_cache.get("_said"):
                _template_cache["_said"] = True
                say(f"  (the model opens its answers with {opening!r}; frames start after it)")
            _template_cache[instr] = cached
    return cached + text


def answer_opening(args, prompt):
    """Greedily generate the first few tokens of the answer; if they contain an end-of-thinking
    marker, return the text up to and including it (special tokens spelled out)."""
    try:
        r = post(args, "/completion", {"prompt": prompt, "n_predict": 32, "temperature": 0,
                                       "return_tokens": True, "cache_prompt": True})
        toks = [t["id"] if isinstance(t, dict) else t for t in (r.get("tokens") or [])]
        if not toks:
            return ""
        ends = set()
        for marker in ("<channel|>", "</think>"):
            ids = [t["id"] if isinstance(t, dict) else t for t in
                   post(args, "/tokenize", {"content": marker, "add_special": False,
                                            "parse_special": True}).get("tokens", [])]
            if len(ids) == 1:
                ends.add(ids[0])
        for i, tid in enumerate(toks):
            if tid in ends:
                return post(args, "/detokenize", {"tokens": toks[:i + 1]}).get("content", "")
    except Exception:  # noqa: BLE001
        pass
    return ""


def next_token_logprobs(args, prompt):
    """Top-N next-token log-probabilities from llama-server's /completion endpoint.
    Returns ({token_id: logprob}, {token_text: logprob}, floor) where floor is the
    smallest logprob returned, i.e. an upper bound for anything not in the list."""
    resp = post(args, "/completion", {
        "prompt": prompt, "n_predict": 1, "n_probs": args.n_probs,
        "temperature": 1.0, "post_sampling_probs": False, "cache_prompt": True,
    })
    cp = resp.get("completion_probabilities") or []
    if not cp:
        raise RuntimeError("server returned no probabilities - is this llama-server's /completion?")
    first = cp[0]
    by_id, by_text = {}, {}
    if "top_logprobs" in first:                      # current llama.cpp format
        for e in first["top_logprobs"]:
            by_id[e.get("id")] = e["logprob"]
            by_text[e.get("token")] = e["logprob"]
    else:                                            # older format: probabilities
        for e in first.get("top_probs") or first.get("probs") or []:
            lp = math.log(max(e["prob"], 1e-30))
            if "id" in e:
                by_id[e["id"]] = lp
            by_text[e.get("token", e.get("tok_str"))] = lp
    floor = min(by_text.values()) if by_text else -30.0
    return by_id, by_text, floor


def check_frames(args, frames, names, traits):
    """Show what the model actually wants to say next, and how much of that the traits cover."""
    trait_tok = {}
    for t in traits:
        ids = tokenize(args, " " + t)
        if len(ids) == 1:
            trait_tok[ids[0]] = t
    for name in names:
        print(f"\n=== {name}")
        for i, f in enumerate(frames):
            prompt = probe_prompt(args, name, f)
            if i == 0 and name == names[0]:
                print("  (exact text sent for the first frame:)\n  " + repr(prompt))
            by_id, by_text, _ = next_token_logprobs(args, prompt)
            top = sorted(by_text.items(), key=lambda kv: -kv[1])[:8]
            mass = sum(math.exp(lp) for i, lp in by_id.items() if i in trait_tok)
            print(f"  {f.format(name=name)!r}")
            print(f"     traits cover {100 * mass:5.2f}% of next-word probability | top: "
                  + ", ".join(f"{tok!r} {100 * math.exp(lp):.0f}%" for tok, lp in top))
    print("\nA good frame gives the traits a few % or more, and its top words are mostly adjectives.")


def cmd_probe(args):
    global PROBE_TEMPLATES
    if args.frames:
        PROBE_TEMPLATES = [f.strip() for f in args.frames.split("|") if "{name}" in f]
        if not PROBE_TEMPLATES:
            sys.exit("--frames needs at least one frame containing {name}, separated by |")
    # ---- which names
    if args.names:
        names = [x.strip() for x in args.names.split(",") if x.strip()]
    elif args.from_report:
        stats_path = args.data / "stats.json"
        if not stats_path.exists():
            sys.exit("No stats.json yet - run `report` first, or pass --names.")
        names = list(json.loads(stats_path.read_text(encoding="utf-8")))[:args.from_report]
    else:
        names = list(PROBE_NAMES)
    groups = {n: "cast" for n in names}
    if args.invented:
        for n in INVENTED_NAMES:
            groups.setdefault(n, "invented")
    traits = [t.strip() for t in (args.traits.split(",") if args.traits else PROBE_TRAITS) if t.strip()]
    if args.check_frames:
        return check_frames(args, PROBE_TEMPLATES, ["David", "Sarah"] + list(groups)[:2], traits)

    # ---- traits must be a single token (with leading space) to be scored exactly
    trait_id = {}
    for t in (_tqdm(traits, desc="Tokenizing traits", unit="trait") if _tqdm else traits):
        ids = tokenize(args, " " + t)
        if len(ids) == 1:
            trait_id[t] = ids[0]
    dropped = [t for t in traits if t not in trait_id]
    if dropped:
        say(f"Skipping multi-token traits (can't score exactly): {', '.join(dropped)}")
    traits = [t for t in traits if t in trait_id]
    if not traits:
        sys.exit("No single-token traits left to score.")

    # ---- one request per (name, template); each gives the whole next-word distribution
    all_names = list(groups) + [b for b in BASELINE_NAMES if b not in groups]
    jobs = [(n, tpl) for n in all_names for tpl in PROBE_TEMPLATES]
    say(f"Probing {len(groups)} names (+{len(all_names) - len(groups)} baselines) x "
        f"{len(PROBE_TEMPLATES)} sentence frames x {len(traits)} traits")

    def one(job):
        name, tpl = job
        by_id, by_text, floor = next_token_logprobs(args, probe_prompt(args, name, tpl))
        row = {}
        for t in traits:
            lp = by_id.get(trait_id[t], by_text.get(" " + t))
            row[t] = (lp, False) if lp is not None else (floor, True)  # True = below top-N cutoff
        return row

    res = run_pool(args, jobs, one, "Probing", "prompt")
    if not res:
        sys.exit("Every probe request failed - check the server URL and that it's llama-server.")

    # ---- which way does the model read each name: he or she?
    # "beautiful" etc. are gendered, so each name is compared with same-gender plain names.
    pron = {p: tokenize(args, " " + p) for p in ("he", "she")}
    gender_frames = ["{name} smiled, and then", "I asked {name} what was wrong, but"]
    gjobs = [(n, f) for n in groups for f in gender_frames]

    def gone(job):
        name, frame = job
        by_id, by_text, floor = next_token_logprobs(args, probe_prompt(args, name, frame))
        get = lambda p: by_id.get(pron[p][0], by_text.get(" " + p, floor)) if len(pron[p]) == 1 else floor
        return get("he") - get("she")

    gres = run_pool(args, gjobs, gone, "Checking he/she", "prompt")
    lean = defaultdict(list)
    for i, v in gres.items():
        lean[gjobs[i][0]].append(v / math.log(2))
    gender = {}
    for n in groups:
        b = sum(lean[n]) / len(lean[n]) if lean[n] else 0.0
        gender[n] = "male" if b > 1 else "female" if b < -1 else "mixed"

    # ---- per sentence frame: absolute logprob, and logprob *relative to the other traits*
    # Relative = "given the model is about to say one of these traits, which one?"
    # That removes the overall shift where odd names make ANY adjective less likely.
    acc_abs = defaultdict(lambda: defaultdict(list))
    acc_rel = defaultdict(lambda: defaultdict(list))
    acc_cap = defaultdict(lambda: defaultdict(list))
    acc_lse = defaultdict(list)
    for i, row in res.items():
        name = jobs[i][0]
        lps = [lp for lp, _ in row.values()]
        m = max(lps)
        lse = m + math.log(sum(math.exp(x - m) for x in lps))
        acc_lse[name].append(lse)
        for t, (lp, capped) in row.items():
            acc_abs[name][t].append(lp)
            acc_rel[name][t].append(lp - lse)
            acc_cap[name][t].append(capped)
    avg = lambda v: sum(v) / len(v)
    mean_abs = {n: {t: avg(v) for t, v in d.items()} for n, d in acc_abs.items()}
    mean_rel = {n: {t: avg(v) for t, v in d.items()} for n, d in acc_rel.items()}
    mean_lse = {n: avg(v) for n, v in acc_lse.items()}
    all_capped = {n: {t: all(v) for t, v in d.items()} for n, d in acc_cap.items()}

    male_b = [b for b in BASELINE_NAMES[0::2] if b in mean_abs and b not in groups]   # David, Michael...
    female_b = [b for b in BASELINE_NAMES[1::2] if b in mean_abs and b not in groups]  # Sarah, Emily...
    pools = {"male": male_b or female_b, "female": female_b or male_b, "mixed": male_b + female_b}
    if not pools["mixed"]:
        sys.exit("All baseline requests failed - nothing to compare against.")
    base_rel = {g: {t: avg([mean_rel[b][t] for b in bs]) for t in traits} for g, bs in pools.items()}
    base_abs = {g: {t: avg([mean_abs[b][t] for b in bs]) for t in traits} for g, bs in pools.items()}
    base_lse = {g: avg([mean_lse[b] for b in bs]) for g, bs in pools.items()}

    probed = [n for n in groups if n in mean_abs]
    coverage = 100 * math.exp(base_lse["mixed"])
    if coverage < 1:
        say(f"WARNING: the traits only get {coverage:.3f}% of next-word probability for plain names - "
            "the sentence frames aren't producing adjectives, so results will be noisy. "
            "Try `probe --check-frames`.")
    L2 = math.log(2)
    lift = {n: {t: (mean_rel[n][t] - base_rel[gender[n]][t]) / L2 for t in traits} for n in probed}
    lift_abs = {n: {t: (mean_abs[n][t] - base_abs[gender[n]][t]) / L2 for t in traits} for n in probed}
    adj_shift = {n: (mean_lse[n] - base_lse[gender[n]]) / L2 for n in probed}

    # ---- outputs
    with (args.data / "probe.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "group", "read_as", "trait", "lift_bits", "lift_abs_bits",
                    "adjective_shift_bits", "logprob", "below_top_n"])
        for n in probed:
            for t in traits:
                w.writerow([n, groups[n], gender[n], t, round(lift[n][t], 3), round(lift_abs[n][t], 3),
                            round(adj_shift[n], 3), round(mean_abs[n][t], 4), all_capped[n][t]])

    L = ["# Name -> trait associations (next-word probability probe)", "",
         "**Lift** (bits) = how much more the model favours this trait *over the other traits* after this "
         "name, compared with plain names of the same gender. +1 = twice as favoured, +2 = 4x, -1 = half. "
         f"Averaged over {len(PROBE_TEMPLATES)} sentence frames.", "",
         f"Baselines - male: {', '.join(male_b)}; female: {', '.join(female_b)}; "
         "names the model reads as neither use both.", "",
         "**Adjective shift** = how much more or less likely ANY of these traits is after the name. "
         "Strongly negative means the model expects something other than an adjective "
         "(the name itself is doing the describing).", "",
         f"Health check: for plain names, these traits together take **{coverage:.2f}%** of the "
         "next-word probability (a few % or more is good; well under 1% means the frames aren't "
         "producing adjectives and the numbers are noisy).", "",
         f"Traits outside the top {args.n_probs} next-words for every frame are too uncertain to rank and are "
         "left out of the lists (shown grey in the heatmap).", ""]
    for n in probed:
        ok = [t for t in traits if not all_capped[n][t]]
        ranked_t = sorted(ok, key=lambda t: -lift[n][t])
        fmt = lambda t: f"{t} {lift[n][t]:+.1f}"
        k = min(6, len(ranked_t) // 2)
        rough = len(traits) - len(ok)
        L += [f"## {n}" + (" (invented)" if groups[n] == "invented" else ""),
              f"- Read as: **{gender[n]}**  |  adjective shift: {adj_shift[n]:+.1f} bits"
              + (f"  |  {rough} traits too rare to score" if rough else ""),
              f"- **Pulls towards:** {', '.join(fmt(t) for t in ranked_t[:k]) or '-'}",
              f"- **Pushes away from:** {', '.join(fmt(t) for t in ranked_t[::-1][:min(4, len(ranked_t) - k)]) or '-'}",
              ""]
    (args.data / "probe.md").write_text("\n".join(L), encoding="utf-8")

    write_heatmap(args.data / "probe_heatmap.html", probed, groups, traits, lift, all_capped,
                  pools["mixed"], gender)
    say(f"Wrote probe.csv, probe.md and probe_heatmap.html to {args.data}/")
    for n in probed[:12]:
        top = sorted([t for t in traits if not all_capped[n][t]], key=lambda t: -lift[n][t])[:3]
        say(f"  {n:<12} ({gender[n]:<6}) -> " + ", ".join(f"{t} ({lift[n][t]:+.1f})" for t in top))


def write_heatmap(path, names, groups, traits, lift, capped, baselines, gender=None):
    # order traits by their average lift so the picture has some structure
    traits = sorted(traits, key=lambda t: -sum(lift[n][t] for n in names) / len(names))
    gender = gender or {}

    def colour(v):
        x = max(-1.0, min(1.0, v / 3.0))  # saturate at +-3 bits (8x)
        if x >= 0:
            return f"rgba(214, 96, 77, {x:.2f})"
        return f"rgba(67, 147, 195, {-x:.2f})"

    head = "".join(f'<th class="t"><div>{html.escape(t)}</div></th>' for t in traits)
    rows = []
    last_group = None
    for n in names:
        if last_group and groups[n] != last_group:
            rows.append(f'<tr class="sep"><td colspan="{len(traits) + 1}">invented names</td></tr>')
        last_group = groups[n]
        cells = "".join(
            f'<td style="background:{"#e6e6e6" if capped[n][t] else colour(lift[n][t])}'
            f'{";color:#aaa" if capped[n][t] else ""}" title="{html.escape(n)} / {html.escape(t)}: '
            f'{lift[n][t]:+.2f} bits ({2 ** lift[n][t]:.2f}x){" - below top-N, rough" if capped[n][t] else ""}">'
            f'{lift[n][t]:+.1f}</td>' for t in traits)
        g = {"male": " &#9794;", "female": " &#9792;"}.get(gender.get(n), "")
        rows.append(f'<tr><th class="n">{html.escape(n)}{g}</th>{cells}</tr>')
    path.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Name trait heatmap</title><style>
body{{font-family:system-ui,sans-serif;background:#fff;color:#222;margin:24px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;font-size:12px}}
td{{width:34px;height:26px;text-align:center;border:1px solid #fff;color:#333}}
th.n{{text-align:right;padding-right:8px;white-space:nowrap}}
th.t{{height:90px;vertical-align:bottom;padding:0}}
th.t div{{writing-mode:vertical-rl;transform:rotate(180deg);font-weight:500;padding:4px 0}}
tr.sep td{{text-align:left;font-style:italic;color:#888;height:22px;border:none}}
p{{max-width:760px;line-height:1.5}}
</style></head><body>
<h1>How strongly each name pulls towards each trait</h1>
<p>Each cell shows how much more the model favours a trait word, <i>relative to the other traits</i>,
after this name than after plain names of the same gender ({html.escape(', '.join(baselines))}).
Units are bits: <b>+1</b> = twice as favoured, <b>+2</b> four times, <b>-1</b> half. Red = pull,
blue = push, grey = too rare to measure. &#9794;/&#9792; = how the model reads the name.
Hover a cell for details.</p>
<div class="wrap"><table><tr><th></th>{head}</tr>{''.join(rows)}</table></div>
</body></html>""", encoding="utf-8")


# --------------------------------------------------------------------------- 6. bio
#
# Ask the model to invent a character from nothing but a name, many times over, extract each
# one with the same schema as the stories, and compare: who is "Elias" when you just ask?

BIO_PROMPTS = [
    "Write a short fictional biography of a character named {name}.",
    "Invent a character called {name} for a novel and describe them in one paragraph: "
    "who they are, what they do, what they want, and what haunts them.",
    "Tell me about {name}, a fictional character. One paragraph.",
]

BIO_NAMES = ["Elias", "Elara", "Clara", "Kaelen", "Kael", "Julian", "Leo", "Silas",
             "Thorne", "Mara"]
BIO_CONTROLS = ["David", "Sarah"]          # plain names, for contrast
BIO_INVENTED = ["Vorrak", "Lumie"]

BIO_SYSTEM = """You are a literary analyst. The text invents a character named {name}.
Describe {name} only (ignore other characters). Be faithful to the text; write "unknown" for
anything not stated or clearly implied. Traits: at most 6 single adjectives.
world = the kind of setting: e.g. contemporary, fantasy, science fiction, historical, gothic, post-apocalyptic."""

_item = EXTRACT_SCHEMA["properties"]["characters"]["items"]
BIO_SCHEMA = {
    "type": "object",
    "properties": {
        "world": {"type": "string"},
        **{k: v for k, v in _item["properties"].items() if k not in ("name", "role", "arc", "relationships")},
    },
    "required": ["world"] + [k for k in _item["required"] if k not in ("name", "role", "arc", "relationships")],
}


def cmd_bio(args):
    if args.names:
        names = [x.strip() for x in args.names.split(",") if x.strip()]
    elif args.from_report:
        sp = args.data / "stats.json"
        if not sp.exists():
            sys.exit("No stats.json yet - run `report` first, or pass --names.")
        names = list(json.loads(sp.read_text(encoding="utf-8")))[:args.from_report]
    else:
        names = list(BIO_NAMES)
    if not args.no_controls:
        names += [n for n in BIO_CONTROLS + BIO_INVENTED if n not in names]

    # ---- 1. generate
    bios_path = args.data / "bios.jsonl"
    have = Counter((r["name"], r["prompt"]) for r in read_jsonl(bios_path))
    jobs = [(n, p) for n in names for p in BIO_PROMPTS for _ in range(max(0, args.n - have[(n, p)]))]
    random.shuffle(jobs)

    def gen(job):
        name, ptpl = job
        text, _ = chat(args, [{"role": "user", "content": ptpl.format(name=name)}],
                       args.temperature, args.max_tokens)
        if len(text) < 80:
            raise RuntimeError(f"suspiciously short biography ({len(text)} chars)")
        append_jsonl(bios_path, {"id": f"b{time.time_ns()}{random.randint(0, 999):03d}",
                                 "name": name, "prompt": ptpl, "text": text})

    run_pool(args, jobs, gen, "Writing biographies", "bio")

    # ---- 2. extract
    ex_path = args.data / "bio_characters.jsonl"
    done = {r["bio_id"] for r in read_jsonl(ex_path)}
    todo = [b for b in read_jsonl(bios_path) if b["id"] not in done and b["name"] in names]
    fmt = {"type": "json_schema", "json_schema": {"name": "bio", "schema": BIO_SCHEMA}}

    def ext(b):
        msgs = [{"role": "system", "content": BIO_SYSTEM.format(name=b["name"])},
                {"role": "user", "content": "Text:\n\n" + b["text"] + "\n\nReturn JSON."}]
        text, _ = chat(args, msgs, 0.0, 1200, None if args.no_schema else fmt)
        append_jsonl(ex_path, {"bio_id": b["id"], "name": b["name"], **parse_json(text)})

    run_pool(args, todo, ext, "Extracting characters", "bio")

    # ---- 3. compare with the stories
    rows = defaultdict(list)
    for r in read_jsonl(ex_path):
        if r["name"] in names:
            rows[r["name"]].append(r)
    story = {}
    sp = args.data / "stats.json"
    if sp.exists():
        story = json.loads(sp.read_text(encoding="utf-8"))

    def top(items, k):
        c = Counter((x or "unknown").strip().lower() for x in items)
        c.pop("unknown", None)
        return c.most_common(k)

    def fmt_c(pairs, n):
        return ", ".join(f"{v} ({round(100 * c / n)}%)" for v, c in pairs) or "-"

    L = ["# Who are they when you just ask?", "",
         f"Each name was given to the model with {len(BIO_PROMPTS)} different 'invent a character' prompts, "
         f"{args.n} times each, at temperature {args.temperature}. Every biography was then extracted with "
         "the same schema as the stories. Plain names (David, Sarah) and invented names are included for contrast.", ""]
    for n in names:
        rs = rows.get(n, [])
        if not rs:
            continue
        k = len(rs)
        traits = Counter(t.strip().lower() for r in rs for t in (r.get("traits") or []) if t.strip())
        tags = []
        if n in BIO_CONTROLS:
            tags.append("control")
        if n in BIO_INVENTED:
            tags.append("invented")
        L += [f"## {n}" + (f" ({', '.join(tags)})" if tags else ""), "",
              f"**When asked directly** ({k} biographies):",
              f"- World: {fmt_c(top([r.get('world') for r in rs], 5), k)}",
              f"- Age: {fmt_c(top([r.get('age') for r in rs], 4), k)}  |  Gender: {fmt_c(top([r.get('gender') for r in rs], 3), k)}",
              f"- Occupation: {fmt_c(top([r.get('occupation') for r in rs], 6), k)}",
              f"- Setting: {fmt_c(top([r.get('setting') for r in rs], 5), k)}",
              f"- Traits: {', '.join(f'{t} ({c})' for t, c in traits.most_common(12))}"]
        if n in story:
            st = story[n]
            s_tr = [t for t, _ in st["traits"][:12]]
            b_tr = [t for t, _ in traits.most_common(12)]
            shared = [t for t in b_tr if t in s_tr]
            s_jobs = {o for o, _ in st["occupation"][:8]} - {"unknown"}
            b_jobs = {o for o, _ in top([r.get('occupation') for r in rs], 8)}
            L += ["", "**In the stories:**",
                  f"- Occupation: {', '.join(o for o, _ in st['occupation'][:6])}",
                  f"- Traits: {', '.join(s_tr)}",
                  f"- **Overlap:** traits in both top-12 lists: {', '.join(shared) or 'none'}"
                  f" ({len(shared)}/12); shared jobs: {', '.join(sorted(s_jobs & b_jobs)) or 'none'}"]
        L += ["", "Sample:"]
        for r in random.sample(rs, min(3, k)):
            L.append(f"  - *{r.get('age', '?')} {r.get('occupation', '?')}* in *{r.get('setting', '?')}*; "
                     f"wants *{r.get('goal', '?')}*; haunted by *{r.get('wound', '?')}*")
        L.append("")
    out = args.data / "bio_report.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    say(f"Wrote {out}")
    for n in names:
        rs = rows.get(n, [])
        if rs:
            o = top([r.get("occupation") for r in rs], 2)
            say(f"  {n:<10} -> " + (", ".join(f"{v} ({round(100 * c / len(rs))}%)" for v, c in o) or "-"))


# --------------------------------------------------------------------------- 7. roulette
#
# Stop the story at the exact moment a name is due ("...an old keeper named ___") and read the
# model's whole probability distribution over the next word. Run it on several models with
# --label (e.g. base / instruct) into the same --data folder to compare them.

ROULETTE_FRAMES = [
    ("lighthouse", "Once upon a time, in a lighthouse at the edge of the sea, there lived an old keeper named"),
    ("clockmaker", "In a cluttered workshop at the end of a narrow street worked an old clockmaker named"),
    ("starship", "The starship drifted through the dark. At the helm sat its captain, a woman named"),
    ("weaver", "In a small village at the edge of an enchanted forest lived a young weaver named"),
    ("manor", "The old manor had stood empty since the death of its owner, a reclusive man named"),
    ("family", "The kitchen was chaos as usual, and in the middle of it all stood the youngest son, a boy named"),
    ("villain", "The villain of the story was a cold, calculating man named"),
    ("hero-woman", "The hero of our story is a young woman named"),
    ("hero-man", "The hero of our story is a young man named"),
    ("a-man", "This is the story of a man named"),
    ("a-woman", "This is the story of a woman named"),
    ("office", "On Monday morning the firm hired a new accountant, a man named"),
]
ROULETTE_INSTRUCTION = "Write a short story."
_NAMEISH = re.compile(r"^ ?[A-Z][a-zà-ÿ'\-]+$")


ROULETTE_TRACK = ["Elias", "Elara", "Kael", "Kaelen", "Clara", "Silas", "Julian", "Thorne", "Mara",
                  "Lyra", "Seraphina", "Elena", "Leo", "Vance", "Voss", "David", "Thomas"]


def token_pieces(args, word):
    """How the tokenizer splits ' word' (the form a name takes mid-sentence)."""
    r = post(args, "/tokenize", {"content": " " + word, "add_special": False, "with_pieces": True})
    out = []
    for t in r.get("tokens", []):
        if isinstance(t, dict):
            pc = t.get("piece", t.get("id"))
            out.append(pc if isinstance(pc, str) else bytes(pc).decode("utf-8", "replace") if isinstance(pc, list) else str(pc))
        else:
            out.append(f"#{t}")
    return out


def cmd_roulette(args):
    if args.report_only:
        return roulette_report(args)
    default = args.model_key + ("-raw" if args.raw and not args.model_is_base else "")
    label = re.sub(r"[^A-Za-z0-9_\-]+", "-", args.label or default)
    frames = ROULETTE_FRAMES
    say(f"Name roulette '{label}': {len(frames)} settings x top {args.n_probs} next words"
        + (" (raw text)" if args.raw else " (chat format)"))
    jobs = list(frames)

    def one(job):
        key, frame = job
        prompt = probe_prompt(args, "", frame, ROULETTE_INSTRUCTION)
        by_id, by_text, floor = next_token_logprobs(args, prompt)
        probs = {t: math.exp(lp) for t, lp in by_text.items() if t is not None}
        names, best_tok = Counter(), {}
        for t, p in probs.items():
            if _NAMEISH.match(t) and t.strip().lower() not in TITLES | NOT_NAMES:
                names[t.strip()] += p          # " Elias" and "Elias" count as one name
                if p > probs.get(best_tok.get(t.strip()), 0):
                    best_tok[t.strip()] = t
        mass = sum(names.values())
        h = -sum((p / mass) * math.log2(p / mass) for p in names.values() if p > 0) if mass else 0.0
        top = sorted(names.items(), key=lambda kv: -kv[1])[:25]
        # What follows each top name's token? Shows names that are really the first piece of a
        # longer one (" Kael" -> "en") and surnames that travel with them (" Elias" -> " Thorne").
        continues = {}
        for n, _ in top[:5]:
            _, nxt, _ = next_token_logprobs(args, prompt + best_tok[n])
            continues[n] = [[t, math.exp(lp)] for t, lp in sorted(nxt.items(), key=lambda kv: -kv[1])[:6]]
        return key, {"frame": frame, "name_mass": mass, "entropy_bits": h, "effective_names": 2 ** h,
                     "top": [[t, p, p / mass if mass else 0] for t, p in top],
                     "continues": continues,
                     "top_any": [[t, p] for t, p in sorted(probs.items(), key=lambda kv: -kv[1])[:8]]}

    res = run_pool(args, jobs, one, "Spinning name roulette", "setting")
    tokenization = {}
    for n in ROULETTE_TRACK:
        try:
            tokenization[n] = token_pieces(args, n)
        except Exception as e:  # noqa: BLE001
            tokenization[n] = [f"? ({str(e)[:60]})"]
    out = {"label": label, "raw": args.raw, "n_probs": args.n_probs, "source": "llama.cpp",
           "tokenization": tokenization,
           "frames": {k: v for k, v in (res[i] for i in sorted(res))}}
    (args.data / f"roulette_{label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    roulette_report(args)
    for k, v in out["frames"].items():
        t = v["top"][:3]
        say(f"  {k:<11} {', '.join(f'{n} {round(100 * q)}%' for n, _, q in t):<40} "
            f"~{v['effective_names']:.1f} effective names")


def roulette_report(args):
    runs = []
    for f in sorted(args.data.glob("roulette_*.json")):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    if not runs:
        say(f"No roulette_*.json files in {args.data}")
        return
    # before/after chat tuning side by side: GGUF pair, PyTorch pair, then chat-format runs
    pref = ["base", "instruct-raw", "base-bf16", "instruct-bf16-raw", "instruct", "instruct-bf16"]
    runs.sort(key=lambda r: (pref.index(r["label"]) if r["label"] in pref else len(pref), r["label"]))
    labels = [r["label"] for r in runs]
    L = ["# Name roulette", "",
         "Each story is stopped at the moment a name is due, and the model's probability for every "
         "possible next word is read directly. Only capitalised name-like words are counted (titles such as "
         "Mr, Dr and Captain are left out); percentages are shares of that name probability. A name in "
         "several tokens shows up as its first piece (e.g. `El` for Elara, Eleanor, Elena): see the last "
         "section for what follows.", "",
         "**Effective names** = how many equally likely names the choice is worth (2^entropy). "
         "1 = it always picks the same name; 50 = a genuinely open choice. Computed over the top "
         f"{runs[0].get('n_probs', '?')} next words, so it slightly understates the spread.", "",
         "## Summary: effective number of names", "",
         "| Setting | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    keys = [k for k, _ in ROULETTE_FRAMES]
    for k in keys:
        cells = []
        for r in runs:
            v = r["frames"].get(k)
            cells.append(f"{v['effective_names']:.1f} ({v['top'][0][0]} {round(100 * v['top'][0][2])}%)"
                         if v and v["top"] else "-")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    for k in keys:
        frame = next((r["frames"][k]["frame"] for r in runs if k in r["frames"]), "")
        L += ["", f"## {k}", f"*\"{frame} ___\"*", ""]
        for r in runs:
            v = r["frames"].get(k)
            if not v:
                continue
            L.append(f"- **{r['label']}** (~{v['effective_names']:.1f} effective names, names take "
                     f"{round(100 * v['name_mass'])}% of next-word probability): "
                     + ", ".join(f"{n} {100 * q:.0f}%" for n, _, q in v["top"][:10]))
    # how names are tokenised, and what follows their first piece
    tok = next((r["tokenization"] for r in runs if r.get("tokenization")), None)
    if tok:
        L += ["", "## How the tokenizer splits the names", "",
              "Names are written as the model sees them mid-sentence (with a leading space). A name in several "
              "pieces is chosen one piece at a time, so at the naming moment roulette really sees its FIRST piece: "
              "a name like Kaelen can hide inside \"Kael\". The next section shows what follows.", "",
              "| Name | Pieces |", "|---|---|"]
        for n, pcs in tok.items():
            L.append(f"| {n} | {' + '.join('`' + p.replace(chr(9601), ' ') + '`' for p in pcs)} |")
    cont = defaultdict(lambda: defaultdict(list))   # run -> name -> list of continuation lists
    for r in runs:
        for v in r["frames"].values():
            for n, c in (v.get("continues") or {}).items():
                cont[r["label"]][n].append(c)
    if cont:
        L += ["", "## What comes right after the name", "",
              "For each run's most-picked names, the most likely next token after the name's first piece, "
              "averaged over the settings where it was a top-5 pick. A word-ending piece (`en`, `ara`) means the "
              "name is longer than it looks; a surname (` Thorne`) means it travels as a pair.", ""]
        for r in runs:
            items = []
            for n, lists in sorted(cont[r["label"]].items(), key=lambda kv: -len(kv[1])):
                acc = Counter()
                for c in lists:
                    for t, p in c:
                        acc[t] += p / len(lists)
                items.append(f"**{n}** → " + ", ".join(f"`{t}` {100 * p:.0f}%" for t, p in acc.most_common(3)))
            if items:
                L += [f"- **{r['label']}:** " + " · ".join(items[:8])]
    (args.data / "roulette.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    write_roulette_chart(args.data / "roulette.html", runs, keys)
    say(f"Wrote {args.data / 'roulette.md'} and roulette.html ({', '.join(labels)})")


def write_roulette_chart(path, runs, keys):
    """Grouped horizontal bars: effective names per setting, one bar per model, log scale."""
    colours = ["#1b7837", "#5aae61", "#4393c3", "#2166ac", "#d6604d", "#762a83", "#e08214", "#666666"]
    vals = [r["frames"][k]["effective_names"] for r in runs for k in keys if k in r["frames"]]
    hi = max([2.0] + vals)
    top_tick = 10 ** math.ceil(math.log10(hi))
    W, left, right, bh, gap = 760, 120, 40, 12, 14
    pw = W - left - right
    X = lambda v: left + pw * math.log10(max(v, 1)) / math.log10(top_tick)
    rows_h = len(keys) * (len(runs) * bh + gap)
    H = 90 + rows_h + 40
    P = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px" role="img" '
         f'aria-label="Effective number of names at the naming moment, by model">']
    P.append('<text x="24" y="28" class="t">How open is the choice of name?</text>')
    P.append('<text x="24" y="48" class="s">Effective number of names at the naming moment (log scale). '
             '1 = always the same name.</text>')
    for i, r in enumerate(runs):
        P.append(f'<rect x="{left + 130 * i}" y="60" width="10" height="10" fill="{colours[i % len(colours)]}"/>'
                 f'<text x="{left + 130 * i + 14}" y="69" class="s">{html.escape(r["label"])}</text>')
    y0 = 90
    t = 1
    while t <= top_tick:
        P.append(f'<line x1="{X(t)}" x2="{X(t)}" y1="{y0 - 6}" y2="{y0 + rows_h}" class="g"/>'
                 f'<text x="{X(t)}" y="{y0 + rows_h + 16}" text-anchor="middle" class="s">{t:g}</text>')
        t *= 10
    y = y0
    for k in keys:
        P.append(f'<text x="{left - 8}" y="{y + len(runs) * bh / 2 + 4}" text-anchor="end" class="k">{html.escape(k)}</text>')
        for i, r in enumerate(runs):
            v = r["frames"].get(k)
            if v:
                e = v["effective_names"]
                top = v["top"][0][0] if v["top"] else ""
                P.append(f'<rect x="{left}" y="{y}" width="{max(X(e) - left, 1):.1f}" height="{bh - 2}" '
                         f'fill="{colours[i % len(colours)]}"><title>{html.escape(r["label"])}: {e:.1f} effective names '
                         f'(top: {html.escape(top)})</title></rect>'
                         f'<text x="{X(e) + 4:.1f}" y="{y + bh - 3}" class="v">{e:.1f}</text>')
            y += bh
        y += gap
    P.append("</svg>")
    path.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Name roulette</title>
<style>:root{{--fg:#222;--bg:#fff;--q:#666;--g:#ddd}}@media (prefers-color-scheme:dark){{:root{{--fg:#eee;--bg:#1b1b1b;--q:#aaa;--g:#3a3a3a}}}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:24px}}
.t{{font-size:16px;font-weight:600;fill:var(--fg)}} .s{{font-size:12px;fill:var(--q)}} .k{{font-size:12.5px;fill:var(--fg)}}
.v{{font-size:10.5px;fill:var(--q)}} .g{{stroke:var(--g)}}</style></head><body>{"".join(P)}</body></html>""",
                    encoding="utf-8")


# --------------------------------------------------------------------------- 8. swap
#
# Is the story chosen before the name, or does the name summon the story?
#   --mode open : the model's story is forced to START with the name ("Elias ..."), so the name
#                 comes before any setting exists. Does "Elias" bring the lighthouse with him?
#   --mode cut  : real stories are cut at the first mention of --target (Elias) and continued with
#                 a different name. A control re-continues with the original name. If David keeps
#                 the lighthouse as often as the re-sampled Elias does, the setting was already
#                 decided; if the lighthouse fades, the name was carrying it.

SWAP_NAMES = ["Elias", "Elara", "Clara", "Silas", "Kael", "Leo", "David", "Sarah", "Thomas", "Mary",
              "Vorrak", "Lumie"]
SWAP_CUT_VARIANTS = ["David", "Thomas", "Vorrak"]
SWAP_INSTRUCTION = "Write a short story."

# Simple keyword markers counted in the generated text (case-insensitive unless a name).
SWAP_MARKERS = [
    ("lighthouse/sea", r"(?i)lighthouse|\bkeeper\b|\bsea\b|\bocean\b|\btides?\b"),
    ("clocks/workshop", r"(?i)\bclocks?\b|clockmaker|workshop|horolog"),
    ("grief/widowhood", r"(?i)\bgrie(f|v\w*)|\bmourn\w*|\bwidow\w*|late wife"),
    ("Clara", r"\bClara\b"),
    ("Oakhaven/Blackwood", r"Oakhaven|Blackwood"),
    ("other ghosts", None),   # any of GHOSTS except the forced name
    ("space", r"(?i)starship|spaceship|space station|\bgalax\w*|\bspacecraft"),
    ("Miller/Seattle", r"\bMillers?\b|Seattle"),
]
GHOSTS = ["Elias", "Elara", "Kael", "Kaelen", "Silas", "Julian", "Thorne", "Mara", "Lyra", "Clara"]


def marker_hits(text, forced):
    hits = {}
    for label, rx in SWAP_MARKERS:
        if rx is None:
            others = [g for g in GHOSTS if g != forced and not (forced == "Kael" and g == "Kaelen")]
            hits[label] = bool(re.search(r"\b(" + "|".join(others) + r")\b", text))
        else:
            hits[label] = bool(re.search(rx, text))
    return hits


def complete(args, prompt, n_predict):
    r = post(args, "/completion", {"prompt": prompt, "n_predict": n_predict, "temperature": args.temperature,
                                   "top_p": 0.95, "top_k": 64, "seed": random.randint(0, 2**31 - 1),
                                   "cache_prompt": True})
    return strip_thinking(r.get("content") or "")


def cmd_swap(args):
    mode = args.mode
    gen_path = args.data / f"swap_{mode}.jsonl"
    have = read_jsonl(gen_path)

    # ---- 1. generate
    if mode == "open":
        names = [x.strip() for x in args.names.split(",") if x.strip()] if args.names else list(SWAP_NAMES)
        done = Counter(r["name"] for r in have)
        jobs = [(n, None) for n in names for _ in range(max(0, args.n - done[n]))]
    else:
        target = args.target
        variants = [target] + ([x.strip() for x in args.names.split(",") if x.strip()] if args.names
                               else SWAP_CUT_VARIANTS)
        names = variants
        stories = [s for s in read_jsonl(args.data / "stories.jsonl") if re.search(rf"\b{target}\b", s["text"])]
        if not stories:
            n_all = len(read_jsonl(args.data / "stories.jsonl"))
            msg = (f"# Name swap: nothing to cut\n\nNone of the {n_all} stories in this folder mention "
                   f"{target}, so there is nothing to re-continue."
                   + (" That is a finding in itself: this model doesn't use him." if n_all else
                      " Run `generate` first."))
            (args.data / "swap_cut.md").write_text(msg + "\n", encoding="utf-8")
            say(msg.replace("# ", "").replace("\n\n", ": "))
            if not n_all:
                sys.exit(1)
            return
        random.Random(0).shuffle(stories)   # same sample every run, so it resumes cleanly
        stories = stories[:args.n]
        done = {(r["source"], r["name"]) for r in have}
        jobs = [(v, s) for s in stories for v in variants if (s["id"], v) not in done]
    random.shuffle(jobs)
    say(f"Name swap ({mode}): {len(jobs)} stories to write"
        + (f" ({len(have)} already done)" if have else ""))

    def gen(job):
        name, story = job
        if story is None:
            frame = ("Here is a short story.\n\n{name}" if args.raw else "{name}")
            text = name + complete(args, probe_prompt(args, name, frame, SWAP_INSTRUCTION), args.max_tokens)
            rec = {"id": f"w{time.time_ns()}{random.randint(0, 999):03d}", "mode": "open", "name": name, "text": text}
        else:
            m = re.search(rf"\b{args.target}\b", story["text"])
            prefix = story["text"][:m.start()]
            frame = prefix.replace("{", "{{").replace("}", "}}") + "{name}"
            cont = complete(args, probe_prompt(args, name, frame, story.get("prompt") or SWAP_INSTRUCTION),
                            args.max_tokens)
            rec = {"id": f"w{time.time_ns()}{random.randint(0, 999):03d}", "mode": "cut", "name": name,
                   "target": args.target, "source": story["id"], "prefix_chars": len(prefix),
                   "text": prefix + name + cont, "continuation": name + cont}
        if len(rec["text"]) < 150:
            raise RuntimeError(f"suspiciously short story ({len(rec['text'])} chars)")
        append_jsonl(gen_path, rec)

    run_pool(args, jobs, gen, "Writing swapped stories", "story")

    # ---- 2. extract who the forced character became
    ex_path = args.data / f"swap_{mode}_characters.jsonl"
    seen = {r["swap_id"] for r in read_jsonl(ex_path)}
    todo = [r for r in read_jsonl(gen_path) if r["id"] not in seen and r["name"] in names]
    fmt = {"type": "json_schema", "json_schema": {"name": "bio", "schema": BIO_SCHEMA}}

    def ext(r):
        msgs = [{"role": "system", "content": BIO_SYSTEM.format(name=r["name"])},
                {"role": "user", "content": "Text:\n\n" + r["text"] + "\n\nReturn JSON."}]
        text, _ = chat(args, msgs, 0.0, 1200, None if args.no_schema else fmt)
        append_jsonl(ex_path, {"swap_id": r["id"], "name": r["name"], **parse_json(text)})

    run_pool(args, todo, ext, "Extracting characters", "story")

    # ---- 3. report
    gens = [r for r in read_jsonl(gen_path) if r["name"] in names]
    chars = {r["swap_id"]: r for r in read_jsonl(ex_path)}
    by = defaultdict(list)
    for r in gens:
        by[r["name"]].append(r)

    def top(items, k):
        c = Counter((x or "unknown").strip().lower() for x in items)
        c.pop("unknown", None)
        return c.most_common(k)

    def share(pairs, n):
        return ", ".join(f"{v} {round(100 * c / n)}%" for v, c in pairs) or "-"

    if mode == "open":
        L = ["# Name swap: stories forced to start with a name", "",
             f"Each story's first word was fixed to the name (prompt: \"{SWAP_INSTRUCTION}\"), so the name comes "
             "before any setting exists; the model then wrote freely. If a name carries its archetype, its "
             "markers should show up far more often than for plain names (David, Sarah, Thomas, Mary).", ""]
    else:
        L = [f"# Name swap: {args.target}'s stories, re-continued with other names", "",
             f"{len({r['source'] for r in gens})} stories that mention {args.target} were cut at his first "
             f"mention and continued with each name. **{args.target}** is the control (same cut, re-sampled). "
             "Markers are counted in the CONTINUATION only, since the text before the cut is shared. If a new "
             f"name keeps the markers about as often as {args.target}, the story was set before the name; "
             "if they fade, the name was carrying them.", ""]
    marks = [m for m, _ in SWAP_MARKERS]
    L += ["## What comes with the name", "", "| Name | n | " + " | ".join(marks) + " |",
          "|---|---|" + "---|" * len(marks)]
    for n in names:
        rs = by.get(n, [])
        if not rs:
            continue
        cnt = Counter()
        for r in rs:
            for k, v in marker_hits(r["continuation"] if mode == "cut" else r["text"], n).items():
                cnt[k] += v
        L.append(f"| {n} | {len(rs)} | " + " | ".join(f"{round(100 * cnt[m] / len(rs))}%" for m in marks) + " |")
    L += ["", "*Keyword matches, not judgements: e.g. \"lighthouse/sea\" = the text mentions a lighthouse, keeper, "
          "sea, ocean or tide; \"other ghosts\" = another recurring name (Elara, Kael, Silas, Clara...) appears.*",
          "", "## Who the character becomes", "",
          "| Name | World | Age | Job | Top traits |", "|---|---|---|---|---|"]
    for n in names:
        cs = [chars[r["id"]] for r in by.get(n, []) if r["id"] in chars]
        if not cs:
            continue
        k = len(cs)
        traits = Counter(t.strip().lower() for c in cs for t in (c.get("traits") or []) if t.strip())
        L.append(f"| {n} | {share(top([c.get('world') for c in cs], 2), k)} | {share(top([c.get('age') for c in cs], 2), k)} "
                 f"| {share(top([c.get('occupation') for c in cs], 3), k)} | {', '.join(t for t, _ in traits.most_common(5))} |")
    L += ["", "## Sample openings", ""]
    for n in names:
        rs = by.get(n, [])
        if not rs:
            continue
        L.append(f"**{n}**")
        L.append("")
        for r in random.Random(1).sample(rs, min(2, len(rs))):
            snippet = (r["continuation"] if mode == "cut" else r["text"])[:280].replace("\n", " ").strip()
            L.append(f"> {snippet}…")
            L.append("")
    out = args.data / f"swap_{mode}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    say(f"Wrote {out}")


# --------------------------------------------------------------------------- 9. genre
#
# Is sci-fi Mara the same person as romance Mara?
#   forced : each name is made the protagonist (the story's first word) of a story in each genre.
#   natural: the names as they already appear in your stories (data/characters.jsonl), split by the
#            genre the story was asked for.
# For every name x genre we build a profile (traits, age, gender, what haunts them) and compare:
#   same name, different genre   vs   different name, same genre.
# If Mara is more like herself across genres than like the other characters in her genre, the name
# carries a persona. If she's more like her genre-mates, the genre makes the character.

GENRES = [
    ("fantasy", "Write a fantasy story."),
    ("sci-fi", "Write a science fiction story."),
    ("romance", "Write a romance story."),
    ("mystery", "Write a mystery story."),
    ("horror", "Write a horror story."),
    ("family", "Write a story about a family."),
    ("literary", "Write a literary short story set in the present day."),
    ("adventure", "Write an adventure story."),
]
GENRE_NAMES = ["Mara", "Elias", "Elara", "Clara", "Kael", "Silas", "Leo", "Julian", "David", "Sarah"]
PROMPT_GENRE = {
    "Write a fantasy story.": "fantasy", "Write a science fiction story.": "sci-fi",
    "Write a romance story.": "romance", "Write a mystery story.": "mystery",
    "Write a story about a family.": "family", "Write a dark story.": "dark",
    "Write an adventure story.": "adventure", "Write a story.": "open", "Tell me a story.": "open",
    "Write a short story.": "open",
}
_STOP = set("a an the of and or to in on for with from by at as is was were be been his her their its "
            "that this those these into over under after before about him she he they them who whom "
            "which what when where while has had have not no never unknown own being".split())


def _wound_words(text):
    words = re.findall(r"[a-z]+", (text or "").lower())
    return [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if len(w) > 3 and w not in _STOP]


def _cos(a, b):
    num = sum(a[k] * b.get(k, 0) for k in a)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0


def _overlap(a, b):
    """Overlap of two distributions (1 = identical, 0 = nothing in common)."""
    ta, tb = sum(a.values()), sum(b.values())
    if not ta or not tb:
        return 0.0
    return sum(min(a[k] / ta, b.get(k, 0) / tb) for k in a)


def _profile(recs):
    c = {"traits": Counter(), "wound": Counter(), "age": Counter(), "gender": Counter(), "job": Counter()}
    for r in recs:
        c["traits"].update(t.strip().lower() for t in (r.get("traits") or []) if t.strip())
        c["wound"].update(_wound_words(r.get("wound")))
        for k, f in (("age", "age"), ("gender", "gender"), ("job", "occupation")):
            v = (r.get(f) or "unknown").strip().lower()
            if v != "unknown":
                c[k][v] += 1
    return c


def genre_analysis(cells, min_n, title, intro):
    """cells: {(name, genre): [records]} -> markdown lines."""
    cells = {k: v for k, v in cells.items() if len(v) >= min_n}
    names = sorted({n for n, _ in cells}, key=lambda n: -sum(len(v) for (m, _), v in cells.items() if m == n))
    genres = [g for g in dict.fromkeys(g for _, g in sorted(cells, key=lambda k: k[1]))]
    prof = {k: _profile(v) for k, v in cells.items()}
    L = [f"## {title}", "", intro, ""]
    summary = []
    for n in names:
        gs = [g for g in genres if (n, g) in prof]
        if len(gs) < 2:
            continue
        same_t, same_w, same_a, other_t, other_w = [], [], [], [], []
        for i, g1 in enumerate(gs):
            for g2 in gs[i + 1:]:
                a, b = prof[(n, g1)], prof[(n, g2)]
                same_t.append(_cos(a["traits"], b["traits"]))
                same_w.append(_cos(a["wound"], b["wound"]))
                same_a.append(_overlap(a["age"], b["age"]))
            for m in names:
                if m != n and (m, g1) in prof:
                    a, b = prof[(n, g1)], prof[(m, g1)]
                    other_t.append(_cos(a["traits"], b["traits"]))
                    other_w.append(_cos(a["wound"], b["wound"]))
        avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
        st, ot = avg(same_t), avg(other_t)
        summary.append((n, gs, st, ot, st - ot, avg(same_w), avg(other_w), avg(same_a)))
    if not summary:
        return L + ["Not enough data: no name has at least "
                    f"{min_n} appearances in two or more genres.", ""]
    L += ["| Name | Genres | Personality: same name, other genres | Personality: other names, same genre | "
          "**Persistence** | Haunted by: same name | Haunted by: other names | Age profile overlap |",
          "|---|---|---|---|---|---|---|---|"]
    for n, gs, st, ot, d, sw, ow, sa in sorted(summary, key=lambda x: -x[4]):
        L.append(f"| {n} | {len(gs)} | {st:.2f} | {ot:.2f} | **{d:+.2f}** | {sw:.2f} | {ow:.2f} | {sa:.0%} |")
    L += ["", "*Similarities are cosines between trait (or 'haunted by' word) profiles, 0 to 1. "
          "**Persistence** = same-name similarity minus same-genre similarity: positive means the character "
          "stays recognisably themselves from genre to genre; negative means the genre shapes them more than the "
          "name does. Exact words are compared, so synonyms (quiet / reserved) count as different: read the "
          "numbers relative to each other, and against the plain-name controls if present.*", ""]
    for n, gs, *_ in sorted(summary, key=lambda x: -x[4]):
        L += [f"### {n}", "", "| Genre | n | Age | Job | Top traits | Haunted by |", "|---|---|---|---|---|---|"]
        for g in gs:
            pf, k = prof[(n, g)], len(cells[(n, g)])
            age = ", ".join(f"{a} {round(100 * c / k)}%" for a, c in pf["age"].most_common(2)) or "-"
            job = ", ".join(j for j, _ in pf["job"].most_common(2)) or "-"
            tr = ", ".join(t for t, _ in pf["traits"].most_common(5))
            wd = ", ".join(w for w, _ in pf["wound"].most_common(4)) or "-"
            L.append(f"| {g} | {k} | {age} | {job} | {tr} | {wd} |")
        L.append("")
    return L


def cmd_genre(args):
    names = [x.strip() for x in args.names.split(",") if x.strip()] if args.names else list(GENRE_NAMES)
    genres = GENRES if not args.genres else [g for g in GENRES if g[0] in args.genres.split(",")]
    L = ["# Is sci-fi Mara the same person as romance Mara?", ""]

    if not args.natural_only:
        gen_path = args.data / "genre_stories.jsonl"
        done = Counter((r["name"], r["genre"]) for r in read_jsonl(gen_path))
        jobs = [(n, g, instr) for n in names for g, instr in genres for _ in range(max(0, args.n - done[(n, g)]))]
        random.shuffle(jobs)
        say(f"Genre test: {len(names)} names x {len(genres)} genres x {args.n} stories "
            f"({len(jobs)} still to write)")

        def gen(job):
            n, g, instr = job
            text = n + complete(args, probe_prompt(args, n, "{name}", instr), args.max_tokens)
            if len(text) < 150:
                raise RuntimeError(f"suspiciously short story ({len(text)} chars)")
            append_jsonl(gen_path, {"id": f"g{time.time_ns()}{random.randint(0, 999):03d}",
                                    "name": n, "genre": g, "prompt": instr, "text": text})

        run_pool(args, jobs, gen, "Writing genre stories", "story")

        ex_path = args.data / "genre_characters.jsonl"
        seen = {r["genre_id"] for r in read_jsonl(ex_path)}
        todo = [r for r in read_jsonl(gen_path) if r["id"] not in seen]
        fmt = {"type": "json_schema", "json_schema": {"name": "bio", "schema": BIO_SCHEMA}}

        def ext(r):
            msgs = [{"role": "system", "content": BIO_SYSTEM.format(name=r["name"])},
                    {"role": "user", "content": "Text:\n\n" + r["text"] + "\n\nReturn JSON."}]
            text, _ = chat(args, msgs, 0.0, 1200, None if args.no_schema else fmt)
            append_jsonl(ex_path, {"genre_id": r["id"], "name": r["name"], "genre": r["genre"], **parse_json(text)})

        run_pool(args, todo, ext, "Extracting characters", "story")

        cells = defaultdict(list)
        for r in read_jsonl(ex_path):
            if r["name"] in names:
                cells[(r["name"], r["genre"])].append(r)
        L += genre_analysis(
            cells, 2, "Forced: the same name as protagonist in every genre",
            f"Each name was made the first word of a story in each of {len(genres)} genres, {args.n} stories "
            "each, then the character was extracted. David and Sarah are plain-name controls: if the fantasy "
            "names persist more than they do, the persona belongs to the name, not to the model's general habits.")

    # natural appearances in the main stories
    nat = defaultdict(list)
    for ex in read_jsonl(args.data / "characters.jsonl"):
        g = PROMPT_GENRE.get(ex.get("prompt"), None)
        if not g or (args.skip_open and g == "open"):
            continue
        for c in ex.get("characters") or []:
            fn = first_name(c.get("name", ""))
            if fn:
                nat[(fn, g)].append(c)
    L += genre_analysis(
        nat, args.min_natural, "Natural: the names as they turn up in your stories",
        f"From `characters.jsonl`, split by the genre the story was asked for (only names with at least "
        f"{args.min_natural} appearances in a genre, in two or more genres). This shows who each character is "
        "when the model brings them into a genre by itself.")
    out = args.data / "genre.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    say(f"Wrote {out}")


# --------------------------------------------------------------------------- llama-server

def model_config(name):
    """A model by its name in ghosts_config.MODELS, or a path to a .gguf file."""
    if CFG and name in CFG.MODELS:
        return dict(CFG.MODELS[name], key=name)
    if name and name.endswith(".gguf"):
        return {"gguf": name, "data": "data", "key": Path(name).stem}
    known = ", ".join(CFG.MODELS) if CFG else "(no ghosts_config.py found)"
    sys.exit(f"Unknown model {name!r}. Known: {known} - or give a path to a .gguf file.")


class LlamaServer:
    """Start llama-server for one GGUF and stop it again; reuse it if it's already running."""

    def __init__(self, gguf, port=None, log_dir=Path("."), extra_args=None, exe=None):
        self.gguf = str(gguf)
        self.port = port or (CFG.PORT if CFG else 8081)
        self.url = f"http://127.0.0.1:{self.port}"
        self.exe = exe or (CFG.LLAMA_SERVER if CFG else "llama-server")
        self.args = extra_args if extra_args is not None else (CFG.SERVER_ARGS if CFG else ["-ngl", "99"])
        self.log_path = Path(log_dir) / "llama_server.log"
        self.proc = None
        self.owned = False

    def _get(self, path, timeout=3):
        with urllib.request.urlopen(self.url + path, timeout=timeout) as r:
            return json.load(r)

    def health(self):
        """'ok', 'loading' or None (nothing there)."""
        try:
            self._get("/health")
            return "ok"
        except urllib.error.HTTPError as e:
            return "loading" if e.code == 503 else None
        except Exception:  # noqa: BLE001
            return None

    def serving(self):
        """Path or name of the model the running server reports, if it says."""
        for path, pick in (("/props", lambda d: d.get("model_path")),
                           ("/v1/models", lambda d: (d.get("data") or [{}])[0].get("id"))):
            try:
                v = pick(self._get(path))
                if v:
                    return str(v)
            except Exception:  # noqa: BLE001
                pass
        return None

    def same_model(self, other):
        return other is not None and Path(other).name == Path(self.gguf).name

    def start(self):
        state = self.health()
        if state:
            running = self.serving()
            if running is None or self.same_model(running):
                say(f"Using the llama-server already running on port {self.port}"
                    + (f" ({Path(running).name})" if running else " (it doesn't say which model - assuming it's right)"))
                self._wait_ready()
                return self
            sys.exit(f"Port {self.port} is already serving {Path(running).name}, not {Path(self.gguf).name}. "
                     "Stop that server first, or set a different PORT in ghosts_config.py.")
        if not Path(self.gguf).exists():
            sys.exit(f"GGUF not found: {self.gguf}  (set GHOSTS_MODELS_DIR, or check MODELS in ghosts_config.py)")
        exe = shutil.which(self.exe) or (self.exe if Path(self.exe).exists() else None)
        if not exe:
            sys.exit(f"llama-server not found at {self.exe!r} (set LLAMA_CPP_DIR, or LLAMA_SERVER in ghosts_config.py)")
        cmd = [exe, "-m", self.gguf, "--port", str(self.port), *self.args]
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log = self.log_path.open("a", encoding="utf-8")
        log.write(f"\n$ {' '.join(cmd)}\n")
        log.flush()
        say(f"Starting llama-server: {Path(self.gguf).name} on port {self.port} (log: {self.log_path})")
        self.proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        self.owned = True
        atexit.register(self.stop)
        self._wait_ready()
        return self

    def _wait_ready(self, limit=900):
        t0 = time.time()
        while time.time() - t0 < limit:
            if self.proc is not None and self.proc.poll() is not None:
                tail = self.log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
                sys.exit(f"llama-server exited (code {self.proc.returncode}). End of its log:\n{tail}")
            if self.health() == "ok":
                if self.proc is not None:
                    say(f"Server ready after {time.time() - t0:.0f}s")
                return
            time.sleep(2)
        self.stop()
        sys.exit("llama-server didn't become ready within 15 minutes")

    def alive(self):
        return self.health() == "ok"

    def restart(self):
        self.stop()
        return self.start()

    def stop(self):
        if self.proc is None or self.proc.poll() is not None:
            self.proc = None
            return
        say("Stopping llama-server")
        self.proc.terminate()
        try:
            self.proc.wait(60)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(30)
        self.proc = None
        time.sleep(3)   # let the GPUs free their memory

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()


def _sigterm(*_):
    raise SystemExit(143)   # so `kill` still stops the server we started


# --------------------------------------------------------------------------- main

def main():
    def common(suppress):
        # Global options work before OR after the command:
        #   ghosts.py --url X probe   and   ghosts.py probe --url X
        p = argparse.ArgumentParser(add_help=False)
        d = (lambda v: argparse.SUPPRESS) if suppress else (lambda v: v)
        p.add_argument("--model", default=d(None),
                       help="model name from ghosts_config.py (instruct, base, ...) or a .gguf path; "
                            "llama-server is started and stopped for you")
        p.add_argument("--url", default=d(None),
                       help="use a llama-server you run yourself instead (e.g. http://127.0.0.1:8081)")
        p.add_argument("--data", type=Path, default=d(None), help="output folder (default: the model's, from the config)")
        p.add_argument("--workers", type=int, default=d(None), help="parallel requests (default: WORKERS in the config)")
        p.add_argument("--timeout", type=int, default=d(600))
        p.add_argument("--top-p", type=float, default=d(0.95))
        return p

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 parents=[common(False)])
    sub_common = common(True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    orig_add_parser = sub.add_parser
    sub.add_parser = lambda name, **kw: orig_add_parser(name, parents=[sub_common], **kw)

    g = sub.add_parser("generate", help="generate stories")
    g.add_argument("--n", type=int, default=50, help="stories per prompt (target total, resumable)")
    g.add_argument("--temperature", type=float, default=1.0)
    g.add_argument("--max-tokens", type=int, default=1500)

    e = sub.add_parser("extract", help="extract named characters from stories")
    e.add_argument("--no-schema", action="store_true", help="skip json_schema constrained decoding")

    r = sub.add_parser("report", help="aggregate stats per name")
    r.add_argument("--min-stories", type=int, default=3)
    r.add_argument("--top", type=int, default=20, help="names to detail in the report")

    p = sub.add_parser("profile", help="LLM-written composite character sheets")
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--names", default="", help="comma list, e.g. Elara,Kaelen,Voss")
    p.add_argument("--samples", type=int, default=30, help="appearances shown to the model per name")

    pr = sub.add_parser("probe", help="name x trait associations from next-word probabilities")
    pr.add_argument("--names", default="", help="comma list of names to probe (default: the usual cast)")
    pr.add_argument("--from-report", type=int, default=0, metavar="N",
                    help="probe the top N names from your own stats.json instead")
    pr.add_argument("--invented", action="store_true", help="also probe made-up harsh/soft names")
    pr.add_argument("--traits", default="", help="comma list of single-word traits (default: built-in 40)")
    pr.add_argument("--frames", default="",
                    help='custom sentence frames separated by |, each with {name}, e.g. "{name} was very|{name} seemed"')
    pr.add_argument("--raw", action="store_true",
                    help="send bare frames instead of wrapping them in the model's chat format")
    pr.add_argument("--check-frames", action="store_true",
                    help="just show what the model wants to say after each frame, then stop")
    pr.add_argument("--n-probs", type=int, default=5000,
                    help="how many top next-tokens to request; larger = fewer rough cells, slower")

    b = sub.add_parser("bio", help="biographies from bare names, compared with the stories")
    b.add_argument("--n", type=int, default=10, help="biographies per name per prompt (resumable)")
    b.add_argument("--names", default="", help="comma list (default: the main cast)")
    b.add_argument("--from-report", type=int, default=0, metavar="N", help="use the top N names from stats.json")
    b.add_argument("--no-controls", action="store_true", help="skip David/Sarah and the invented names")
    b.add_argument("--temperature", type=float, default=1.0)
    b.add_argument("--max-tokens", type=int, default=700)
    b.add_argument("--no-schema", action="store_true", help="skip json_schema constrained decoding")

    ro = sub.add_parser("roulette", help="probability of each name at the moment a name is due")
    ro.add_argument("--label", default="", help="name for this model's run, e.g. base / instruct")
    ro.add_argument("--raw", action="store_true", help="bare text (for base models); default wraps in chat format")
    ro.add_argument("--n-probs", type=int, default=2000)
    ro.add_argument("--report-only", action="store_true",
                    help="just rebuild roulette.md/.html from the roulette_*.json files in --data")

    sw = sub.add_parser("swap", help="does the name summon the story? force or swap names and compare")
    sw.add_argument("--mode", choices=["open", "cut"], default="open")
    sw.add_argument("--n", type=int, default=20, help="open: stories per name; cut: source stories to cut")
    sw.add_argument("--names", default="", help="open: names to force; cut: replacement names (default David,Thomas,Vorrak)")
    sw.add_argument("--target", default="Elias", help="cut: the name to cut at and replace")
    sw.add_argument("--temperature", type=float, default=1.0)
    sw.add_argument("--max-tokens", type=int, default=700)
    sw.add_argument("--raw", action="store_true", help="bare text instead of chat format")
    sw.add_argument("--no-schema", action="store_true")

    ge = sub.add_parser("genre", help="is the same name the same character in every genre?")
    ge.add_argument("--n", type=int, default=6, help="stories per name per genre (forced test)")
    ge.add_argument("--names", default="", help="comma list (default: Mara, Elias, Elara, ... + David, Sarah)")
    ge.add_argument("--genres", default="", help="comma list of genre keys to use (default: all 8)")
    ge.add_argument("--natural-only", action="store_true", help="skip the forced test; only analyse your stories")
    ge.add_argument("--min-natural", type=int, default=3, help="min appearances per name per genre (natural)")
    ge.add_argument("--skip-open", action="store_true", help="natural: leave out the no-genre prompts")
    ge.add_argument("--temperature", type=float, default=1.0)
    ge.add_argument("--max-tokens", type=int, default=700)
    ge.add_argument("--raw", action="store_true")
    ge.add_argument("--no-schema", action="store_true")

    args = ap.parse_args()
    # resolve the model, its folder and the server
    if args.model is None:
        args.model = CFG.DEFAULT_MODEL if CFG else None
    mcfg = model_config(args.model) if args.model else {"data": "data", "key": "model"}
    if args.data is None:
        # every model's roulette goes in one folder, so the chart can compare them
        args.data = Path("data_roulette") if args.cmd == "roulette" else Path(mcfg.get("data", "data"))
    if args.workers is None:
        args.workers = CFG.WORKERS if CFG else 4
    args.model_key = mcfg.get("key", "model")
    args.model_is_base = bool(mcfg.get("raw"))
    if mcfg.get("raw") and hasattr(args, "raw") and not args.raw:
        args.raw = True
        say(f"{mcfg['key']} is a base model: using bare text (no chat format)")
    args.data.mkdir(parents=True, exist_ok=True)
    needs_server = not (args.cmd == "report"
                        or (args.cmd == "roulette" and args.report_only)
                        or (args.cmd == "genre" and args.natural_only))
    run = {"generate": cmd_generate, "extract": cmd_extract, "report": cmd_report, "profile": cmd_profile,
           "probe": cmd_probe, "bio": cmd_bio, "roulette": cmd_roulette, "swap": cmd_swap,
           "genre": cmd_genre}[args.cmd]
    if not needs_server or args.url:
        args.url = args.url or ""
        run(args)
        sys.exit(exit_code_for_failures())
    if "gguf" not in mcfg:
        sys.exit("No model to start: give --model (see ghosts_config.py) or --url for your own server.")
    signal.signal(signal.SIGTERM, _sigterm)
    with LlamaServer(mcfg["gguf"], log_dir=args.data) as srv:
        args.url = srv.url
        run(args)
    sys.exit(exit_code_for_failures())



if __name__ == "__main__":
    main()
