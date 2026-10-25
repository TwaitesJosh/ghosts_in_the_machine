# Name -> trait associations (next-word probability probe)

**Lift** (bits) = how much more the model favours this trait *over the other traits* after this name, compared with plain names of the same gender. +1 = twice as favoured, +2 = 4x, -1 = half. Averaged over 6 sentence frames.

Baselines - male: David, Michael, James, John, Robert, Daniel; female: Sarah, Emily, Laura, Anna, Mary, Rachel; names the model reads as neither use both.

**Adjective shift** = how much more or less likely ANY of these traits is after the name. Strongly negative means the model expects something other than an adjective (the name itself is doing the describing).

Health check: for plain names, these traits together take **12.72%** of the next-word probability (a few % or more is good; well under 1% means the frames aren't producing adjectives and the numbers are noisy).

Traits outside the top 5000 next-words for every frame are too uncertain to rank and are left out of the lists (shown grey in the heatmap).

## Kaelen
- Read as: **mixed**  |  adjective shift: -0.2 bits
- **Pulls towards:** reckless +1.5, beautiful +1.4, cold +1.4, mysterious +1.2, dangerous +1.2, shy +1.1
- **Pushes away from:** generous -0.7, proud -0.4, wise -0.3, loyal -0.3

## Elara
- Read as: **female**  |  adjective shift: +0.3 bits
- **Pulls towards:** dangerous +4.2, cunning +3.8, reckless +3.7, cold +3.1, mysterious +3.1, arrogant +3.0
- **Pushes away from:** funny -1.5, generous -1.4, warm -1.1, honest -0.8

## Lyra
- Read as: **female**  |  adjective shift: +0.2 bits
- **Pulls towards:** cunning +4.4, dangerous +4.4, reckless +4.1, lonely +3.6, lazy +3.3, greedy +3.2
- **Pushes away from:** warm -1.8, generous -1.4, kind -1.0, patient -1.0

## Soren
- Read as: **male**  |  adjective shift: +0.1 bits
- **Pulls towards:** cold +2.6, beautiful +2.4, angry +2.3, lonely +2.3, cruel +2.1, fierce +2.1
- **Pushes away from:** generous -1.1, honest -0.7, funny -0.5, kind -0.4

## Voss
- Read as: **male**  |  adjective shift: -0.2 bits
- **Pulls towards:** dangerous +4.4, cold +3.2, naive +3.2, cruel +3.2, beautiful +3.1, bitter +2.8
- **Pushes away from:** kind -0.9, patient -0.6, warm -0.3, cheerful -0.1

## Elias
- Read as: **male**  |  adjective shift: +0.1 bits
- **Pulls towards:** dangerous +1.7, cruel +1.7, cold +1.5, angry +1.5, beautiful +1.5, lonely +1.4
- **Pushes away from:** generous -0.7, loyal -0.6, honest -0.5, funny -0.4

## Marcus
- Read as: **male**  |  adjective shift: -0.1 bits
- **Pulls towards:** arrogant +0.7, reckless +0.6, cold +0.6, dangerous +0.6, fierce +0.6, beautiful +0.5
- **Pushes away from:** proud -0.5, generous -0.4, loyal -0.2, kind -0.2

## Elena
- Read as: **female**  |  adjective shift: +0.2 bits
- **Pulls towards:** dangerous +1.6, arrogant +1.3, greedy +1.2, angry +1.1, reckless +1.1, cruel +1.0
- **Pushes away from:** funny -0.4, honest -0.4, wise -0.4, loyal -0.3

## Seraphina
- Read as: **female**  |  adjective shift: +0.4 bits
- **Pulls towards:** dangerous +5.0, cunning +4.7, reckless +4.1, lonely +3.6, cruel +3.6, greedy +3.5
- **Pushes away from:** warm -1.7, generous -1.3, funny -1.2, patient -1.1

## Thorne
- Read as: **male**  |  adjective shift: -0.1 bits
- **Pulls towards:** dangerous +3.6, cruel +3.0, naive +2.7, fierce +2.7, reckless +2.6, cold +2.6
- **Pushes away from:** kind -0.7, patient -0.3, warm -0.3, funny -0.2

## Silas
- Read as: **male**  |  adjective shift: +0.2 bits
- **Pulls towards:** cruel +2.7, angry +2.6, dangerous +2.5, lonely +2.5, grumpy +2.4, cold +2.4
- **Pushes away from:** generous -1.0, warm -0.8, funny -0.7, honest -0.6

## Mara
- Read as: **female**  |  adjective shift: +0.0 bits
- **Pulls towards:** dangerous +2.2, arrogant +1.7, reckless +1.6, cruel +1.6, lazy +1.4, cunning +1.4
- **Pushes away from:** warm -0.5, generous -0.3, cheerful -0.3, kind -0.2

## Kira
- Read as: **female**  |  adjective shift: -0.1 bits
- **Pulls towards:** reckless +2.2, dangerous +2.2, arrogant +2.1, lazy +2.0, cold +1.6, angry +1.6
- **Pushes away from:** warm -0.7, generous -0.7, kind -0.3, funny -0.2

## Aris
- Read as: **male**  |  adjective shift: -0.0 bits
- **Pulls towards:** beautiful +2.8, fierce +1.7, cold +1.7, dangerous +1.6, cruel +1.5, greedy +1.4
- **Pushes away from:** loyal -0.6, honest -0.5, funny -0.5, generous -0.5

## Vance
- Read as: **male**  |  adjective shift: -0.4 bits
- **Pulls towards:** dangerous +2.4, reckless +1.9, greedy +1.9, arrogant +1.9, cruel +1.9, naive +1.8
- **Pushes away from:** kind -0.5, gentle -0.4, patient -0.3, warm -0.3

## Vex
- Read as: **mixed**  |  adjective shift: +0.0 bits
- **Pulls towards:** dangerous +5.3, cunning +4.6, reckless +4.5, cruel +4.0, lonely +3.9, mysterious +3.9
- **Pushes away from:** warm -1.9, generous -1.6, kind -1.2, honest -0.8

## Vorrak (invented)
- Read as: **male**  |  adjective shift: -0.1 bits
- **Pulls towards:** dangerous +5.5, cunning +4.8, cruel +4.6, greedy +4.5, fierce +4.1, cold +3.9
- **Pushes away from:** kind -1.0, funny -0.9, patient -0.7, warm -0.6

## Grishnak (invented)
- Read as: **male**  |  adjective shift: +0.3 bits
- **Pulls towards:** dangerous +6.5, cruel +6.0, cunning +6.0, greedy +5.9, fierce +5.5, angry +4.5
- **Pushes away from:** warm -2.2, honest -2.1, kind -2.0, generous -1.8

## Kragthul (invented)
- Read as: **male**  |  adjective shift: +0.2 bits
- **Pulls towards:** dangerous +6.1, cruel +5.5, beautiful +5.1, cunning +5.1, greedy +5.0, fierce +4.3
- **Pushes away from:** funny -1.7, honest -1.7, patient -1.0, kind -0.8

## Zorvex (invented)
- Read as: **male**  |  adjective shift: -0.5 bits
- **Pulls towards:** dangerous +4.5, reckless +3.5, cruel +3.4, beautiful +3.4, cunning +3.3, greedy +3.3
- **Pushes away from:** funny -0.7, generous -0.6, kind -0.6, cheerful -0.6

## Lumie (invented)
- Read as: **female**  |  adjective shift: +0.1 bits
- **Pulls towards:** lazy +3.5, dangerous +3.4, grumpy +3.2, greedy +2.9, cunning +2.8, arrogant +2.7
- **Pushes away from:** warm -1.0, beautiful -0.6, kind -0.5, generous -0.3

## Miwela (invented)
- Read as: **female**  |  adjective shift: +0.1 bits
- **Pulls towards:** dangerous +3.1, lazy +2.4, arrogant +2.4, greedy +1.9, reckless +1.9, cunning +1.9
- **Pushes away from:** warm -0.9, funny -0.5, generous -0.3, wise -0.2

## Oona (invented)
- Read as: **female**  |  adjective shift: +0.2 bits
- **Pulls towards:** dangerous +2.1, grumpy +2.0, mysterious +1.8, cunning +1.7, lazy +1.7, lonely +1.6
- **Pushes away from:** honest -0.7, warm -0.6, patient -0.6, kind -0.3

## Liloa (invented)
- Read as: **mixed**  |  adjective shift: +0.6 bits
- **Pulls towards:** greedy +4.4, cunning +4.3, dangerous +3.5, mysterious +3.2, fierce +3.1, lazy +3.1
- **Pushes away from:** funny -1.4, warm -1.2, honest -1.0, patient -0.6
