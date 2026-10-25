# Name -> trait associations (next-word probability probe)

**Lift** (bits) = how much more the model favours this trait *over the other traits* after this name, compared with plain names of the same gender. +1 = twice as favoured, +2 = 4x, -1 = half. Averaged over 6 sentence frames.

Baselines - male: David, Michael, James, John, Robert, Daniel; female: Sarah, Emily, Laura, Anna, Mary, Rachel; names the model reads as neither use both.

**Adjective shift** = how much more or less likely ANY of these traits is after the name. Strongly negative means the model expects something other than an adjective (the name itself is doing the describing).

Health check: for plain names, these traits together take **9.01%** of the next-word probability (a few % or more is good; well under 1% means the frames aren't producing adjectives and the numbers are noisy).

Traits outside the top 5000 next-words for every frame are too uncertain to rank and are left out of the lists (shown grey in the heatmap).

## Elias
- Read as: **male**  |  adjective shift: +0.0 bits
- **Pulls towards:** dangerous +1.8, cruel +1.8, lonely +1.6, mysterious +1.3, solitary +1.2, weary +0.9
- **Pushes away from:** loyal -0.5, honest -0.4, warm -0.2, kind -0.2

## Elara
- Read as: **female**  |  adjective shift: -0.1 bits
- **Pulls towards:** dangerous +4.5, mysterious +3.3, cruel +3.1, lonely +3.0, solitary +3.0, weary +2.3
- **Pushes away from:** warm -0.8, nurturing -0.8, honest -0.5, vibrant -0.3

## Clara
- Read as: **female**  |  adjective shift: +0.1 bits
- **Pulls towards:** lonely +1.5, solitary +1.3, dangerous +1.2, mysterious +1.1, cruel +1.1, quiet +0.8
- **Pushes away from:** warm -0.2, honest -0.2, patient -0.1, nurturing -0.1

## Kaelen
- Read as: **mixed**  |  adjective shift: -0.2 bits
- **Pulls towards:** mysterious +1.2, dangerous +1.2, cruel +0.9, quiet +0.8, weary +0.7, lonely +0.6
- **Pushes away from:** loyal -0.4, wise -0.3, honest -0.3, warm -0.2

## Kael
- Read as: **male**  |  adjective shift: -0.1 bits
- **Pulls towards:** cruel +2.6, dangerous +2.5, mysterious +2.4, lonely +2.3, solitary +2.0, weary +1.9
- **Pushes away from:** honest -0.5, kind -0.4, warm -0.3, patient +0.1

## Julian
- Read as: **male**  |  adjective shift: -0.1 bits
- **Pulls towards:** cruel +1.3, dangerous +1.1, mysterious +1.0, lonely +0.9, solitary +0.8, brave +0.8
- **Pushes away from:** loyal -0.4, honest -0.3, kind -0.1, skilled -0.1

## Leo
- Read as: **male**  |  adjective shift: -0.0 bits
- **Pulls towards:** cruel +1.8, lonely +1.7, dangerous +1.7, mysterious +1.4, solitary +1.3, brave +1.1
- **Pushes away from:** honest -0.2, kind -0.2, skilled -0.1, warm +0.1

## Silas
- Read as: **male**  |  adjective shift: +0.1 bits
- **Pulls towards:** cruel +2.8, lonely +2.6, dangerous +2.6, solitary +2.2, mysterious +2.1, weary +2.0
- **Pushes away from:** warm -0.7, honest -0.5, kind -0.3, vibrant -0.1

## Thorne
- Read as: **male**  |  adjective shift: -0.5 bits
- **Pulls towards:** dangerous +3.8, cruel +3.2, solitary +2.8, mysterious +2.7, lonely +2.2, weary +2.0
- **Pushes away from:** kind -0.4, warm +0.0, patient +0.0, honest +0.4

## Seraphina
- Read as: **female**  |  adjective shift: -0.1 bits
- **Pulls towards:** dangerous +5.5, solitary +4.2, cruel +4.1, lonely +4.1, mysterious +3.8, weary +3.1
- **Pushes away from:** warm -1.2, nurturing -1.0, patient -0.6, kind -0.4
