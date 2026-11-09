<!-- About 简介（推送后填写到仓库 About 栏）：
短剧剧本专家：题材到分集剧本的爆款流水线——题材立项、分集大纲（每集 3~5 个反转）、单集剧本（分场格式+台词）、开场钩子专项、时长与台词量确定性检测。 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-drama-script
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, short-drama, scriptwriting, micro-drama, hook, reversal -->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="lhg-drama-script — 短剧剧本专家">
</p>

> **一句话介绍**：短剧剧本专家：题材到分集剧本的爆款流水线——题材立项、分集大纲（每集 3~5 个反转）、单集剧本（分场格式+台词）、开场钩子专项、时长与台词量确定性检测。

**一键安装**：在 Claude Code 里运行

```bash
/plugin marketplace add lhg-plugs/lhg-drama-script
/plugin install lhg-drama-script@lhg-plugs
```

## 它能帮你做出什么

每条产出先过确定性脚本自查，再交人工复核清单——数字全部数自仓库里的审计脚本，不靠模型"自觉"。

| 自查脚本 | 规则数 | blocker | warning | nit | 覆盖 |
|---|---|---|---|---|---|
| `scripts/audit/drama_audit.py` | 22 | 6 | 14 | 2 | 格式、反转、钩子、时长、人物、台词、场次、卡点 |
| **合计** | **22** | **6** | **14** | **2** | |

- **零 LLM 成本**：规则是纯 Python 脚本，零第三方依赖，本地运行。
- **坏 / 好对照可验**：`fixtures/` 里备有坏/好用例，冒烟测试断言命中情况。
- **冒烟全绿**：`python3 smoke_test.py` 58 项全部通过（JSON 合法、frontmatter 完整、命令/skill/agent 齐全）。

## 它是什么

`lhg-drama-script` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`drama-audit` 剧本自检、`drama-episode` 写单集剧本、`drama-hook` 开场钩子专项、`drama-new` 短剧从零立项
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：lhg-ds-audit, lhg-ds-episode, lhg-ds-outline, lhg-ds-theme
- **3 个专家 agent**：plotter, qa-reviewer, scriptwriter
- **1 个 hooks**（`hooks/`：pre_deliver_check.py），关键操作前自动把关
- **22 条确定性自查规则**：纯 Python 脚本，见上表

## 为什么是它

不是一个 prompt，而是一套互相兜底的机制：

1. **确定性脚本（机器）+ 人工复核清单（人）**：先跑 `scripts/` 下的审计脚本（共 22 条规则），发现分三级：**blocker**（必须修）、**warning**（修或写豁免理由）、**nit**（顺手修）；再按对应 skill 的复核清单过一遍脚本抓不到的（内容真实性、越权、口径一致）。blocker 清零才算做完；为清零改规则算作弊，不许。
2. **硬门，不是提醒**：hooks 在关键操作前自动拦截或警告（见 `hooks/`），而不是只在文档里写一句"请注意"。
3. **方法论沉淀在 skill 里**：流程、检查清单、口径都写在 `skills/` 的方法论里，命令只是入口；换个 agent 平台也能复用同一套做法。
4. **可验，不是可信**：`fixtures/` 备有坏/好对照用例，`smoke_test.py` 一键验证，规则有没有生效、自己跑一遍就知道。

## 快速上手

```bash
# 1. 安装（Claude Code 里运行）
/plugin marketplace add lhg-plugs/lhg-drama-script
/plugin install lhg-drama-script@lhg-plugs

# 2. 短剧从零立项：一句话题材→爆款元素打分→赛道定位→人物小传→分集大纲（每集 3~
/lhg-drama-script:drama-new "赘婿首富" --eps 60
```

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-drama-script:drama-audit` | 剧本自检：审计脚本（反转数/钩子/时长/人物一致性）+ 人工评审 12 条清单 + 长叙事一致性检查，输出定稿判定。 | `/lhg-drama-script:drama-audit ./scripts/` |
| `/lhg-drama-script:drama-episode` | 写单集剧本：选定集数→按大纲取反转→分场剧本（钩子/台词/动作）→反转标注→审计脚本校验→人工清单复核。 | `/lhg-drama-script:drama-episode 3` |
| `/lhg-drama-script:drama-hook` | 开场钩子专项：给一集写 3 版不同类型的钩子（30 秒内），用户拍板后再进正文。专治"前 3 秒留不住人"。 | `/lhg-drama-script:drama-hook 1` |
| `/lhg-drama-script:drama-new` | 短剧从零立项：一句话题材→爆款元素打分→赛道定位→人物小传→分集大纲（每集 3~5 反转+情绪曲线+集末卡点）。 | `/lhg-drama-script:drama-new "赘婿首富" --eps 60` |

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你需要剧本自检时 → 用 `/lhg-drama-script:drama-audit`
- 你需要写单集剧本时 → 用 `/lhg-drama-script:drama-episode`
- 你需要开场钩子专项时 → 用 `/lhg-drama-script:drama-hook`

**什么时候不用：**

- 你只需要其中一个零散能力时 → 本插件是成套流程，单点需求用更轻量的 skill 更合适
- 你希望 AI 完全自由发挥、不接受任何自查与硬门时 → 它的规则审计与 hooks 会介入（可关，但那就别装它）
- 你的场景不在上面命令表覆盖范围内时 → 先看命令表，没有对应命令就别硬套

## 目录结构

```
lhg-drama-script/
├── smoke_test.py          # 一键冒烟测试
├── ATTRIBUTION.md         # 灵感来源与许可声明
├── LICENSE                # MIT
├── README.md              # 本文件
├── .claude-plugin/
├── __pycache__/
├── agents/
├── commands/
├── fixtures/
├── hooks/
├── scripts/
├── skills/
```

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（本次实测 58 项全部通过）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-drama-script/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

同门插件见 [lhg-plugs](https://github.com/lhg-plugs)，86 个插件的完整矩阵在 [marketplace](https://github.com/lhg-plugs/marketplace) 维护。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
