import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import flip_test as ft

PAIRS = ROOT / "examples" / "pairs.jsonl"


class FlipTestControls(unittest.TestCase):
    def setUp(self):
        self.pairs = ft.load_pairs(PAIRS)

    def test_naive_extractor_is_caught(self):
        extract = ft.python_extractor(str(ROOT / "examples" / "naive_extractor.py") + ":extract")
        counts = ft.summarize(ft.run_pairs(self.pairs, extract))
        self.assertEqual(counts["PASS"], 0)
        self.assertEqual(counts["STUCK"], len(self.pairs))
        self.assertGreater(counts["single_correct"], 0)

    def test_reference_extractor_passes(self):
        extract = ft.python_extractor(str(ROOT / "examples" / "reference_extractor.py") + ":extract")
        counts = ft.summarize(ft.run_pairs(self.pairs, extract))
        self.assertEqual(counts["PASS"], len(self.pairs))

    def test_command_mode_matches_python_mode(self):
        cmd = f"{sys.executable} {ROOT / 'examples' / 'reference_extractor.py'}"
        counts = ft.summarize(ft.run_pairs(self.pairs, ft.command_extractor(cmd)))
        self.assertEqual(counts["PASS"], len(self.pairs))


class JudgePair(unittest.TestCase):
    PAIR = {"id": "x", "a": {"input": "A", "expect": {"k": 1}}, "b": {"input": "B", "expect": {"k": 2}}}

    def test_wrong_but_not_stuck(self):
        r = ft.judge_pair(self.PAIR, {"k": 1}, {"k": 3})
        self.assertEqual(r["verdict"], "WRONG")

    def test_stuck(self):
        r = ft.judge_pair(self.PAIR, {"k": 1}, {"k": 1})
        self.assertEqual(r["verdict"], "STUCK")

    def test_dotted_fields(self):
        pair = {"id": "y", "a": {"input": "A", "expect": {"q.type": "need"}},
                "b": {"input": "B", "expect": {"q.type": "has"}}}
        r = ft.judge_pair(pair, {"q": {"type": "need"}}, {"q": {"type": "has"}})
        self.assertEqual(r["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
