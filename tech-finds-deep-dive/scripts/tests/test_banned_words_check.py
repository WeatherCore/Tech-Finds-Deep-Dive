#!/usr/bin/env python3
"""banned_words_check.py 单元测试。"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from banned_words_check import apply_persona_exemptions, scan_text  # noqa: E402


class BannedWordsCheckTests(unittest.TestCase):
    """验证违禁词扫描、防误报、改写建议。"""

    @classmethod
    def setUpClass(cls) -> None:
        words_file = (
            Path(__file__).parent.parent.parent / "assets" / "banned-words.json"
        )
        cls.words_data = json.loads(words_file.read_text(encoding="utf-8"))

    def test_absolute_word_hit(self) -> None:
        text = "这个项目全网最强，闭眼入"
        hits = scan_text(text, self.words_data)
        words = {h["word"] for h in hits}
        self.assertIn("最强", words)
        self.assertIn("全网", words)

    def test_single_character_neutral_compound_skipped(self) -> None:
        text = "这是最后的方案，最初的想法"
        hits = scan_text(text, self.words_data)
        msg = f"应跳过'最后/最初'等中性词，但命中: {hits}"
        self.assertEqual(len(hits), 0, msg)

    def test_ordinal_measure_skipped(self) -> None:
        text = "第一天运行，第一个版本，最近一次"
        hits = scan_text(text, self.words_data)
        msg = f"应跳过'第一+量词'序数用法，但命中: {hits}"
        self.assertEqual(len(hits), 0, msg)

    def test_replacement_suggestions_present(self) -> None:
        text = "这个项目破解了部署难题"
        hits = scan_text(text, self.words_data)
        hit = next((h for h in hits if h["word"] == "破解"), None)
        self.assertIsNotNone(hit)
        assert hit is not None  # 类型收窄: 上面断言后 hit 必非 None
        self.assertTrue(len(hit["suggestions"]) > 0)

    def test_no_false_positive_on_normal_tech_terms(self) -> None:
        text = "我修改了脚本，用 Python 脚本跑测试"
        hits = scan_text(text, self.words_data)
        self.assertEqual(len(hits), 0)

    def test_neutral_chong_compounds_skipped(self) -> None:
        text = "解决版本冲突，自带缓冲区，冲刺阶段也不慌"
        hits = scan_text(text, self.words_data)
        msg = f"冲突/缓冲/冲刺 是中性技术词，应跳过，但命中: {hits}"
        self.assertEqual(len(hits), 0, msg)

    def test_helper_and_proxy_terms_not_flagged(self) -> None:
        text = "写了个辅助函数处理代理模式，还配了反向代理"
        hits = scan_text(text, self.words_data)
        msg = f"辅助函数/代理模式 是中性技术词，不应命中，但命中: {hits}"
        self.assertEqual(len(hits), 0, msg)

    def test_overlapping_hits_keep_longest_match(self) -> None:
        text = "性能最好"
        hits = scan_text(text, self.words_data)
        self.assertEqual([h["word"] for h in hits], ["最好"])

    def test_chong_exaggeration_still_flagged(self) -> None:
        text = "都给我冲"
        hits = scan_text(text, self.words_data)
        self.assertIn("冲", {h["word"] for h in hits})

    def test_persona_exemption_splits_hits(self) -> None:
        text = "这个项目绝了，也是真的香，但性能最强"
        hits = scan_text(text, self.words_data)
        active, exempt = apply_persona_exemptions(hits, self.words_data, "student")
        self.assertEqual({h["word"] for h in exempt}, {"绝了", "真的香"})
        self.assertEqual([h["word"] for h in active], ["最强"])

    def test_persona_none_returns_all_hits(self) -> None:
        text = "这个项目绝了"
        hits = scan_text(text, self.words_data)
        active, exempt = apply_persona_exemptions(hits, self.words_data, None)
        self.assertEqual(len(active), 1)
        self.assertEqual(exempt, [])


if __name__ == "__main__":
    unittest.main()
