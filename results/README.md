# Results

Outputs from one overnight run on **Gemma 4 26B-A4B** (October 2026): the chat model (`google/gemma-4-26B-A4B-it`) and its base model (`google/gemma-4-26B-A4B`), converted to Q8_0 GGUF for llama.cpp and loaded in bf16 for PyTorch.

| File | Experiment |
|---|---|
| `report.md` | 1,000 stories from 10 prompts: name leaderboard, surnames, and a profile of each main character |
| `sheets/` | Composite character sheets **written by Gemma** from the extracted data. Read them for flavour; take numbers from `report.md` |
| `bio_report.md` | Biographies from the bare name (30 per name), compared with who the name is in the stories |
| `genre.md` | Each name as the hero of 8 genres, with David and Sarah as controls |
| `swap_open.md` | Stories forced to open with each name (20 per name) |
| `swap_cut.md` | 20 of Elias's stories cut where he first appears and continued as David, Thomas or Vorrak |
| `probe/` | Next-word trait probabilities after each name. `instruct_*` = chat model, `base_*` = base model; `story_traits` uses the traits from the stories, `general_traits` a general adjective list with invented names |
| `roulette.md`, `roulette.html` | Effective number of names at 12 naming moments, base vs chat, llama.cpp vs PyTorch |
| `lens_instruct.md` | Logit lens on the chat model at each naming moment |
| `steer.md` | Subtracting an "Elias direction" at layer 15 |

Notes:

- In `roulette.md`, ignore the `instruct-bf16-raw` column (see Known issues in the main README).
- The `probe/` files were labelled base or chat after the run, from their health-check figures.
