#!/usr/bin/env python3
"""违禁词自检脚本:扫描文案,标注命中的违禁词,提供改写建议。

读取 assets/banned-words.json,扫描输入文案,输出命中报告(位置/级别/原句/建议改写词)。
可选 --persona 传入当前人设,自动应用 persona_exemptions 豁免清单,豁免命中单独列出不强制改。
实际改写由 skill 步骤 7 的 LLM 执行(考虑上下文,不机械替换);
改写后必须复检一遍,通过才算过关。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 默认 assets 路径(脚本相对位置:../assets/banned-words.json)
DEFAULT_WORDS_FILE = Path(__file__).parent.parent / "assets" / "banned-words.json"

LEVEL_EMOJI = {
    "illegal": "🚫",
    "sensitive": "⚠️",
    "limit": "📉",
}

# 单字违禁词的防误报组合:
# next=后接字构成中性词(最后/最初/冲突/冲刺/冲击),prev=前接字构成中性词(缓冲)
COMPOUND_SKIP = {
    "最": {"next": {"后", "初", "近", "终", "先"}},
    "冲": {"next": {"突", "洗", "锋", "刺", "击"}, "prev": {"缓"}},
}

# "第一"后接量词/序数单位(第一个/第一次/第一天)时是事实陈述,不是排名宣传,跳过防误报
ORDINAL_MEASURE = {"个", "次", "天", "年", "篇", "周", "月", "步", "轮", "期", "集",
                   "家", "位", "批", "份", "场", "段", "层", "版", "首", "套"}


def load_words(words_file: Path) -> dict:
    """加载违禁词清单 json"""
    if not words_file.exists():
        print(f"[ERROR] 违禁词清单不存在: {words_file}", file=sys.stderr)
        print("        请确认 assets/banned-words.json 已生成", file=sys.stderr)
        sys.exit(1)
    with open(words_file, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_text(text: str, words_data: dict) -> list:
    """扫描文本,返回命中清单(按位置排序)"""
    hits = []
    categories = words_data.get("categories", {})
    replacements = words_data.get("replacements", {})

    for cat_key, cat in categories.items():
        level = cat.get("level", "sensitive")
        cat_desc = cat.get("description", "")
        for word in cat.get("words", []):
            if not word:
                continue
            start = 0
            while True:
                idx = text.find(word, start)
                if idx == -1:
                    break
                # 单字词防误报:与相邻字构成中性技术词(最后/冲突/缓冲)时跳过
                if len(word) == 1:
                    rule = COMPOUND_SKIP.get(word, {})
                    nxt = text[idx + 1] if idx + 1 < len(text) else ""
                    prv = text[idx - 1] if idx > 0 else ""
                    if nxt in rule.get("next", ()):
                        start = idx + 2
                        continue
                    if prv in rule.get("prev", ()):
                        start = idx + 1
                        continue
                # "第一"防误报:后接量词(个/次/天...)时是序数用法,不是排名宣传,跳过
                if (
                    word == "第一"
                    and idx + 2 < len(text)
                    and text[idx + 2] in ORDINAL_MEASURE
                ):
                    start = idx + 3
                    continue
                # 提取上下文(前后 20 字)
                ctx_start = max(0, idx - 20)
                ctx_end = min(len(text), idx + len(word) + 20)
                context = text[ctx_start:ctx_end]
                suggestions = replacements.get(word, [])
                hits.append({
                    "word": word,
                    "category": cat_key,
                    "category_desc": cat_desc,
                    "level": level,
                    "position": idx,
                    "context": context,
                    "suggestions": suggestions,
                })
                start = idx + len(word)

    # 同位置/包含关系去重:"性能最好"只报最长的"最好",不重复报"最"
    hits.sort(key=lambda h: (h["position"], -len(h["word"])))
    kept: list = []
    for h in hits:
        start, end = h["position"], h["position"] + len(h["word"])
        contained = any(
            k["position"] <= start and end <= k["position"] + len(k["word"])
            for k in kept
        )
        if not contained:
            kept.append(h)
    return kept


def apply_persona_exemptions(
    hits: list, words_data: dict, persona: str | None
) -> tuple:
    """按 persona_exemptions 人设豁免清单拆分命中,返回 (需处理, 已豁免)。

    豁免按词精确匹配(如 student 的"绝了");换人设后需重新检查。
    """
    if not persona:
        return hits, []
    exemptions = words_data.get("persona_exemptions", {}).get(persona, [])
    active, exempt = [], []
    for h in hits:
        if h["word"] in exemptions:
            h["exempt"] = True
            exempt.append(h)
        else:
            active.append(h)
    return active, exempt


def _print_exempt_summary(exempt_hits: list, persona: str) -> None:
    """打印人设豁免摘要"""
    words = "、".join(sorted({h["word"] for h in exempt_hits}))
    print(f"**人设豁免(persona={persona})**: {len(exempt_hits)} 处({words})")
    print("按 assets/banned-words.json 的 persona_exemptions 不强制改;换人设需复检。\n")


def print_report(
    text: str, hits: list, exempt_hits: list = None, persona: str = None
) -> None:
    """打印 markdown 格式扫描报告(hits=需处理,exempt_hits=人设豁免命中)"""
    if not hits and not exempt_hits:
        print("## 违禁词自检报告\n\n✅ 未命中违禁词,文案可发布。\n")
        return
    if not hits:
        print(
            f"## 违禁词自检报告\n\n"
            f"✅ 未命中需处理的违禁词(persona={persona} 豁免 "
            f"{len(exempt_hits)} 处),文案可发布。\n"
        )
        _print_exempt_summary(exempt_hits, persona)
        return

    level_count = {}
    for h in hits:
        level_count[h["level"]] = level_count.get(h["level"], 0) + 1

    print("## 违禁词自检报告\n")
    print(f"**总命中**: {len(hits)} 处\n")
    print("**级别分布**:")
    for level in ["illegal", "sensitive", "limit"]:
        if level in level_count:
            emoji = LEVEL_EMOJI.get(level, "❓")
            print(f"- {emoji} {level}: {level_count[level]} 处")
    print()

    if exempt_hits:
        _print_exempt_summary(exempt_hits, persona)

    print("**命中详情**:")
    for i, h in enumerate(hits, 1):
        emoji = LEVEL_EMOJI.get(h["level"], "❓")
        print(f"\n{i}. {emoji} `{h['word']}` [{h['level']}] - {h['category']}")
        print(f"   上下文: ...{h['context']}...")
        if h["suggestions"]:
            print(f"   建议改写: {' / '.join(h['suggestions'])}")
        else:
            print("   建议改写: (无预设替换,需 LLM 根据上下文改写)")

    print("\n---")
    print("**下一步**: skill 步骤 7 的 LLM 拿到此报告后,在原文案中改写命中段落。")
    print("改写要考虑上下文语义,不能机械替换(如'破解'在不同语境改法不同)。")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="违禁词自检:扫描文案,标注命中,提供改写建议"
    )
    parser.add_argument("text", nargs="?", help="待检文案(直接传字符串)")
    parser.add_argument("--file", help="从文件读取待检文案")
    parser.add_argument(
        "--words-file",
        default=str(DEFAULT_WORDS_FILE),
        help=f"违禁词清单 json(默认 {DEFAULT_WORDS_FILE})",
    )
    parser.add_argument(
        "--persona",
        choices=["student", "coder", "blogger", "jobseeker"],
        help="当前人设,自动应用 persona_exemptions 豁免清单",
    )
    parser.add_argument(
        "--output", choices=["markdown", "json"], default="markdown",
        help="输出格式:markdown 或 json(默认)",
    )
    args = parser.parse_args()

    # 获取文案
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    elif args.text:
        text = args.text
    else:
        print("[ERROR] 必须提供文案(位置参数)或 --file <path>", file=sys.stderr)
        return 1

    words_file = Path(args.words_file)
    words_data = load_words(words_file)
    hits = scan_text(text, words_data)
    active, exempt = apply_persona_exemptions(hits, words_data, args.persona)

    if args.output == "json":
        print(json.dumps(
            {
                "persona": args.persona,
                "total_hits": len(active),
                "hits": active,
                "exempt_hits": exempt,
            },
            ensure_ascii=False, indent=2,
        ))
    else:
        print_report(text, active, exempt, args.persona)
    return 0


if __name__ == "__main__":
    sys.exit(main())
