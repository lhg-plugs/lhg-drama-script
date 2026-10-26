<!-- About 简介（推送后填写到仓库 About 栏）：
短剧剧本专家：题材到分集剧本的爆款流水线 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-drama-script
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, short-drama, scriptwriting -->

# lhg-drama-script：短剧剧本专家

> **一句话介绍**：短剧剧本专家——从一句话题材到分集剧本的爆款流水线：题材立项、分集大纲（每集 3~5 个反转）、单集剧本（分场格式+台词）、开场钩子专项，外加 22 条确定性规则的时长/台词量/反转数自检。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-drama-script
> /plugin install lhg-drama-script@lhg-plugs
> ```

## 它是什么

`lhg-drama-script` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"想写短剧但不知道从哪下手"的小白设计：

- **4 个命令**（小白入口）：`drama-new` 一句话题材→分集大纲，`drama-episode` 选集写单集剧本，`drama-hook` 开场钩子专项（3 版让用户选），`drama-audit` 剧本自检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：题材立项、分集大纲、单集剧本、剧本自检
- **3 个专家 agent**：大纲师、剧本师、独立质检员（不许审自己写过的稿）
- **1 个硬门 hook**：剧本定稿/交付前自动跑审计，有 blocker 直接拦截（可一键豁免，不骚扰）
- **22 条确定性自查规则**：反转数、钩子位置、预估时长、人物一致性、台词长度、场次、结尾卡点，纯 Python、零第三方依赖，秒级出结果

工作流：`drama-new`（题材→大纲）→ `drama-episode`（单集剧本）→ `drama-audit`（查一遍），也可以只用其中一段。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-drama-script:drama-new` | 一句话题材→爆款元素打分→人物小传→分集大纲（每集 3~5 反转+卡点） | `/lhg-drama-script:drama-new "赘婿首富" --eps 60` |
| `/lhg-drama-script:drama-episode` | 选定集数→分场剧本（钩子/台词/动作/反转标注/结尾卡点）→审计校验 | `/lhg-drama-script:drama-episode 3` |
| `/lhg-drama-script:drama-hook` | 开场钩子专项：3 版不同类型钩子，用户拍板后再写正文 | `/lhg-drama-script:drama-hook 1` |
| `/lhg-drama-script:drama-audit` | 剧本自检（22 条规则 + 人工评审 12 条清单 + 长叙事一致性） | `/lhg-drama-script:drama-audit ./scripts/` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/drama_audit.py`（22 条规则：格式 4、反转 3、钩子 2、时长 2、人物 2、台词 3、场次 4、卡点 2），零 LLM 成本；
2. 发现分三级：**blocker**（必须修，定稿前 hook 会拦截）、**warning**（修或写 `<!-- 豁免：理由 -->`）、**nit**（顺手修）；
3. 再按 `lhg-ds-audit` skill 的 12 条人工清单过一遍脚本抓不到的（钩子够不够炸、钉子句够不够狠、反转有没有代价）。

blocker 清零才算做完；为清零改规则、删 `【反转】` 标记算作弊，不许。

## 目录结构

```
lhg-drama-script/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：drama-new / drama-episode / drama-hook / drama-audit
├── skills/                  # 4 个平台中立 skill（题材立项/分集大纲/单集剧本/剧本自检）
├── agents/                  # 3 个专家 agent（plotter / scriptwriter / qa-reviewer）
├── hooks/                   # 1 个硬门（定稿前剧本审计）+ 豁免说明
├── scripts/audit/           # 22 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 剧本文件格式（一句话版）

单集剧本是 Markdown，审计脚本按标记解析：`# 《剧名》第 N 集` 标题、`【人物】` 登记、`## 第 N 场` 分场、`【钩子】`（30 秒内）、台词（`人名：台词`）、`【反转N】`（3~5 个）、`【结尾卡点】`（有且仅有一处）。完整规范见 skill `lhg-ds-episode` 第 7 节。

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你有个短剧想法，但不知道题材能不能火、大纲怎么排时 → 用 `/lhg-drama-script:drama-new`，从爆款元素打分到分集大纲一次走完
- 你要写某一集，但前 3 秒不知道怎么抓人时 → 用 `/lhg-drama-script:drama-hook` 先定钩子，再进正文
- 你写完剧本，怕反转不够、时长超标、人物穿帮时 → 跑 `/lhg-drama-script:drama-audit`，机器 22 条规则先查一遍
- 你想给编剧团队立一套"定稿必须过自检"的纪律时 → 它的 hook 硬门与审计脚本开箱即用

**什么时候不用：**

- 你写的是长剧/电影剧本（三幕式长片结构）→ 本插件是"竖屏短剧"专家，单集 1–2.5 分钟的节奏假设不适用于长片
- 你要的是"一句话生成 80 集完整剧本" → 本插件是流水线不是印钞机：大纲和剧本都要逐集过，大纲质量决定剧本上限
- 你的剧本是英文或纯方言对白 → 时长换算按中文语速（4.5 字/秒）标定，其他语言请先自行校准换算系数

**风险点诚实说明：**

- **方法论来源**：短剧方法论部分借鉴了 MIT 许可的开源 skill 与短剧行业公开资料的高层思路（详见 ATTRIBUTION.md），实现与文案均为原创；行业经验类内容带有主观性，请结合自身赛道判断
- **审计是启发式**：22 条规则查的是结构（反转数、钩子位置、时长），查不出"钩子够不够炸""反转有没有代价"——这些永远是人工评审清单的事
- **时长换算系数**：台词 4.5 字/秒按短剧偏快语速标定，实际拍摄因演员语速、停顿、打戏会有偏差，`【时长目标】` 偏差在 20% 内都算正常
- **相关插件**：`lhg-fiction`（长篇小说插件，规划中）——两者"长叙事一致性检测"思路互通、各自实现、互不依赖，仓库发布后此处补链接

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-drama-script](https://github.com/lhg-plugs/lhg-drama-script) | 短剧剧本专家：题材到分集剧本的爆款流水线 | `/plugin install lhg-drama-script@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、22 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-drama-script/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
