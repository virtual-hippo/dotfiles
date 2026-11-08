#!/usr/bin/python3
# Claude Code status line (2 lines)
#  1: dir  git-branch/status  PR  worktree  session-name
#  2: model [effort]  ctx  5h/7d usage  cache  +/-lines  duration  cost
#
# 例:
#   ~/misc │  main ✓
#  󰚩 Opus 5.5 [high] │  ████░░░░░░ 42%/200k │  5h 63%(2h15m) 7d 18%(3d6h) │  91%(43m) │ +120 -8 │  38m │ ~$1.84
#  - 42%/200k: コンテキストの使用率 / 上限
#  - 5h 63%(2h15m): 5 時間枠の使用率（リセットまでの時間）。7d は 7 日枠
#  - 91%(43m): プロンプトキャッシュのヒット率（切れるまでの時間）。切れたら cold
#  - +120 -8: 追加・削除した行数。38m: 経過時間。~$1.84: 概算コスト
#  - Git: +ステージ済み ~変更 ?未追跡 !コンフリクト ↑↓ push/pull 待ち。変更なしは ✓
#
# 色: 使用率（ctx、5h/7d）は 50% 未満が緑、50% 以上が黄、80% 以上が赤
import json, os, subprocess, sys, time

try:
    d = json.load(sys.stdin)
except Exception:
    d = {}

def g(*keys):
    v = d
    for k in keys:
        if not isinstance(v, dict):
            return None
        v = v.get(k)
    return v

R, B, DIM = "\033[0m", "\033[1m", "\033[2m"
RED, GRN, YEL, BLU, MAG, CYA = (f"\033[{n}m" for n in (31, 32, 33, 34, 35, 36))
SEP = f" {DIM}│{R} "

def color(p):
    return RED if p >= 80 else YEL if p >= 50 else GRN

def bar(p, w=10):
    n = min(w, max(0, round(p / 100 * w)))
    return "█" * n + "░" * (w - n)

def dur(s):
    s = int(s)
    if s <= 0: return "0m"
    if s >= 86400: return f"{s//86400}d{s%86400//3600}h"
    if s >= 3600: return f"{s//3600}h{s%3600//60}m"
    return f"{s//60}m"

# ---------- line 1: location ----------
cwd = g("workspace", "current_dir") or g("cwd") or os.getcwd()
home = os.path.expanduser("~")
shown = "~" + cwd[len(home):] if cwd == home or cwd.startswith(home + "/") else cwd
l1 = [f"{BLU}{B} {shown}{R}"]

def git_info(path):
    try:
        out = subprocess.run(
            ["git", "-C", path, "--no-optional-locks", "status", "--porcelain=v2", "--branch"],
            capture_output=True, text=True, timeout=1.5)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    branch, ahead, behind, staged, changed, untracked, conflict = "?", 0, 0, 0, 0, 0, 0
    for line in out.stdout.splitlines():
        if line.startswith("# branch.head "):
            branch = line.split(" ", 2)[2]
        elif line.startswith("# branch.oid ") and branch == "(detached)":
            branch = line.split(" ", 2)[2][:7]
        elif line.startswith("# branch.ab "):
            a, b = line.split()[2:4]; ahead, behind = int(a), -int(b)
        elif line[:1] in "12":
            xy = line.split()[1]
            staged += xy[0] != "."; changed += xy[1] != "."
        elif line[:1] == "u": conflict += 1
        elif line[:1] == "?": untracked += 1
    s = f"{MAG} {branch}{R}"
    flags = ""
    if staged:    flags += f"{GRN}+{staged}{R}"
    if changed:   flags += f"{YEL}~{changed}{R}"
    if untracked: flags += f"{DIM}?{untracked}{R}"
    if conflict:  flags += f"{RED}!{conflict}{R}"
    if ahead:     flags += f"{CYA}↑{ahead}{R}"
    if behind:    flags += f"{CYA}↓{behind}{R}"
    if not (staged or changed or untracked or conflict): flags = f"{GRN}✓{R}" + flags
    return s + " " + flags

gi = git_info(cwd)
if gi: l1.append(gi)
wt = g("workspace", "git_worktree")
if wt: l1.append(f"{DIM} {R}{wt}")
pr = g("pr", "number")
if pr:
    st = g("pr", "review_state")
    stc = {"approved": GRN, "changes_requested": RED}.get(st, YEL)
    l1.append(f" {'!' if g('pr','kind')=='mr' else '#'}{pr}" + (f" {stc}{st}{R}" if st else ""))
if g("agent", "name"): l1.append(f"{CYA}@{g('agent','name')}{R}")
if g("session_name"): l1.append(f"{DIM}{g('session_name')}{R}")

# ---------- line 2: model & usage ----------
model = g("model", "display_name") or g("model", "id") or "?"
m = f"{CYA}{B}󰚩 {model}{R}"
if g("effort", "level"): m += f" {MAG}[{g('effort','level')}]{R}"
if g("fast_mode"): m += f" {YEL}fast{R}"
if g("vim", "mode"): m += f" {DIM}{g('vim','mode')}{R}"
l2 = [m]

ctx = g("context_window", "used_percentage")
size = g("context_window", "context_window_size")
if ctx is not None:
    sz = f"{DIM}/{int(size)//1000}k{R}" if size else ""
    l2.append(f" {color(ctx)}{bar(ctx)} {ctx:.0f}%{R}{sz}")
else:
    l2.append(f"{DIM} --{R}")

now = time.time()
usage = []
for label, key in (("5h", "five_hour"), ("7d", "seven_day")):
    p = g("rate_limits", key, "used_percentage")
    if p is None: continue
    r = g("rate_limits", key, "resets_at")
    usage.append(f"{label} {color(p)}{p:.0f}%{R}" + (f"{DIM}({dur(r-now)}){R}" if r else ""))
l2.append(f" " + (" ".join(usage) if usage else f"{DIM}--{R}"))

pc = g("prompt_cache")
if isinstance(pc, dict) and pc.get("caching_observed"):
    hr = pc.get("hit_ratio")
    hrs = f"{hr*100:.0f}%" if hr is not None else "--"
    if pc.get("warm"):
        exp = pc.get("expires_at")
        l2.append(f" {GRN}{hrs}{R}" + (f"{DIM}({dur(exp-now)}){R}" if exp else ""))
    else:
        l2.append(f" {RED}cold{R} {DIM}{hrs}{R}")

add, rem = g("cost", "total_lines_added") or 0, g("cost", "total_lines_removed") or 0
if add or rem: l2.append(f"{GRN}+{add}{R} {RED}-{rem}{R}")
ms = g("cost", "total_duration_ms")
if ms: l2.append(f"{DIM} {dur(ms/1000)}{R}")
cost = g("cost", "total_cost_usd")
if cost: l2.append(f"{DIM}~${cost:.2f}{R}")

print(SEP.join(l1))
print(SEP.join(l2))
