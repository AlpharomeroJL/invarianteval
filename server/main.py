from __future__ import annotations

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from invarianteval.core.runner import Runner
from invarianteval.core.suite import load_suite
from invarianteval.ingest.otel import ingest_otel_file
from invarianteval.providers.fixture import FixtureProvider
from server.auth_password import hash_password, verify_password
from server.db import (
    ApiKey,
    Membership,
    OnlineEvalConfig,
    OnlineEvalQueue,
    Organization,
    RunRecord,
    SuiteRecord,
    User,
    get_db,
    init_db,
)

SECRET = os.environ.get("INVARIANTEVAL_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"

app = FastAPI(title="InvariantEval API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str


class RunRequest(BaseModel):
    suite_path: str
    fixtures_path: str


class OnlineSampleRequest(BaseModel):
    suite_name: str
    fixture: dict


class AuthContext(BaseModel):
    user_id: int
    org_id: int
    role: str


def create_token(user_id: int, org_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "org_id": org_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def get_auth(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> AuthContext:
    if x_api_key:
        key_hash = _hash_key(x_api_key)
        record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if not record:
            raise HTTPException(401, "Invalid API key")
        membership = (
            db.query(Membership)
            .filter(Membership.org_id == record.org_id)
            .first()
        )
        role = membership.role if membership else "viewer"
        return AuthContext(user_id=0, org_id=record.org_id, role=role)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return AuthContext(
            user_id=int(payload["sub"]),
            org_id=int(payload["org_id"]),
            role=str(payload["role"]),
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, "Invalid token") from exc


def require_role(auth: AuthContext, min_role: str) -> None:
    order = {"viewer": 0, "editor": 1, "admin": 2}
    if order.get(auth.role, -1) < order.get(min_role, 99):
        raise HTTPException(403, "Insufficient permissions")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not membership:
        raise HTTPException(403, "No organization membership")
    token = create_token(user.id, membership.org_id, membership.role)
    return {"access_token": token, "role": membership.role}


@app.get("/runs")
def list_runs(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> list:
    rows = (
        db.query(RunRecord)
        .filter(RunRecord.org_id == auth.org_id)
        .order_by(RunRecord.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "run_id": r.run_id,
            "suite_name": r.suite_name,
            "passed_cases": r.passed_cases,
            "total_cases": r.total_cases,
            "invariant_failures": r.invariant_failures,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@app.get("/runs/{run_id}")
def get_run(run_id: str, auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(RunRecord)
        .filter(RunRecord.org_id == auth.org_id, RunRecord.run_id == run_id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Run not found")
    return row.payload


@app.post("/runs")
def create_run(
    body: RunRequest,
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
) -> dict:
    require_role(auth, "editor")
    suite = load_suite(Path(body.suite_path))
    provider = FixtureProvider(Path(body.fixtures_path))
    run = Runner(suite, provider, provider_mode="fixture").run()
    record = RunRecord(
        org_id=auth.org_id,
        suite_name=run.suite_name,
        run_id=run.run_id,
        provider_mode=run.provider_mode,
        payload=run.model_dump(),
        invariant_failures=run.summary.metrics.invariant_failures if run.summary else 0,
        passed_cases=run.summary.metrics.passed_cases if run.summary else 0,
        total_cases=run.summary.metrics.total_cases if run.summary else 0,
    )
    db.add(record)
    db.commit()
    return {"run_id": run.run_id, "invariant_failures": record.invariant_failures}


@app.get("/baselines/{suite_name}")
def get_baseline(suite_name: str, auth: AuthContext = Depends(get_auth)) -> dict:
    baseline_path = Path(f"examples/{suite_name}/baseline.json")
    if not baseline_path.exists():
        baseline_path = Path("examples/fire-inspection-extraction/baseline.json")
    if not baseline_path.exists():
        raise HTTPException(404, "Baseline not found")
    import json

    return json.loads(baseline_path.read_text(encoding="utf-8"))


@app.get("/suites/{suite_id}")
def get_suite(suite_id: int, auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(SuiteRecord)
        .filter(SuiteRecord.org_id == auth.org_id, SuiteRecord.id == suite_id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Suite not found")
    return {"id": row.id, "name": row.name, "yaml_content": row.yaml_content}


@app.get("/suites")
def list_suites(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> list:
    rows = db.query(SuiteRecord).filter(SuiteRecord.org_id == auth.org_id).all()
    return [{"id": s.id, "name": s.name, "updated_at": s.updated_at.isoformat()} for s in rows]


class SuiteUpsert(BaseModel):
    name: str
    yaml_content: str


@app.post("/suites")
def upsert_suite(
    body: SuiteUpsert,
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
) -> dict:
    require_role(auth, "editor")
    row = (
        db.query(SuiteRecord)
        .filter(SuiteRecord.org_id == auth.org_id, SuiteRecord.name == body.name)
        .first()
    )
    if row:
        row.yaml_content = body.yaml_content
        row.updated_at = datetime.now(UTC)
    else:
        row = SuiteRecord(org_id=auth.org_id, name=body.name, yaml_content=body.yaml_content)
        db.add(row)
    db.commit()
    return {"id": row.id, "name": row.name}


@app.post("/ingest/otel")
async def ingest_otel(
    file: UploadFile,
    out_dir: str,
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
) -> dict:
    require_role(auth, "editor")
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    out = Path(out_dir)
    case_ids = ingest_otel_file(tmp_path, out)
    tmp_path.unlink(missing_ok=True)
    return {"case_ids": case_ids, "out_dir": str(out)}


@app.post("/online/sample")
def online_sample(
    body: OnlineSampleRequest,
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
) -> dict:
    require_role(auth, "editor")
    import random

    config = db.query(OnlineEvalConfig).filter(OnlineEvalConfig.org_id == auth.org_id).first()
    rate = config.sample_rate if config else 0.05
    if random.random() > rate:
        return {"sampled": False}
    item = OnlineEvalQueue(
        org_id=auth.org_id,
        suite_name=body.suite_name,
        fixture_payload=body.fixture,
    )
    db.add(item)
    db.commit()
    return {"sampled": True, "queue_id": item.id}


@app.get("/online/alerts")
def online_alerts(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> dict:
    config = db.query(OnlineEvalConfig).filter(OnlineEvalConfig.org_id == auth.org_id).first()
    threshold = config.alert_threshold if config else 3
    recent = (
        db.query(OnlineEvalQueue)
        .filter(
            OnlineEvalQueue.org_id == auth.org_id,
            OnlineEvalQueue.processed == True,  # noqa: E712
            OnlineEvalQueue.invariant_failed == True,  # noqa: E712
        )
        .order_by(OnlineEvalQueue.created_at.desc())
        .limit(threshold * 2)
        .all()
    )
    failures = [r for r in recent if r.invariant_failed]
    alert = len(failures) >= threshold
    return {
        "alert": alert,
        "failure_count": len(failures),
        "threshold": threshold,
        "recent": [
            {"id": r.id, "detail": r.result_detail, "at": r.created_at.isoformat()}
            for r in failures[:10]
        ],
    }


@app.get("/members")
def list_members(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)) -> list:
    require_role(auth, "admin")
    rows = db.query(Membership).filter(Membership.org_id == auth.org_id).all()
    return [{"user_id": m.user_id, "role": m.role} for m in rows]


class ApiKeyCreate(BaseModel):
    name: str


@app.post("/api-keys")
def create_api_key(
    body: ApiKeyCreate,
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
) -> dict:
    require_role(auth, "admin")
    raw_key = secrets.token_urlsafe(32)
    record = ApiKey(org_id=auth.org_id, name=body.name, key_hash=_hash_key(raw_key))
    db.add(record)
    db.commit()
    return {"name": body.name, "api_key": raw_key}


def seed_demo(db: Session) -> None:
    if db.query(Organization).first():
        return
    org = Organization(name="demo")
    db.add(org)
    db.flush()
    user = User(email="admin@demo.local", password_hash=hash_password("admin"))
    db.add(user)
    db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role="admin"))
    db.add(OnlineEvalConfig(org_id=org.id, sample_rate=1.0, alert_threshold=3))
    db.commit()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}
