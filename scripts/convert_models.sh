#!/usr/bin/env bash
# convert_models.sh - download stock Gemma 4 26B-A4B (instruct + base) from Hugging Face and convert
# both to Q8_0 GGUF with your existing llama.cpp. llama.cpp and the PyTorch experiments then use the
# exact same weights: the GGUFs are made from the very files ghosts_torch.py loads.
#
#   bash scripts/convert_models.sh
#
# Needs about 160 GB free: 2 x ~52 GB downloads (kept: PyTorch uses them) + 2 x ~27 GB GGUFs.
# Safe to re-run: finished downloads and conversions are skipped.
set -euo pipefail

LLAMA_CPP="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"    # your existing llama.cpp checkout
OUT="${GHOSTS_MODELS_DIR:-$HOME/models}"          # where the GGUFs go (matches ghosts_config.py)
REPOS=("google/gemma-4-26B-A4B-it" "google/gemma-4-26B-A4B")

mkdir -p "$OUT"
cd "$LLAMA_CPP"

# This llama.cpp's converter must know Gemma 4 (a recent build).
if ! grep -q "Gemma4" convert_hf_to_gguf.py; then
  echo "convert_hf_to_gguf.py in $LLAMA_CPP doesn't mention Gemma 4 - stopping before any download."
  exit 1
fi

for REPO in "${REPOS[@]}"; do
  NAME="$(basename "$REPO")"
  GGUF="$OUT/${NAME}-Q8_0.gguf"
  if [ -s "$GGUF" ]; then
    echo "== $NAME: already converted ($GGUF)"
    continue
  fi
  echo "== $NAME: downloading (skipped if already in the Hugging Face cache)"
  SRC="$(python -c "from huggingface_hub import snapshot_download; print(snapshot_download('$REPO'))")"
  echo "   weights: $SRC"
  echo "== $NAME: converting to $GGUF (several minutes)"
  python convert_hf_to_gguf.py "$SRC" --outtype q8_0 --outfile "$GGUF.part"
  mv "$GGUF.part" "$GGUF"      # only a finished file gets the real name
done

echo
ls -lh "$OUT"/gemma-4-26B-A4B*-Q8_0.gguf
echo "Done. Next: python overnight.py --check"
