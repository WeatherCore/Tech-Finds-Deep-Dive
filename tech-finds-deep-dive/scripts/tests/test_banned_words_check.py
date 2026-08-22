#!/usr/bin/env python3
"""banned_words_check.py 单元测试。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from banned_words_check import scan_text


class BannedWordsCheckTests(unittest.TestCase):
    """验证违禁词扫描、防误报、改写建议。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.words_file = Path(__file__).parent.parent.parent / "assets" / "banned-words.json"
        cls.words_data = json.loads(cls.words_file.read_text(encoding="utf-8"))

    def test_absolute_word_hit(self) -> None:
        text = "这个项目全网最强，闭眼入"
        hits = scan_text(text, self.words_data)
        words = {h["word"] for h in hits}
        self.assertIn("最强", words)
        self.assertIn("全网", words)

    def test_single_character_neutral_compound_skipped(self) -> None:
        text = "这是最后的方案，最初的想法"
        hits = scan_text(text, self.words_data)
        self.assertEqual(len(hits), 0, f"应跳过'最后/最初'等中性词，但命中: {hits}")

    def test_ordinal_measure_skipped(self) -> None:
        text = "第一天运行，第一个版本，最近一次"
        hits = scan_text(text, self.words_data)
        self.assertEqual(len(hits), 0, f"应跳过'第一+量词'序数用法，但命中: {hits}")

    def test_replacement_suggestions_present(self) -> None:
        text = "这个项目破解了部署难题"
        hits = scan_text(text, self.words_data)
        hit = next((h for h in hits if h["word"] == "破解"), None)
        self.assertIsNotNone(hit)
        self.assertTrue(len(hit["suggestions"]) > 0)

    def test_no_false_positive_on_normal_tech_terms(self) -> None:
        text = "我修改了脚本，用 Python 脚本跑测试"
        hits = scan_text(text, self.words_data)
        self.assertEqual(len(hits), 0)


if __name__ == "__main__":
    unittest.main()
