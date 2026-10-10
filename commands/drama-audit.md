---
description: 剧本自检：审计脚本（反转数/钩子/时长/人物一致性）+ 人工评审 12 条清单 + 长叙事一致性检查，输出定稿判定。
argument-hint: [剧本目录] [--fail-on blocker]
---

# /lhg-drama-script:drama-audit —— 剧本自检

用户输入在 `$ARGUMENTS` 中：`[剧本目录] [--fail-on blocker|warning|nit]`。缺省查当前目录。

加载 `lhg-ds-audit` 全文指导；人工评审部分可分派给 `qa-reviewer` agent（独立视角，不许自己审自己的稿）。

## 流程

### 1. 机器先查
- 跑 `python3 scripts/audit/drama_audit.py --target <剧本目录> --format text --fail-on <级别>`。
- blocker：必须修，不许豁免；warning：修或写 `<!-- 豁免：理由 -->`；nit：顺手修。

### 2. 人工再查
- 按 lhg-ds-audit 第 5 节 12 条清单逐条给结论（通过/不通过 + 改写建议）。
- 10 集以上项目：加查第 6 节长叙事一致性（伏笔回收表、战力账本、称呼冻结、时间线）。

### 3. 定稿判定
- blocker=0 且人工清单全过 → "可定稿"。
- 否则输出必修清单（按 blocker → 人工不通过项 → warning 排序），不许说"差不多行了"。

## 硬规则
- 跳过机器直奔人工清单 → 不许（低级错误不值得用人眼查）。
- 为清零改审计规则、删 `` 标记 → 算作弊，不许。
- 定稿后还想改剧情 → 回到 `/lhg-drama-script:drama-episode` 重走流程，不许直接改文件。
