"""Streaming CLI: one dice expression per line in, one result line out.

Input is consumed with a plain `for line in stream` loop rather than
.read() or .readlines(), so a multi-gigabyte file of expressions is
processed one line at a time instead of being pulled into memory first.
"""

import sys

from .notation import expression_distribution, summarize


def process_stream(lines, out):
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        try:
            dist = expression_distribution(line)
            lo, hi, mean, outcome_count = summarize(dist)
        except ValueError as exc:
            print(f"{lineno}: {line} -> error: {exc}", file=out, flush=True)
            continue

        print(
            f"{line} -> min={lo} max={hi} mean={mean:.3f} outcomes={outcome_count}",
            file=out,
            flush=True,
        )


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if argv:
        with open(argv[0], "r", encoding="utf-8") as f:
            process_stream(f, sys.stdout)
    else:
        process_stream(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
