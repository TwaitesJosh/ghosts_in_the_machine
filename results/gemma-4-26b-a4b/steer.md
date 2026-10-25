# Exorcising Elias

The 'Elias direction' is the average difference, at layer 15 of 30, between the model's internal state on the token 'Elias' and on 20 other male names in identical sentences. Below, that direction is subtracted (strength **alpha**, in multiples of the direction) at every position while the model writes.

## At the naming moment: P(Elias) and who replaces him

| Setting | alpha 0 | alpha 0.5 | alpha 1 | alpha 2 |
|---|---|---|---|---|
| lighthouse | 99.3% — Elias 99%, Silas 1%, El 0% | 99.5% — Elias 99%, Silas 0%, El 0% | 99.5% — Elias 99%, Silas 1%, El 0% | 98.7% — Elias 99%, Silas 1%, El 0% |
| clockmaker | 100.0% — Elias 100%, Silas 0%, El 0% | 100.0% — Elias 100%, Silas 0%, El 0% | 100.0% — Elias 100%, Silas 0%, El 0% | 99.9% — Elias 100%, Silas 0%, El 0% |
| starship | 7.5% — El 91%, Elias 8%, Elena 0% | 16.1% — El 82%, Elias 16%, Elena 1% | 28.7% — El 69%, Elias 29%, Elena 2% | 61.6% — Elias 62%, El 33%, Elena 3% |
| weaver | 1.8% — El 98%, Elias 2%, Silas 0% | 6.8% — El 93%, Elias 7%, Silas 0% | 13.3% — El 87%, Elias 13%, Silas 0% | 46.1% — El 52%, Elias 46%, Silas 1% |
| manor | 90.5% — Elias 91%, Silas 8%, Al 1% | 91.1% — Elias 91%, Silas 7%, Al 1% | 90.7% — Elias 91%, Silas 7%, Al 1% | 83.7% — Elias 85%, Silas 11%, Al 3% |
| family | 24.0% — Leo 74%, Elias 24%, El 2% | 24.1% — Leo 74%, Elias 24%, El 1% | 29.0% — Leo 69%, Elias 29%, El 0% | 19.6% — Leo 78%, Elias 20%, Arthur 2% |
| villain | 91.5% — Elias 92%, Silas 5%, Arthur 3% | 92.7% — Elias 93%, Arthur 5%, Silas 2% | 92.9% — Elias 93%, Arthur 5%, Silas 2% | 79.0% — Elias 79%, Arthur 18%, Silas 3% |
| hero-woman | 0.2% — El 100%, Elias 0%, Clara 0% | 0.9% — El 99%, Elias 1%, Clara 0% | 2.6% — El 97%, Elias 3%, Clara 0% | 16.0% — El 81%, Elias 16%, Clara 1% |
| hero-man | 98.2% — Elias 98%, El 1%, Silas 0% | 99.0% — Elias 99%, El 1%, Silas 0% | 99.1% — Elias 99%, Silas 0%, El 0% | 97.0% — Elias 97%, Silas 1%, Leo 1% |
| a-man | 99.6% — Elias 100%, Silas 0%, El 0% | 99.6% — Elias 100%, Silas 0%, Arthur 0% | 99.4% — Elias 99%, Silas 0%, Arthur 0% | 96.7% — Elias 97%, Arthur 2%, Silas 1% |
| a-woman | 2.3% — El 97%, Elias 2%, Clara 1% | 5.9% — El 93%, Elias 6%, Clara 1% | 14.6% — El 84%, Elias 15%, Clara 1% | 44.7% — El 51%, Elias 45%, Clara 3% |
| office | 13.6% — Arthur 58%, Elias 35%, Perc 2% | 12.2% — Arthur 65%, Elias 27%, Perc 3% | 8.6% — Arthur 64%, Elias 24%, Miller 4% | 2.3% — Arthur 72%, Miller 11%, Elias 8% |

## Stories written with the direction removed

Same random seeds at every strength, so differences come from the steering. Prompt: "Write a short story.", 250 tokens max.

### alpha 0

**Story 1**

The clock on Elias’s wall didn’t tick; it hummed. It was a low, rhythmic vibration that felt less like time passing and more like the universe breathing.



Elias was a Clockmaker, but not the kind who worked with gears and springs. He worked with moments. People came to his small, cluttered shop at the edge of the city when they had too much of something, or not enough of something else.



One rainy Tuesday, a woman named Clara entered. She didn't look like the usual clientele—the frantic businessmen trying to buy extra minutes for meetings, or the grieving widows looking to stretch a final goodbye. Clara looked hollow, as if she were made of glass that had been shattered and glued back together too many times.



"I want to give some away," she said, her voice barely a whisper.



Elias looked up from a delicate assembly of golden light. "Giving away time is dangerous, Clara. It leaves holes. You might find yourself standing in a room wondering why you’re there, or why you’re crying, or why you’re holding a cup of tea that has gone cold."



"I have too much of it," she insisted, sitting on

**Story 2**

The clock in Elias’s workshop didn’t tick; it hummed. It was a low, rhythmic vibration that lived in the floorboards and settled in the marrow of his bones. 



Elias was a Fixer, though not of the kind who dealt with leaky faucets or broken chairs. He fixed things that had lost their "why." He fixed music boxes that had forgotten how to sing, compasses that no longer knew where North was, and pocket watches that had grown tired of measuring time.



On a Tuesday, draped in the gray light of a coastal fog, a girl entered his shop. She couldn't have been more than ten, wearing a yellow raincoat that looked two sizes too large. In her hands, she cradled something wrapped in a silk scarf.



"Can you fix it?" she asked. Her voice was small, but steady.



Elias peered over his spectacles. "That depends, little one. What is it?"



She unwrapped the scarf. Resting in her palms was a glass jar, or rather, the shards of one. Inside the fragments lay a swirl of iridescent mist, pulsing weakly like a dying ember.



Elias leaned in. He didn't see glass;

### alpha 2

**Story 1**

The clock on Elias’s desk didn’t tick; it hummed. It was a low, rhythmic vibration that felt less like a measurement of time and more like a pulse.



In the dim light of his basement workshop, surrounded by the skeletal remains of discarded grandfather clocks and disassembled wristwatches, the hum was the only company he had. It was a comforting sound. It was reliable.



"Almost there," he whispered to the silence.



On the velvet-lined tray before him lay the heart of his obsession: a gear no larger than a grain of sand. It was made of a strange, iridescent alloy that seemed to swallow the light from his desk lamp and spit it back out as a dull, violet glow.



For three years, the neighbors in the quiet suburb of Oley’s Mill had known of Mr. Henderson as the "Quiet Man." He was the man who pruned his hedges with mathematical precision and walked his terrier, Barnaby, at exactly 4:00 PM. But they didn't know about the basement. They didn't know about the device.



The device was a Sphere. It was a seamless orb of brass and glass, roughly the size of a grapefruit, but inside

**Story 2**

The clock on the wall didn’t tick; it pulsed. It was a heavy, rhythmic thud that seemed to vibrate through the velvet upholstery of the armchair where Elias sat, staring at the tea cooling in his hands.



He was eighty-four years old, and for the first time in his life, he was profoundly bored. It was a terrifying realization. For decades, his life had been a frantic sprint of deadlines, deadlines, meetings, and milestones. Now, the finish line had passed, and he was just circling the stadium.



The silence in the house was thick, like a heavy wool blanket.



"The tea is cold, dear," a voice said.



It was a soft, ephemeral sound, like the rustle of dry leaves. Elizabeth was standing in the doorway. She was wearing the blue dress she had worn to the jazz club in 1962, the one that made her eyes look like deep pools of ink.



"I know," Elizabeth said, or rather, the memory of her said.



She didn't appear as a ghost—not the cinematic kind with chains and moaning. She appeared in the periphery of his vision, a shimmer in the light, a scent of

