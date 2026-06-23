from __future__ import annotations

from invarianteval.mcp.list_suite import list_invariants
from invarianteval.mcp.verify import check_invariants


def create_server():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("invarianteval")

    @mcp.tool()
    def check_invariants_tool(
        model_parsed: dict,
        final_output: dict,
        suite_path: str | None = None,
        policy: dict | None = None,
        human_confirmed: dict | None = None,
        case_input: str = "",
    ) -> dict:
        """Verify declared safety invariants before finalizing structured output.

        Provide suite_path to an existing suite.yaml, or an inline policy dict with
        field_policies and assertions. Returns passed/invariant_passed and failures.
        """
        return check_invariants(
            suite_path=suite_path,
            policy=policy,
            model_parsed=model_parsed,
            final_output=final_output,
            human_confirmed=human_confirmed,
            case_input=case_input,
        )

    @mcp.tool()
    def list_invariants_tool(suite_path: str) -> dict:
        """Read-only: list field policies, equivalence classes, and per-case assertions."""
        return list_invariants(suite_path)

    return mcp


async def main() -> None:
    mcp = create_server()
    await mcp.run_stdio_async()
