# dice-odds-cli

Answers one question: for a dice notation expression like `3d6+2`, what is
the exact range and average of the result, and how many distinct totals
are possible?

It's not a dice roller. It doesn't produce a random outcome — it computes
the full outcome distribution by convolution and reports the min, max,
and mean, so you can sanity-check things like "is `4d6-drop-lowest`
actually a wider spread than `3d6`" without simulating millions of rolls.
(Keep/drop modifiers aren't supported yet — see the roadmap in the repo.)

## Usage

One expression per line, on stdin or a file:

```
$ echo "3d6+2" | python -m diceprobe.cli
3d6+2 -> min=5 max=20 mean=12.500 outcomes=16
```

```
$ cat rolls.txt
d20
2d6+1d4
1d100-10
$ python -m diceprobe.cli rolls.txt
d20 -> min=1 max=20 mean=10.500 outcomes=20
2d6+1d4 -> min=3 max=16 mean=9.500 outcomes=14
1d100-10 -> min=-9 max=90 mean=40.500 outcomes=100
```

Blank lines and lines starting with `#` are skipped. A line that doesn't
parse prints an error instead of stopping the whole run:

```
$ echo "not-dice" | python -m diceprobe.cli
1: not-dice -> error: unexpected characters in 'not-dice' at position 0
```

## Notation

- `NdM` — roll N dice with M sides each (`N` defaults to 1, so `d20` == `1d20`)
- Plain integers are flat modifiers
- Terms combine with `+` and `-`: `2d6+1d4-3`

## Why streaming matters here

Input is read with a line-by-line loop (`for line in stream`), never
`.read()` or `.readlines()`. A file with ten million expressions in it is
processed one line at a time with constant memory, not loaded whole
before the first result is printed. Each line's own distribution is
still bounded by the size of that expression (a `500d500` line will do
real work), but the size of the input stream itself is never a limit.

## Install

No dependencies, no build step. Clone it and run it with Python 3.9+.

## As a library

```python
from diceprobe.notation import expression_distribution, summarize

dist = expression_distribution("2d6")
print(summarize(dist))  # (2, 12, 7.0, 11)
```
