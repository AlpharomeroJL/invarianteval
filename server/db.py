from __future__ import annotations

import os
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = os.environ.get("INVARIANTEVAL_DB", "invarianteval.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Membership(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # viewer, editor, admin


class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class SuiteRecord(Base):
    __tablename__ = "suites"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(200), nullable=False)
    yaml_content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))


class RunRecord(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    suite_name = Column(String(200), nullable=False)
    run_id = Column(String(50), unique=True, nullable=False)
    provider_mode = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    invariant_failures = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    total_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class OnlineEvalQueue(Base):
    __tablename__ = "online_eval_queue"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    fixture_payload = Column(JSON, nullable=False)
    suite_name = Column(String(200), nullable=False)
    processed = Column(Boolean, default=False)
    invariant_failed = Column(Boolean, default=False)
    result_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class OnlineEvalConfig(Base):
    __tablename__ = "online_eval_config"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), unique=True, nullable=False)
    sample_rate = Column(Float, default=0.05)
    mode = Column(String(20), default="warn")
    alert_threshold = Column(Integer, default=3)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
