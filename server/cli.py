from __future__ import annotations

import typer

from server.db import SessionLocal, init_db
from server.main import seed_demo

server_app = typer.Typer(help="InvariantEval server management")


@server_app.command("init")
def server_init() -> None:
    """Initialize database and seed demo org."""
    init_db()
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()
    typer.echo("Database initialized. Demo login: admin@demo.local / admin")


@server_app.command("run")
def server_run(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    init_db()
    uvicorn.run("server.main:app", host=host, port=port, reload=False)
