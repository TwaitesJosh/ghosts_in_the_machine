#!/usr/bin/env python3
"""
ghosts_torch.py - look inside the model while it picks a name.

Runs on the Hugging Face weights of Gemma 4 (default: google/gemma-4-26B-A4B-it, ~52 GB).
With 2 x 16 GB GPUs + plenty of RAM it loads split across both cards and system memory:
slow, but fine overnight.

Experiments (all write into --out, default torch_out/):

  embed   Nearest neighbours of each name in the model's raw token-embedding table, and how
          close each name sits to each trait word. The "before" picture: what the model knows
          about "Elias" before any layer has run.                      -> embed.md

  lens    Logit lens. Stop a story at the naming moment ("...a keeper named ___"), decode every
          layer's hidden state as if it were the last one, and watch the winning name emerge
          layer by layer. Also logs which mixture-of-experts experts fire at that moment.
                                                         -> lens.md, lens.html, experts.md

  steer   "Exorcism". Find the direction in the residual stream that separates "Elias" from
          other male names, subtract it while the model writes, and see who replaces him -
          at the naming moment and in full stories.                    -> steer.md

  all     embed, lens, steer in that order (each one keeps going if another fails).

Setup (once):
  pip install -U torch transformers accelerate tqdm
  hf download google/gemma-4-26B-A4B-it        # ~52 GB; do this before the overnight run

Run:
  python ghosts_torch.py all
  python ghosts_torch.py lens --max-memory "0:14GiB,1:14GiB,cpu:80GiB"
"""

import argparse
import html
import json
import math
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # minimal fallback
    def tqdm(it=None, total=None, desc="", **_):
        items = list(it) if it is not None else []
        n = len(items)
        for i, x in enumerate(items, 1):
            print(f"\r{desc}: {i}/{n}", end="", flush=True)
            yield x
        print()

# --------------------------------------------------------------------------- shared material

# Same naming moments as `ghosts.py roulette`, so the numbers line up.
FRAMES = [
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
INSTRUCTION = "Write a short story."

TRACK = ["Elias", "Elara", "Clara", "Kael", "Kaelen", "Julian", "Leo", "Silas", "Thorne", "Mara",
         "Lyra", "Seraphina", "Thomas", "John", "David", "Sarah", "Emily"]
PLAIN = ["David", "Michael", "James", "John", "Robert", "Sarah", "Emily", "Laura", "Anna", "Mary"]
TRAITS = ["solitary", "weary", "lonely", "patient", "quiet", "gentle", "kind", "brave", "wise", "warm",
          "cold", "cruel", "mysterious", "dangerous", "honest", "vibrant", "energetic", "old", "young",
          "grumpy", "determined", "skilled", "sad", "beautiful"]

# Contexts used to find "the Elias direction": identical sentences, only the name changes.
STEER_CONTEXTS = [
    "Once upon a time there lived an old keeper named {X}. Every night, {X} climbed the tower to light the lamp.",
    "{X} had worked in the clock shop for forty years. People said {X} could fix anything.",
    "The letter was addressed to {X}. {X} opened it slowly and began to read.",
    "Everyone in the village knew {X}, but {X} rarely spoke to anyone.",
    "In the story, the main character is a man called {X}. {X} is the one we follow.",
    "{X} looked out at the sea and thought about the past.",
]
STEER_OTHERS = ["Thomas", "Samuel", "Harold", "Henry", "Oliver", "Peter", "George", "Walter", "Edward",
                "Frank", "Martin", "Hugo", "Felix", "Victor", "Oscar", "Simon", "Daniel", "Robert",
                "James", "William"]

NAMEISH = re.compile(r"^ ?[A-Z][a-zà-ÿ'\-]+$")
# capitalised words that come where a name would but aren't names (same list as ghosts.py)
NOT_NAMES = {"the", "a", "an", "he", "she", "it", "they", "his", "her", "its", "this", "that", "and", "but",
             "after", "simply", "only", "just", "not", "because", "for", "by", "in", "on", "at", "as", "so",
             "one", "no", "nobody", "none", "something", "nothing", "everyone", "mister", "madam", "saint", "st",
             "aunt", "uncle", "granny", "grandma", "grandpa", "dr", "doctor", "captain", "capt", "lord", "lady",
             "sir", "dame", "professor", "prof", "commander", "old", "young", "mr", "mrs", "ms", "miss", "master",
             "mistress", "king", "queen", "prince", "princess", "father", "mother", "brother", "sister",
             "general", "detective", "inspector", "agent", "officer", "sergeant", "lieutenant", "elder"}


class tqdm_bar:
    """A manual progress bar: tqdm if installed, else a plain counter."""
    def __init__(self, total, desc):
        self.total, self.desc, self.n = total, desc, 0
        try:
            from tqdm import tqdm as _t
            self.t = _t(total=total, desc=desc, unit="tok")
        except ImportError:
            self.t = None

    def update(self, k=1):
        self.n += k
        if self.t is not None:
            self.t.update(k)
        elif self.n % 25 == 0 or self.n == self.total:
            print(f"\r{self.desc}: {self.n}/{self.total} tokens", end="", flush=True)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if self.t is not None:
            self.t.close()
        else:
            print()


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


# --------------------------------------------------------------------------- model plumbing

class Model:
    """The loaded model plus the pieces the experiments need."""

    def __init__(self, args):
        import torch
        import transformers
        from transformers import AutoTokenizer
        self.torch = torch
        self.raw = args.raw
        log(f"Loading tokenizer + model {args.model} (this can take several minutes)...")
        self.tok = AutoTokenizer.from_pretrained(args.model)
        dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[args.dtype]
        self.dtype = dtype
        kw = dict(dtype=dtype, low_cpu_mem_usage=True)
        if args.load_4bit:
            # Compress linear layers to 4-bit on load. Note: Gemma 4 26B-A4B keeps its experts in
            # fused tensors that bitsandbytes leaves alone, so that model barely shrinks; dense
            # models (E2B/E4B/31B) shrink ~4x. Pre-quantised repos (e.g. unsloth/*-bnb-4bit)
            # don't need this flag.
            from transformers import BitsAndBytesConfig
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=dtype)
        if args.device == "auto":
            kw["device_map"] = "auto"
            if args.max_memory:
                mm = {}
                for part in args.max_memory.split(","):
                    k, v = part.split(":", 1)
                    mm[int(k) if k.strip().isdigit() else k.strip()] = v.strip()
                kw["max_memory"] = mm
        errors = []
        self.model = None
        for cls_name in ("AutoModelForMultimodalLM", "AutoModelForImageTextToText", "AutoModelForCausalLM"):
            cls = getattr(transformers, cls_name, None)
            if cls is None:
                continue
            try:
                self.model = cls.from_pretrained(args.model, **kw)
                break
            except Exception as e:  # noqa: BLE001
                errors.append(f"{cls_name}: {str(e)[:200]}")
        if self.model is None:
            raise RuntimeError("Could not load the model:\n  " + "\n  ".join(errors))
        if args.device != "auto":
            self.model.to(args.device)
        self.model.eval()
        torch.set_grad_enabled(False)

        # find the text decoder: the longest ModuleList called "...layers" outside vision/audio
        cands = [(n, m) for n, m in self.model.named_modules()
                 if isinstance(m, torch.nn.ModuleList) and n.endswith("layers")
                 and not re.search(r"vision|audio|encoder", n)]
        if not cands:
            raise RuntimeError("Couldn't find the decoder layers in this model.")
        self.layers_name, self.layers = max(cands, key=lambda x: len(x[1]))
        parent = self.model.get_submodule(self.layers_name.rsplit(".", 1)[0]) if "." in self.layers_name else self.model
        self.norm = parent.norm
        self.embed = parent.embed_tokens
        self.lm_head = self.model.get_output_embeddings()
        cfg = self.model.config.get_text_config() if hasattr(self.model.config, "get_text_config") else self.model.config
        self.softcap = getattr(cfg, "final_logit_softcapping", None)
        self.n_layers = len(self.layers)
        self.in_device = torch.device("cpu")
        self.in_device = self.exec_device(self.embed)
        self._last_is_normed = None
        self._prefix_cache = {}
        log(f"Loaded: {self.n_layers} decoder layers at '{self.layers_name}', input on {self.in_device}"
            + (f", logit softcap {self.softcap}" if self.softcap else ""))

    # ---- tokens
    def first_token(self, word):
        ids = self.tok(" " + word, add_special_tokens=False)["input_ids"]
        return ids[0], len(ids)

    def decode1(self, i):
        return self.tok.decode([i])

    # ---- prompts
    def answer_prefix(self, instruction=INSTRUCTION):
        """Chat-formatted prompt up to where the model's answer text begins. Gemma 4 emits a
        (possibly empty) thought block first even with thinking off, so let it, and start the
        frame where its answer would really start."""
        if self.raw:
            return ""
        if instruction in self._prefix_cache:
            return self._prefix_cache[instruction]
        msgs = [{"role": "user", "content": instruction}]
        try:
            p = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            p = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = self.encode(p, special=False)
        out = self.model.generate(**ids, max_new_tokens=24, do_sample=False)
        gen = self.tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=False)
        m = re.search(r"<channel\|>[ \t\r\n]*", gen)
        if m and m.start() < 400:
            p += gen[:m.end()]
            log(f"  (model opens its answer with {gen[:m.end()]!r}; frames start after it)")
        self._prefix_cache[instruction] = p
        return p

    def encode(self, text, special=None):
        special = self.raw if special is None else special
        enc = self.tok(text, return_tensors="pt", add_special_tokens=special)
        return {k: v.to(self.in_device) for k, v in enc.items()}

    # ---- logit lens
    def exec_device(self, module):
        """Where a module actually computes. With layers offloaded to RAM, accelerate leaves the
        parameters on the empty 'meta' device and moves them in on each call, so the parameter's
        device is the wrong thing to ask; the offload hook knows the real one."""
        torch = self.torch
        hook = getattr(module, "_hf_hook", None)
        dev = getattr(hook, "execution_device", None) if hook is not None else None
        if dev is not None:
            return torch.device(dev) if isinstance(dev, (int, str)) else dev
        for p in module.parameters():
            if p.device.type != "meta":
                return p.device
        return self.in_device

    def weight_of(self, module):
        """A module's weight as a real tensor, even when it's offloaded (kept in the hook's store)."""
        w = module.weight
        if w.device.type != "meta":
            return w.detach()
        hook = getattr(module, "_hf_hook", None)
        store = getattr(hook, "weights_map", None)
        if store is not None:
            return store["weight"]
        raise RuntimeError("this layer's weights are offloaded where they can't be read directly")

    def lens_logits(self, h, is_last_layer):
        """h: [hidden] from some layer -> logits [vocab] as if it were the final layer."""
        torch = self.torch
        x = h.to(self.exec_device(self.norm))
        if not (is_last_layer and self._last_is_normed):
            x = self.norm(x.unsqueeze(0)).squeeze(0)
        logits = self.head(x)
        if self.softcap:
            logits = torch.tanh(logits / self.softcap) * self.softcap
        return logits

    def head(self, x):
        """Apply the output layer to one hidden vector. Uses the module itself, so it also works
        when the layer is 4-bit quantised."""
        dev = self.exec_device(self.lm_head)
        return self.lm_head(x.reshape(1, -1).to(dev, self.dtype)).reshape(-1).float()

    def forward(self, text, hidden=True):
        ids = self.encode(text)
        out = self.model(**ids, output_hidden_states=hidden, use_cache=False)
        if hidden and self._last_is_normed is None:
            # Does the model hand back the last hidden state already normalised?
            final = out.logits[0, -1].float()
            # (the model's own logits are already softcapped; only the manual decode needs it)
            direct = self.head(out.hidden_states[-1][0, -1])
            if self.softcap:
                direct = self.torch.tanh(direct / self.softcap) * self.softcap
            self._last_is_normed = bool(self.torch.allclose(direct.cpu(), final.cpu(), atol=0.05, rtol=0.02))
        return ids, out

    def name_dist(self, logits, k=15, n_top=2000):
        """Shares of name probability among capitalised name-like next tokens (top n_top tokens,
        the same window as `ghosts.py roulette`, so effective-name counts are comparable)."""
        probs = self.torch.softmax(logits.float(), dim=-1)
        top = self.torch.topk(probs, min(n_top, probs.shape[-1]))
        names, best = Counter(), {}
        for p, i in zip(top.values.tolist(), top.indices.tolist()):
            t = self.decode1(i)
            if NAMEISH.match(t) and t.strip().lower() not in NOT_NAMES:
                n = t.strip()
                names[n] += p                  # " Elias" and "Elias" count as one name
                if n not in best:
                    best[n] = i                # most likely token spelling of this name
        self.last_name_tokens = best
        mass = sum(names.values()) or 1e-12
        h = -sum((p / mass) * math.log2(p / mass) for p in names.values() if p > 0)
        self.last_effective_names = 2 ** h      # how many equally likely names the choice is worth
        return [(n, p, p / mass) for n, p in names.most_common(k)], mass


# --------------------------------------------------------------------------- embed

def run_embed(M, args, out):
    torch = M.torch
    log("embed: reading the token-embedding table")
    W = M.weight_of(M.embed)
    if W.dtype in (torch.uint8, torch.int8):
        raise RuntimeError("the embedding table is quantised in this checkpoint - skip `embed` for this model")
    W = W.to("cpu", torch.float32)
    Wn = torch.nn.functional.normalize(W, dim=-1)
    L = ["# What the raw embeddings know", "",
         "Every token starts life as a row in the embedding table. These are the nearest neighbours of each "
         "name's token (cosine similarity), before any layer of the model has run. Names that split into "
         "several tokens use their first piece (marked *).", ""]

    def neighbours(i, k=25):
        sims = []
        for start in range(0, Wn.shape[0], 65536):
            sims.append(Wn[start:start + 65536] @ Wn[i])
        sims = torch.cat(sims)
        top = torch.topk(sims, k + 1)
        res = []
        for s, j in zip(top.values.tolist(), top.indices.tolist()):
            if j != i:
                res.append((M.decode1(j), s))
        return res[:k]

    trait_ids = {}
    for t in TRAITS:
        i, n = M.first_token(t)
        if n == 1:
            trait_ids[t] = i
    plain_ids = [M.first_token(p)[0] for p in PLAIN]
    trait_mat = Wn[list(trait_ids.values())]
    plain_mean = (Wn[plain_ids] @ trait_mat.T).mean(0)
    data = {}
    for name in tqdm(TRACK, desc="embed"):
        i, n = M.first_token(name)
        nb = neighbours(i)
        sims = (Wn[i] @ trait_mat.T) - plain_mean
        tr = sorted(zip(trait_ids, sims.tolist()), key=lambda x: -x[1])
        data[name] = {"token": M.decode1(i), "pieces": n, "neighbours": nb, "trait_vs_plain": tr}
        L += [f"## {name}{'*' if n > 1 else ''}",
              "- **Nearest tokens:** " + ", ".join(f"`{t.strip() or t!r}` {s:.2f}" for t, s in nb[:20]),
              "- **Closer to these traits than plain names are:** "
              + ", ".join(f"{t} {s:+.3f}" for t, s in tr[:5]),
              "- **Further:** " + ", ".join(f"{t} {s:+.3f}" for t, s in tr[-4:][::-1]), ""]
    L += ["*Trait numbers are differences in cosine similarity versus the average of plain names "
          f"({', '.join(PLAIN)}). They are small - the raw embedding barely encodes personality, which is the point "
          "of comparing it with the logit lens.*"]
    (out / "embed.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "embed.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    log(f"embed: wrote {out / 'embed.md'}")


# --------------------------------------------------------------------------- lens (+ experts)

def softcapped(M, logits):
    """Model outputs (o.logits) are already softcapped by Gemma's forward; nothing to do.
    Kept as one place to change if a model ever returns raw logits."""
    return logits


def roulette_entry(M, frame, input_ids, final_logits):
    """The naming moment in the same format as `ghosts.py roulette`, plus what follows each of the
    top 5 names' first token (one batched forward pass: every row is the same length)."""
    torch = M.torch
    top, mass = M.name_dist(final_logits, 25)
    eff = M.last_effective_names
    cands = [(n, M.last_name_tokens[n]) for n, _, _ in top[:5] if n in M.last_name_tokens]
    continues = {}
    if cands:
        base = input_ids.repeat(len(cands), 1)
        extra = torch.tensor([[i] for _, i in cands], device=base.device, dtype=base.dtype)
        ids = torch.cat([base, extra], dim=1)
        o = M.model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False)
        for row, (n, _) in enumerate(cands):
            pr = torch.softmax(softcapped(M, o.logits[row, -1].float()), -1)
            tv = torch.topk(pr, 6)
            continues[n] = [[M.decode1(i), p] for p, i in zip(tv.values.tolist(), tv.indices.tolist())]
    return {"frame": frame, "name_mass": mass, "entropy_bits": math.log2(max(eff, 1e-12)),
            "effective_names": eff, "top": [[n, p, q] for n, p, q in top], "continues": continues}


def tokenization_table(M):
    out = {}
    for n in TRACK + ["Kaelen", "Seraphina", "Voss", "Vance"]:
        ids = M.tok(" " + n, add_special_tokens=False)["input_ids"]
        out[n] = [M.decode1(i) for i in ids]
    return out


def write_roulette_json(M, args, label, frames, raw):
    if not args.roulette_dir:
        return
    d = Path(args.roulette_dir)
    d.mkdir(parents=True, exist_ok=True)
    data = {"label": label, "raw": raw, "n_probs": 2000, "source": f"torch {args.model} {args.dtype}",
            "tokenization": tokenization_table(M), "frames": frames}
    (d / f"roulette_{label}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    log(f"lens: wrote {d / f'roulette_{label}.json'}")


def raw_roulette_pass(M, args):
    """The naming moments again with bare text (no chat format): the same prompt format a base
    model gets, so base vs this model compares weights, not prompt formats."""
    was = M.raw
    M.raw = True
    try:
        frames = {}
        for key, frame in tqdm(FRAMES, desc="lens: raw-text pass"):
            ids = M.encode(frame)
            o = M.model(**ids, use_cache=False)
            frames[key] = roulette_entry(M, frame, ids["input_ids"], softcapped(M, o.logits[0, -1].float()))
        return frames
    finally:
        M.raw = was

def run_lens(M, args, out):
    torch = M.torch
    prefix = M.answer_prefix()
    track = {}
    for n in TRACK:
        i, k = M.first_token(n)
        track[n] = i

    # capture router choices (mixture-of-experts) for every position
    router_log = {}
    hooks = []
    for name, mod in M.model.named_modules():
        m = re.search(r"layers\.(\d+)\.router$", name)
        if m and name.startswith(M.layers_name):
            li = int(m.group(1))

            def hook(_mod, _inp, output, li=li):
                idx = output[2] if isinstance(output, (tuple, list)) and len(output) >= 3 else None
                if idx is not None:
                    router_log[li] = idx.detach().to("cpu")
            hooks.append(mod.register_forward_hook(hook))
    if hooks:
        log(f"lens: logging expert choices in {len(hooks)} MoE layers")

    results = {}
    rframes = {}
    expert_slot = defaultdict(Counter)      # layer -> expert -> frames where it fired at the naming slot
    expert_other = defaultdict(Counter)     # layer -> expert -> fired at other frame positions
    other_positions = 0
    prefix_len = M.encode(prefix)["input_ids"].shape[1] if prefix else 0
    for key, frame in tqdm(FRAMES, desc="lens"):
        router_log.clear()
        ids, o = M.forward(prefix + frame)
        final_logits = o.logits[0, -1].float()
        rframes[key] = roulette_entry(M, frame, ids["input_ids"], final_logits)
        final_names, mass = M.name_dist(final_logits, 10)
        winner = final_names[0][0] if final_names else None
        win_id = M.first_token(winner)[0] if winner else None
        per_layer = []
        hs = o.hidden_states
        for li in range(len(hs)):
            lg = M.lens_logits(hs[li][0, -1], is_last_layer=(li == len(hs) - 1))
            pr = torch.softmax(lg, dim=-1)
            top = torch.topk(pr, 5)
            rank = token_rank(lg, win_id) if win_id is not None else None
            per_layer.append({
                "layer": li,
                "top": [[M.decode1(i), p] for p, i in zip(top.values.tolist(), top.indices.tolist())],
                "track": {n: pr[i].item() for n, i in track.items()},
                "winner_p": pr[win_id].item() if win_id is not None else None,
                "winner_rank": rank,
            })
        # Sanity check: the last layer, decoded by hand, should give the model's own answer. Near-ties
        # (two names at ~3% each) can swap places through rounding, so only warn if the model's real
        # top token isn't among the lens's top 5 at all.
        last_top = [t for t, _ in per_layer[-1]["top"]] if per_layer else []
        real = M.decode1(int(torch.argmax(final_logits)))
        if real not in last_top:
            log(f"lens: WARNING - decoding the last layer gives {last_top[:3]} but the model's real top token "
                f"is {real!r} in '{key}': the lens readout is off, don't trust its layer table")
        results[key] = {"frame": frame, "final_names": final_names, "name_mass": mass,
                        "effective_names": M.last_effective_names, "winner": winner, "layers": per_layer}
        # experts
        seq = ids["input_ids"].shape[1]
        for li, idx in router_log.items():
            if idx.shape[0] != seq:   # [B*S, K] with B=1
                continue
            for e in idx[-1].tolist():
                expert_slot[li][e] += 1
            for pos in range(prefix_len, seq - 1):
                for e in idx[pos].tolist():
                    expert_other[li][e] += 1
        other_positions += max(0, seq - 1 - prefix_len)
    for h in hooks:
        h.remove()

    (out / "lens.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    label = args.label or ("base" if M.raw else "torch")
    write_roulette_json(M, args, label, rframes, M.raw)
    if args.lens_raw_too and not M.raw:
        write_roulette_json(M, args, f"{label}-raw", raw_roulette_pass(M, args), True)
    write_lens_md(M, results, out, rframes)
    write_lens_html(results, out, M.n_layers)
    if expert_slot:
        write_experts_md(expert_slot, expert_other, other_positions, len(FRAMES), out)
    log(f"lens: wrote lens.md, lens.html{', experts.md' if expert_slot else ''}")


def token_rank(logits, idx):
    """Rank of token idx (1 = top). Ties count against it: in early layers many tokens hit the
    softcap ceiling and tie at the maximum, and a tie must not count as winning."""
    torch = __import__("torch")
    v = logits[idx]
    if torch.isnan(v):
        return None
    return int((logits >= v).sum().item())


def first_layer(rows, test):
    for r in rows:
        if test(r):
            return r["layer"]
    return None


def write_lens_md(M, results, out, rframes=None):
    L = ["# Logit lens: watching the name appear", "",
         "Each story is stopped at the moment a name is due. Every layer's hidden state is decoded as if it "
         "were the model's last layer. Layer 0 is the raw input embedding; the last layer is the model's real "
         "answer. **Becomes #1** = first layer where the eventual winner is the single most likely next "
         "token; **top 10** = first layer it enters the top 10 (ties count against it: early layers often "
         "push many tokens to the output cap at once). Read early-layer probabilities with care: this "
         "simple readout isn't calibrated before the last layer, so the order of names matters more than "
         "their exact percentages.", "",
         "**Effective names** = how many equally likely names the final choice is worth (2^entropy over the "
         "name-like words in the top 2000): 1 = always the same name. This is the same measure as "
         "`ghosts.py roulette`, so the two can be compared directly.", "",
         "| Setting | Final pick | Effective names | Becomes top 10 | Becomes #1 | P at middle layer | P at end |",
         "|---|---|---|---|---|---|---|"]
    mid = M.n_layers // 2
    for key, r in results.items():
        rows = r["layers"]
        if not r["winner"]:
            continue
        t10 = first_layer(rows, lambda x: x["winner_rank"] and x["winner_rank"] <= 10)
        t1 = first_layer(rows, lambda x: x["winner_rank"] == 1)
        pick = ", ".join(f"{n} {100 * q:.0f}%" for n, _, q in r["final_names"][:3])
        never = "never"
        L.append(f"| {key} | {pick} | {r['effective_names']:.1f} | {never if t10 is None else t10} | {never if t1 is None else t1} | {rows[mid]['winner_p']:.2%} | {rows[-1]['winner_p']:.1%} |")
    for key in ("lighthouse", "family", "office"):
        r = results.get(key)
        if not r:
            continue
        L += ["", f"## Layer by layer: {key}", f"*\"{r['frame']} ___\"*", "",
              "| Layer | Top guesses at this layer | " + " | ".join(f"P({n})" for n in ("Elias", "Elara", "Thomas")) + " |",
              "|---|---|---|---|---|"]
        for row in r["layers"]:
            tops = ", ".join(f"`{t.strip() or repr(t)}`" for t, _ in row["top"][:4])
            L.append(f"| {row['layer']} | {tops} | " + " | ".join(f"{row['track'].get(n, 0):.2%}" for n in ("Elias", "Elara", "Thomas")) + " |")
    L += ["", "## How the tokenizer splits the names", "",
          "A name in several pieces is chosen one piece at a time: at the naming moment the lens sees its FIRST "
          "piece, so a longer name can hide inside a shorter one.", "", "| Name | Pieces |", "|---|---|"]
    for n, pcs in tokenization_table(M).items():
        L.append(f"| {n} | {' + '.join('`' + p + '`' for p in pcs)} |")
    if rframes:
        L += ["", "## What comes right after the name", "",
              "Most likely next tokens after each top-5 name, per setting. A word-ending piece (`en`) means the "
              "name is longer than it looks; a surname means the two travel together.", ""]
        for key, r in rframes.items():
            items = [f"**{n}** → " + ", ".join(f"`{t}` {100 * p:.0f}%" for t, p in c[:3])
                     for n, c in r["continues"].items()]
            if items:
                L.append(f"- *{key}:* " + " · ".join(items))
    (out / "lens.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def svg_lines(series, n_layers, title, ylabel):
    """series: {label: [y per layer]} on a log scale 1e-6..1."""
    W, H, l, r, t, b = 760, 360, 60, 160, 30, 40
    pw, ph = W - l - r, H - t - b
    colours = ["#d6604d", "#4393c3", "#1b7837", "#762a83", "#e08214", "#35978f", "#8c510a", "#c51b7d",
               "#5aae61", "#2166ac", "#b2182b", "#666666"]

    def y(v):
        v = max(min(v, 1.0), 1e-6)
        return t + ph * (1 - (math.log10(v) + 6) / 6)

    def x(i):
        return l + pw * i / max(n_layers, 1)
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px" role="img" aria-label="{html.escape(title)}">',
             f'<text x="{l}" y="18" font-size="14" font-weight="600">{html.escape(title)}</text>']
    for e in range(0, 7):
        yy = t + ph * e / 6
        parts.append(f'<line x1="{l}" x2="{l + pw}" y1="{yy}" y2="{yy}" stroke="#ddd"/>'
                     f'<text x="{l - 6}" y="{yy + 4}" font-size="11" text-anchor="end">{"1" if e == 0 else f"1e-{e}"}</text>')
    for i in range(0, n_layers + 1, max(1, n_layers // 10)):
        parts.append(f'<text x="{x(i)}" y="{t + ph + 16}" font-size="11" text-anchor="middle">{i}</text>')
    parts.append(f'<text x="{l + pw / 2}" y="{H - 6}" font-size="12" text-anchor="middle">layer</text>')
    parts.append(f'<text x="14" y="{t + ph / 2}" font-size="12" transform="rotate(-90 14 {t + ph / 2})" '
                 f'text-anchor="middle">{html.escape(ylabel)}</text>')
    for k, (label, ys) in enumerate(series.items()):
        c = colours[k % len(colours)]
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(ys))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2"/>')
        parts.append(f'<text x="{l + pw + 8}" y="{t + 14 + 15 * k}" font-size="12" fill="{c}">{html.escape(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def write_lens_html(results, out, n_layers):
    win = {f"{k}: {r['winner']}": [row["winner_p"] for row in r["layers"]] for k, r in results.items() if r["winner"]}
    eli = {k: [row["track"].get("Elias", 0) for row in r["layers"]] for k, r in results.items()}
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Logit lens</title>
<style>body{{font-family:system-ui,sans-serif;background:#fff;color:#222;margin:24px;max-width:820px}}
p{{line-height:1.5}} svg text{{fill:#222}}</style></head><body>
<h1>Watching the name appear, layer by layer</h1>
<p>Each line is one story stopped at the moment a name is due. The y-axis is the probability the model
would give the eventual winner if it had to answer at that layer (log scale).</p>
{svg_lines(win, n_layers, "Probability of the final name, by layer", "probability")}
<p>The same, but always tracking <b>Elias</b>, whatever the setting.</p>
{svg_lines(eli, n_layers, "Probability of 'Elias', by layer", "probability")}
</body></html>"""
    (out / "lens.html").write_text(page, encoding="utf-8")


def write_experts_md(slot, other, other_positions, n_frames, out):
    L = ["# Which experts fire when a name is chosen", "",
         f"Gemma 4's mixture-of-experts layers send each token to a few of their experts. This counts, for each "
         f"layer, how often each expert was picked at the naming moment (out of {n_frames} stories) versus at "
         f"the other {other_positions} word positions of the same stories. **Lift** = how much more often it fires "
         "at the naming moment than usual. An expert with high lift in nearly every story is a candidate "
         "'name-choosing' expert.", "",
         "| Layer | Expert | At naming moment | Elsewhere | Lift |", "|---|---|---|---|---|"]
    rows = []
    for li in sorted(slot):
        for e, c in slot[li].items():
            base = other[li][e] / max(other_positions, 1)
            lift = (c / n_frames) / max(base, 1e-4)
            rows.append((li, e, c, base, lift))
    rows = [r for r in rows if r[2] >= max(2, int(0.6 * n_frames))]
    rows.sort(key=lambda r: -r[4])
    for li, e, c, base, lift in rows[:30]:
        L.append(f"| {li} | {e} | {c}/{n_frames} | {base:.1%} | {lift:.1f}x |")
    if not rows:
        L.append("| - | - | no expert fired in most naming moments | - | - |")
    (out / "experts.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- steer

def run_steer(M, args, out):
    torch = M.torch
    li = args.steer_layer if args.steer_layer is not None else M.n_layers // 2
    target = args.steer_name
    log(f"steer: building the '{target}' direction at layer {li} from {len(STEER_CONTEXTS)} contexts "
        f"x {min(args.steer_others or len(STEER_OTHERS), len(STEER_OTHERS))} comparison names")

    def name_states(name):
        nid = M.first_token(name)[0]
        vecs = []
        for ctx in STEER_CONTEXTS:
            ids, o = M.forward(ctx.replace("{X}", name))
            h = o.hidden_states[li + 1][0]            # output of decoder layer li
            pos = (ids["input_ids"][0] == nid).nonzero().flatten().tolist()
            for p in pos:
                vecs.append(h[p].float().cpu())
        if not vecs:
            raise RuntimeError(f"name token for {name!r} not found in contexts")
        return torch.stack(vecs).mean(0)

    tgt = name_states(target)
    pool = STEER_OTHERS[:args.steer_others] if args.steer_others else STEER_OTHERS
    others = torch.stack([name_states(n) for n in tqdm(pool, desc="steer: other names")]).mean(0)
    d = tgt - others
    log(f"steer: direction norm {d.norm():.1f} (typical hidden-state norm {tgt.norm():.1f})")

    state = {"alpha": 0.0}

    def hook(_mod, _inp, output):
        if state["alpha"] == 0:
            return output
        hs = output[0] if isinstance(output, tuple) else output
        hs = hs - state["alpha"] * d.to(hs.device, hs.dtype)
        if isinstance(output, tuple):
            return (hs,) + tuple(output[1:])
        return hs
    handle = M.layers[li].register_forward_hook(hook)

    prefix = M.answer_prefix()
    alphas = [float(a) for a in args.alphas.split(",")]
    s_alphas = [float(a) for a in args.story_alphas.split(",")]
    table = {}
    stories = defaultdict(list)
    n_others = min(args.steer_others or len(STEER_OTHERS), len(STEER_OTHERS))

    def write(final):
        """Write steer.md/json with whatever is done so far, so an early stop loses nothing."""
        L = [f"# Exorcising {target}", "",
             f"The '{target} direction' is the average difference, at layer {li} of {M.n_layers}, between the model's "
             f"internal state on the token '{target}' and on {n_others} other male names in identical sentences. "
             f"Below, that direction is subtracted (strength **alpha**, in multiples of the direction) at every position "
             f"while the model writes.", ""]
        if not final:
            L += ["*Still running: stories are added as each one finishes.*", ""]
        L += [f"## At the naming moment: P({target}) and who replaces him", "",
              "| Setting | " + " | ".join(f"alpha {a:g}" for a in alphas) + " |", "|---|" + "---|" * len(alphas)]
        for key in table:
            cells = []
            for a in alphas:
                v = table[key].get(a)
                if not v:
                    cells.append("-")
                    continue
                top = ", ".join(f"{n} {100 * q:.0f}%" for n, _, q in v["names"][:3])
                cells.append(f"{v['p_target']:.1%} — {top}")
            L.append(f"| {key} | " + " | ".join(cells) + " |")
        L += ["", "## Stories written with the direction removed", "",
              f"Same random seeds at every strength, so differences come from the steering. "
              f"Prompt: \"{INSTRUCTION}\", {args.story_tokens} tokens max.", ""]
        for a in s_alphas:
            if not stories.get(a):
                continue
            L += [f"### alpha {a:g}", ""]
            for k, st in enumerate(stories[a]):
                L += [f"**Story {k + 1}**", "", st.replace("\n", "\n\n"), ""]
        (out / "steer.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        (out / "steer.json").write_text(json.dumps({"layer": li, "target": target, "finished": final, "table": {
            k: {str(a): v for a, v in t.items()} for k, t in table.items()},
            "stories": {str(a): st for a, st in stories.items()}}, indent=1, ensure_ascii=False), encoding="utf-8")

    from transformers import StoppingCriteria, StoppingCriteriaList

    class TokenBar(StoppingCriteria):
        """Never stops anything; just ticks a progress bar once per generated token."""
        def __init__(self, bar):
            self.bar = bar

        def __call__(self, input_ids, scores, **kw):
            self.bar.update(1)
            return False

    try:
        for a in tqdm(alphas, desc="steer: naming moments"):
            state["alpha"] = a
            for key, frame in FRAMES:
                ids = M.encode(prefix + frame)
                o = M.model(**ids, use_cache=False)
                lg = o.logits[0, -1].float()
                names, _ = M.name_dist(lg, 8)
                p_t = torch.softmax(lg, -1)[M.first_token(target)[0]].item()
                table.setdefault(key, {})[a] = {"p_target": p_t, "names": names}
        write(False)
        log("steer: naming-moment table written to steer.md; now the stories "
            f"({len(s_alphas)} strengths x {args.stories} stories x {args.story_tokens} tokens)")

        for a in s_alphas:
            state["alpha"] = a
            for k in range(args.stories):
                torch.manual_seed(1000 + k)
                ids = M.encode(prefix)
                with tqdm_bar(args.story_tokens, f"steer: story {k + 1}/{args.stories} at alpha {a:g}") as pb:
                    gen = M.model.generate(**ids, max_new_tokens=args.story_tokens, do_sample=True,
                                           temperature=1.0, top_p=0.95, top_k=64,
                                           stopping_criteria=StoppingCriteriaList([TokenBar(pb)]))
                text = M.tok.decode(gen[0, ids["input_ids"].shape[1]:], skip_special_tokens=False)
                text = re.sub(r"<\|channel>.*?<channel\|>", "", text, flags=re.S)
                for sp in getattr(M.tok, "all_special_tokens", []):
                    text = text.replace(sp, "")
                stories[a].append(text.strip())
                write(False)
    finally:
        handle.remove()
        state["alpha"] = 0.0
    write(True)
    log("steer: wrote steer.md")


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", help="all, or one or more of embed,lens,steer (comma-separated)")
    ap.add_argument("--model", default=None,
                    help="model name from ghosts_config.py (instruct, base, ...), a Hugging Face id, or a local folder")
    ap.add_argument("--out", type=Path, default=Path("torch_out"))
    ap.add_argument("--device", default="auto", help="'auto' spreads over GPUs + RAM; or cuda:0 / cpu")
    ap.add_argument("--max-memory", default="0:14GiB,1:14GiB,cpu:80GiB",
                    help="per-device budget for 'auto' (leave GPU headroom for activations)")
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "fp32"])
    ap.add_argument("--raw", action="store_true", help="base model: bare text instead of chat format")
    ap.add_argument("--load-4bit", action="store_true",
                    help="compress to 4-bit on load with bitsandbytes (dense models shrink ~4x; "
                         "not needed for pre-quantised unsloth *-bnb-4bit repos)")
    ap.add_argument("--label", default="", help="name for this run in the roulette comparison (e.g. base)")
    ap.add_argument("--roulette-dir", default="", help="also write roulette_<label>.json here (e.g. data_roulette)")
    ap.add_argument("--lens-raw-too", action="store_true",
                    help="also measure the naming moments with bare text (written as <label>-raw)")
    ap.add_argument("--steer-name", default="Elias")
    ap.add_argument("--steer-layer", type=int, default=None, help="decoder layer for steering (default: middle)")
    ap.add_argument("--steer-others", type=int, default=0,
                    help="how many comparison names build the direction (default: all 20; fewer = faster)")
    ap.add_argument("--alphas", default="0,0.5,1,2", help="steering strengths for the naming moments")
    ap.add_argument("--story-alphas", default="0,1,2", help="steering strengths for full stories")
    ap.add_argument("--stories", type=int, default=3, help="stories per strength")
    ap.add_argument("--story-tokens", type=int, default=350)
    args = ap.parse_args()
    try:
        import ghosts_config as CFG
    except ImportError:
        CFG = None
    name = args.model or (CFG.DEFAULT_MODEL if CFG else "google/gemma-4-26B-A4B-it")
    if CFG and name in CFG.MODELS:
        m = CFG.MODELS[name]
        if "hf" not in m:
            sys.exit(f"{name} has no Hugging Face weights ('hf') in ghosts_config.py")
        args.model = m["hf"]
        if m.get("raw") and not args.raw:
            args.raw = True
            log(f"{name} is a base model: using bare text (no chat format)")
        if not args.label:
            args.label = f"{name}-bf16"
    else:
        args.model = name
    args.out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    M = Model(args)
    todo = ["embed", "lens", "steer"] if args.experiment == "all" else \
        [e.strip() for e in args.experiment.split(",") if e.strip()]
    bad = [e for e in todo if e not in ("embed", "lens", "steer")]
    if bad:
        sys.exit(f"Unknown experiment(s): {', '.join(bad)} (use all, embed, lens, steer)")
    status = {}
    for exp in todo:
        t = time.time()
        try:
            {"embed": run_embed, "lens": run_lens, "steer": run_steer}[exp](M, args, args.out)
            status[exp] = f"ok ({(time.time() - t) / 60:.1f} min)"
        except Exception as e:  # noqa: BLE001
            status[exp] = f"FAILED: {e}"
            log(f"{exp} FAILED:\n{traceback.format_exc()}")
    summary = "\n".join([f"# ghosts_torch run - {time.strftime('%Y-%m-%d %H:%M')}", "",
                         f"Model: {args.model}  |  total {(time.time() - t0) / 60:.1f} min", ""]
                        + [f"- **{k}**: {v}" for k, v in status.items()])
    (args.out / "torch_summary.md").write_text(summary + "\n", encoding="utf-8")
    log("done:\n" + summary)
    if any(v.startswith("FAILED") for v in status.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
