#!/usr/bin/env python3
"""lhg-drama-script 确定性剧本审计：22 条规则，零第三方依赖。

扫描目标目录下的单集剧本 Markdown 文件（格式见 skill lhg-ds-episode
第 7 节），检查反转数、钩子位置、预估时长、人物一致性、台词、场次、
结尾卡点；输出 JSON 与人类可读报告。

用法：
    python3 drama_audit.py --target <目录> [--format json|text]
                           [--fail-on blocker|warning|nit]

exit code：2=有 blocker；1=仅 warning（或 fail-on 级别命中）；
0=通过。--fail-on 控制"非零退出"的门限，默认 blocker。

规则文案均为本项目原创（方法论思路受 MIT 许可的开源短剧 skill
与短剧行业公开资料启发，未复制任何第三方原文；详见 ATTRIBUTION.md）。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-drama-script/drama-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}

# 时长换算（见 lhg-ds-episode 第 6 节）
DIAL_CPS = 4.5      # 台词：每秒字数
ACTION_CPS = 10.0  # 动作描写：每秒字数
SCENE_SWITCH_SEC = 2.0  # 每次转场保底秒数

TITLE_RE = re.compile(r"^#\s+.*第\s*(\d+)\s*集")
SCENE_RE = re.compile(r"^##\s+第\s*(\d+)\s*场")
CHARS_RE = re.compile(r"^【人物】\s*(.+)$")
TARGET_RE = re.compile(r"^【时长目标】\s*(\d+)")
HOOK_RE = re.compile(r"【钩子】")
REV_RE = re.compile(r"【反转(\d+)】")
END_RE = re.compile(r"【结尾卡点】")
MARKER_RE = re.compile(r"【([^】]{1,12})】")
KNOWN_MARKERS = {"人物", "时长目标", "场景", "钩子", "结尾卡点"}
EXEMPT_RE = re.compile(r"<!--\s*豁免\s*[:：]\s*(.+?)\s*-->")
DIAL_RE = re.compile(r"^([^：:【】#\s][^：:]{0,11})[:：]\s*(.+)$")
PAREN_RE = re.compile(r"（[^）]*）$")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file",
                 "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file,
                 line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return None


def is_episode_script(path, text):
    """剧本文件指纹：含【人物】行，或标题含"第 N 集"。"""
    if not path.lower().endswith(".md"):
        return False
    return bool(CHARS_RE.search(text) or TITLE_RE.search(text))


def collect(target):
    found = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            p = os.path.join(root, f)
            text = read_text(p)
            if text is None:
                continue
            if is_episode_script(p, text):
                found.append((p, text))
    return found


def clean_name(name):
    """去掉"管家（电话）"这类括号备注，取登记名。"""
    return PAREN_RE.sub("", name).strip()


def parse_chars(decl):
    # 人名只用 / 分隔（身份备注里的 、 ， 不能当分隔符）
    names = []
    for part in decl.split("/"):
        part = part.strip()
        if not part:
            continue
        # 去掉"（男主，赘婿/首富）"这类身份备注
        part = re.sub(r"（[^）]*）", "", part).strip()
        part = re.sub(r"\([^)]*\)", "", part).strip()
        # 残留的 、 ，分隔（如"张三、李四"）再拆一次
        for sub in re.split(r"[、，,]", part):
            sub = sub.strip()
            if sub:
                names.append(sub)
    return names


class Episode:
    """单集解析结果。"""

    def __init__(self, path, text):
        self.path = path
        self.lines = text.split("\n")
        self.has_title = False
        self.ep_no = None
        self.has_chars_line = False
        self.declared = []          # 登记的人物名
        self.target_sec = None
        self.scenes = []            # [(编号, 行号)]
        self.hook_at = None         # 钩子出现的预估秒数
        self.hook_line = None
        self.reversals = []         # [(编号, 行号)]
        self.end_hooks = []         # [行号]
        self.dialogues = []         # [(人名, 台词, 行号)]
        self.action_lines = 0       # 动作行数
        self.content_lines = 0      # 内容行数（台词+动作）
        self.scene_action = {}      # 场次编号 -> 是否有动作行
        self.scene_dialog = {}      # 场次编号 -> 是否有台词
        self.total_sec = 0.0
        self.unknown_markers = []   # [(标记, 行号)]
        self.exempt_lines = set()   # 含豁免注释的行号
        self._parse()

    def _parse(self):
        t = 0.0
        cur_scene = None
        for i, raw in enumerate(self.lines, start=1):
            line = raw.strip()
            if EXEMPT_RE.search(line):
                self.exempt_lines.add(i)
            # 去掉豁免注释后再解析与计时
            line = EXEMPT_RE.sub("", line).strip()
            if not line:
                continue
            m = TITLE_RE.match(line)
            if m:
                self.has_title = True
                self.ep_no = int(m.group(1))
                continue
            m = SCENE_RE.match(line)
            if m:
                no = int(m.group(1))
                self.scenes.append((no, i))
                cur_scene = no
                self.scene_action.setdefault(no, False)
                self.scene_dialog.setdefault(no, False)
                t += SCENE_SWITCH_SEC
                continue
            m = CHARS_RE.match(line)
            if m:
                self.has_chars_line = True
                self.declared = parse_chars(m.group(1))
                continue
            m = TARGET_RE.match(line)
            if m:
                self.target_sec = int(m.group(1))
                continue
            # 标记
            for mk in MARKER_RE.findall(line):
                if mk.startswith("反转"):
                    continue  # 由 REV_RE 单独处理
                if mk not in KNOWN_MARKERS:
                    self.unknown_markers.append((mk, i))
            for rno in REV_RE.findall(line):
                self.reversals.append((int(rno), i))
            if HOOK_RE.search(line) and self.hook_at is None:
                self.hook_at = t
                self.hook_line = i
            for _ in END_RE.findall(line):
                self.end_hooks.append(i)
            # 台词
            dm = DIAL_RE.match(line)
            if dm and not line.startswith("【"):
                name = clean_name(dm.group(1))
                text = dm.group(2).strip()
                self.dialogues.append((name, text, i))
                self.content_lines += 1
                if cur_scene is not None:
                    self.scene_dialog[cur_scene] = True
                t += len(text) / DIAL_CPS
                continue
            if line.startswith("#"):
                continue
            # 其余非空行计为动作/叙述行
            self.action_lines += 1
            self.content_lines += 1
            if cur_scene is not None:
                self.scene_action[cur_scene] = True
            # 去掉【场景】等标记头再计时
            body = MARKER_RE.sub("", line)
            t += len(body) / ACTION_CPS
        self.total_sec = t


# ---------------------------------------------------------------- 规则注册表
RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _mk(rule_id, path, line, snippet):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet[:160], r["detail"])


# ------------------------------------------------------------ 格式 FMT
@rule("FMT-TITLE-001", "blocker", "格式", "缺少集标题行",
      "剧本必须以 `# 《剧名》第 N 集：集标题` 开头（含“第 N 集”）。")
def _c(ep, out):
    if not ep.has_title:
        out.append(_mk("FMT-TITLE-001", ep.path, 1,
                       ep.lines[0] if ep.lines else ""))


@rule("FMT-CHARS-001", "blocker", "格式", "缺少【人物】行",
      "必须有【人物】行登记本集出场人物（人名用 / 分隔），台词人名据此校验。")
def _c(ep, out):
    if not ep.has_chars_line:
        out.append(_mk("FMT-CHARS-001", ep.path, 1, ""))


@rule("FMT-SCENE-001", "blocker", "格式", "无分场",
      "单集至少要有 1 个 `## 第 N 场`。")
def _c(ep, out):
    if not ep.scenes:
        out.append(_mk("FMT-SCENE-001", ep.path, 1, ""))


@rule("FMT-MARKER-001", "nit", "格式", "未知标记（疑似拼写错误）",
      "发现不在规范中的【标记】，请检查是否把【反转N】写成了【反转】、"
      "【钩子】写成了【勾子】等。")
def _c(ep, out):
    seen = set()
    for mk, ln in ep.unknown_markers:
        if mk in seen:
            continue
        seen.add(mk)
        out.append(_mk("FMT-MARKER-001", ep.path, ln, "【%s】" % mk))


# ------------------------------------------------------------ 反转 REV
@rule("REV-COUNT-001", "blocker", "反转", "反转不足 3 个",
      "每集至少 3 个【反转N】标记（见 lhg-ds-outline 反转库 8 类）。"
      "少了观众会觉得“这集没讲啥”。")
def _c(ep, out):
    if len(ep.reversals) < 3:
        out.append(_mk("REV-COUNT-001", ep.path,
                       ep.reversals[0][1] if ep.reversals else 1,
                       "本集仅 %d 个反转标记" % len(ep.reversals)))


@rule("REV-COUNT-002", "warning", "反转", "反转超过 5 个",
      "一集塞超过 5 个反转容易变成闹剧，观众跟不上。请合并或移到下一集。")
def _c(ep, out):
    if len(ep.reversals) > 5:
        out.append(_mk("REV-COUNT-002", ep.path, ep.reversals[-1][1],
                       "本集 %d 个反转标记" % len(ep.reversals)))


@rule("REV-ORDER-001", "warning", "反转", "反转编号不连续",
      "【反转N】编号应从 1 连续递增，跳号多半是漏写了一处反转内容。")
def _c(ep, out):
    nums = sorted(n for n, _ in ep.reversals)
    if nums and nums != list(range(1, len(nums) + 1)):
        out.append(_mk("REV-ORDER-001", ep.path, ep.reversals[-1][1],
                       "编号序列：%s" % nums))


# ------------------------------------------------------------ 钩子 HOOK
@rule("HOOK-MISSING-001", "blocker", "钩子", "缺少开场钩子",
      "单集必须有【钩子】标记（见 lhg-ds-episode 第 3 节钩子库 6 类）。"
      "没有钩子 = 默认观众会划走。")
def _c(ep, out):
    if ep.hook_at is None:
        out.append(_mk("HOOK-MISSING-001", ep.path, 1, ""))


@rule("HOOK-LATE-001", "warning", "钩子", "钩子位置超过 30 秒",
      "短剧观众 3 秒划走，钩子必须在 30 秒内出现，越早越好。")
def _c(ep, out):
    if ep.hook_at is not None and ep.hook_at > 30:
        f = _mk("HOOK-LATE-001", ep.path, ep.hook_line or 1,
                "钩子位于预估 %.0f 秒处" % ep.hook_at)
        f.detail = ("钩子出现在预估 %.0f 秒处。短剧观众 3 秒划走，"
                    "钩子必须在 30 秒内出现，越早越好。" % ep.hook_at)
        out.append(f)


# ------------------------------------------------------------ 时长 DUR
@rule("DUR-RANGE-001", "warning", "时长", "预估时长超出 60-150 秒",
      "按“台词字数÷4.5＋动作字数÷10＋转场 2 秒/场”换算，单集宜 60-150 秒"
      "（1-2.5 分钟）。超了先砍台词，再砍场次，最后才动反转。")
def _c(ep, out):
    if ep.total_sec < 60 or ep.total_sec > 150:
        f = _mk("DUR-RANGE-001", ep.path, 1,
                "预估总时长约 %.0f 秒" % ep.total_sec)
        f.detail = ("预估总时长约 %.0f 秒，超出 60-150 秒区间。"
                    "超了先砍台词，再砍场次，最后才动反转。" % ep.total_sec)
        out.append(f)


@rule("DUR-TARGET-001", "warning", "时长", "与时长目标偏差超过 20%",
      "【时长目标】写了就要兑现：预估时长与目标偏差超过 20% 说明节奏失控。")
def _c(ep, out):
    if ep.target_sec:
        dev = abs(ep.total_sec - ep.target_sec) / ep.target_sec
        if dev > 0.20:
            f = _mk("DUR-TARGET-001", ep.path, 1,
                    "目标 %d 秒，预估约 %.0f 秒" % (ep.target_sec, ep.total_sec))
            f.detail = ("目标 %d 秒，预估约 %.0f 秒，偏差 %.0f%% 超过 20%%。"
                        % (ep.target_sec, ep.total_sec, dev * 100))
            out.append(f)


# ------------------------------------------------------------ 人物 CHAR
@rule("CHAR-UNKNOWN-001", "blocker", "人物", "台词人物未在【人物】登记",
      "台词里出现的人名必须在【人物】行登记，否则是穿帮或笔误。")
def _c(ep, out):
    known = set(ep.declared)
    seen = set()
    for name, _text, ln in ep.dialogues:
        if name and name not in known and name not in seen:
            seen.add(name)
            out.append(_mk("CHAR-UNKNOWN-001", ep.path, ln,
                           "未登记人物：%s" % name))


@rule("CHAR-IDLE-001", "warning", "人物", "登记人物全集未出场",
      "【人物】里登记了却一句台词都没有的人物：要么加戏，要么从名单删掉，"
      "酱油人物会稀释观众注意力。")
def _c(ep, out):
    spoken = set(n for n, _t, _l in ep.dialogues if n)
    for name in ep.declared:
        if name not in spoken:
            out.append(_mk("CHAR-IDLE-001", ep.path, 1,
                           "全集未出场：%s" % name))


# ------------------------------------------------------------ 台词 DIAL
@rule("DIAL-LONG-001", "warning", "台词", "单句台词超过 40 字",
      "单句台词请控制在 25 字内（审计红线 40 字）。超长台词演员念着累、"
      "观众听着困，请拆成两句或转成动作。")
def _c(ep, out):
    for name, text, ln in ep.dialogues:
        if len(text) > 40:
            out.append(_mk("DIAL-LONG-001", ep.path, ln,
                           "%s：%s（%d 字）" % (name, text[:30], len(text))))
            break  # 每文件只报一次，避免刷屏


@rule("DIAL-NOACTION-001", "warning", "台词", "某场只有台词没有动作",
      "短剧是拍给眼睛看的：整场纯台词没有动作行，等于广播剧。"
      "吵架超过 5 句必须有动作打断。")
def _c(ep, out):
    scene_line = dict(ep.scenes)
    for no in scene_line:
        if ep.scene_dialog.get(no) and not ep.scene_action.get(no):
            out.append(_mk("DIAL-NOACTION-001", ep.path, scene_line[no],
                           "第 %d 场无动作行" % no))


@rule("DIAL-ACTION-001", "warning", "台词", "动作行占比过低",
      "全集动作行占比低于 20%。“能动手的别吵吵”——"
      "把心理活动和长对白转成动作。")
def _c(ep, out):
    if ep.content_lines >= 10:
        ratio = ep.action_lines / ep.content_lines
        if ratio < 0.20:
            f = _mk("DIAL-ACTION-001", ep.path, 1,
                    "动作行 %d / 内容行 %d"
                    % (ep.action_lines, ep.content_lines))
            f.detail = ("全集动作行占比 %.0f%%，低于 20%%。“能动手的别吵吵”——"
                        "把心理活动和长对白转成动作。" % (ratio * 100))
            out.append(f)


# ------------------------------------------------------------ 场次 SCENE
@rule("SCENE-COUNT-001", "warning", "场次", "场次超过 6 场",
      "单集宜 2-4 场，超过 6 场观众情绪会被切碎。请合并场景。")
def _c(ep, out):
    if len(ep.scenes) > 6:
        out.append(_mk("SCENE-COUNT-001", ep.path, ep.scenes[-1][1],
                       "本集 %d 场" % len(ep.scenes)))


@rule("SCENE-ORDER-001", "warning", "场次", "场次编号不连续",
      "`## 第 N 场` 应从 1 连续递增，跳号多半是删场后忘了重排。")
def _c(ep, out):
    nums = sorted(n for n, _ in ep.scenes)
    if nums and nums != list(range(1, len(nums) + 1)):
        out.append(_mk("SCENE-ORDER-001", ep.path, ep.scenes[-1][1],
                       "场次编号：%s" % nums))


@rule("SCENE-LONG-001", "warning", "场次", "单场预估时长超过 60 秒",
      "单场超过 60 秒观众会觉得“这场戏怎么还不完”。请拆场或删减。")
def _c(ep, out):
    t = 0.0
    cur = None
    starts = {}
    for i, raw in enumerate(ep.lines, start=1):
        line = EXEMPT_RE.sub("", raw.strip()).strip()
        if not line:
            continue
        m = SCENE_RE.match(line)
        if m:
            if cur is not None:
                starts[cur] = (starts[cur][0], t)
            cur = int(m.group(1))
            starts[cur] = (i, 0.0)
            t = SCENE_SWITCH_SEC
            continue
        if cur is None:
            continue
        if TITLE_RE.match(line) or CHARS_RE.match(line) or TARGET_RE.match(line):
            continue
        if line.startswith("#"):
            continue
        dm = DIAL_RE.match(line)
        if dm and not line.startswith("【"):
            t += len(dm.group(2).strip()) / DIAL_CPS
        else:
            t += len(MARKER_RE.sub("", line)) / ACTION_CPS
    if cur is not None:
        starts[cur] = (starts[cur][0], t)
    for no, (ln, sec) in sorted(starts.items()):
        if sec > 60:
            out.append(_mk("SCENE-LONG-001", ep.path, ln,
                           "第 %d 场预估约 %.0f 秒" % (no, sec)))


@rule("SCENE-EMPTY-001", "warning", "场次", "空场（无台词无动作）",
      "该场没有任何台词和动作行，是忘记写内容还是删场后残留？")
def _c(ep, out):
    for no, ln in ep.scenes:
        if not ep.scene_dialog.get(no) and not ep.scene_action.get(no):
            out.append(_mk("SCENE-EMPTY-001", ep.path, ln,
                           "第 %d 场为空" % no))


# ------------------------------------------------------------ 结尾 END
@rule("END-HOOK-001", "warning", "卡点", "缺少结尾卡点",
      "单集结尾必须有【结尾卡点】：把“观众最想看的那 1 秒”留到下一集。"
      "没有卡点 = 主动放观众走。")
def _c(ep, out):
    if not ep.end_hooks:
        out.append(_mk("END-HOOK-001", ep.path, len(ep.lines),
                       "全文无【结尾卡点】"))


@rule("END-MULTI-001", "nit", "卡点", "结尾卡点出现多次",
      "【结尾卡点】有且仅有一处，卡点贵在“只卡一次、卡在最疼处”。")
def _c(ep, out):
    if len(ep.end_hooks) > 1:
        out.append(_mk("END-MULTI-001", ep.path, ep.end_hooks[1],
                       "共出现 %d 次" % len(ep.end_hooks)))


# ---------------------------------------------------------------- 运行
def audit_file(path, text):
    ep = Episode(path, text)
    findings = []
    for r in RULES:
        try:
            r["check"](ep, findings)
        except Exception:
            continue  # 单条规则出错不影响整体：fail-open
    # 豁免：warning/nit 且行号在豁免集合中 → 跳过
    kept, exempted = [], 0
    for f in findings:
        if f.severity != "blocker" and f.line in ep.exempt_lines:
            exempted += 1
            continue
        kept.append(f)
    return kept, exempted, ep


def run(target, fmt):
    files = collect(target)
    all_findings, total_exempt = [], 0
    for path, text in files:
        findings, exempted, _ep = audit_file(path, text)
        all_findings.extend(findings)
        total_exempt += exempted
    sev_rank = {"blocker": 0, "warning": 1, "nit": 2}
    all_findings.sort(key=lambda f: (sev_rank.get(f.severity, 3),
                                     f.rule_id, f.file, f.line))
    summary = {"blocker": 0, "warning": 0, "nit": 0,
               "rules_run": len(RULES), "files_scanned": len(files),
               "exempted": total_exempt}
    for f in all_findings:
        if f.severity in summary:
            summary[f.severity] += 1
    return all_findings, summary


def print_text(target, findings, summary):
    print("剧本审计报告：%s" % target)
    print("扫描文件 %d 个，规则 %d 条；blocker=%d warning=%d nit=%d（已豁免 %d）"
          % (summary["files_scanned"], summary["rules_run"],
             summary["blocker"], summary["warning"], summary["nit"],
             summary["exempted"]))
    print("-" * 60)
    if not findings:
        print("干净：未发现任何问题。")
        return
    for f in findings:
        try:
            rel = os.path.relpath(f.file, target)
        except Exception:
            rel = f.file
        print("[%s] %s %s:%d" % (f.severity.upper(), f.rule_id, rel, f.line))
        print("  %s" % f.title)
        if f.snippet:
            print("  → %s" % f.snippet)
        print("  %s" % f.detail)
        print()


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-drama-script 确定性剧本审计")
    ap.add_argument("--target", required=True, help="剧本文件目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker", help="非零退出的门限")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print("目标不是目录：%s" % args.target, file=sys.stderr)
        return 2

    findings, summary = run(target, args.format)

    if args.format == "json":
        payload = {"tool": TOOL, "version": VERSION,
                   "target": target, "summary": summary,
                   "findings": [f.to_dict() for f in findings]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(args.target, findings, summary)

    order = {"blocker": 0, "warning": 1, "nit": 2}
    threshold = order[args.fail_on]
    bad = any(order.get(f.severity, 9) <= threshold for f in findings)
    if any(f.severity == "blocker" for f in findings):
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
