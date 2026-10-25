# Name -> trait associations (next-word probability probe)

**Lift** (bits) = how much more the model favours this trait *over the other traits* after this name, compared with plain names of the same gender. +1 = twice as favoured, +2 = 4x, -1 = half. Averaged over 6 sentence frames.

Baselines - male: David, Michael, James, John, Robert, Daniel; female: Sarah, Emily, Laura, Anna, Mary, Rachel; names the model reads as neither use both.

**Adjective shift** = how much more or less likely ANY of these traits is after the name. Strongly negative means the model expects something other than an adjective (the name itself is doing the describing).

Health check: for plain names, these traits together take **44.08%** of the next-word probability (a few % or more is good; well under 1% means the frames aren't producing adjectives and the numbers are noisy).

Traits outside the top 5000 next-words for every frame are too uncertain to rank and are left out of the lists (shown grey in the heatmap).

## Elias
- Read as: **male**  |  adjective shift: +0.4 bits
- **Pulls towards:** gentle +2.1, solitary +1.7, quiet +1.6, weary +0.8, observant +0.5, lonely +0.3
- **Pushes away from:** loyal -6.8, energetic -5.6, honest -5.1, resilient -4.7

## Elara
- Read as: **female**  |  adjective shift: -0.4 bits  |  1 traits too rare to score
- **Pulls towards:** mysterious +3.5, skilled +3.1, dangerous +3.1, wise +2.2, solitary +2.1, quiet +1.5
- **Pushes away from:** warm -4.1, energetic -3.9, nurturing -2.8, kind -2.7

## Clara
- Read as: **female**  |  adjective shift: -0.2 bits  |  1 traits too rare to score
- **Pulls towards:** observant +1.5, gentle +1.4, wise +1.0, brave +0.8, quiet +0.8, vibrant +0.7
- **Pushes away from:** kind -2.1, loyal -1.4, protective -1.1, nurturing -1.0

## Kaelen
- Read as: **male**  |  adjective shift: -0.0 bits  |  1 traits too rare to score
- **Pulls towards:** mysterious +3.6, skilled +3.2, dangerous +3.0, vibrant +2.9, brave +2.5, resilient +2.4
- **Pushes away from:** patient -3.3, kind -2.8, warm -2.4, honest -2.4

## Kael
- Read as: **male**  |  adjective shift: +0.2 bits  |  1 traits too rare to score
- **Pulls towards:** mysterious +5.4, dangerous +3.9, solitary +3.7, skilled +3.1, brave +2.2, lonely +2.1
- **Pushes away from:** warm -4.9, kind -3.9, patient -3.4, gentle -3.0

## Julian
- Read as: **male**  |  adjective shift: -1.6 bits  |  1 traits too rare to score
- **Pulls towards:** mysterious +4.5, dangerous +2.9, observant +2.2, skilled +1.7, cruel +1.4, vibrant +1.3
- **Pushes away from:** loyal -4.8, resilient -4.8, honest -2.7, determined -2.7

## Leo
- Read as: **male**  |  adjective shift: +0.3 bits  |  1 traits too rare to score
- **Pulls towards:** vibrant +8.6, energetic +7.3, brave +6.6, warm +5.4, protective +4.2, resilient +3.3
- **Pushes away from:** patient -1.2, cruel -0.9, skilled -0.8, solitary -0.8

## Silas
- Read as: **male**  |  adjective shift: +0.6 bits
- **Pulls towards:** solitary +5.1, mysterious +2.6, quiet +2.3, dangerous +1.9, lonely +1.2, observant +1.1
- **Pushes away from:** resilient -8.4, loyal -8.1, energetic -7.5, kind -7.5

## Thorne
- Read as: **male**  |  adjective shift: -5.1 bits  |  1 traits too rare to score
- **Pulls towards:** dangerous +15.8, solitary +13.7, protective +11.4, mysterious +9.2, skilled +9.2, cruel +7.6
- **Pushes away from:** gentle -4.6, warm -2.9, kind -2.5, patient -0.4

## Seraphina
- Read as: **female**  |  adjective shift: -2.6 bits  |  1 traits too rare to score
- **Pulls towards:** dangerous +9.6, mysterious +8.1, skilled +6.4, cruel +6.1, wise +6.0, solitary +5.7
- **Pushes away from:** observant -1.2, energetic -1.1, resilient -0.6, determined -0.2
