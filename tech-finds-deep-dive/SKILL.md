---
name: tech-finds-deep-dive
description: 深度读懂技术项目/开源项目/skill,产出可直接发布的小红书等平台的种草文案。4人设按品类自动匹配,8种爆文结构模板,违禁词自检+改写。Use when asked to 把技术项目写成小红书种草文案、技术项目推广、开源项目分享、简历项目包装、源码拆解、学生党转码项目推荐。不触发:电商实物商品、纯SaaS推广、非技术产品测评。
---

# Tech Finds Deep Dive

## Goal

深度读懂一款技术项目 / 开源项目 / 自研工具 / skill,产出符合小红书语言风格、可直接发布、不千篇一律的种草文案。解决市面同类 skill "只给一篇文案、不深挖产品、不分人设、不管违禁词" 的敷衍问题。

## 核心机制

- **四维卖点硬约束**:≥6 差异化卖点 + ≥3 用户画像痛点场景 + ≥2 竞品差异 + ≥1 反直觉卖点,缺一不可。
- **4 人设按品类自动匹配**:学生党 / 转码人 / 技术博主 / 求职者,用户可 override。
- **违禁词自检→改写→复检闭环**:命中必改,改后再检,直到通过。
- **脚本 fallback**:脚本不可用时 LLM 用 Read 工具直接读核心文件,不中断流程。

## 执行指令

LLM 执行本 skill 时,直接消费 `references/execution-prompt.md` 中的十步 workflow、decision tree、constraints、validation。

## Workflow(摘要)

1. 确认输入(项目路径 / GitHub 链接 / 文档文本)
2. 读取项目核心文件(`scripts/read_project.py` 或 Read 工具 fallback)
3. 提取四维卖点(`references/selling-points-framework.md`)
4. 按品类匹配人设(`references/persona-*.md`)
5. 选爆文结构模板(`references/post-templates.md`)
6. 生成文案(参考 `references/example-posts.md`)
7. 违禁词自检(`scripts/banned_words_check.py` + `assets/banned-words.json`)
8. 可选配图建议(`--with-image`)
9. 按 `references/output-template.md` 输出文案 + 卖点清单
10. 用户反馈迭代(局部重写,换项目才重跑)

## Decision Tree(摘要)

- 项目路径 → `read_project.py`;脚本不可用时 Read 工具 fallback
- GitHub 链接 → WebFetch 抓 README + 提示补充结构
- 文档文本 → 跳过步骤 2
- 4 维缺一 → 回步骤 3 重提
- 违禁词命中且非人设豁免 → 改写 → 复检
- 用户调人设/模板/语气 → 局部重写步骤 6-9
- 用户换项目/换输入 → 从步骤 1 重跑

## Constraints

- 四维卖点缺一不可,产出前必须自检全有。
- 违禁词必须自检并改写,改写后必须复检到通过。
- 命中词若在当前人设豁免清单(`assets/banned-words.json` `persona_exemptions`)内,不强制改;换人设需重检。
- 人设按品类自动匹配,不能固定单一 "种草博主" 人设。
- 爆文结构从内置 8 种选,不外搜小红书。
- 产品范围限定:技术项目 / 开源项目 / 自研工具 / skill。**不处理电商实物商品、纯 SaaS 商品**。
- 输出默认不带配图建议,仅 `--with-image` 开启时给。
- 标签热度动态,提醒用户发布前自行确认。
- skill 存项目级,git 操作归用户,不自作主张 commit/push。
- 用户给不出具体信息时,先按框架产出并留占位,后续迭代补充。

## Validation

- 4 维卖点(6+3+2+反直觉)是否全产出?
- 违禁词自检是否通过(含复检)?
- 人设是否匹配(自动或用户指定)?
- 爆文结构是否从 8 种里选?

## Resources

- `scripts/read_project.py`:读项目核心文件,产出结构化摘要
- `scripts/banned_words_check.py`:违禁词自检
- `assets/banned-words.json`:违禁词清单 + 人设豁免表
- `references/execution-prompt.md`:LLM 执行用轻量指令
- `references/output-template.md`:最终输出格式模板
- `references/selling-points-framework.md`:4 维卖点提取框架
- `references/post-templates.md`:8 种爆文结构模板
- `references/persona-*.md`:4 种人设
- `references/example-posts.md`:2 篇范文
