# Name roulette

Each story is stopped at the moment a name is due, and the model's probability for every possible next word is read directly. Only capitalised name-like words are counted (titles such as Mr, Dr and Captain are left out); percentages are shares of that name probability. A name in several tokens shows up as its first piece (e.g. `El` for Elara, Eleanor, Elena): see the last section for what follows.

**Effective names** = how many equally likely names the choice is worth (2^entropy). 1 = it always picks the same name; 50 = a genuinely open choice. Computed over the top 2000 next words, so it slightly understates the spread.

## Summary: effective number of names

| Setting | base | instruct-raw | base-bf16 | instruct-bf16-raw | instruct | instruct-bf16 |
|---|---|---|---|---|---|---|
| lighthouse | 302.8 (Thomas 7%) | 1.0 (Elias 100%) | 309.4 (Thomas 7%) | 26.9 (Daniel 15%) | 1.0 (Elias 99%) | 1.0 (Elias 99%) |
| clockmaker | 851.7 (John 2%) | 100.2 (Stein 10%) | 849.7 (John 2%) | 7.9 (Cl 55%) | 1.0 (Elias 100%) | 1.0 (Elias 100%) |
| starship | 626.5 (Sarah 4%) | 3.2 (Elena 73%) | 609.3 (Sarah 4%) | 5.6 (Alice 68%) | 1.4 (El 92%) | 1.4 (El 91%) |
| weaver | 79.6 (El 31%) | 7.2 (Port 31%) | 86.2 (El 29%) | 29.8 (Alice 17%) | 1.1 (El 98%) | 1.1 (El 98%) |
| manor | 118.2 (Edward 7%) | 41.1 (Nik 34%) | 112.3 (Edward 7%) | 34.8 (Carter 12%) | 1.4 (Elias 91%) | 1.4 (Elias 91%) |
| family | 847.6 (Jack 1%) | 50.1 (Adam 16%) | 837.4 (Jack 1%) | 36.7 (Arthur 31%) | 2.0 (Leo 73%) | 2.0 (Leo 74%) |
| villain | 256.3 (Victor 15%) | 30.4 (Coleman 32%) | 210.6 (Victor 16%) | 78.7 (John 11%) | 1.5 (Elias 91%) | 1.4 (Elias 92%) |
| hero-woman | 791.3 (Anna 2%) | 2.4 (El 58%) | 795.3 (Mary 2%) | 24.7 (Isabella 14%) | 1.0 (El 100%) | 1.0 (El 100%) |
| hero-man | 642.4 (Jack 3%) | 4.0 (Elias 76%) | 646.3 (John 3%) | 26.2 (Ar 22%) | 1.1 (Elias 98%) | 1.1 (Elias 98%) |
| a-man | 565.0 (Joe 4%) | 147.4 (Friedrich 12%) | 558.3 (John 4%) | 23.7 (Cl 16%) | 1.0 (Elias 100%) | 1.0 (Elias 100%) |
| a-woman | 869.7 (Mary 2%) | 4.0 (Clara 79%) | 866.6 (Mary 2%) | 82.4 (Marie 9%) | 1.2 (El 97%) | 1.2 (El 97%) |
| office | 673.5 (John 3%) | 96.2 (Luis 10%) | 699.0 (John 3%) | 87.4 (John 9%) | 2.2 (Arthur 69%) | 2.9 (Arthur 58%) |

## lighthouse
*"Once upon a time, in a lighthouse at the edge of the sea, there lived an old keeper named ___"*

- **base** (~302.8 effective names, names take 84% of next-word probability): Thomas 7%, Henry 5%, Tom 4%, John 3%, Jack 3%, Ben 2%, Sam 2%, George 2%, Samuel 1%, William 1%
- **instruct-raw** (~1.0 effective names, names take 89% of next-word probability): Elias 100%, El 0%, Eld 0%, Silas 0%, Eli 0%, Al 0%, Th 0%, Friedrich 0%, Keeper 0%, Thal 0%
- **base-bf16** (~309.4 effective names, names take 83% of next-word probability): Thomas 7%, Henry 5%, John 4%, Tom 4%, Jack 3%, Ben 2%, Sam 1%, William 1%, Samuel 1%, George 1%
- **instruct-bf16-raw** (~26.9 effective names, names take 0% of next-word probability): Daniel 15%, Henry 14%, Ar 12%, Duy 8%, Christian 7%, English 4%, Alex 3%, Taylor 3%, West 2%, Thomas 2%
- **instruct** (~1.0 effective names, names take 100% of next-word probability): Elias 99%, Silas 1%, El 0%, Arthur 0%, Barn 0%, Th 0%, Al 0%, Amos 0%, Ar 0%, Bram 0%
- **instruct-bf16** (~1.0 effective names, names take 100% of next-word probability): Elias 99%, Silas 1%, El 0%, Arthur 0%, Barn 0%, Al 0%, Th 0%, Amos 0%, Elijah 0%, Ar 0%

## clockmaker
*"In a cluttered workshop at the end of a narrow street worked an old clockmaker named ___"*

- **base** (~851.7 effective names, names take 68% of next-word probability): John 2%, Peter 2%, Jacob 2%, George 1%, Joseph 1%, Thomas 1%, William 1%, Martin 1%, Simon 1%, Jean 1%
- **instruct-raw** (~100.2 effective names, names take 0% of next-word probability): Stein 10%, Friedrich 7%, Volk 6%, Klaus 5%, Yamada 4%, Vec 4%, Dan 2%, Smith 2%, Fritz 2%, Fuj 2%
- **base-bf16** (~849.7 effective names, names take 69% of next-word probability): John 2%, Peter 2%, Jacob 2%, George 1%, Joseph 1%, William 1%, Simon 1%, Thomas 1%, Martin 1%, Jean 1%
- **instruct-bf16-raw** (~7.9 effective names, names take 0% of next-word probability): Cl 55%, Ar 6%, English 4%, August 4%, These 3%, Charles 2%, Ed 2%, Ol 2%, Col 2%, El 2%
- **instruct** (~1.0 effective names, names take 100% of next-word probability): Elias 100%, Silas 0%, El 0%, Th 0%, Ar 0%, Al 0%, Elijah 0%, Ezra 0%, Bram 0%, Arthur 0%
- **instruct-bf16** (~1.0 effective names, names take 100% of next-word probability): Elias 100%, Silas 0%, El 0%, Th 0%, Ar 0%, Al 0%, Ezra 0%, Elijah 0%, Bram 0%, Arthur 0%

## starship
*"The starship drifted through the dark. At the helm sat its captain, a woman named ___"*

- **base** (~626.5 effective names, names take 77% of next-word probability): Sarah 4%, El 2%, Jane 1%, Anya 1%, Ser 1%, Mira 1%, Al 1%, Zara 1%, Amelia 1%, Elena 1%
- **instruct-raw** (~3.2 effective names, names take 1% of next-word probability): Elena 73%, Clara 14%, El 5%, Alexa 1%, Al 1%, Le 0%, Greta 0%, Anya 0%, Cora 0%, Emil 0%
- **base-bf16** (~609.3 effective names, names take 77% of next-word probability): Sarah 4%, El 2%, Ser 1%, Anya 1%, Mira 1%, Al 1%, Jane 1%, Zara 1%, Amelia 1%, Elena 1%
- **instruct-bf16-raw** (~5.6 effective names, names take 0% of next-word probability): Alice 68%, Chloe 6%, Ar 5%, Clara 3%, Or 3%, Cl 1%, Atlas 1%, Al 1%, Kleid 1%, Marie 1%
- **instruct** (~1.4 effective names, names take 100% of next-word probability): El 92%, Elias 7%, Elena 0%, Ly 0%, Ar 0%, Clara 0%, Silas 0%, Mara 0%, Al 0%, Mira 0%
- **instruct-bf16** (~1.4 effective names, names take 100% of next-word probability): El 91%, Elias 8%, Elena 0%, Ly 0%, Ar 0%, Clara 0%, Mara 0%, Silas 0%, Al 0%, Mira 0%

## weaver
*"In a small village at the edge of an enchanted forest lived a young weaver named ___"*

- **base** (~79.6 effective names, names take 91% of next-word probability): El 31%, Lila 7%, Lily 4%, Elias 2%, Ly 2%, Eli 1%, Clara 1%, Elena 1%, Lena 1%, Ella 1%
- **instruct-raw** (~7.2 effective names, names take 0% of next-word probability): Port 31%, We 29%, Friedrich 12%, English 11%, Weaver 4%, Im 3%, Files 3%, Sq 1%, Da 1%, Summary 1%
- **base-bf16** (~86.2 effective names, names take 91% of next-word probability): El 29%, Lila 7%, Lily 4%, Elias 2%, Ly 2%, Eli 1%, Clara 1%, Lena 1%, Elena 1%, Emma 1%
- **instruct-bf16-raw** (~29.8 effective names, names take 0% of next-word probability): Alice 17%, Sofia 15%, Taylor 9%, Polly 7%, Laura 6%, Alex 3%, Lily 3%, John 3%, Sarah 3%, Gemma 3%
- **instruct** (~1.1 effective names, names take 100% of next-word probability): El 98%, Elias 2%, Silas 0%, Leo 0%, Clara 0%, Elena 0%, Ly 0%, Eli 0%, Ar 0%, Elise 0%
- **instruct-bf16** (~1.1 effective names, names take 100% of next-word probability): El 98%, Elias 2%, Silas 0%, Leo 0%, Clara 0%, Elena 0%, Eli 0%, Ly 0%, Ar 0%, Elise 0%

## manor
*"The old manor had stood empty since the death of its owner, a reclusive man named ___"*

- **base** (~118.2 effective names, names take 67% of next-word probability): Edward 7%, Henry 5%, Samuel 4%, Elias 4%, Thomas 3%, Jonathan 3%, Archibald 3%, William 3%, Reginald 2%, Charles 2%
- **instruct-raw** (~41.1 effective names, names take 0% of next-word probability): Nik 34%, Nut 6%, David 4%, Walter 3%, Gerald 3%, Alexander 2%, Friedrich 2%, Peter 2%, Ivan 2%, Adam 2%
- **base-bf16** (~112.3 effective names, names take 67% of next-word probability): Edward 7%, Henry 5%, Samuel 4%, Jonathan 4%, Elias 4%, Thomas 3%, John 3%, William 3%, Charles 3%, Archibald 3%
- **instruct-bf16-raw** (~34.8 effective names, names take 0% of next-word probability): Carter 12%, Tu 9%, Robert 6%, Ar 5%, Hilbert 4%, December 4%, February 3%, Il 3%, Romeo 3%, America 3%
- **instruct** (~1.4 effective names, names take 100% of next-word probability): Elias 91%, Silas 8%, Al 1%, Arthur 0%, Julian 0%, El 0%, Th 0%, Evelyn 0%, Barn 0%, Elijah 0%
- **instruct-bf16** (~1.4 effective names, names take 100% of next-word probability): Elias 91%, Silas 8%, Al 1%, Arthur 0%, Julian 0%, El 0%, Th 0%, Evelyn 0%, Elijah 0%, Perc 0%

## family
*"The kitchen was chaos as usual, and in the middle of it all stood the youngest son, a boy named ___"*

- **base** (~847.6 effective names, names take 76% of next-word probability): Jack 1%, Harry 1%, John 1%, Peter 1%, Sam 1%, Tom 1%, Alex 1%, Tommy 1%, James 1%, Ben 1%
- **instruct-raw** (~50.1 effective names, names take 9% of next-word probability): Adam 16%, Bor 12%, Gabriel 7%, Bo 6%, Friedrich 6%, Ald 5%, Timur 3%, John 3%, Flav 2%, Fug 2%
- **base-bf16** (~837.4 effective names, names take 76% of next-word probability): Jack 1%, Harry 1%, John 1%, Tom 1%, Peter 1%, Sam 1%, Alex 1%, Tommy 1%, Ben 1%, James 1%
- **instruct-bf16-raw** (~36.7 effective names, names take 0% of next-word probability): Arthur 31%, Boris 11%, Alice 7%, Daniel 3%, Christian 2%, Thomas 2%, Ar 2%, Ben 1%, Sofia 1%, Alex 1%
- **instruct** (~2.0 effective names, names take 100% of next-word probability): Leo 73%, Elias 25%, El 1%, Silas 0%, Arthur 0%, Oliver 0%, Eli 0%, Toby 0%, Milo 0%, Theo 0%
- **instruct-bf16** (~2.0 effective names, names take 100% of next-word probability): Leo 74%, Elias 24%, El 2%, Silas 0%, Arthur 0%, Eli 0%, Oliver 0%, Toby 0%, Milo 0%, Theo 0%

## villain
*"The villain of the story was a cold, calculating man named ___"*

- **base** (~256.3 effective names, names take 65% of next-word probability): Victor 15%, Viktor 4%, John 3%, Alexander 2%, Marcus 2%, Vladimir 2%, Richard 1%, James 1%, Ethan 1%, Charles 1%
- **instruct-raw** (~30.4 effective names, names take 11% of next-word probability): Coleman 32%, Kurt 7%, Diego 5%, Alan 4%, Gabriel 3%, Adam 3%, Alexander 3%, Luis 3%, Yamada 2%, Vincent 2%
- **base-bf16** (~210.6 effective names, names take 64% of next-word probability): Victor 16%, John 4%, Viktor 4%, Alexander 2%, Marcus 2%, James 2%, Vladimir 2%, Ethan 2%, Richard 1%, Charles 1%
- **instruct-bf16-raw** (~78.7 effective names, names take 4% of next-word probability): John 11%, Alex 5%, Joe 5%, Sam 4%, Steve 4%, Oscar 4%, Senator 3%, Gemma 3%, David 3%, Robert 3%
- **instruct** (~1.5 effective names, names take 100% of next-word probability): Elias 91%, Arthur 4%, Silas 4%, Al 0%, Julian 0%, Victor 0%, Mal 0%, Ar 0%, Eld 0%, El 0%
- **instruct-bf16** (~1.4 effective names, names take 100% of next-word probability): Elias 92%, Silas 5%, Arthur 3%, Al 0%, Julian 0%, Victor 0%, Mal 0%, Ar 0%, El 0%, Eld 0%

## hero-woman
*"The hero of our story is a young woman named ___"*

- **base** (~791.3 effective names, names take 81% of next-word probability): Anna 2%, Mary 2%, Sarah 1%, Alice 1%, Emma 1%, Maria 1%, Jane 1%, Emily 1%, Lily 1%, Elizabeth 1%
- **instruct-raw** (~2.4 effective names, names take 95% of next-word probability): El 58%, Elena 35%, Clara 7%, Al 0%, Elise 0%, Elisa 0%, Eld 0%, Evelyn 0%, Gemma 0%, Cora 0%
- **base-bf16** (~795.3 effective names, names take 81% of next-word probability): Mary 2%, Sarah 2%, Anna 2%, Alice 1%, Maria 1%, Jane 1%, Emily 1%, Emma 1%, Lily 1%, Elizabeth 1%
- **instruct-bf16-raw** (~24.7 effective names, names take 0% of next-word probability): Isabella 14%, Ar 10%, Alice 9%, English 4%, Sarah 4%, Patricia 4%, Sofia 4%, Maria 3%, America 3%, Paris 3%
- **instruct** (~1.0 effective names, names take 100% of next-word probability): El 100%, Elias 0%, Clara 0%, Elena 0%, Ly 0%, Maya 0%, Silas 0%, Evelyn 0%, Aria 0%, Mira 0%
- **instruct-bf16** (~1.0 effective names, names take 100% of next-word probability): El 100%, Elias 0%, Clara 0%, Elena 0%, Ly 0%, Maya 0%, Silas 0%, Evelyn 0%, Elise 0%, Mira 0%

## hero-man
*"The hero of our story is a young man named ___"*

- **base** (~642.4 effective names, names take 78% of next-word probability): Jack 3%, John 3%, Alex 3%, Peter 1%, David 1%, Ivan 1%, Max 1%, Sam 1%, Tom 1%, Michael 1%
- **instruct-raw** (~4.0 effective names, names take 2% of next-word probability): Elias 76%, Eld 7%, El 4%, Eli 2%, Kob 1%, Zel 1%, Kald 1%, Leop 0%, Kato 0%, Eck 0%
- **base-bf16** (~646.3 effective names, names take 78% of next-word probability): John 3%, Jack 3%, Alex 3%, Sam 1%, David 1%, Max 1%, Peter 1%, Ivan 1%, Tom 1%, Michael 1%
- **instruct-bf16-raw** (~26.2 effective names, names take 0% of next-word probability): Ar 22%, Gemma 8%, Christ 8%, English 5%, August 3%, Richie 3%, David 3%, Sofia 3%, Ari 3%, Marcus 2%
- **instruct** (~1.1 effective names, names take 100% of next-word probability): Elias 98%, El 1%, Silas 0%, Leo 0%, Arthur 0%, Eli 0%, Elijah 0%, Ar 0%, Oliver 0%, Milo 0%
- **instruct-bf16** (~1.1 effective names, names take 100% of next-word probability): Elias 98%, El 1%, Silas 0%, Leo 0%, Arthur 0%, Eli 0%, Elijah 0%, Oliver 0%, Ar 0%, Milo 0%

## a-man
*"This is the story of a man named ___"*

- **base** (~565.0 effective names, names take 78% of next-word probability): Joe 4%, John 3%, Jack 3%, Fred 2%, George 2%, Bob 1%, Michael 1%, Henry 1%, Sam 1%, Paul 1%
- **instruct-raw** (~147.4 effective names, names take 66% of next-word probability): Friedrich 12%, Gro 4%, Saul 3%, Elias 3%, John 3%, Claus 3%, Alexander 2%, Brook 2%, Klaus 2%, Frank 2%
- **base-bf16** (~558.3 effective names, names take 78% of next-word probability): John 4%, Joe 4%, Jack 3%, George 2%, Fred 2%, Bob 2%, Michael 1%, Henry 1%, Sam 1%, Paul 1%
- **instruct-bf16-raw** (~23.7 effective names, names take 0% of next-word probability): Cl 16%, Ar 15%, Alice 10%, Il 9%, Al 8%, Cr 5%, Alex 3%, Christ 2%, Arctic 2%, Charles 2%
- **instruct** (~1.0 effective names, names take 100% of next-word probability): Elias 100%, Silas 0%, El 0%, Arthur 0%, Elijah 0%, Eld 0%, Eli 0%, Barn 0%, Th 0%, Otis 0%
- **instruct-bf16** (~1.0 effective names, names take 100% of next-word probability): Elias 100%, Silas 0%, El 0%, Arthur 0%, Elijah 0%, Eld 0%, Eli 0%, Barn 0%, Th 0%, Otis 0%

## a-woman
*"This is the story of a woman named ___"*

- **base** (~869.7 effective names, names take 79% of next-word probability): Mary 2%, Sarah 1%, Maria 1%, Anna 1%, Elizabeth 1%, Jane 1%, Alice 1%, Grace 1%, Margaret 1%, Rose 1%
- **instruct-raw** (~4.0 effective names, names take 82% of next-word probability): Clara 79%, Gemma 3%, Jane 2%, Maria 1%, Greta 1%, Elena 1%, Luna 1%, Alexa 1%, Kate 0%, Ruth 0%
- **base-bf16** (~866.6 effective names, names take 78% of next-word probability): Mary 2%, Sarah 1%, Maria 1%, Anna 1%, Elizabeth 1%, Jane 1%, Alice 1%, Grace 1%, Rose 1%, Margaret 1%
- **instruct-bf16-raw** (~82.4 effective names, names take 9% of next-word probability): Marie 9%, Leslie 7%, Alice 6%, Isabella 5%, Al 4%, Sarah 4%, Beatrice 3%, Alex 3%, Chris 3%, Christina 3%
- **instruct** (~1.2 effective names, names take 100% of next-word probability): El 97%, Elias 2%, Clara 1%, Elena 0%, Evelyn 0%, Silas 0%, Eleanor 0%, Elise 0%, Elisa 0%, Eld 0%
- **instruct-bf16** (~1.2 effective names, names take 100% of next-word probability): El 97%, Elias 2%, Clara 1%, Elena 0%, Evelyn 0%, Silas 0%, Eleanor 0%, Elise 0%, Elisa 0%, Claire 0%

## office
*"On Monday morning the firm hired a new accountant, a man named ___"*

- **base** (~673.5 effective names, names take 73% of next-word probability): John 3%, George 1%, Robert 1%, Bob 1%, James 1%, Frank 1%, William 1%, Charles 1%, David 1%, Tom 1%
- **instruct-raw** (~96.2 effective names, names take 25% of next-word probability): Luis 10%, Cecil 9%, Anthony 7%, John 6%, Friedrich 4%, Diaz 2%, Joseph 2%, Kog 2%, Josef 2%, Gerald 2%
- **base-bf16** (~699.0 effective names, names take 72% of next-word probability): John 3%, George 1%, Robert 1%, Bob 1%, James 1%, William 1%, Frank 1%, David 1%, Tom 1%, Michael 1%
- **instruct-bf16-raw** (~87.4 effective names, names take 0% of next-word probability): John 9%, Christian 6%, Robert 5%, Hector 5%, Alice 4%, Marcus 4%, Him 3%, Taylor 3%, Arthur 2%, Eric 2%
- **instruct** (~2.2 effective names, names take 65% of next-word probability): Arthur 69%, Elias 28%, Silas 1%, Perc 1%, Barn 0%, Ar 0%, Miller 0%, Eust 0%, El 0%, Theodore 0%
- **instruct-bf16** (~2.9 effective names, names take 39% of next-word probability): Arthur 58%, Elias 35%, Perc 2%, Silas 2%, Barn 1%, Miller 0%, Ar 0%, Eust 0%, Thomas 0%, El 0%

## How the tokenizer splits the names

Names are written as the model sees them mid-sentence (with a leading space). A name in several pieces is chosen one piece at a time, so at the naming moment roulette really sees its FIRST piece: a name like Kaelen can hide inside "Kael". The next section shows what follows.

| Name | Pieces |
|---|---|
| Elias | ` Elias` |
| Elara | ` El` + `ara` |
| Kael | ` K` + `ael` |
| Kaelen | ` K` + `ael` + `en` |
| Clara | ` Clara` |
| Silas | ` Silas` |
| Julian | ` Julian` |
| Thorne | ` Thorne` |
| Mara | ` Mara` |
| Lyra | ` Ly` + `ra` |
| Seraphina | ` Ser` + `aph` + `ina` |
| Elena | ` Elena` |
| Leo | ` Leo` |
| Vance | ` Vance` |
| Voss | ` Voss` |
| David | ` David` |
| Thomas | ` Thomas` |

## What comes right after the name

For each run's most-picked names, the most likely next token after the name's first piece, averaged over the settings where it was a top-5 pick. A word-ending piece (`en`, `ara`) means the name is longer than it looks; a surname (` Thorne`) means it travels as a pair.

- **base:** **John** → `.` 30%, `,` 9%, ` who` 4% · **Jack** → `.` 51%, `,` 16%, ` who` 7% · **Peter** → `.` 33%, `,` 13%, ` Parker` 7% · **George** → `.` 13%, `,` 10%, ` who` 4% · **Sarah** → `.` 46%, `,` 19%, ` who` 10% · **Thomas** → `.` 35%, ` and` 4%, ` Black` 3% · **Henry** → `.` 36%, ` and` 5%, `,` 3% · **El** → `ara` 96%, `ian` 1%, `ora` 1%
- **instruct-raw:** **Friedrich** → `-` 89%, `el` 5%, `er` 3% · **El** → `ara` 88%, `ian` 12%, `ar` 0% · **Elias** → `.` 63%, `-` 24%, `,` 6% · **Clara** → `-` 75%, `,` 24%, `.` 1% · **Eld** → `red` 48%, `ar` 41%, `en` 9% · **Eli** → `.` 55%, `-` 10%, `ים` 7% · **Elena** → `,` 69%, `.` 15%, ` way` 9% · **Al** → `ena` 40%, `the` 25%, `iyah` 20%
- **base-bf16:** **John** → `.` 32%, `,` 9%, ` who` 4% · **Jack** → `.` 52%, `,` 15%, ` who` 8% · **George** → `.` 15%, `,` 10%, ` who` 4% · **Sarah** → `.` 47%, `,` 17%, ` who` 11% · **Henry** → `.` 37%, ` and` 5%, ` Black` 3% · **Tom** → `.` 65%, `,` 9%, ` and` 4% · **Peter** → `.` 37%, `,` 12%, ` who` 2% · **El** → `ara` 95%, `ian` 1%, `ora` 1%
- **instruct-bf16-raw:** **Ar** → `-` 29%, `

` 12%, `<turn|>` 11% · **Alice** → `.` 43%, `,` 41%, ` is` 7% · **Christian** → `,` 67%, `.` 32%, `...` 0% · **English** → ` woman` 33%, ` man` 33%, ` English` 29% · **Daniel** → `,` 50%, `.` 48%, `...` 1% · **Cl** → `Cl` 48%, `ou` 12%, `.` 9% · **August** → `.` 64%, ` of` 22%, ` in` 2% · **Robert** → `,` 100%, `.` 0%, `'` 0%
- **instruct:** **Elias** → `,` 32%, `.` 26%, ` Thorne` 17% · **Silas** → `.` 37%, ` who` 16%, `,` 16% · **El** → `ara` 54%, `ian` 46%, `ías` 0% · **Arthur** → `,` 29%, ` who` 19%, ` Vance` 17% · **Elena** → `,` 73%, ` and` 20%, ` who` 4% · **Leo** → `,` 35%, `.` 33%, ` who` 29% · **Clara** → `,` 47%, `.` 33%, ` and` 17% · **Barn** → `aby` 100%, `abas` 0%, `abus` 0%
- **instruct-bf16:** **Elias** → `,` 32%, `.` 26%, ` Thorne` 18% · **Silas** → `.` 36%, ` who` 18%, `,` 15% · **El** → `ara` 54%, `ian` 46%, `ías` 0% · **Arthur** → `,` 29%, ` who` 21%, ` Vance` 17% · **Elena** → `,` 71%, ` and` 22%, ` who` 5% · **Leo** → `,` 35%, `.` 33%, ` who` 29% · **Clara** → `,` 45%, `.` 33%, ` and` 18% · **Barn** → `aby` 100%, `abas` 0%, `abus` 0%
