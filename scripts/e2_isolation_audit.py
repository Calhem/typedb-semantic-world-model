"""LABS-1.065: audit the isolation of E2 author and verifier sessions from their own transcripts.

Every tool call a session made is checked:
- file tools (Read, Write, Edit, Glob, Grep, NotebookEdit): the path must lie inside the session's work directory, or
  be a persisted tool-result file that the same session's own earlier tool output named (the harness saves large
  outputs there);
- Bash: every absolute path in the command must lie inside the work directory (system interpreters and /dev/null
  allowed); commands touching version control, package managers, databases, containers, the home directory or a
  parent directory are flagged;
- tools that reach outside (Agent, WebFetch, WebSearch, Skill, MCP tools) are flagged.

    python3 -I scripts/e2_isolation_audit.py <roles.json> > audit.json
    roles.json: {"<role>": {"transcript": "<path>.jsonl", "workdir": "<path>"}}

The output names paths relative to each work directory, so it can be committed without local paths.
"""
import json
import os
import re
import sys
from pathlib import Path

FILE_TOOLS = {"Read": "file_path", "Write": "file_path", "Edit": "file_path", "NotebookEdit": "notebook_path",
              "Glob": "path", "Grep": "path"}
ALLOWED_TOOLS = set(FILE_TOOLS) | {"Bash", "ToolSearch", "TodoWrite", "mcp__ccd_turn__update_plan",
                                   "SubagentHandback"}       # the harness's own reply-to-parent tool
ROOTS = r"(Users|private|tmp|var|etc|opt|home|Volumes|System|Library|usr|bin|sbin|dev|proc)"
SYSTEM = re.compile(r"^/(usr|bin|opt/homebrew/bin|dev/null|tmp/[^ ]*\.py$)")
FORBIDDEN_CMD = re.compile(r"(^|[\s;&|(])(git|uv|pip3?|typedb|docker|curl|wget|ssh|sudo)\b|~/|\$HOME|\bfind /|\bls /")


def tool_calls(transcript):
    for line in open(transcript):
        d = json.loads(line)
        content = (d.get("message") or {}).get("content")
        if isinstance(content, list):
            for x in content:
                yield x


def audit(role, transcript, workdir):
    wd = str(Path(workdir).resolve()).replace("/private/tmp", "/tmp")
    own_results, calls, issues = set(), {}, []

    def inside(p):
        q = os.path.normpath(str(p)).replace("/private/tmp", "/tmp")
        return q == wd or q.startswith(wd + "/")
    for x in tool_calls(transcript):
        if x.get("type") == "tool_result":
            own_results |= set(re.findall(r"tool-results/[A-Za-z0-9_.-]+", json.dumps(x.get("content"))))
            continue
        if x.get("type") != "tool_use":
            continue
        name, inp = x["name"], x.get("input") or {}
        calls[name] = calls.get(name, 0) + 1
        if name not in ALLOWED_TOOLS:
            issues.append({"tool": name, "why": "tool not allowed for an isolated session"})
            continue
        if name in FILE_TOOLS:
            p = inp.get(FILE_TOOLS[name])
            if p is None and name in ("Glob", "Grep"):
                issues.append({"tool": name, "why": "no path (searches the session's cwd, outside the work directory)"})
            elif p is not None and not inside(p):
                tr = re.search(r"tool-results/[A-Za-z0-9_.-]+$", p)
                if not (tr and tr.group(0) in own_results and name == "Read"):
                    issues.append({"tool": name, "path": p, "why": "outside the work directory"})
        if name == "Bash":
            cmd = inp.get("command", "")
            for p in re.findall(r"(?<![\w./])(/" + ROOTS + r"(?:/[^\s'\"|;&)<>]*)?)", cmd):
                p = (p[0] if isinstance(p, tuple) else p).rstrip(":,.;")
                if not inside(p) and not SYSTEM.match(p):
                    issues.append({"tool": "Bash", "path": p, "why": "absolute path outside the work directory"})
            bare = cmd.replace(str(Path(workdir)), "WORK").replace(wd, "WORK")
            # shell structure only: drop heredoc bodies and quoted strings (program text and data written to files)
            shell = re.sub(r"<<-?\s*'?\"?(\w+)'?\"?.*?\n\1\b", "<<HEREDOC", bare, flags=re.S)
            shell = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", shell)
            # relative escapes: two levels up, `cd ..`, or one level up from the work directory's root
            if re.search(r"\.\./\.\.|(^|[\s;&|(])cd \.\.(/|\s|$)|cd WORK\s*(&&|;)[^;&|]*?(\s|^)\.\./", bare):
                issues.append({"tool": "Bash", "command": cmd[:300], "why": "relative path may leave the work directory"})
            if FORBIDDEN_CMD.search(shell):
                issues.append({"tool": "Bash", "command": cmd[:300], "why": "command reaches outside the pack"})
    scrub = lambda s: s.replace(wd, "<work>").replace(str(Path(workdir)), "<work>")
    return {"role": role, "tool_calls": calls, "issues": json.loads(scrub(json.dumps(issues))),
            "isolated": not issues}


def main():
    roles = json.loads(Path(sys.argv[1]).read_text())
    out = [audit(r, v["transcript"], v["workdir"]) for r, v in roles.items()]
    print(json.dumps(out, indent=1))
    return 0 if all(o["isolated"] for o in out) else 1


if __name__ == "__main__":
    sys.exit(main())
