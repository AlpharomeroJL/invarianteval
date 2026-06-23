# MCP server for InvariantEval

Thin stdio MCP server that runs your **declared** safety invariants against raw model output and an intended final output. It does not infer rules, rewrite output, or call a live model.

## Install

```bash
pip install -e ".[mcp]"
```

## Register in Cursor or Claude Desktop

Add to your MCP config (`mcp.json`):

```json
{
  "mcpServers": {
    "invarianteval": {
      "command": "invarianteval-mcp"
    }
  }
}
```

If the command is not on PATH, use the full path to your venv:

```json
{
  "mcpServers": {
    "invarianteval": {
      "command": "/path/to/venv/bin/invarianteval-mcp"
    }
  }
}
```

On Windows, point `command` at `Scripts\invarianteval-mcp.exe` inside your virtual environment.

## Tools

### `check_invariants` (primary)

Verifies invariant-tier assertions before you finalize structured output.

**Inputs:**

| Field | Required | Description |
|-------|----------|-------------|
| `model_parsed` | yes | Raw parsed model output (dict) |
| `final_output` | yes | Intended final output (dict) |
| `suite_path` | one of | Path to `suite.yaml` |
| `policy` | one of | Inline policy dict (`field_policies`, `assertions`, optional `equivalence_classes`, `schema_file`) |
| `human_confirmed` | no | Map of field names to confirmation flags |
| `case_input` | no | Source text for grounded `schema_faithful` checks |

**Returns:** `{ "passed", "invariant_passed", "failures": [{ "name", "detail", "tier" }] }`

### `list_invariants` (read-only)

Lists `field_policies`, `equivalence_classes`, and per-case assertion specs from a suite file.

## Example: fire inspection `panel-001`

Good output (passes `never_auto_filled` on `pass_fail_result`):

```json
{
  "suite_path": "examples/fire-inspection-extraction/suite.yaml",
  "model_parsed": {
    "panel_model": "ABC-100",
    "devices": [
      { "device_id": "101", "model_family": "XF-200" },
      { "device_id": "102", "model_family": "XF-200" }
    ],
    "notes": "Routine quarterly check."
  },
  "final_output": {
    "panel_model": "ABC-100",
    "device_status": "operational",
    "devices": [
      { "device_id": "101", "model_family": "XF-200" },
      { "device_id": "102", "model_family": "XF-200" }
    ],
    "notes": "Routine quarterly check."
  },
  "human_confirmed": {}
}
```

Regressed output (model volunteered `pass_fail_result` on a locked field):

```json
{
  "suite_path": "examples/fire-inspection-extraction/suite.yaml",
  "model_parsed": {
    "panel_model": "ABC-100",
    "pass_fail_result": "pass",
    "devices": [
      { "device_id": "101", "model_family": "XF-200" },
      { "device_id": "102", "model_family": "XF-200" }
    ],
    "notes": "Routine quarterly check."
  },
  "final_output": {
    "panel_model": "ABC-100",
    "device_status": "operational",
    "pass_fail_result": "pass",
    "devices": [
      { "device_id": "101", "model_family": "XF-200" },
      { "device_id": "102", "model_family": "XF-200" }
    ],
    "notes": "Routine quarterly check."
  },
  "human_confirmed": {}
}
```

The regressed call should return `passed: false` with a failure on `never_auto_filled[pass_fail_result]`.

## Positioning

InvariantEval enforces **your declared** invariants. The caller passes raw model output and the intended final output; the tool derives provenance and flags when a locked field was model-auto-filled. It refuses to treat the output as safe when invariants fail. It does not make the agent correct or self-heal violations.

## Agent skill

For Cursor or Claude Code without MCP, copy `agent-skill/invarianteval` to your skills folder. See [agent-skill/invarianteval/README.md](../agent-skill/invarianteval/README.md).
