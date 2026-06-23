---
name: invarianteval
description: >-
  Before finalizing structured or extracted output in a domain with declared
  safety invariants, verify the output against your invariant suite and refuse
  to ship when a locked field was model-auto-filled. Invoke when the user or
  task involves high-stakes structured extraction, compliance fields, or
  pass/fail results that humans must own.
---

# InvariantEval agent skill

InvariantEval enforces the invariants **you declare**. It does not make an agent
"correct" and it does not rewrite output for you. The only honest claim: your
agent runs your declared safety rules on every output and **refuses to finalize**
when a locked field was auto-filled without human confirmation.

## When to use this skill

Use before finalizing any structured JSON (or similar) output when:

- The domain has **declared** locked fields (pass/fail, compliance status, etc.)
- You have (or need) a `suite.yaml` with `field_policies` and invariant assertions
- A human is supposed to own certain fields and the model must not volunteer them

Do **not** use this skill to guess invariants. Your job is to make **declaring**
them frictionless, not to infer them.

## Workflow

### 1. Locate or create a declared suite

- Find an existing `suite.yaml` in the project, or
- Copy [`suite.template.yaml`](suite.template.yaml) to the project and have the
  user fill in `field_policies`, `equivalence_classes`, and `assertions`.

Never invent locked fields without user declaration in the suite.

### 2. Run the invariant check before finalize

You have the model's raw parsed output and the intended final output. Run:

```bash
python agent-skill/invarianteval/check.py \
  --suite path/to/suite.yaml \
  --case-id agent-check \
  --model-parsed /tmp/model_parsed.json \
  --final-output /tmp/final_output.json \
  --human-confirmed /tmp/human_confirmed.json
```

Write the JSON files from the current turn. `--human-confirmed` is optional
(use `{}` when nothing was explicitly confirmed).

The suite must contain a case with the given `--case-id` (default: `agent-check`)
and the assertions you want enforced.

### 3. If the check fails: STOP

- **Do not** finalize, commit, or present the output as complete.
- Surface the exact invariant failure from CLI output (e.g.
  `never_auto_filled[pass_fail_result]`).
- Require one of:
  - User edits the final output to remove or correct the violation, or
  - User explicitly confirms the field (`human_confirmed` in the fixture), or
  - User updates the declared suite if the rule was wrong (rare).

### 4. If the check passes: proceed

Finalize only after exit code `0`.

## MCP alternative

If the environment has the `[mcp]` extra installed, prefer the
`check_invariants` MCP tool for the same inputs. See [docs/mcp.md](../../docs/mcp.md).

## Honest framing (required)

- Say: "declared invariants", "refuses to finalize", "locked field auto-filled"
- Never say: "self-correct", "makes the agent correct", "auto-infer invariants"
