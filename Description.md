# Description

## 中文版

tech-finds-deep-dive 是深度读懂技术项目/开源项目/skill、产出可直接发布小红书种草文案的 skill。其含金量在把"读懂"做成可验收的硬标准：四维卖点约束（6 差异化卖点+3 用户画像痛点场景+2 竞品对比+1 反直觉卖点）缺一回炉，4 人设按品类自动匹配并带词汇表豁免避免正常表达被强改，违禁词自检→改写→复检闭环并做单字词防误报（最后/第一+量词跳过），保证文案发出去能过审。工程由 read_project.py、banned_words_check.py 两个 Python 脚本+违禁词清单 JSON+7 个 Markdown 知识包构成，仅用标准库无第三方依赖，兼容 14 种语言技术栈项目。适合开源项目推广、简历项目包装、学生党转码项目推荐等场景。

## English

tech-finds-deep-dive is a skill that deep-dives into a tech project, open-source repo, or skill and turns it into a publish-ready Xiaohongshu (RED) recommendation post. It makes "deep read" a verifiable standard: a four-dimensional selling-point checklist (6 differentiated selling points, 3 user-persona pain scenarios, 2 competitor comparisons, 1 counterintuitive hook) that fails the run if any dimension is missing; 4 personas auto-matched by project category, with a persona vocabulary-exemption list so normal expressions aren't force-rewritten; and a banned-word self-check → rewrite → re-scan loop with single-character false-positive suppression (neutral compounds and ordinal "第一+measure word" are skipped), so the copy actually survives platform review. It is built from two dependency-free Python scripts (read_project.py, banned_words_check.py), a banned-words JSON, and seven markdown knowledge packs, and reads projects across 14 language stacks. It fits open-source promotion, résumé-project packaging, and student-oriented project recommendations.
