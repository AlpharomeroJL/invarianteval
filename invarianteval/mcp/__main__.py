from __future__ import annotations

import asyncio

from invarianteval.mcp.server import main as async_main


def main() -> None:
    asyncio.run(async_main())
