"""Parse dice notation (3d6+2) and compute exact outcome distributions.

Distributions are counted as integers (ways to reach each total) rather
than floats, so results stay exact even after many convolutions. Callers
divide by the total to get a probability.
"""

import math
import re
from collections import defaultdict

_TOKEN = re.compile(r"([+-]?)(\d*[dD]\d+(?:(?:[kK][hHlL]|[dD][hHlL])\d+)?|\d+)")
_DICE_TOKEN = re.compile(r"^(\d*)[dD](\d+)(?:([kKdD][hHlL])(\d+))?$")


def parse_terms(expr):
    """Split a dice expression into (sign, token) pairs.

    Tokens are either dice terms like "3d6" / "d20" / "4d6kh3", or plain
    integer constants like "2". Raises ValueError on anything that doesn't
    parse cleanly, including trailing garbage.
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


def _keep_distribution(count, sides, keep, highest):
    """Distribution of the sum of the `keep` highest (or lowest) of `count` d`sides` dice.

    Computed by a DP over face values from best to worst: at each face we
    choose how many of the still-unassigned dice land on it (a binomial
    coefficient), and the first `keep` dice assigned that way contribute to
    the kept sum. This stays polynomial in count and sides, which matters
    because the naive approach - enumerate all sides**count rolls and sort
    each one - is exponential and unusable past a handful of dice.
    """
    if keep == 0:
        return {0: 1}

    faces = range(sides, 0, -1) if highest else range(1, sides + 1)
    dp = {(count, keep): {0: 1}}

    for face in faces:
        next_dp = defaultdict(lambda: defaultdict(int))
        for (remaining, keep_left), dist in dp.items():
            for taken in range(remaining + 1):
                ways = math.comb(remaining, taken)
                added = min(taken, keep_left) * face
                bucket = next_dp[(remaining - taken, max(keep_left - taken, 0))]
                for total, total_ways in dist.items():
                    bucket[total + added] += total_ways * ways
        dp = next_dp

    return dict(dp[(0, 0)])


def expression_distribution(expr):
    """Return {total: ways_to_reach_it} for a dice notation expression.

    Divide a count by sum(distribution.values()) to get a probability.
    """
    terms = parse_terms(expr)
    dist = {0: 1}

    for sign, token in terms:
        dice_match = _DICE_TOKEN.match(token)
        if dice_match:
            count_str, sides_str, modifier, mod_count_str = dice_match.groups()
            count = int(count_str) if count_str else 1
            sides = int(sides_str)
            if count < 1:
                raise ValueError(f"dice count must be at least 1, got {count}")

            if modifier:
                keep_count = int(mod_count_str)
                if not 1 <= keep_count <= count:
                    raise ValueError(
                        f"{token}: keep/drop count must be between 1 and {count}, "
                        f"got {keep_count}"
                    )
                modifier = modifier.lower()
                if modifier in ("kh", "kl"):
                    effective_keep, keep_highest = keep_count, modifier == "kh"
                else:
                    effective_keep, keep_highest = count - keep_count, modifier == "dl"
                term_dist = _keep_distribution(count, sides, effective_keep, keep_highest)
            else:
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
