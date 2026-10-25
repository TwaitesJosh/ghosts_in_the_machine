"""
ghosts_config.py - shared settings for ghosts.py, ghosts_torch.py and overnight.py.

Edit this file (or set the environment variables below), not the scripts. Models are picked
by name everywhere:

    python ghosts.py --model instruct probe          # starts llama-server on the instruct GGUF, stops it after
    python ghosts.py --model base roulette           # base model: bare text is used automatically
    python ghosts_torch.py lens --model base         # PyTorch, on the base model's Hugging Face weights

If llama-server is already running the same model on PORT, the scripts use it and leave it running.
"""

import os

# Where your llama.cpp build and your GGUF files live. Override with environment variables,
# e.g.  export LLAMA_CPP_DIR=~/src/llama.cpp  GHOSTS_MODELS_DIR=/data/models
LLAMA_CPP_DIR = os.path.expanduser(os.environ.get("LLAMA_CPP_DIR", "~/llama.cpp"))
MODELS_DIR = os.path.expanduser(os.environ.get("GHOSTS_MODELS_DIR", "~/models"))

LLAMA_SERVER = os.path.join(LLAMA_CPP_DIR, "build", "bin", "llama-server")
PORT = int(os.environ.get("GHOSTS_PORT", "8081"))

# Flags passed to llama-server on top of the model and port. Keep -np equal to WORKERS.
SERVER_ARGS = ["-ngl", "99", "-c", "32768", "-np", "4", "--jinja"]
WORKERS = 4

DEFAULT_MODEL = "instruct"

# Each model: a GGUF for llama.cpp, optionally the Hugging Face repo for the PyTorch experiments,
# the output folder, and "raw": True for base models (bare text, no chat template).
# scripts/convert_models.sh makes both GGUFs below from the official weights.
# To compare another model, add an entry and pass its name with --model.
MODELS = {
    "instruct": {   # google/gemma-4-26B-A4B-it - the main model
        "gguf": os.path.join(MODELS_DIR, "gemma-4-26B-A4B-it-Q8_0.gguf"),
        "hf": "google/gemma-4-26B-A4B-it",
        "data": "data",
    },
    "base": {       # google/gemma-4-26B-A4B - pre-trained only, no chat tuning
        "gguf": os.path.join(MODELS_DIR, "gemma-4-26B-A4B-Q8_0.gguf"),
        "hf": "google/gemma-4-26B-A4B",
        "data": "data_base",
        "raw": True,
    },
}
