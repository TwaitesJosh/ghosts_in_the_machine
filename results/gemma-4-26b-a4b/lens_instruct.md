# Logit lens: watching the name appear

Each story is stopped at the moment a name is due. Every layer's hidden state is decoded as if it were the model's last layer. Layer 0 is the raw input embedding; the last layer is the model's real answer. **Becomes #1** = first layer where the eventual winner is the single most likely next token; **top 10** = first layer it enters the top 10 (ties count against it: early layers often push many tokens to the output cap at once). Read early-layer probabilities with care: this simple readout isn't calibrated before the last layer, so the order of names matters more than their exact percentages.

**Effective names** = how many equally likely names the final choice is worth (2^entropy over the name-like words in the top 2000): 1 = always the same name. This is the same measure as `ghosts.py roulette`, so the two can be compared directly.

| Setting | Final pick | Effective names | Becomes top 10 | Becomes #1 | P at middle layer | P at end |
|---|---|---|---|---|---|---|
| lighthouse | Elias 99%, Silas 1%, El 0% | 1.0 | 25 | 26 | 0.00% | 99.3% |
| clockmaker | Elias 100%, Silas 0%, El 0% | 1.0 | 23 | 25 | 0.00% | 100.0% |
| starship | El 91%, Elias 8%, Elena 0% | 1.4 | 28 | 28 | 0.00% | 91.5% |
| weaver | El 98%, Elias 2%, Silas 0% | 1.1 | 27 | 28 | 0.00% | 98.1% |
| manor | Elias 91%, Silas 8%, Al 1% | 1.4 | 25 | 26 | 0.00% | 90.4% |
| family | Leo 74%, Elias 24%, El 2% | 2.0 | 26 | 28 | 0.00% | 73.4% |
| villain | Elias 92%, Silas 5%, Arthur 3% | 1.4 | 25 | 27 | 0.00% | 90.9% |
| hero-woman | El 100%, Elias 0%, Clara 0% | 1.0 | 28 | 28 | 0.00% | 99.7% |
| hero-man | Elias 98%, El 1%, Silas 0% | 1.1 | 25 | 26 | 0.00% | 98.2% |
| a-man | Elias 100%, Silas 0%, El 0% | 1.0 | 25 | 26 | 0.00% | 99.6% |
| a-woman | El 97%, Elias 2%, Clara 1% | 1.2 | 28 | 28 | 0.00% | 96.7% |
| office | Arthur 58%, Elias 35%, Perc 2% | 2.9 | 27 | never | 0.00% | 24.0% |

## Layer by layer: lighthouse
*"Once upon a time, in a lighthouse at the edge of the sea, there lived an old keeper named ___"*

| Layer | Top guesses at this layer | P(Elias) | P(Elara) | P(Thomas) |
|---|---|---|---|---|
| 0 | `the`, `�`, `al`, `om` | 0.00% | 0.00% | 0.00% |
| 1 | `<|tool>`, `<eos>`, `'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'`, `<sup>` | 0.00% | 0.00% | 0.00% |
| 2 | `<td>`, `<caption>`, `<i>`, `�` | 0.00% | 0.00% | 0.00% |
| 3 | `<unused0>`, `<bos>`, `<unused1>`, `<unused38>` | 0.00% | 0.00% | 0.00% |
| 4 | `<unused0>`, `<bos>`, `<unused38>`, `<|"|>` | 0.00% | 0.00% | 0.00% |
| 5 | `<|"|>`, `<tool|>`, `<|channel>`, `<code>` | 0.00% | 0.00% | 0.00% |
| 6 | `f`, `<body>`, `ir`, `ade` | 0.00% | 0.00% | 0.00% |
| 7 | `me`, `pl`, `atures`, `prop` | 0.00% | 0.00% | 0.00% |
| 8 | `데`, `lặng`, `동시에`, `まま` | 0.00% | 0.00% | 0.00% |
| 9 | `데`, `lặng`, `동시에`, `gọi` | 0.00% | 0.00% | 0.00% |
| 10 | `데`, `동시에`, `gọi`, `lặng` | 0.00% | 0.00% | 0.00% |
| 11 | `데`, `own`, `gọi`, `동시에` | 0.00% | 0.00% | 0.00% |
| 12 | `데`, `own`, `gọi`, `동시에` | 0.00% | 0.00% | 0.00% |
| 13 | `데`, `own`, `gọi`, `唯一` | 0.00% | 0.00% | 0.00% |
| 14 | `데`, `own`, `gọi`, `lặng` | 0.00% | 0.00% | 0.00% |
| 15 | `데`, `gọi`, `唯一`, `既` | 0.00% | 0.00% | 0.00% |
| 16 | `own`, `로`, `서`, `야` | 0.00% | 0.00% | 0.00% |
| 17 | `로`, `서`, `야`, `데` | 0.00% | 0.00% | 0.00% |
| 18 | `로`, `서`, `으로`, `야` | 0.00% | 0.00% | 0.00% |
| 19 | `로`, `서`, `으로`, `own` | 0.00% | 0.00% | 0.00% |
| 20 | `로`, `서`, `own`, `𒇏` | 0.00% | 0.00% | 0.00% |
| 21 | `로`, `서`, `own`, `야` | 0.00% | 0.00% | 0.00% |
| 22 | `로`, `서`, `own`, `야` | 0.00% | 0.00% | 0.00% |
| 23 | `own`, `로`, `마다`, `⚓` | 1.00% | 0.00% | 0.00% |
| 24 | `lighthouse`, `로`, `마다`, `⚓` | 0.56% | 0.00% | 0.00% |
| 25 | `lighthouse`, `마다`, `Elias`, `서` | 1.64% | 0.00% | 0.00% |
| 26 | `Elias`, `Silas`, `Callum`, `lighthouse` | 3.26% | 0.01% | 0.02% |
| 27 | `Elias`, `Silas`, `Callum`, `old` | 11.85% | 0.02% | 0.04% |
| 28 | `Elias`, `Silas`, `El`, `way` | 6.70% | 3.80% | 1.26% |
| 29 | `Elias`, `Silas`, `E`, `Barn` | 2.80% | 1.36% | 0.57% |
| 30 | `Elias`, `Silas`, `El`, `Arthur` | 99.29% | 0.11% | 0.00% |

## Layer by layer: family
*"The kitchen was chaos as usual, and in the middle of it all stood the youngest son, a boy named ___"*

| Layer | Top guesses at this layer | P(Elias) | P(Elara) | P(Thomas) |
|---|---|---|---|---|
| 0 | `the`, `�`, `al`, `om` | 0.00% | 0.00% | 0.00% |
| 1 | `<|tool>`, `<eos>`, `<unused83>`, `'               '` | 0.00% | 0.00% | 0.00% |
| 2 | `<caption>`, `<unused36>`, `<tr>`, `<s>` | 0.00% | 0.00% | 0.00% |
| 3 | `<unused0>`, `<bos>`, `<unused1>`, `<tool|>` | 0.00% | 0.00% | 0.00% |
| 4 | `<unused0>`, `<bos>`, `<tool|>`, `<|think|>` | 0.00% | 0.00% | 0.00% |
| 5 | `<|"|>`, `<tool|>`, `<|think|>`, `<i>` | 0.00% | 0.00% | 0.00% |
| 6 | `ro`, `<body>`, `ir`, `out` | 0.00% | 0.00% | 0.00% |
| 7 | `me`, `ir`, `ational`, `iversity` | 0.00% | 0.00% | 0.00% |
| 8 | `まま`, `gọi`, `동시에`, `데` | 0.00% | 0.00% | 0.00% |
| 9 | `데`, `lặng`, `まま`, `gọi` | 0.00% | 0.00% | 0.00% |
| 10 | `데`, `gọi`, `lặng`, `나` | 0.00% | 0.00% | 0.00% |
| 11 | `데`, `gọi`, `나`, `lặng` | 0.00% | 0.00% | 0.00% |
| 12 | `데`, `gọi`, `동시에`, `나` | 0.00% | 0.00% | 0.00% |
| 13 | `데`, `gọi`, `나`, `동시에` | 0.00% | 0.00% | 0.00% |
| 14 | `데`, `gọi`, `나`, `chuyện` | 0.00% | 0.00% | 0.00% |
| 15 | `데`, `gọi`, `나`, `ある` | 0.00% | 0.00% | 0.00% |
| 16 | `own`, `서`, `로`, `야` | 0.00% | 0.00% | 0.00% |
| 17 | `로`, `서`, `야`, `quilted` | 0.00% | 0.00% | 0.00% |
| 18 | `로`, `서`, `으로`, `𒇏` | 0.00% | 0.00% | 0.00% |
| 19 | `로`, `서`, `𒑟`, `𒆾` | 0.00% | 0.00% | 0.00% |
| 20 | `로`, `서`, `𒑟`, `𒇏` | 0.00% | 0.00% | 0.00% |
| 21 | `로`, `서`, `own`, `𒇏` | 0.00% | 0.00% | 0.00% |
| 22 | `로`, `서`, `own`, `𒇏` | 0.00% | 0.00% | 0.00% |
| 23 | `로`, `서`, `으로`, `youngest` | 0.02% | 0.00% | 0.00% |
| 24 | `로`, `서`, `으로`, `👦` | 0.00% | 0.00% | 0.00% |
| 25 | `서`, `Callum`, `Leo`, `Luca` | 0.04% | 0.00% | 0.00% |
| 26 | `Leo`, `Leo`, `서`, `Elias` | 0.78% | 0.00% | 0.00% |
| 27 | `Leo`, `Leo`, `Elias`, `서` | 3.64% | 0.00% | 0.00% |
| 28 | `Leo`, `Leo`, `Elias`, `Toby` | 3.30% | 0.92% | 0.08% |
| 29 | `Leo`, `Leo`, `Elias`, `Milo` | 1.81% | 0.69% | 0.11% |
| 30 | `Leo`, `Elias`, `El`, `Silas` | 24.53% | 1.45% | 0.00% |

## Layer by layer: office
*"On Monday morning the firm hired a new accountant, a man named ___"*

| Layer | Top guesses at this layer | P(Elias) | P(Elara) | P(Thomas) |
|---|---|---|---|---|
| 0 | `the`, `�`, `al`, `om` | 0.00% | 0.00% | 0.00% |
| 1 | `<|tool>`, `<eos>`, `<tool|>`, `<caption>` | 0.00% | 0.00% | 0.00% |
| 2 | `<unused28>`, `<bos>`, `<a>`, `�` | 0.00% | 0.00% | 0.00% |
| 3 | `<unused0>`, `<bos>`, `<unused1>`, `<tool|>` | 0.00% | 0.00% | 0.00% |
| 4 | `<tool|>`, `<unused0>`, `<|"|>`, `<|channel>` | 0.00% | 0.00% | 0.00% |
| 5 | `<|channel>`, `<|"|>`, `<i>`, `` | 0.00% | 0.00% | 0.00% |
| 6 | `ir`, `�`, `ch`, `me` | 0.00% | 0.00% | 0.00% |
| 7 | `ational`, `me`, `ار`, `vo` | 0.00% | 0.00% | 0.00% |
| 8 | `데`, `동시에`, `lặng`, `まま` | 0.00% | 0.00% | 0.00% |
| 9 | `데`, `lặng`, `まま`, `랑` | 0.00% | 0.00% | 0.00% |
| 10 | `데`, `나`, `gọi`, `대로` | 0.00% | 0.00% | 0.00% |
| 11 | `데`, `own`, `gọi`, `대로` | 0.00% | 0.00% | 0.00% |
| 12 | `데`, `own`, `gọi`, `い` | 0.00% | 0.00% | 0.00% |
| 13 | `데`, `own`, `gọi`, `lặng` | 0.00% | 0.00% | 0.00% |
| 14 | `데`, `gọi`, `own`, `ある` | 0.00% | 0.00% | 0.00% |
| 15 | `데`, `gọi`, `ある`, `い` | 0.00% | 0.00% | 0.00% |
| 16 | `own`, `로`, `서`, `으로` | 0.00% | 0.00% | 0.00% |
| 17 | `로`, `서`, `own`, `way` | 0.00% | 0.00% | 0.00% |
| 18 | `로`, `서`, `으로`, `커피` | 0.00% | 0.00% | 0.00% |
| 19 | `로`, `𒇾`, `𒃩`, `𒃄` | 0.00% | 0.00% | 0.00% |
| 20 | `로`, `서`, `𒃄`, `𒇾` | 0.00% | 0.00% | 0.00% |
| 21 | `서`, `로`, `𒃄`, `𒇾` | 0.00% | 0.00% | 0.00% |
| 22 | `로`, `서`, `own`, `𒃄` | 0.00% | 0.00% | 0.00% |
| 23 | `own`, `ketogenic`, `formaldehyde`, `chamomile` | 0.00% | 0.00% | 0.00% |
| 24 | `own`, `𒊤`, `𒁌`, `𒈟` | 0.00% | 0.00% | 0.00% |
| 25 | `Mr`, `own`, `서`, `Mr` | 0.01% | 0.00% | 0.00% |
| 26 | `Mr`, `own`, `Mr`, `서` | 0.08% | 0.00% | 0.00% |
| 27 | `Mr`, `Mr`, `Arthur`, `ARTHUR` | 0.47% | 0.00% | 0.00% |
| 28 | `Mr`, `Mr`, `Arthur`, `mr` | 2.61% | 0.00% | 0.72% |
| 29 | `Mr`, `Arthur`, `Mr`, `Arthur` | 0.27% | 0.00% | 0.07% |
| 30 | `Mr`, `Arthur`, `Elias`, `Silas` | 13.79% | 0.04% | 0.04% |

## How the tokenizer splits the names

A name in several pieces is chosen one piece at a time: at the naming moment the lens sees its FIRST piece, so a longer name can hide inside a shorter one.

| Name | Pieces |
|---|---|
| Elias | ` Elias` |
| Elara | ` El` + `ara` |
| Clara | ` Clara` |
| Kael | ` K` + `ael` |
| Kaelen | ` K` + `ael` + `en` |
| Julian | ` Julian` |
| Leo | ` Leo` |
| Silas | ` Silas` |
| Thorne | ` Thorne` |
| Mara | ` Mara` |
| Lyra | ` Ly` + `ra` |
| Seraphina | ` Ser` + `aph` + `ina` |
| Thomas | ` Thomas` |
| John | ` John` |
| David | ` David` |
| Sarah | ` Sarah` |
| Emily | ` Emily` |
| Voss | ` Voss` |
| Vance | ` Vance` |

## What comes right after the name

Most likely next tokens after each top-5 name, per setting. A word-ending piece (`en`) means the name is longer than it looks; a surname means the two travel together.

- *lighthouse:* **Elias** → `.` 100%, ` who` 0%, ` and` 0% · **Silas** → `.` 100%, ` who` 0%, ` and` 0% · **El** → `ara` 79%, `ian` 21%, `ías` 0% · **Arthur** → `.` 100%, ` who` 0%, ` and` 0% · **Barn** → `aby` 100%, `abas` 0%, `abus` 0%
- *clockmaker:* **Elias** → `.` 100%, `,` 0%, ` who` 0% · **Silas** → `.` 100%, ` who` 0%, `,` 0% · **El** → `ian` 91%, `ara` 9%, `ías` 0% · **Th** → `adde` 99%, `istle` 1%, `eron` 0% · **Ar** → `is` 100%, `lo` 0%, `low` 0%
- *starship:* **El** → `ara` 100%, `ora` 0%, `ia` 0% · **Elias** → `,` 77%, ` who` 15%, ` whose` 6% · **Elena** → `,` 83%, ` who` 10%, ` whose` 5% · **Ly** → `ra` 100%, `re` 0%, `ara` 0% · **Ar** → `is` 100%, `ra` 0%, `isa` 0%
- *weaver:* **El** → `ara` 100%, `in` 0%, `ora` 0% · **Elias** → `.` 100%, ` who` 0%, ` named` 0% · **Silas** → `.` 100%, ` who` 0%, ` closely` 0% · **Leo** → `.` 100%, ` who` 0%, ` else` 0% · **Clara** → `.` 100%, ` much` 0%, ` who` 0%
- *manor:* **Elias** → ` Thorne` 98%, `,` 1%, ` Vance` 1% · **Silas** → ` Thorne` 79%, ` V` 16%, ` who` 2% · **Al** → `ist` 100%, `aric` 0%, `ast` 0% · **Arthur** → ` Pen` 35%, ` Vance` 24%, ` P` 21% · **Julian** → ` Thorne` 66%, ` V` 28%, `,` 2%
- *family:* **Leo** → ` who` 88%, `,` 6%, ` with` 5% · **Elias** → ` who` 76%, `,` 13%, ` with` 8% · **El** → `ian` 100%, `ara` 0%, `io` 0% · **Silas** → ` who` 78%, ` with` 11%, `,` 7% · **Arthur** → ` who` 91%, `,` 5%, ` with` 4%
- *villain:* **Elias** → ` Thorne` 100%, ` Vance` 0%, ` than` 0% · **Silas** → ` V` 77%, ` Thorne` 22%, `,` 1% · **Arthur** → ` Vance` 91%, `,` 4%, ` Pen` 2% · **Al** → `ist` 100%, `aric` 0%, `ast` 0% · **Julian** → ` V` 81%, ` Thorne` 18%, `,` 1%
- *hero-woman:* **El** → `ara` 100%, `ora` 0%, `iana` 0% · **Elias** → `,` 99%, ` who` 1%, `.` 0% · **Clara** → `,` 100%, ` who` 0%, `.` 0% · **Elena** → `,` 100%, ` who` 0%, `.` 0% · **Ly** → `ra` 100%, `ria` 0%, `re` 0%
- *hero-man:* **Elias** → `,` 100%, ` who` 0%, `.` 0% · **El** → `ian` 100%, `ara` 0%, `io` 0% · **Silas** → `,` 100%, ` who` 0%, `.` 0% · **Leo** → `,` 100%, ` who` 0%, `.` 0% · **Arthur** → `,` 100%, ` who` 0%, `.` 0%
- *a-man:* **Elias** → ` and` 62%, `,` 33%, ` who` 5% · **Silas** → ` and` 78%, `,` 20%, ` who` 3% · **El** → `ian` 100%, `ara` 0%, `ías` 0% · **Arthur** → `,` 90%, ` who` 5%, ` and` 5% · **Elijah** → ` and` 69%, `,` 29%, ` who` 2%
- *a-woman:* **El** → `ara` 100%, `ora` 0%, `ARA` 0% · **Elias** → ` and` 83%, `,` 14%, ` who` 3% · **Clara** → ` and` 53%, `,` 36%, ` who` 10% · **Elena** → ` and` 65%, `,` 31%, ` who` 4% · **Evelyn** → ` and` 93%, ` who` 5%, `,` 2%
- *office:* **Arthur** → ` who` 47%, ` P` 47%, `.` 3% · **Elias** → `,` 42%, ` who` 29%, ` Thorne` 15% · **Perc** → `ival` 100%, `iv` 0%, `imal` 0% · **Silas** → ` who` 75%, `.` 21%, ` V` 2% · **Barn** → `aby` 100%, `abas` 0%, `abus` 0%
