#!/usr/bin/env python3
"""
overnight.py - run every Ghosts-in-the-Machine experiment unattended.

It starts llama-server with each model in turn, runs the ghosts.py steps for that model,
stops the server, and finally runs the PyTorch experiments (ghosts_torch.py) once the GPUs
are free. Every step is logged; a failed step is recorded and the run carries on.
Everything is resumable: if you stop it in the morning, run it again later and finished
work is skipped.

1. Model paths, llama-server location and flags: ghosts_config.py (shared with ghosts.py).
   What to run and how much: the CONFIG section below.
2. Stop any llama-server you're running yourself.
3. Check the plan:      python overnight.py --check
4. Dress rehearsal:     python overnight.py --smoke        (~30-45 min, tiny sizes, into smoke/)
5. Go to bed:           python overnight.py --stop-at 07:30
6. In the morning:      open overnight_summary.md - it lists every output file.

Run it inside tmux (or with nohup) so closing the terminal doesn't stop it. Ctrl-C or `kill`
stops it cleanly: the running step and llama-server are shut down, and a re-run resumes.

Options:
  --check            preflight only: paths, server binary, torch model, the plan
  --smoke            every step at tiny sizes into smoke/, to prove the whole night works
  --only a,b         run only these phases: model names from ghosts_config (instruct, base), torch
  --stop-at 07:30    don't START any step after this time (keeps the machine free in the morning)
"""

# =============================================================================== CONFIG

# Model paths, the llama-server location and its flags are in ghosts_config.py.
import ghosts_config as CFG  # noqa: E402

# What to run for each model (names match ghosts_config.MODELS). "enabled": False skips a model.
RUNS = {
    "instruct": {     # stock Gemma 4 - the main model
        "enabled": True,
        "stories_per_prompt": 100,      # 10 prompts -> 1000 stories
        "bios_per_prompt": 10,          # x 3 prompts x 14 names
        "genre_n": 6,                   # genre test: stories per name per genre (10 names x 8 genres)
    },
    "base": {         # bare text only: roulette + probes. Needs its GGUF (convert_models.sh);
        "enabled": True,                # set False if you skip that - PyTorch still covers the base model
    },
}


def model(key):
    m = {**CFG.MODELS[key], **RUNS.get(key, {})}
    if SMOKE:
        m["data"] = f"smoke/{m['data']}"
    return m


ROULETTE_DIR = "data_roulette"          # all models' roulette results side by side

# Smoke test first (10 minutes, small download) to prove the PyTorch side works on your machine:
#   pip install bitsandbytes
#   python ghosts_torch.py lens --model unsloth/gemma-4-E4B-it-unsloth-bnb-4bit --out torch_smoke
#
# Alternative main model if the 26B downloads/speed are a problem (fits in 2 x 16 GB, no offload,
# but it's a different, dense model with no experts to inspect):
#   "model": "unsloth/gemma-4-31B-it-unsloth-bnb-4bit", "args": ["--max-memory", "0:15GiB,1:15GiB"]
#
# PyTorch experiments on the Hugging Face weights. Download both beforehand (~52 GB each):
#   hf download google/gemma-4-26B-A4B-it
#   hf download google/gemma-4-26B-A4B
# "early" runs come before the long story runs (quick: ~10 min); "late" runs come last, because
# steering writes stories with the model half in RAM (several seconds per word) and is the one
# step that can run long. --stop-at stops it starting if the night is nearly over.
TORCH_RUNS = [
    {   # stock instruct: embeddings + logit lens + experts (+ the bare-text naming moments)
        "enabled": True, "phase": "early",
        "model": "instruct",            # a name from ghosts_config.MODELS (its "hf" weights)
        "experiment": "embed,lens",
        "out": "torch_out",
        "args": ["--max-memory", "0:14GiB,1:14GiB,cpu:80GiB", "--roulette-dir", ROULETTE_DIR, "--lens-raw-too"],
    },
    {   # base (pre-trained, no chat tuning): logit lens (bare text is automatic)
        "enabled": True, "phase": "early",
        "model": "base",
        "experiment": "lens",
        "out": "torch_out_base",
        "args": ["--max-memory", "0:14GiB,1:14GiB,cpu:80GiB", "--roulette-dir", ROULETTE_DIR],
    },
    {   # stock instruct: the exorcism - remove the Elias direction, see who replaces him
        "enabled": True, "phase": "late",
        "model": "instruct",
        "experiment": "steer",
        "out": "torch_out",
        "args": ["--max-memory", "0:14GiB,1:14GiB,cpu:80GiB", "--alphas", "0,0.5,1,2",
                 "--story-alphas", "0,2", "--stories", "2", "--story-tokens", "250"],
    },
]

# Names and traits for the probe (the commonest traits in the story report)
PROBE_NAMES = "Elias,Elara,Clara,Kaelen,Kael,Julian,Leo,Silas,Thorne,Seraphina"
PROBE_TRAITS = ("solitary,weary,lonely,patient,observant,determined,brave,resilient,skilled,loyal,"
                "protective,warm,grieving,vibrant,kind,wise,mysterious,dangerous,gentle,quiet,cruel,"
                "honest,energetic,nurturing")

# Order: quick experiments on every model first, then PyTorch, then the long story/bio runs
# (those are resumable, so if the night runs out, run this again tomorrow to finish them).
# "post" rebuilds the roulette comparison (all models + both PyTorch runs) and its chart.
ORDER = ["quick:instruct", "quick:base", "torch:early", "post",
         "long:instruct", "torch:late", "post"]

# Name swap: stories forced to start with each name (per model), and Elias's stories cut at his
# first mention and continued as David / Thomas / Vorrak (needs that model's stories).
SWAP_OPEN_N = 20      # stories per name (12 names)
SWAP_CUT_N = 20       # source stories to cut (x 4 variants)

# =============================================================================== end of CONFIG

import argparse
import datetime as dt
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import ghosts as _ghosts
from ghosts import LlamaServer

HERE = Path(__file__).resolve().parent
SMOKE = False


def apply_smoke():
    """Tiny sizes, separate folders: every step runs for real, just briefly."""
    global SMOKE, ROULETTE_DIR, LOG, SUMMARY, SWAP_OPEN_N, SWAP_CUT_N
    SMOKE = True
    (HERE / "smoke").mkdir(exist_ok=True)
    ROULETTE_DIR = "smoke/data_roulette"
    LOG, SUMMARY = HERE / "smoke" / "overnight.log", HERE / "smoke" / "overnight_summary.md"
    SWAP_OPEN_N, SWAP_CUT_N = 1, 2
    for r in RUNS.values():
        r.update(stories_per_prompt=1, bios_per_prompt=1, genre_n=1)
    for r in TORCH_RUNS:
        r["out"] = f"smoke/{r['out']}"
        args = [a for a in r["args"]]
        if "--roulette-dir" in args:
            args[args.index("--roulette-dir") + 1] = ROULETTE_DIR
        if r["experiment"] == "steer":
            args = ["--max-memory", "0:14GiB,1:14GiB,cpu:80GiB", "--steer-others", "3", "--alphas", "0,1",
                    "--story-alphas", "1", "--stories", "1", "--story-tokens", "20"]
        r["args"] = args
LOG = HERE / "overnight.log"
SUMMARY = HERE / "overnight_summary.md"
URL = f"http://127.0.0.1:{CFG.PORT}"
PY = sys.executable


def now():
    return time.strftime("%H:%M:%S")


def say(msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# --------------------------------------------------------------------------- steps

def ghosts(model_key, *a, data=None):
    # overnight.py keeps one server up per phase, so each step points at it with --url
    return [PY, str(HERE / "ghosts.py"), "--model", model_key, "--url", URL, "--workers", str(CFG.WORKERS),
            "--data", str(data or model(model_key)["data"]), *a]


def quick_steps(key):
    m = model(key)
    raw = ["--raw"] if m.get("raw") else []
    d = m["data"]
    return [
        (f"{key}: name roulette", ghosts(key, "roulette", "--label", key, *raw, data=ROULETTE_DIR)),
    ] + ([] if m.get("raw") else [
        # the same naming moments as bare text: the prompt format the base model gets
        (f"{key}: name roulette (bare text)", ghosts(key, "roulette", "--label", f"{key}-raw", "--raw", data=ROULETTE_DIR)),
    ]) + [
        (f"{key}: probe (story traits)",
         ghosts(key, "probe", "--names", PROBE_NAMES, "--traits", PROBE_TRAITS, *raw, data=f"{d}/probe_storytraits")),
        (f"{key}: probe (invented names)", ghosts(key, "probe", "--invented", *raw, data=f"{d}/probe_invented")),
    ] + ([] if m.get("raw") else [
        (f"{key}: name swap (stories start with the name)", ghosts(key, "swap", "--mode", "open", "--n", str(SWAP_OPEN_N))),
    ]) + ([(f"{key}: name swap (Elias's stories re-continued)", ghosts(key, "swap", "--mode", "cut", "--n", str(SWAP_CUT_N)))]
          if not m.get("raw") and (HERE / d / "stories.jsonl").exists() else [])


def long_steps(key):
    m = model(key)
    if m.get("raw"):
        return []
    return [
        (f"{key}: generate stories", ghosts(key, "generate", "--n", str(m["stories_per_prompt"]))),
        (f"{key}: extract characters", ghosts(key, "extract")),
        (f"{key}: report", ghosts(key, "report")),
        (f"{key}: character sheets", ghosts(key, "profile", "--top", "3" if SMOKE else "8")),
        (f"{key}: name swap (Elias's stories re-continued)", ghosts(key, "swap", "--mode", "cut", "--n", str(SWAP_CUT_N))),
        (f"{key}: genre test (same name, every genre)",
         ghosts(key, "genre", "--n", str(m.get("genre_n", 6)),
                *(["--names", "Mara,David", "--genres", "fantasy,romance"] if SMOKE else []))
         if m.get("genre_n", 6) else ghosts(key, "genre", "--natural-only")),
        (f"{key}: biographies", ghosts(key, "bio", "--n", str(m["bios_per_prompt"]),
                                       *(["--names", "Elias", "--no-controls"] if SMOKE else []))),
    ]


def torch_steps(phase):
    return [(f"torch: {r['experiment']} on {r['model']}",
             [PY, str(HERE / "ghosts_torch.py"), r["experiment"], "--model", r["model"], "--out", r["out"], *r["args"]])
            for r in TORCH_RUNS if r.get("enabled", True) and r.get("phase", "early") == phase]


def build_plan(only):
    plan = []   # (phase, model_key or None, [(label, cmd)])
    for item in ORDER:
        kind, _, key = item.partition(":")
        if kind == "torch":
            if torch_steps(key) and (not only or "torch" in only):
                plan.append((f"torch:{key}", None, torch_steps(key)))
            continue
        if kind == "post":
            plan.append(("post", None, [("roulette comparison + chart",
                                         [PY, str(HERE / "ghosts.py"), "--data", ROULETTE_DIR, "roulette",
                                          "--report-only"])]))
            continue
        if key not in CFG.MODELS or not RUNS.get(key, {}).get("enabled", True) or (only and key not in only):
            continue
        steps = quick_steps(key) if kind == "quick" else long_steps(key)
        if steps:
            plan.append((item, key, steps))
    return plan


# --------------------------------------------------------------------------- running a step

_child = None


def run_step(cmd):
    """Run one step, its output into the log. If overnight.py is stopped, the step is stopped too."""
    global _child
    env = dict(os.environ)
    if "ghosts_torch.py" in " ".join(cmd):
        env["HF_HUB_OFFLINE"] = "1"      # models are already downloaded: no network calls at 3 a.m.
    with LOG.open("a", encoding="utf-8") as lf:
        lf.write(f"$ {' '.join(cmd)}\n")
        lf.flush()
        _child = subprocess.Popen(cmd, cwd=HERE, stdout=lf, stderr=subprocess.STDOUT, env=env)
        try:
            return _child.wait()
        finally:
            if _child.poll() is None:
                say("    stopping the running step")
                _child.terminate()
                try:
                    _child.wait(60)
                except subprocess.TimeoutExpired:
                    _child.kill()
            _child = None


def _on_sigterm(*_):
    raise KeyboardInterrupt   # same clean shutdown as Ctrl-C


# --------------------------------------------------------------------------- server

def server_for(key):
    """The shared llama-server manager from ghosts.py (same code as a manual run)."""
    return LlamaServer(CFG.MODELS[key]["gguf"], log_dir=HERE)


# --------------------------------------------------------------------------- preflight

def preflight(plan):
    problems, notes = [], []
    exe = shutil.which(CFG.LLAMA_SERVER) or (CFG.LLAMA_SERVER if Path(CFG.LLAMA_SERVER).exists() else None)
    keys = sorted({key for _, key, _ in plan if key})
    if keys and not exe:
        problems.append(f"llama-server not found: {CFG.LLAMA_SERVER!r} (set LLAMA_CPP_DIR, or LLAMA_SERVER in ghosts_config.py)")
    for key in keys:
        if not Path(CFG.MODELS[key]["gguf"]).exists():
            problems.append(f"{key}: GGUF not found: {CFG.MODELS[key]['gguf']} (ghosts_config.py)")
    for f in ("ghosts.py", "ghosts_torch.py", "ghosts_config.py"):
        if not (HERE / f).exists():
            problems.append(f"{f} must be in the same folder as overnight.py")
    if keys:
        probe = LlamaServer(CFG.MODELS[keys[0]]["gguf"])
        if probe.health():
            running = probe.serving()
            problems.append(f"A llama-server is already running on port {CFG.PORT}"
                            + (f" ({Path(running).name})" if running else "")
                            + " - stop it so the run can switch models.")
    if any(p.startswith("torch") for p, _, _ in plan):
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            gpus = torch.cuda.device_count()
            notes.append(f"torch {torch.__version__}, transformers {transformers.__version__}, {gpus} GPU(s) visible")
            if gpus == 0:
                problems.append("PyTorch sees no GPU - install the CUDA build of torch, or the torch phase will crawl on CPU.")
        except ImportError as e:
            problems.append(f"PyTorch phase needs: pip install -U torch transformers accelerate ({e})")
        for r in TORCH_RUNS:
            hf = CFG.MODELS.get(r["model"], {}).get("hf", r["model"])
            if not r.get("enabled", True) or Path(hf).exists():
                continue
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(hf, local_files_only=True)
                notes.append(f"{hf} found in the Hugging Face cache")
            except Exception:  # noqa: BLE001
                problems.append(f"{hf} isn't downloaded yet. Do it now (~52 GB): hf download {hf}")
    try:
        import tqdm  # noqa: F401
    except ImportError:
        notes.append("tip: pip install tqdm for nicer progress bars in the logs")
    return problems, notes


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="preflight checks and the plan, then stop")
    ap.add_argument("--only", default="", help="comma list of phases: instruct, base, torch")
    ap.add_argument("--stop-at", default="", help="HH:MM - don't start new steps after this time")
    ap.add_argument("--smoke", action="store_true", help="every step at tiny sizes into smoke/ (dress rehearsal)")
    args = ap.parse_args()
    if args.smoke:
        apply_smoke()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    plan = build_plan(only)

    deadline = None
    if args.stop_at:
        h, m = map(int, args.stop_at.split(":"))
        d = dt.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if d <= dt.datetime.now():
            d += dt.timedelta(days=1)
        deadline = d

    print("Plan:")
    for phase, key, steps in plan:
        print(f"  [{phase}]" + (f"  (llama-server: {Path(CFG.MODELS[key]['gguf']).name})" if key else ""))
        for label, _ in steps:
            print(f"     - {label}")
    if deadline:
        print(f"  No new step starts after {deadline:%a %H:%M}.")
    problems, notes = preflight(plan)
    for n in notes:
        print("  ok: " + n)
    for p in problems:
        print("  PROBLEM: " + p)
    if args.check:
        print("\nAll clear - ready to run." if not problems else "\nFix the problems above first.")
        return
    if problems:
        sys.exit("Fix the problems above first (or run with --check to see them again).")

    _ghosts.say = say          # llama-server start/stop messages go into overnight.log too
    signal.signal(signal.SIGTERM, _on_sigterm)
    say("=" * 60)
    say(f"Overnight run starting: {sum(len(s) for _, _, s in plan)} steps")
    results = []   # (label, status, minutes)
    t_all = time.time()
    stopped = False
    try:
        for _phase, key, steps in plan:
            if deadline and dt.datetime.now() >= deadline:
                for label, _ in steps:
                    results.append((label, "skipped (past --stop-at)", 0))
                continue
            srv = None
            try:
                if key:
                    srv = server_for(key).start()
            except (Exception, SystemExit) as e:  # noqa: BLE001  (start() exits with a message on failure)
                say(f"Couldn't start the server for {key}: {e}")
                for label, _ in steps:
                    results.append((label, f"skipped (server failed: {e})", 0))
                continue
            try:
                for label, cmd in steps:
                    if deadline and dt.datetime.now() >= deadline:
                        results.append((label, "skipped (past --stop-at)", 0))
                        continue
                    say(f"--> {label}")
                    t = time.time()
                    rc = run_step(cmd)
                    mins = (time.time() - t) / 60
                    status = ("ok" if rc == 0 else
                          "MOSTLY FAILED: many items failed, see overnight.log" if rc == 3 else
                          f"FAILED (exit {rc}, see overnight.log)")
                    say(f"    {status} in {mins:.1f} min")
                    results.append((label, status, mins))
                    if srv and not srv.alive():
                        say("    server stopped responding - restarting it")
                        try:
                            srv.restart()
                        except (Exception, SystemExit) as e:  # noqa: BLE001
                            say(f"    couldn't restart it: {e} - skipping the rest of this phase")
                            break
            finally:
                if srv:
                    srv.stop()
    except KeyboardInterrupt:
        stopped = True
        say("Stopped (Ctrl-C or kill). The running step and llama-server were shut down; "
            "run the same command again to resume.")
        done = {lbl for lbl, _, _ in results}
        for _phase, _key, steps in plan:
            for label, _ in steps:
                if label not in done:
                    results.append((label, "not run (stopped)", 0))

    total = (time.time() - t_all) / 60
    outputs = []
    pre = "smoke/" if SMOKE else ""
    for pattern in ("data*/report.md", "data*/bio_report.md", "data*/sheets/*.md", "data*/probe_*/probe.md",
                    "data*/probe_*/probe_heatmap.html", "data_roulette/roulette.md", "data_roulette/roulette.html",
                    "data*/swap_*.md", "data*/genre.md", "torch_out*/*.md", "torch_out*/*.html"):
        outputs += sorted(str(p.relative_to(HERE)) for p in HERE.glob(pre + pattern))
    L = [f"# {'Smoke test' if SMOKE else 'Overnight run'} - {time.strftime('%Y-%m-%d %H:%M')}"
         + (" (stopped early)" if stopped else ""), "",
         f"Total time: {total / 60:.1f} hours  |  ok: {sum(1 for _, st, _ in results if st == 'ok')} of {len(results)} steps",
         "", "| Step | Result | Minutes |", "|---|---|---|"]
    L += [f"| {lbl} | {st} | {m:.0f} |" for lbl, st, m in results]
    L += ["", "## Where to look", "",
          "- **The headline chart - how open is the choice of name, base vs chat-tuned:** `"
          + f"{ROULETTE_DIR}/roulette.html" + "` (numbers, tokenizer splits and what follows each name: `roulette.md`). "
          "The clean before/after-chat-tuning pairs (same prompt format) are `base` vs `instruct-raw` "
          "(Q8_0 GGUF) and `base-bf16` vs `instruct-bf16-raw` (PyTorch): two independent measurements.",
          "- **Does the name summon the story?** `data/swap_open.md`, `data/swap_cut.md`",
          "- **Is sci-fi Mara the same person as romance Mara?** `data/genre.md`",
          "- **Inside the model (stock instruct):** `torch_out/lens.html`, `lens.md`, `experts.md`, `embed.md`, `steer.md`",
          "- **Base model (before chat tuning):** `torch_out_base/lens.md` - compare its 'Effective names' "
          "column with `torch_out/lens.md` and the roulette",
          "- **Stories and character sheets:** `data/report.md`, `data/sheets/`",
          "- **Biographies vs stories:** `data/bio_report.md`",
          "- **Probes:** `*/probe_storytraits/probe.md` and `*/probe_invented/probe.md` (check the health line first)",
          "", "## All output files", ""] + [f"- `{o}`" for o in outputs]
    SUMMARY.write_text("\n".join(L) + "\n", encoding="utf-8")
    say(f"Done in {total / 60:.1f} h. Summary: {SUMMARY}")


if __name__ == "__main__":
    main()
