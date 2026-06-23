# InvariantEval agent skill

Give a coding agent a **declared safety gate** it can run before finalizing
structured output. InvariantEval enforces rules you declare in `suite.yaml`. It
does not score accuracy, does not infer invariants, and does not rewrite output.

## Install

**Cursor** (project or personal):

```bash
cp -r agent-skill/invarianteval ~/.cursor/skills/invarianteval
```

**Claude Code**:

```bash
cp -r agent-skill/invarianteval ~/.claude/skills/invarianteval
```

From a clone of this repo, adjust the source path. Restart the agent after copying.

## Prerequisites

```bash
pip install -e ".[dev]"
```

## Quick start

1. Copy `suite.template.yaml` to your project as `suite.yaml` and declare your
   locked fields and assertions.
2. Create `data/agent-check.txt` (or any path referenced by the `agent-check` case).
3. Before finalizing model output, run:

```bash
python agent-skill/invarianteval/check.py \
  --suite suite.yaml \
  --model-parsed model.json \
  --final-output final.json
```

Exit code `0` means invariant tier passed. Non-zero means **do not finalize**.

## What this is not

- Not a general eval framework for accuracy
- Not an MCP gateway or router
- Not a system that makes the agent "correct" or self-heal violations

It only verifies declared invariants and blocks finalize on violation.

## See also

- [Main README](../../README.md)
- [MCP server](../../docs/mcp.md)
- [Fire inspection example](../../examples/fire-inspection-extraction/)
