# Name -> trait associations (next-word probability probe)

**Lift** (bits) = how much more the model favours this trait *over the other traits* after this name, compared with plain names of the same gender. +1 = twice as favoured, +2 = 4x, -1 = half. Averaged over 6 sentence frames.

Baselines - male: David, Michael, James, John, Robert, Daniel; female: Sarah, Emily, Laura, Anna, Mary, Rachel; names the model reads as neither use both.

**Adjective shift** = how much more or less likely ANY of these traits is after the name. Strongly negative means the model expects something other than an adjective (the name itself is doing the describing).

Health check: for plain names, these traits together take **5.74%** of the next-word probability (a few % or more is good; well under 1% means the frames aren't producing adjectives and the numbers are noisy).

Traits outside the top 5000 next-words for every frame are too uncertain to rank and are left out of the lists (shown grey in the heatmap).

## Kaelen
- Read as: **male**  |  adjective shift: -1.0 bits
- **Pulls towards:** fierce +7.8, beautiful +5.1, mysterious +4.6, dangerous +3.9, reckless +3.7, cunning +3.4
- **Pushes away from:** patient -2.3, kind -1.8, generous -1.7, honest -1.5

## Elara
- Read as: **female**  |  adjective shift: -0.2 bits
- **Pulls towards:** cunning +4.0, calm +3.7, mysterious +3.2, fierce +3.1, curious +3.1, dangerous +2.9
- **Pushes away from:** cheerful -4.3, warm -4.3, generous -2.8, loyal -2.7

## Lyra
- Read as: **female**  |  adjective shift: +0.4 bits
- **Pulls towards:** reckless +6.6, fierce +5.9, curious +5.9, cunning +5.9, dangerous +4.4, clever +4.4
- **Pushes away from:** warm -5.4, patient -4.3, kind -3.3, cheerful -2.1

## Soren
- Read as: **male**  |  adjective shift: -0.5 bits
- **Pulls towards:** calm +3.1, cold +2.8, mysterious +2.1, beautiful +2.0, quiet +1.6, lonely +1.0
- **Pushes away from:** warm -4.7, kind -4.6, generous -4.5, stubborn -4.3

## Voss
- Read as: **male**  |  adjective shift: -1.1 bits
- **Pulls towards:** cold +14.6, cunning +12.0, dangerous +10.2, stern +8.1, arrogant +7.9, reckless +5.5
- **Pushes away from:** gentle -6.3, kind -5.8, warm -4.4, shy -2.6

## Elias
- Read as: **male**  |  adjective shift: -0.3 bits
- **Pulls towards:** gentle +2.7, quiet +1.9, calm +1.7, beautiful +0.5, lonely +0.5, mysterious +0.4
- **Pushes away from:** loyal -6.5, funny -5.5, stubborn -5.2, honest -4.9

## Marcus
- Read as: **male**  |  adjective shift: -1.0 bits
- **Pulls towards:** stern +7.6, cold +5.2, fierce +5.0, arrogant +4.8, ambitious +4.7, cunning +4.2
- **Pushes away from:** gentle -3.3, shy -2.8, kind -2.3, curious -1.3

## Elena
- Read as: **female**  |  adjective shift: -0.8 bits
- **Pulls towards:** fierce +4.6, cunning +3.9, calm +3.5, dangerous +3.4, proud +3.2, beautiful +3.2
- **Pushes away from:** cheerful -3.1, shy -1.9, kind -1.6, patient -0.8

## Seraphina
- Read as: **female**  |  adjective shift: -0.3 bits
- **Pulls towards:** beautiful +8.1, cold +8.0, dangerous +7.7, mysterious +6.4, calm +6.0, proud +5.4
- **Pushes away from:** cheerful -3.3, shy -2.9, stubborn -1.9, warm -1.8

## Thorne
- Read as: **male**  |  adjective shift: -4.8 bits
- **Pulls towards:** cold +18.5, dangerous +14.6, stern +12.9, beautiful +12.8, fierce +10.5, bitter +10.3
- **Pushes away from:** gentle -5.4, warm -3.7, kind -3.1, generous -1.7

## Silas
- Read as: **male**  |  adjective shift: +0.3 bits
- **Pulls towards:** cold +5.5, cunning +3.4, mysterious +3.0, quiet +2.7, dangerous +2.4, lonely +1.6
- **Pushes away from:** loyal -7.8, stubborn -7.4, kind -7.2, warm -6.9

## Mara
- Read as: **female**  |  adjective shift: -1.0 bits
- **Pulls towards:** cunning +6.4, cold +5.9, dangerous +4.6, calm +4.6, fierce +4.5, mysterious +4.3
- **Pushes away from:** cheerful -4.7, kind -3.6, warm -3.5, shy -2.8

## Kira
- Read as: **female**  |  adjective shift: -1.0 bits
- **Pulls towards:** cunning +6.3, mysterious +5.7, fierce +4.6, cold +4.6, dangerous +4.5, charming +4.4
- **Pushes away from:** gentle -3.0, kind -2.9, warm -2.6, patient -2.5

## Aris
- Read as: **male**  |  adjective shift: -1.1 bits
- **Pulls towards:** fierce +6.1, cunning +5.3, mysterious +4.5, beautiful +4.5, clever +4.1, curious +3.9
- **Pushes away from:** honest -2.6, kind -2.5, warm -2.0, loyal -1.9

## Vance
- Read as: **male**  |  adjective shift: +0.4 bits
- **Pulls towards:** cunning +8.7, arrogant +8.7, cold +8.3, charming +7.5, dangerous +5.9, reckless +4.6
- **Pushes away from:** gentle -9.5, kind -6.7, shy -5.8, quiet -4.7

## Vex
- Read as: **female**  |  adjective shift: -1.8 bits
- **Pulls towards:** cunning +15.9, charming +9.9, clever +9.5, dangerous +9.0, reckless +7.8, bitter +6.7
- **Pushes away from:** warm -11.4, gentle -11.0, kind -9.0, brave -8.3

## Vorrak (invented)
- Read as: **male**  |  adjective shift: -0.3 bits
- **Pulls towards:** cunning +17.8, cold +12.1, dangerous +10.3, greedy +8.7, bitter +7.5, stern +7.1
- **Pushes away from:** gentle -8.4, kind -7.1, warm -6.7, quiet -4.8

## Grishnak (invented)
- Read as: **male**  |  adjective shift: +2.5 bits
- **Pulls towards:** cruel +20.5, greedy +19.8, strong +18.3, cunning +17.6, angry +16.4, dangerous +16.0
- **Pushes away from:** kind -11.3, calm -10.7, quiet -10.4, charming -8.1

## Kragthul (invented)
- Read as: **male**  |  adjective shift: +0.9 bits
- **Pulls towards:** cold +16.7, cunning +12.3, cruel +12.3, bitter +11.6, dangerous +11.6, arrogant +10.7
- **Pushes away from:** kind -6.4, charming -5.7, warm -5.7, gentle -5.0

## Zorvex (invented)
- Read as: **male**  |  adjective shift: +0.2 bits
- **Pulls towards:** cold +16.4, cunning +15.5, arrogant +13.2, dangerous +11.3, ambitious +8.3, brilliant +6.9
- **Pushes away from:** gentle -12.3, warm -8.7, kind -8.5, quiet -7.1

## Lumie (invented)
- Read as: **female**  |  adjective shift: -1.8 bits
- **Pulls towards:** gentle +7.7, cheerful +7.0, naive +5.3, curious +3.7, shy +2.9, generous +2.7
- **Pushes away from:** fierce -7.8, ambitious -5.5, strong -5.2, calm -4.2

## Miwela (invented)
- Read as: **female**  |  adjective shift: +0.6 bits
- **Pulls towards:** charming +4.0, cunning +4.0, gentle +3.6, mysterious +3.3, curious +3.2, shy +3.0
- **Pushes away from:** kind -1.3, loyal -1.1, strong -1.0, funny -0.9

## Oona (invented)
- Read as: **female**  |  adjective shift: +1.2 bits
- **Pulls towards:** quiet +3.5, mysterious +2.8, wise +1.4, gentle +1.3, curious +1.3, calm +1.0
- **Pushes away from:** ambitious -6.2, kind -6.2, warm -5.5, cheerful -4.4

## Liloa (invented)
- Read as: **female**  |  adjective shift: +0.8 bits
- **Pulls towards:** gentle +6.2, calm +6.0, reckless +5.0, mysterious +4.9, fierce +3.7, dangerous +3.6
- **Pushes away from:** kind -2.4, ambitious -2.1, funny -1.9, loyal -1.7
