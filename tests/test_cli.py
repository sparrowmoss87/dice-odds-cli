import contextlib
import io
import os
import tempfile
import unittest

from diceprobe.cli import main, process_stream


def run(text):
    out = io.StringIO()
    process_stream(io.StringIO(text), out)
    return out.getvalue().splitlines()


class ProcessStreamTest(unittest.TestCase):
    def test_result_line(self):
        self.assertEqual(
            run("3d6+2\n"), ["3d6+2 -> min=5 max=20 mean=12.500 outcomes=16"]
        )

    def test_keep_result_line(self):
        self.assertEqual(
            run("4d6kh3\n"), ["4d6kh3 -> min=3 max=18 mean=12.245 outcomes=16"]
        )

    def test_blank_and_comment_lines_are_skipped(self):
        self.assertEqual(run("\n   \n# note\n"), [])

    def test_error_does_not_stop_the_run(self):
        lines = run("not-dice\nd4\n")
        self.assertEqual(
            lines[0],
            "1: not-dice -> error: unexpected characters in 'not-dice' at position 0",
        )
        self.assertEqual(lines[1], "d4 -> min=1 max=4 mean=2.500 outcomes=4")

    def test_error_line_numbers_count_skipped_lines(self):
        lines = run("\n# c\n2d6kh5\n")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("3: 2d6kh5 -> error:"))

    def test_input_is_consumed_lazily(self):
        out = io.StringIO()
        seen = []

        def source():
            for expr in ["d4", "d6", "d8"]:
                # Each earlier line must already have produced its output
                # before the next one is pulled from the stream.
                seen.append(len(out.getvalue().splitlines()))
                yield expr + "\n"

        process_stream(source(), out)
        self.assertEqual(seen, [0, 1, 2])


class MainTest(unittest.TestCase):
    def test_reads_file_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "rolls.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("d20\n2d6+1d4\n1d100-10\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main([path])
        self.assertEqual(
            buf.getvalue().splitlines(),
            [
                "d20 -> min=1 max=20 mean=10.500 outcomes=20",
                "2d6+1d4 -> min=3 max=16 mean=9.500 outcomes=14",
                "1d100-10 -> min=-9 max=90 mean=40.500 outcomes=100",
            ],
        )


if __name__ == "__main__":
    unittest.main()
