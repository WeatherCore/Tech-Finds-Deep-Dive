# 执行指南(轻量版)

> 本文件供 LLM 执行 skill 时直接消费。SKILL.md 保留完整设计说明,本文件只保留执行所需的最小指令集。

## Goal

深度读懂一款技术项目 / 开源项目 / 自研工具 / skill,产出可直接发布的小红书种草文案。读懂必须达四维标准,人设按品类自动匹配,违禁词发前自检改写。

## Workflow(十步)

1. **确认输入**:项目路径(优先) / GitHub 链接 / 项目文档文本。三选一,默认读项目路径。
2. **读取项目核心文件**:运行本 skill 目录下的 `scripts/read_project.py`。脚本不可用时,用 Read 工具按相同范围 fallback。
3. **提取四维卖点**(缺一不可):
   - ≥6 个差异化卖点(禁"性能好"空话;数字卖点必须有出处:README/源码/实测/用户提供)
   - ≥3 种典型用户画像的痛点场景
   - ≥2 个最接近竞品并说清差异
   - ≥1 个反直觉卖点
   详见 `references/selling-points-framework.md`。
4. **匹配人设**:按品类自动匹配,用户可 override。
   - 学生项目/教学类 → 学生党
   - 工具类/工作流类 → 转码人
   - 框架/库/开源项目 → 技术博主
   - 简历项目/求职作品 → 求职者
5. **选爆文结构模板**:从 `references/post-templates.md` 8 种里选 1 种。
6. **生成文案**:1 主推标题 + 2 备选 + 正文 + 话题标签。
7. **违禁词自检**:运行 `scripts/banned_words_check.py --persona {当前人设}`(脚本不可用时 LLM 对照 `assets/banned-words.json` 自查),命中 → LLM 改写 → 复检到通过。
8. **可选配图建议**:仅 `--with-image` 开启时输出。
9. **输出**:最终文案 + 四维卖点清单(供验收)。
10. **可选反馈迭代**:局部重写受影响部分,换项目/换输入才从头跑。

## Decision Tree

```
输入类型判断
├── 项目路径(本地目录)
│   └── 运行 scripts/read_project.py
│       └── 脚本不可用? → Read 工具 fallback
├── GitHub 链接
│   └── WebFetch 抓 README + 提示用户提供项目结构信息
└── 项目文档文本
    └── 跳过步骤 2,直接进入步骤 3

卖点完整性判断
├── 4 维卖点全有 → 进入步骤 4
└── 缺一维 → 回到步骤 3 重提

人设判断
├── 用户指定 → 用指定人设
└── 未指定 → 按品类自动匹配

违禁词判断
├── 未命中 → 通过
├── 命中在 exempt_hits(--persona 已自动标出) → 人设豁免,不强制改
└── 命中在 hits → LLM 改写 → 复检
    └── 仍命中 → 继续改写

迭代判断
├── 用户换项目/换输入 → 从步骤 1 重跑
└── 用户只调人设/模板/语气/突出卖点 → 局部重写步骤 6-9
```

## Constraints(唯一权威版本,SKILL.md 不复述)

- 四维卖点缺一不可,产出前自检全有。
- 数字卖点必须有出处(README/源码/实测/用户提供);无出处的删数字、改定性或标"(待实测)",不编造数字。
- 违禁词必须自检并改写,改写后必须复检到通过。
- 人设豁免以 `assets/banned-words.json` 的 `persona_exemptions` 为唯一权威,`--persona` 自动应用;换人设需重检。
- 人设按品类自动匹配,不能固定单一 "种草博主" 人设。
- 爆文结构从内置 8 种选,不外搜小红书。
- 产品范围限定:技术项目 / 开源项目 / 自研工具 / skill。不处理电商实物、纯 SaaS 商品。
- 输出默认不带配图建议,仅 `--with-image` 开启时给。
- 话题标签仅作参考,发布前需用户自行确认热度。
- skill 产出存项目级,git 操作(commit/push)归用户,不自作主张。
- 用户给不出具体信息时,先按框架产出并留占位,后续迭代补充。

## Validation

- 4 维卖点是否全产出?
- 数字卖点是否都有出处(或标"待实测")?
- 违禁词自检是否通过(含复检)?
- 人设是否匹配(自动或指定)?
- 爆文结构是否从 8 种里选?

## Resources

- `references/selling-points-framework.md`:4 维卖点提取框架
- `references/persona-student.md` / `persona-coder.md` / `persona-blogger.md` / `persona-jobseeker.md`:4 种人设
- `references/post-templates.md`:8 种爆文结构
- `references/example-posts.md`:2 篇范文
- `references/output-template.md`:最终输出格式模板
- `scripts/read_project.py`:读项目摘要
- `scripts/banned_words_check.py`:违禁词自检(带 `--persona` 自动豁免)
- `assets/banned-words.json`:违禁词清单
