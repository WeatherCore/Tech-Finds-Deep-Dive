# Description

## 中文版

Tech-Finds-Deep-Dive 是深度读懂技术项目后产出可直接发布小红书种草文案的 AI skill，解决同类 skill 只给一篇文案、不深挖产品、不管违禁词的敷衍问题。含金量在工程化：四维卖点硬约束（6 卖点+3 画像+2 竞品+反直觉，缺一不可；数字卖点必须有出处，禁编造）、违禁词自检-改写-复检闭环（--persona 自动人设豁免、最长匹配去重、单字/序数/中性技术词三重防误报）、4 人设按品类自动匹配、8 爆文模板内置。工程为 read_project.py 与 banned_words_check.py 两脚本，14 语言栈识别、50KB 截断防 context 爆炸、多语言依赖结构化解析。适合推广技术项目、开源项目、自研工具与 skill。

## English

Tech-Finds-Deep-Dive is an AI skill that reads a tech project to the bone and turns it into a ready-to-post Xiaohongshu copy, fighting the lazy pattern of one generic blurb with no product insight, no persona, no moderation. The value is in the engineering: a four-dimension selling-point gate (6 differentiators + 3 user personas + 2 competitor comparisons + 1 counterintuitive hook, all mandatory, with every number in a claim traceable to README, source code, or real testing — no fabricated figures), a banned-word self-check-rewrite-recheck loop with --persona-based auto exemptions, longest-match deduplication, and false-positive guards for neutral compounds, ordinals, and everyday tech terms (辅助函数/代理模式-style words). Built as two Python scripts: read_project.py (14-language stack detection, 50KB truncation against context explosion, structured dependency parsing for pyproject.toml/go.mod/Cargo.toml) and banned_words_check.py. Great for promoting tech projects, open-source repos, self-built tools, and skills themselves.
