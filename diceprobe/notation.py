"""Parse dice notation (3d6+2) and compute exact outcome distributions.

Distributions are counted as integers (ways to reach each total) rather
than floats, so results stay exact even after many convolutions. Callers
divide by the total to get a probability.
"""

import re
from collections import defaultdict

_TOKEN = re.compile(r"([+-]?)(\d*[dD]\d+|\d+)")


def parse_terms(expr):
    """Split a dice expression into (sign, token) pairs.

    Tokens are either dice terms like "3d6" / "d20", or plain integer
    constants like "2". Raises ValueError on anything that doesn't parse
    cleanly, including trailing garbage.
    """
    compact = re.sub(r"\s+", "", expr)
    if not compact:
        raise ValueError("empty expression")

    terms = []
    pos = 0
    for match in _TOKEN.finditer(compact):
        if match.start() != pos:
            raise ValueError(f"unexpected characters in {expr!r} at position {pos}")
        sign = -1 if match.group(1) == "-" else 1
        terms.append((sign, match.group(2)))
        pos = match.end()

    if pos != len(compact):
        raise ValueError(f"unexpected characters in {expr!r} at position {pos}")
    if not terms:
        raise ValueError(f"no terms found in {expr!r}")
    return terms


def _die_distribution(sides):
    if sides < 1:
        raise ValueError(f"a die needs at least 1 side, got {sides}")
    return {face: 1 for face in range(1, sides + 1)}


def _convolve(a, b):
    # Every combination of an outcome from a and an outcome from b lands on
    # the summed value; the number of ways to reach it multiplies.
    result = defaultdict(int)
    for value_a, ways_a in a.items():
        for value_b, ways_b in b.items():
            result[value_a + value_b] += ways_a * ways_b
    return dict(result)


def _negate(dist):
    return {-value: ways for value, ways in dist.items()}


def expression_distribution(expr):
    """Return {total: ways_to_reach_it} for a dice notation expression.

    Divide a count by sum(distribution.values()) to get a probability.
    """
    terms = parse_terms(expr)
    dist = {0: 1}

    for sign, token in terms:
        if "d" in token.lower():
            count_str, sides_str = re.split("[dD]", token)
            count = int(count_str) if count_str else 1
            sides = int(sides_str)
            if count < 1:
                raise ValueError(f"dice count must be at least 1, got {count}")

            single = _die_distribution(sides)
            term_dist = {0: 1}
            for _ in range(count):
                term_dist = _convolve(term_dist, single)
            if sign < 0:
                term_dist = _negate(term_dist)
        else:
            term_dist = {int(token) * sign: 1}

        dist = _convolve(dist, term_dist)

    return dist


def summarize(dist):
    """Return (minimum, maximum, mean, outcome_count) for a distribution."""
    total_ways = sum(dist.values())
    total_value = sum(value * ways for value, ways in dist.items())
    return min(dist), max(dist), total_value / total_ways, len(dist)
