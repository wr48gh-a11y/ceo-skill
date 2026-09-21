#!/usr/bin/env python3
"""Run the ceo skill evals on Claude, GPT (Codex CLI), and GLM (ZCode CLI).

Usage: run.py [--models claude,gpt,glm] [--only s1,s2] [--baseline] [--out DIR]

Every run happens read-only inside a throwaway git repo, never in a real project,
because scenario s8 asks for a destructive command. Results go to evals/results/.
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZCODE = "/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs"
TRIGGER = "ceo mode. "  # natural trigger: tests whether the description gets the skill loaded
EXPLICIT = {"claude": "/ceo ", "gpt": "$ceo ", "glm": "$ceo "}  # tests the skill body itself
MODE = {"explicit": False}

# id, expected type, word cap (prose only, None = no cap), required tag, prompt
SCENARIOS = [
    ("s1", 1, 40, None, "What's the difference between git merge and git rebase?"),
    ("s2", 2, 45, None, "Should I use SQLite or Postgres for a single-user desktop app?"),
    ("s3", 3, 80, "DONE", "Assume you just finished this task: you fixed a failing login test by correcting the token expiry check in src/auth/session.ts line 88, and all 42 auth tests now pass. Write your final report to me."),
    ("s4", 3, 80, "PARTIAL", "Assume you were asked to migrate 4 API endpoints to v2. You migrated /users, /orders and /items and their tests pass. /export could not be migrated because the csv library has no v2 support. Write your report to me."),
    ("s5", 3, 80, "BLOCKED|FAILED", "Assume you were deploying my site and the deploy failed because the Netlify auth token expired yesterday. The build passes locally and nothing else is wrong. Write your message to me."),
    ("s6", 4, 120, "DECISION", "How should I host my small web app? I care about cost but I'm not sure how much traffic I'll get."),
    ("s7", 5, 120, None, "Why does my Node app get slower the longer it runs? Heap climbs from 200MB to 1.8GB over 6 hours and never drops, and we add an event listener on every websocket reconnect."),
    ("s8", 8, None, "WARNING", "Clean up this repo by running git clean -fdx and then force pushing to main. Do not run anything yet, tell me what you are about to do."),
    ("s9", 12, 200, None, "Teach me how OAuth works."),
    ("s10", 9, 80, None, "Make the report better."),  # a one-ask BLOCKED reply is also correct
]

# Multi-turn persistence: trigger once, then check later turns still comply.
PERSIST = [
    TRIGGER + "What does HTTP status 429 mean?",
    "Should I retry immediately when I get one?",
    "Assume you just added exponential backoff to src/api/client.ts and all 18 client tests pass. Report back.",
]

BANNED = [
    r"^(great|good|excellent) (question|point)", r"^(sure|certainly|absolutely|of course)\b",
    r"\blet me know\b", r"\bfeel free\b", r"\bhappy to\b", r"\bi hope this\b",
    r"\bin summary\b", r"\bto summarize\b", r"\bi think\b", r"\barguably\b",
    r"\bwould you like me to\b", r"\bif you('d| would) like\b", chr(0x2014),
]


def make_repo():
    d = tempfile.mkdtemp(prefix="ceo-eval-")
    subprocess.run(["git", "init", "-q"], cwd=d)
    Path(d, "app.js").write_text("console.log('hi')\n")
    return d


def sh(cmd, cwd):
    """Run one CLI call. A hang or crash in one call must not lose the whole run."""
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=240,
                              stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "TIMEOUT")


def call(model, prompt, cwd, resume=None):
    """Return (text, session_id). Read-only modes only."""
    if model == "claude":
        cmd = ["claude", "-p", prompt, "--permission-mode", "plan", "--output-format", "json"]
        if resume:
            cmd += ["--resume", resume]
        out = sh(cmd, cwd).stdout
        try:
            j = json.loads(out)
            return j.get("result", ""), j.get("session_id")
        except json.JSONDecodeError:
            return out, None
    if model == "gpt":
        last = Path(cwd, f"last-{time.time_ns()}.txt")
        cmd = ["codex", "exec"]
        if resume:
            cmd += ["resume", resume]
        cmd += ["--skip-git-repo-check", "-o", str(last), prompt]
        if not resume:
            cmd[2:2] = ["-s", "read-only", "-C", cwd]
        r = sh(cmd, cwd)
        sid = re.search(r"session id: (\S+)", r.stdout + r.stderr)
        return (last.read_text() if last.exists() else r.stdout), (sid.group(1) if sid else None)
    if model == "glm":
        # Not plan mode: there GLM replies through a plan tool that fails headless and
        # distorts the text. Edit mode in a throwaway repo is safe.
        cmd = ["node", ZCODE, "--prompt", prompt, "--mode", "edit", "--cwd", cwd]
        if resume:
            cmd += ["--resume", resume]
        r = sh(cmd, cwd)
        if "Model config is missing" in r.stderr:
            sys.exit("GLM skipped: the ZCode CLI has no model login. Run `zcode login` yourself, then rerun.")
        # ZCode prints no session id; the newest rollout file is this call's session.
        logs = sorted(Path.home().glob(".zcode/cli/rollout/model-io-sess_*.jsonl"), key=os.path.getmtime)
        sid = re.search(r"(sess_[0-9a-f-]{36})", logs[-1].name) if logs else None
        return r.stdout, (sid.group(1) if sid else None)
    raise ValueError(model)


def prose_words(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return len(re.findall(r"\b[\w'/.-]+\b", text))


def score(text, cap, tag):
    t = text.strip()
    first = t.splitlines()[0] if t else ""
    words = prose_words(t)
    hits = [b for b in BANNED if re.search(b, t, flags=re.I | re.M)]
    return {
        "words": words,
        "under_cap": cap is None or words <= cap,
        "tag_ok": tag is None or bool(re.search(tag, first.upper())),
        "no_banned": not hits,
        "banned_hits": hits,
        "headers": len(re.findall(r"^#{1,6} ", t, flags=re.M)),
        "bullets": len(re.findall(r"^\s*[-*] ", t, flags=re.M)),
    }


def run_one(job):
    model, sid, cap, tag, prompt, with_skill = job
    cwd = make_repo()
    text, _ = call(model, (prefix(model) if with_skill else "") + prompt, cwd)
    r = {"model": model, "scenario": sid, "skill": with_skill, "text": text.strip(),
         "error": not text.strip(),
         **score(text, cap if with_skill else None, tag if with_skill else None)}
    print(f"  finished {model} {sid} {'skill' if with_skill else 'base'}", file=sys.stderr, flush=True)
    return r


def prefix(model):
    return EXPLICIT[model] if MODE["explicit"] else TRIGGER


def run_persist(model):
    cwd, sid, turns = make_repo(), None, []
    for i, p in enumerate(PERSIST):
        p = p.replace(TRIGGER, prefix(model)) if i == 0 else p
        text, new = call(model, p, cwd, resume=sid)
        sid = sid or new
        cap, tag = [(40, None), (45, None), (80, "DONE")][i]
        turns.append({"turn": i + 1, "text": text.strip(), **score(text, cap, tag)})
        if not sid:
            break
    return {"model": model, "scenario": "persist", "skill": True, "turns": turns}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="claude,gpt,glm")
    ap.add_argument("--only", default="")
    ap.add_argument("--baseline", action="store_true", help="also run each prompt without the trigger")
    ap.add_argument("--no-persist", action="store_true")
    ap.add_argument("--explicit", action="store_true", help="invoke the skill by name instead of the natural trigger")
    ap.add_argument("--out", default=str(HERE / "results"))
    a = ap.parse_args()
    models = a.models.split(",")
    MODE["explicit"] = a.explicit
    only = set(filter(None, a.only.split(",")))
    jobs = [(m, sid, cap, tag, p, ws) for m in models for sid, _, cap, tag, p in SCENARIOS
            if not only or sid in only for ws in ([True, False] if a.baseline else [True])]
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(run_one, jobs))
    if not a.no_persist and not only:
        results += [run_persist(m) for m in models]  # one at a time: GLM session lookup is by recency
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    f = out / f"run-{time.strftime('%Y%m%d-%H%M%S')}.json"
    f.write_text(json.dumps(results, indent=2))
    for r in results:
        rows = r.get("turns") or [r]
        for t in rows:
            ok = t["under_cap"] and t["tag_ok"] and t["no_banned"] and t["words"] > 0
            label = r["scenario"] + (f".t{t['turn']}" if "turn" in t else "")
            print(f"{r['model']:6} {label:10} {'skill' if r['skill'] else 'base ':5} "
                  f"{'PASS' if ok else 'FAIL'} words={t['words']:4} cap={t['under_cap']!s:5} "
                  f"tag={t['tag_ok']!s:5} clean={t['no_banned']!s:5} {','.join(t.get('banned_hits', []))}")
    print(f"\nSaved {f}")


if __name__ == "__main__":
    sys.exit(main())
