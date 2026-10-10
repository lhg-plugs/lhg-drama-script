#!/usr/bin/env python3
"""lhg-drama-script 硬门：剧本定稿/交付前跑确定性审计。

触发：PreToolUse / Bash。脚本先判断本次 Bash 命令是否为"定稿/交付"
意图（命令含 定稿/交付/发布剧本/deliver-script 等关键词），不是则
0 开销直接放行；是则在当前项目目录查找剧本文件并跑 drama_audit.py。

门禁：有 blocker → 拦截（deny），列出 blocker 清单；
无 blocker → 放行；找不到剧本文件 → 提醒式放行（additionalContext）。

逃生方式（按推荐度排序）：
  1. 修好剧本后重新定稿（推荐）。
  2. 紧急情况：LHG_DS_HOOKS_OFF=1 <定稿命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-drama-script（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到审计脚本、解析失败等）时 fail-open
直接放行，不因插件自身故障骚扰用户；真正的门禁在
/lhg-drama-script:drama-audit。零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

# 定稿/交付意图：中文关键词 + 英文脚本名
DELIVER_RE = re.compile(
    r"定稿|交付|发布剧本|deliver-script|publish-script",
)
# 排除审计脚本自身的运行，避免自我干扰
SELF_RE = re.compile(r"drama_audit\.py|smoke_test\.py")


def find_audit_script():
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    cands = []
    if root:
        cands.append(os.path.join(root, "scripts", "audit", "drama_audit.py"))
    # 兜底：脚本所在目录的上级
    here = os.path.dirname(os.path.abspath(__file__))
    cands.append(os.path.join(here, "..", "scripts", "audit", "drama_audit.py"))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_DS_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非定稿命令：快速放行；审计脚本自身：放行
    if not DELIVER_RE.search(command) or SELF_RE.search(command):
        return 0

    audit = find_audit_script()
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if audit is None:
        return 0  # 找不到审计脚本：fail-open

    try:
        r = subprocess.run(
            [sys.executable, audit, "--target", project_dir,
             "--format", "json", "--fail-on", "blocker"],
            capture_output=True, text=True, timeout=60)
        data = json.loads(r.stdout)
    except Exception:
        return 0  # 审计执行/解析失败：fail-open

    summary = data.get("summary", {}) or {}
    if summary.get("files_scanned", 0) == 0:
        # 找不到剧本文件：提醒式放行（可能定的不是剧本）
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    "提醒：本次定稿未在当前目录找到剧本文件（*.md 含【人物】行）。"
                    "如果是交付 lhg-drama-script 的剧本，请确认剧本文件格式"
                    "（见 skill lhg-ds-episode 第 7 节），否则跳过此提醒。"
                ),
            }
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0

    blockers = [f for f in data.get("findings", [])
                if f.get("severity") == "blocker"]
    if not blockers:
        return 0  # 无 blocker：放行

    lines = [
        "定稿被 lhg-drama-script 硬门拦截：剧本审计发现 %d 个 blocker，修好再定稿。"
        % len(blockers),
        "",
    ]
    for f in blockers[:10]:
        lines.append("- [%s] %s:%s %s" % (
            f.get("rule_id"), os.path.basename(f.get("file", "")),
            f.get("line"), f.get("title")))
    if len(blockers) > 10:
        lines.append("…另有 %d 个" % (len(blockers) - 10))
    lines += [
        "",
        "修复方式：跑 /lhg-drama-script:drama-audit 看完整报告（含改写建议）；",
        "紧急豁免（单次）：LHG_DS_HOOKS_OFF=1 <定稿命令>",
    ]
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
