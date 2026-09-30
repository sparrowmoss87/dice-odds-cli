import unittest

from diceprobe.notation import expression_distribution, parse_terms, summarize


class ParseTermsTest(unittest.TestCase):
    def test_dice_and_constant(self):
        self.assertEqual(parse_terms("3d6+2"), [(1, "3d6"), (1, "2")])

    def test_whitespace_is_ignored(self):
        self.assertEqual(parse_terms(" 2d6 - 1d4 "), [(1, "2d6"), (-1, "1d4")])

    def test_leading_minus(self):
        self.assertEqual(parse_terms("-2"), [(-1, "2")])

    def test_implicit_count(self):
        self.assertEqual(parse_terms("d20"), [(1, "d20")])

    def test_keep_and_drop_tokens(self):
        self.assertEqual(
            parse_terms("4d6kh3+2d8dl1"), [(1, "4d6kh3"), (1, "2d8dl1")]
        )

    def test_rejects_malformed_input(self):
        for bad in ["", "   ", "3d", "3d6+", "3d6++2", "abc", "3d6+x", "3d6kh"]:
            with self.subTest(expr=bad):
                with self.assertRaises(ValueError):
                    parse_terms(bad)

    def test_error_reports_position(self):
        with self.assertRaises(ValueError) as ctx:
            parse_terms("3d6+x")
        self.assertIn("position 3", str(ctx.exception))


class DistributionTest(unittest.TestCase):
    def test_single_die_is_uniform(self):
        self.assertEqual(expression_distribution("d4"), {1: 1, 2: 1, 3: 1, 4: 1})

    def test_two_d6(self):
        dist = expression_distribution("2d6")
        self.assertEqual(sum(dist.values()), 36)
        self.assertEqual(dist[2], 1)
        self.assertEqual(dist[7], 6)
        self.assertEqual(dist[12], 1)
        self.assertEqual(min(dist), 2)
        self.assertEqual(max(dist), 12)

    def test_constants(self):
        self.assertEqual(expression_distribution("5"), {5: 1})
        self.assertEqual(expression_distribution("-5"), {-5: 1})

    def test_modifier_shifts_range(self):
        dist = expression_distribution("2d6+3")
        self.assertEqual((min(dist), max(dist)), (5, 15))
        self.assertEqual(dist[10], 6)

    def test_subtracted_dice_are_symmetric(self):
        dist = expression_distribution("1d6-1d6")
        self.assertEqual(sum(dist.values()), 36)
        self.assertEqual(dist[0], 6)
        self.assertEqual(dist[5], 1)
        self.assertEqual(dist[-5], 1)

    def test_case_insensitive(self):
        self.assertEqual(
            expression_distribution("2D6KH1"), expression_distribution("2d6kh1")
        )

    def test_one_sided_die(self):
        self.assertEqual(expression_distribution("3d1"), {3: 1})


class KeepDropTest(unittest.TestCase):
    def test_keep_highest_of_two_d2(self):
        # rolls (1,1) (1,2) (2,1) (2,2) keep 1, 2, 2, 2
        self.assertEqual(expression_distribution("2d2kh1"), {1: 1, 2: 3})

    def test_keep_lowest_of_two_d2(self):
        self.assertEqual(expression_distribution("2d2kl1"), {1: 3, 2: 1})

    def test_drop_is_keep_of_the_rest(self):
        self.assertEqual(
            expression_distribution("2d2dl1"), expression_distribution("2d2kh1")
        )
        self.assertEqual(
            expression_distribution("2d2dh1"), expression_distribution("2d2kl1")
        )

    def test_keeping_everything_matches_plain_roll(self):
        self.assertEqual(
            expression_distribution("3d6kh3"), expression_distribution("3d6")
        )
        self.assertEqual(
            expression_distribution("3d6kl3"),
            expression_distribution("3d6"),
        )

    def test_four_d6_keep_three_totals(self):
        dist = expression_distribution("4d6kh3")
        self.assertEqual(sum(dist.values()), 6 ** 4)
        self.assertEqual((min(dist), max(dist)), (3, 18))
        self.assertEqual(dist[3], 1)
        self.assertEqual(dist[18], 21)

    def test_negated_keep_term(self):
        dist = expression_distribution("-2d2kh1")
        self.assertEqual(dist, {-1: 1, -2: 3})

    def test_large_keep_does_not_enumerate(self):
        # 20d10 has 10**20 rolls; this only returns if the DP is used.
        dist = expression_distribution("20d10kh2")
        self.assertEqual(sum(dist.values()), 10 ** 20)
        self.assertEqual(max(dist), 20)

    def test_invalid_counts(self):
        for bad in ["2d6kh3", "2d6kh0", "2d6dl0", "2d6dh3", "0d6", "1d0", "0d0"]:
            with self.subTest(expr=bad):
                with self.assertRaises(ValueError):
                    expression_distribution(bad)


class SummarizeTest(unittest.TestCase):
    def test_two_d6(self):
        self.assertEqual(summarize(expression_distribution("2d6")), (2, 12, 7.0, 11))

    def test_constant(self):
        self.assertEqual(summarize({4: 1}), (4, 4, 4.0, 1))

    def test_negative_range(self):
        lo, hi, mean, count = summarize(expression_distribution("1d4-10"))
        self.assertEqual((lo, hi, count), (-9, -6, 4))
        self.assertAlmostEqual(mean, -7.5)


if __name__ == "__main__":
    unittest.main()
