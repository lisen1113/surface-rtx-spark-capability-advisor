"""Local-first authentication, approval, tenant and license enforcement."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
import sqlite3

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from .catalog import connection

router = APIRouter(prefix="/api", tags=["auth"])
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16, type=Type.ID)


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat()


def audit(conn: sqlite3.Connection, action: str, *, actor=None, organization_id=None, target_type=None, target_id=None, details=None):
    conn.execute("INSERT INTO audit_logs (occurred_at,actor_user_id,organization_id,action,target_type,target_id,details_json) VALUES (?,?,?,?,?,?,?)",
                 (iso(now()), actor, organization_id, action, target_type, str(target_id) if target_id is not None else None, json.dumps(details or {}, ensure_ascii=False)))


class RegisterInput(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=256)


class LoginInput(BaseModel):
    email: str
    password: str


class LicenseInput(BaseModel):
    organization_id: int
    seats: int = Field(ge=1, le=100000)
    expires_at: datetime


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(422, "邮箱格式无效")
    return normalized


def register_user(data: RegisterInput) -> dict:
    email = _email(data.email)
    with connection() as conn:
        try:
            created = iso(now())
            org = conn.execute("INSERT INTO organizations (name,status,created_at) VALUES (?,'pending',?)", (data.organization_name.strip(), created))
            user = conn.execute("INSERT INTO users (organization_id,email,password_hash,role,status,created_at) VALUES (?,?,?,'owner','pending',?)",
                                (org.lastrowid, email, hasher.hash(data.password), created))
            audit(conn, "user.registered", actor=user.lastrowid, organization_id=org.lastrowid, target_type="user", target_id=user.lastrowid)
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, "邮箱已注册")
    return {"status": "pending_email_verification_and_admin_approval", "email": email}


def bootstrap_admin(email: str, password: str) -> int:
    """Create the first admin explicitly; no default credentials are generated."""
    normalized = _email(email)
    if len(password) < 12:
        raise ValueError("Admin password must contain at least 12 characters")
    with connection() as conn:
        if conn.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            raise ValueError("An admin already exists")
        created = iso(now())
        user = conn.execute("INSERT INTO users (organization_id,email,password_hash,role,status,email_verified,created_at,approved_at) VALUES (NULL,?,?,'admin','approved',1,?,?)",
                            (normalized, hasher.hash(password), created, created))
        audit(conn, "admin.bootstrapped", actor=user.lastrowid, target_type="user", target_id=user.lastrowid)
        conn.commit()
        return user.lastrowid


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "需要登录")
    token = authorization[7:].strip()
    with connection() as conn:
        row = conn.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>?",
                           (_token_hash(token), iso(now()))).fetchone()
    if not row:
        raise HTTPException(401, "会话无效或已过期")
    return dict(row)


def require_admin(user=Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user


def _license_check(conn: sqlite3.Connection, user: sqlite3.Row):
    if user["role"] == "admin":
        return
    license_row = conn.execute("SELECT * FROM licenses WHERE organization_id=?", (user["organization_id"],)).fetchone()
    if not license_row or license_row["status"] != "active":
        raise HTTPException(403, "组织尚未获得有效 License")
    if datetime.fromisoformat(license_row["expires_at"]) <= now():
        raise HTTPException(403, "License 已过期")
    active = conn.execute("SELECT COUNT(DISTINCT user_id) FROM sessions s JOIN users u ON u.id=s.user_id WHERE u.organization_id=? AND s.revoked_at IS NULL AND s.expires_at>?",
                          (user["organization_id"], iso(now()))).fetchone()[0]
    existing = conn.execute("SELECT 1 FROM sessions WHERE user_id=? AND revoked_at IS NULL AND expires_at>?", (user["id"], iso(now()))).fetchone()
    if not existing and active >= license_row["seats"]:
        raise HTTPException(403, "License 席位已用完")


@router.post("/auth/register", status_code=201)
def register(data: RegisterInput):
    return register_user(data)


@router.post("/auth/login")
def login(data: LoginInput):
    email = _email(data.email)
    with connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            raise HTTPException(401, "邮箱或密码错误")
        if user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > now():
            raise HTTPException(429, "登录尝试过多，请稍后再试")
        try:
            hasher.verify(user["password_hash"], data.password)
        except VerifyMismatchError:
            failures = user["failed_login_count"] + 1
            locked = iso(now() + timedelta(minutes=15)) if failures >= 5 else None
            conn.execute("UPDATE users SET failed_login_count=?,locked_until=? WHERE id=?", (failures, locked, user["id"]))
            audit(conn, "auth.login_failed", organization_id=user["organization_id"], target_type="user", target_id=user["id"])
            conn.commit()
            raise HTTPException(401, "邮箱或密码错误")
        if not user["email_verified"]:
            raise HTTPException(403, "邮箱尚未验证")
        if user["status"] != "approved":
            raise HTTPException(403, "账号等待管理员审批")
        _license_check(conn, user)
        token = secrets.token_urlsafe(32)
        expires = now() + timedelta(hours=12)
        conn.execute("UPDATE users SET failed_login_count=0,locked_until=NULL WHERE id=?", (user["id"],))
        conn.execute("INSERT INTO sessions VALUES (?,?,?,?,NULL)", (_token_hash(token), user["id"], iso(now()), iso(expires)))
        audit(conn, "auth.login_succeeded", actor=user["id"], organization_id=user["organization_id"])
        conn.commit()
    return {"access_token": token, "token_type": "bearer", "expires_at": iso(expires)}


@router.get("/auth/me")
def me(user=Depends(current_user)):
    return {key: user[key] for key in ("id", "organization_id", "email", "role", "status", "email_verified")}


@router.post("/auth/logout", status_code=204)
def logout(authorization: str = Header(), user=Depends(current_user)):
    token = authorization[7:].strip()
    with connection() as conn:
        conn.execute("UPDATE sessions SET revoked_at=? WHERE token_hash=?", (iso(now()), _token_hash(token)))
        audit(conn, "auth.logout", actor=user["id"], organization_id=user["organization_id"])
        conn.commit()


@router.post("/admin/users/{user_id}/verify-email")
def verify_email(user_id: int, admin=Depends(require_admin)):
    with connection() as conn:
        target = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not target: raise HTTPException(404, "用户不存在")
        conn.execute("UPDATE users SET email_verified=1 WHERE id=?", (user_id,))
        audit(conn, "user.email_verified", actor=admin["id"], organization_id=target["organization_id"], target_type="user", target_id=user_id)
        conn.commit()
    return {"status": "verified"}


@router.post("/admin/users/{user_id}/approve")
def approve_user(user_id: int, admin=Depends(require_admin)):
    with connection() as conn:
        target = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not target: raise HTTPException(404, "用户不存在")
        if not target["email_verified"]: raise HTTPException(409, "必须先验证邮箱")
        approved = iso(now())
        conn.execute("UPDATE users SET status='approved',approved_at=? WHERE id=?", (approved, user_id))
        conn.execute("UPDATE organizations SET status='approved' WHERE id=?", (target["organization_id"],))
        audit(conn, "user.approved", actor=admin["id"], organization_id=target["organization_id"], target_type="user", target_id=user_id)
        conn.commit()
    return {"status": "approved"}


@router.put("/admin/licenses")
def set_license(data: LicenseInput, admin=Depends(require_admin)):
    if data.expires_at <= now(): raise HTTPException(422, "License 到期时间必须在未来")
    with connection() as conn:
        if not conn.execute("SELECT 1 FROM organizations WHERE id=?", (data.organization_id,)).fetchone(): raise HTTPException(404, "组织不存在")
        conn.execute("INSERT OR REPLACE INTO licenses VALUES (?,?,?,'active',?)", (data.organization_id, data.seats, iso(data.expires_at), iso(now())))
        audit(conn, "license.updated", actor=admin["id"], organization_id=data.organization_id, target_type="license", target_id=data.organization_id, details={"seats": data.seats, "expires_at": iso(data.expires_at)})
        conn.commit()
    return {"status": "active", "organization_id": data.organization_id, "seats": data.seats, "expires_at": iso(data.expires_at)}


@router.get("/admin/users")
def list_users(status: str | None = None, admin=Depends(require_admin)):
    with connection() as conn:
        sql = "SELECT id,organization_id,email,role,status,email_verified,created_at,approved_at FROM users"
        params = ()
        if status:
            sql += " WHERE status=?"
            params = (status,)
        items = [dict(row) for row in conn.execute(sql + " ORDER BY created_at DESC", params)]
    return {"items": items}


@router.get("/admin/licenses")
def list_licenses(admin=Depends(require_admin)):
    with connection() as conn:
        items = [dict(row) for row in conn.execute("SELECT l.*,o.name AS organization_name FROM licenses l JOIN organizations o ON o.id=l.organization_id ORDER BY o.name")]
    return {"items": items}


@router.get("/admin/audit")
def list_audit(limit: int = 100, admin=Depends(require_admin)):
    limit = min(max(limit, 1), 500)
    with connection() as conn:
        items = [dict(row) for row in conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))]
    return {"items": items}
