# Who are the ghosts in the machine?

*October 2026*

Ask a chat model for a story and you will meet Elias. I asked one model, Gemma 4, for 1,000 stories. Elias was in 762 of them.

He is an old clockmaker, or a lighthouse keeper, or a detective, or a father in a busy kitchen. He is quiet and observant, and something from his past weighs on him. Very often a woman named Clara walks into his shop.

Anyone who has read much AI fiction knows the names: Elias, Elara, Kaelen, Lyra, Silas, Thorne. People have counted them. This post asks the next question: who are these people? What are they like, what do they want, and does the name decide any of it?

The short answer is that the cast is tiny and the name decides less than you would think. A name tells the model what *kind of world* the story is set in. The genre tells it who the person is. And inside the network, the name is picked in the last few layers, after the model has already pictured the scene.

## Everyone has counted the names

The names are well documented. What nobody has done is ask who the characters behind them are.

- **[Hamilton & Mimno, "Elias in the Lighthouse, Again?"](https://arxiv.org/pdf/2605.26492)** collected 20,000 stories from four models. Eleven words, including Elias, Elara, lighthouse and keeper, appear in 88% of them. They trace the habit to preference tuning rather than pre-training. They code each story's name, job and setting, but not the person.
- **["The Ghost Couple"](https://tldr.takara.ai/p/2606.02184)** finds that names come in pairs and trios, and that each model family has its own. For Claude it's Elena Vasquez and Marcus Chen; for GPT, Elara Voss.
- **[Max Read, "Who is Elara Voss?"](https://maxread.substack.com/p/who-is-elara-voss)** follows one name into dozens of published books.
- **[404 Media](https://404media.co/elias-thorne-chatbots-llms-chatgpt-lighthouse-keeper-story/)** tracks Elias Thorne into AI-written books, YouTube and fake news sites, and **[Laura Wattenberg](https://www.aol.com/articles/ai-generated-baby-name-rolls-195619325.html)** made Elara her 2025 Name of the Year.

So we know the names. This post is about the people: their personalities, what they want, what haunts them, and whether the name carries any of it.

## What I did

Everything ran overnight on a home PC: two 16 GB RTX 5060 Ti cards and 96 GB of RAM. The model is Google's **Gemma 4 26B-A4B**, a mixture-of-experts model with 30 layers. I used the chat-tuned version and the base model it was trained from, both converted myself from Google's own weights. Stories came from llama.cpp; the experiments that needed the weights ran in PyTorch.

| Experiment | What it asks | How |
| --- | --- | --- |
| Stories | Who turns up? | 1,000 stories from 10 short prompts ("Write a story.", "Write a mystery story.", ...), then every named character extracted into a sheet: role, job, traits, goal, wound, fate |
| Biographies | Who is "Elias" with no story around him? | "Invent a character called X", 30 times per name, including plain and made-up names |
| Genre test | Is sci-fi Mara the same person as romance Mara? | Each name forced as the hero of 8 genres, compared with David and Sarah |
| Name swaps | Does the name bring its story with it? | Stories forced to start with a name; and Elias's stories cut where he first appears, then continued as someone else |
| Trait probe | What does the bare name suggest? | The probability of trait words (gentle, cruel...) straight after the name |
| Name roulette | How open is the choice? | The model stopped at "...an old keeper named \_\_\_" in 12 scenes; its probability for every possible name read off |
| Logit lens and steering | Where inside the network is the name chosen, and can we remove it? | Each layer's state decoded as if it were the last; then an "Elias direction" subtracted while the model writes |

The chat model wrote the stories at its default settings. A second pass of the same model turned each story into structured data. Plain names (David, Sarah, Thomas, Mary) and invented ones (Vorrak, Lumie) run through every test as controls.

## The cast

A thousand stories used just 74 different first names. Every single story had at least one of the top ten.

| Name | Stories | Usual role | Usual setting | Top traits |
| --- | --- | --- | --- | --- |
| Elias | 762 | Hero (96%) | Oakhaven, Blackwood Manor, Seattle | observant, skilled, weary, wise |
| Clara | 319 | Supporting (73%) | Oakhaven, Seattle, Blackwood Manor | vibrant, grieving, desperate, warm |
| Elara | 215 | Hero (97%) | Oakhaven, the Outer Rim | determined, brave, resilient, resourceful |
| Kaelen | 120 | Companion (76%) | Oakhaven | protective, cautious, observant, brave |
| Julian | 114 | Supporting (69%) | Blackwood Manor (52%) | wealthy, deceased, eccentric, nervous |
| Leo | 107 | Supporting (93%) | The Miller household | energetic, imaginative, playful, young |
| Maya | 100 | Supporting (88%) | The Miller household | imaginative, energetic, studious, artistic |
| Kael | 76 | Companion (88%) | Oakhaven, the *Rust-Bucket* | loyal, protective, cautious, observant |
| Sarah | 74 | Supporting (55%) | The Miller household | nurturing, observant, organized, graceful |
| Arthur | 62 | Supporting (69%) | Blackwood Manor (89%) | wealthy, secretive, habitual, calculating |

The surnames are just as narrow. Thorne turned up 246 times, and 242 of those were Elias. Blackwood belongs to the manor and the men who die in it; Vane and Vance are spread across the mystery cast.

It works like a small theatre company. A few actors play every part, and each has a type.

### Elias, the man who mends things

Elias is the lead in almost everything. In open prompts he is a clockmaker, a keeper or a "fixer" of broken things. In mysteries he is the investigator. In family stories he is the dad. When an age is given, it is usually elderly.

He is observant, skilled, weary and alone. He wants order: to mend the clock, keep the light, hold the family steady. He is haunted by a loss, often a wife or a daughter. His story is a move from rigidity to release. Nearly half end hopeful, with Elias accepting that some things can't be fixed. One sample sums him up: he wants "to mend the broken time and regrets of others", and in the end "he returns to his workbench to struggle with his own unfixable clock".

### Clara, the one who walks in

Clara appears in 318 of Elias's stories and almost never without him. She is the catalyst. She is vibrant and warm when she is his love interest, and grieving and desperate when she comes to his shop to trade away a memory. In dark stories she is often his dead wife, sometimes come back to punish him.

### Elara and her guards

Elara is the fantasy and sci-fi lead: a scavenger, a weaver of magic or a ship's captain. She is determined above all. Her stories end hopeful 65% of the time, often with her sacrificing part of herself to save a dying world.

She almost never travels alone. Kaelen (protective, weary, often an old warden) and Kael (loyal, anxious, usually the navigator) walk beside her. Their stories end hopeful too: they are there to make sure she survives.

### The household and the manor

Ask for a family story and you get the Millers. Elias is the father and Sarah the mother. Leo is the energetic young son who can't find his football kit, and Maya the moody teenage daughter with a violin solo. The stories end hopeful 80–86% of the time.

Ask for a mystery and you go to Blackwood Manor. Arthur Blackwood is usually the patriarch, and is usually dead of poisoning. Julian is the indebted heir or the man who staged a theft. Inspector Miller arrives to make an arrest.

And in space there is always a ship's AI: Ada, Pip, Aris or Mira. They are analytical, soothing and loyal.

## The name picks the world, not the person

So far this looks like a set of characters with fixed personalities. The controlled tests say otherwise. **Force a name into a story and the genre decides who they are.** What the name carries is the kind of world they live in.

### Is sci-fi Mara the same person as romance Mara?

No. I made each of ten names the hero of eight genres, six stories each, and compared their traits. A name that kept its personality would look more like itself across genres than like the other names in the same genre. None did.

Every name scored between −0.19 and −0.32 on that measure: the genre shaped them more than the name. The fantasy names did no better than David and Sarah, my plain-name controls. The model gave Elias, David, Clara and Leo the same romance personality:

| Genre | Elias | David | Clara | Leo |
| --- | --- | --- | --- | --- |
| Romance | book restorer; silent, meticulous, predictable | librarian; predictable, orderly, routine-oriented | archival restorer; predictable, quiet, cautious | accountant; predictable, solitary, structural |
| Sci-fi | scavenger; lonely, focused, determined | scavenger; observant, skilled, weary | scavenger of echoes; observant, determined | scavenger; observant, determined |
| Mystery | retired clockmaker; precise, solitary | retired clockmaker; precise, meticulous | estate liquidator; observant, skeptical | retired forensic horologist; precise, observant |

In the stories the model writes for itself, Elara and Kaelen *do* look consistent. That's casting, not character: the model only ever puts them in fantasy and sci-fi. Moved into a romance, they become quiet archivists like everyone else.

### Who is "Elias" when you just ask?

Asking for a character by name gives the same answer. Elias comes back as a quiet, observant archivist or clockmaker, haunted by someone he failed to save. So does David: archivist 33%, clockmaker 20%, "quiet" his top trait. So does Sarah, who is an archivist 40% of the time; in every sample I read, the loss she carries is a sister.

The model has one default person: **a quiet, observant restorer of old things, haunted by a loss.** Most names get that person.

### What the name does carry

What changes from name to name is the world around that person:

- **Fantasy names bring fantasy.** Biographies for Elara are fantasy 83% of the time, Kaelen 90%. David's and Julian's are contemporary 80%, Sarah's 90%.
- **Stories forced to open on a name follow the same split.** Elara's are fantasy 85% of the time, Kael's and Vorrak's 70%. Thomas's are contemporary 65%.
- **Thorne makes a mercenary.** Asked for a character called Thorne, the model writes a cynical, disgraced fixer or relic-hunter.
- **Invented names get their own texture.** Lumie becomes a small, bioluminescent guardian; Vorrak a spindly, many-limbed scavenger in a nebula.

### Clara follows the name, not the story

One test separates the story from the name. I took 20 of Elias's stories, cut each one at the moment he first appears, and let the model carry on with a different name.

| Continued as | Lighthouse or sea | Clocks or workshop | Clara appears |
| --- | --- | --- | --- |
| Elias (same cut, re-run) | 45% | 30% | 35% |
| David | 40% | 30% | 10% |
| Thomas | 30% | 35% | 0% |
| Vorrak | 25% | 20% | 5% |

The lighthouse and the clocks stay, because the story has already set them up. Clara mostly doesn't. She is attached to the name Elias, not to anything in the story. With 20 stories per row this is a strong hint rather than proof, but it's the clearest sign that the model stores these characters as pairs.

## Inside the model

The stories show *what* the model does. The weights let us look at *how*. Three experiments here go below the text: reading the model's odds for every possible name, watching the name form layer by layer, and trying to cut Elias out.

### Name roulette: hundreds of names collapse to one

I stopped the model at the moment a name was due ("...there lived an old keeper named \_\_\_") and read its probability for every name in its vocabulary. I turned that into an *effective number of names*: 1 means it always picks the same one, 500 means a wide-open choice.

![The base model weighs hundreds of names; the chat model about one](name-roulette.png)

*Source: [`results/gemma-4-26b-a4b/roulette.md`](../results/gemma-4-26b-a4b/roulette.md). llama.cpp Q8_0, Gemma 4 26B-A4B base and chat models, top 2,000 next words. Elara shows as its first piece "El", which the model completes as "ara".*

The base model, before any chat training, spreads its bets across ordinary names that fit the scene: Thomas for the keeper, Victor for the villain, Mary for "a woman". The chat model makes the same choice from about one. Only the youngest son (Leo) and the accountant (Arthur) escape Elias and Elara.

Three checks back this up:

- **It isn't quantisation.** The llama.cpp copy (8-bit) and the full-precision PyTorch weights give the same numbers: 303 vs 309 for the base model at the lighthouse, and 1.0 vs 1.0 for the chat model.
- **It isn't the chat format.** Given plain text with no chat wrapper, the chat model still calls the keeper Elias 100% of the time and "a woman" Clara 79%.
- **The seed was already there.** For the village weaver, even the base model's favourite is "El-" (31%), which it finishes as "-ara" 96% of the time. Chat training didn't invent Elara; it turned a habit into a reflex. That fits Hamilton and Mimno's finding that the pattern comes from preference tuning.

### The logit lens: when does the name appear?

A transformer passes a running state up through its layers; Gemma 4 has 30. The [logit lens](https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens) decodes that state at every layer as if it were the last, which shows what the model is "thinking of" partway up.

For the lighthouse keeper:

- **Layers 0–22: no names at all.** Elias's probability is 0.00% at the middle layer. The top guesses are mostly Korean and Vietnamese grammar pieces: the Korean particles `로` and `서`, and Vietnamese `gọi`, "to be called". This fits the finding that multilingual models work in a language-neutral concept space in their middle layers ([Wendler et al., 2024](https://arxiv.org/abs/2402.10588)).
- **Layers 23–24: the scene.** The top guesses become "lighthouse" and ⚓. For the family prompt they are "youngest" and 👦.
- **Layers 25–28: the name.** Elias becomes the top guess at layer 26, with Silas and Callum behind him. Names like Elara arrive later, at layer 28.
- **Layer 30: the collapse.** At layer 29 Elias is still at 2.8%. The final layer takes him to 99.3%.

So the model works out what kind of person fits the scene first, and only names him in the last few layers. Almost always, that name is Elias.

### Steering: trying to exorcise Elias

The obvious next step was to remove him. I found an "Elias direction": the average difference in the model's internal state, at layer 15, between reading "Elias" and reading 20 other men's names in the same sentences. Then I subtracted it while the model wrote.

It didn't work, and how it failed is instructive.

| Scene | P(Elias) normally | With the direction removed (strength 2) |
| --- | --- | --- |
| Lighthouse keeper | 99.3% | 98.7% |
| Clockmaker | 100% | 99.9% |
| Starship captain (a woman) | 7.5% | 61.6% |
| "A woman named" | 2.3% | 44.7% |
| Accountant | 13.6% | 2.3% |

Where Elias is the default, he barely moved. In the women's scenes he went *up*, taking ground from Elara. My best guess is that the direction mostly captured the "El-" sound the two names share. Removing it weakened "El", Elara's first piece, more than Elias, who is a single token.

The lens explains the rest. I measured the direction in the middle of the network, on the word "Elias" after it had been read. But the choice is made ten layers later, at the moment *before* the name is written. Steering in the wrong place moved the wrong thing.

One steered story did change: it opened at "Elias's desk", and four paragraphs later its hero had become "Mr. Henderson". That is one story out of two, so treat it as a curiosity.

## What this does and doesn't show

These are **Gemma's** ghosts. The names other people complain about mostly come from other models: in 1,000 Gemma stories Lyra appears three times, and Soren and Voss never appear. Every model family seems to have its own cast. The method should carry over, but the people may not.

Other limits worth knowing:

- **Gemma wrote and then read its own stories.** The same model extracted each character's traits, so its own habits may colour the descriptions. The counts (names, roles, settings) are on firmer ground than the adjectives.
- **Some tests are small.** The name-swap and genre tests use 20 and 6 stories per cell, so read them as strong hints.
- **Traits are compared as exact words.** "Quiet" and "reserved" count as different, so the genre scores are best read against each other and against the David and Sarah controls.

## So who are the ghosts?

They are less a cast of characters than a set of defaults. There is one default person: quiet, observant, mending something old, haunted by a loss. There are a few default worlds: Oakhaven, Blackwood Manor, the *Rust-Bucket*, the Miller kitchen. And there is one default name for each slot, picked in the last few layers of the network after everything else is decided.

The base model knew a thousand names for an old lighthouse keeper. Chat training taught it that the right answer is Elias.

**Next:** the same tests on a second model family, and steering aimed where the lens says the decision is made: the moment before the name, around layer 26.

*The code that produced every number here is in this repository, and the full outputs are in [`results/`](../results/).*
