import json
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .auth import validate_telegram_init_data
from .config import ADMIN_TELEGRAM_IDS
from .db import conn, init_db


app = FastAPI(
    title="Sar Morabi Sho API",
    version="1.0.0-stage1"
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "Sar Morabi Sho API",
        "stage": 1
    }


def current_user(init_data: str):
    try:
        pairs = validate_telegram_init_data(init_data)
        user = json.loads(pairs.get("user", "{}"))
        return int(user["id"]), user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def ph(c):
    return "%s" if hasattr(c, "info") else "?"


def is_admin(tid):
    return tid in ADMIN_TELEGRAM_IDS


class RoleBody(BaseModel):
    telegram_id: int


class PermissionBody(BaseModel):
    telegram_id: int
    can_report_names: bool = True
    can_view_reports: bool = False
    can_moderate: bool = False


class ReportBody(BaseModel):
    target_telegram_id: int
    target_name: Optional[str] = None
    reason: str


@app.get("/api/me")
def me(x_telegram_init_data: str = Header(default="")):
    tid, user = current_user(x_telegram_init_data)

    with conn() as c:
        p = ph(c)

        row = c.execute(
            f"""
            SELECT
                telegram_id,
                manager_name,
                team_name,
                euros,
                diamonds,
                trophies,
                manager_points
            FROM users
            WHERE telegram_id={p}
            """,
            (tid,)
        ).fetchone()

    return {
        "telegram_id": tid,
        "telegram_user": user,
        "is_admin": is_admin(tid),
        "profile": dict(row) if row else None
    }


@app.post("/api/admin/game-manager")
def set_game_manager(
    body: RoleBody,
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    if not is_admin(actor):
        raise HTTPException(403, "Admin only")

    with conn() as c:
        p = ph(c)

        c.execute(
            "DELETE FROM game_roles WHERE role='game_manager'"
        )

        c.execute(
            f"""
            INSERT INTO game_roles
            (telegram_id, role, assigned_by)
            VALUES ({p}, 'game_manager', {p})
            """,
            (body.telegram_id, actor)
        )

    return {
        "ok": True,
        "game_manager": body.telegram_id
    }


@app.delete("/api/admin/game-manager")
def remove_game_manager(
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    if not is_admin(actor):
        raise HTTPException(403, "Admin only")

    with conn() as c:
        c.execute(
            "DELETE FROM game_roles WHERE role='game_manager'"
        )

    return {"ok": True}


@app.post("/api/admin/supervisor")
def add_supervisor(
    body: RoleBody,
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    if not is_admin(actor):
        raise HTTPException(403, "Admin only")

    with conn() as c:
        p = ph(c)

        if hasattr(c, "info"):
            c.execute(
                f"""
                INSERT INTO game_roles
                (telegram_id, role, assigned_by)
                VALUES ({p}, 'supervisor', {p})
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    role='supervisor',
                    assigned_by={p}
                """,
                (body.telegram_id, actor, actor)
            )

            c.execute(
                f"""
                INSERT INTO supervisor_permissions
                (telegram_id)
                VALUES ({p})
                ON CONFLICT DO NOTHING
                """,
                (body.telegram_id,)
            )

        else:
            c.execute(
                f"""
                INSERT OR REPLACE INTO game_roles
                (telegram_id, role, assigned_by)
                VALUES ({p}, 'supervisor', {p})
                """,
                (body.telegram_id, actor)
            )

            c.execute(
                f"""
                INSERT OR IGNORE INTO supervisor_permissions
                (telegram_id)
                VALUES ({p})
                """,
                (body.telegram_id,)
            )

    return {
        "ok": True,
        "supervisor": body.telegram_id
    }


@app.delete("/api/admin/supervisor/{telegram_id}")
def remove_supervisor(
    telegram_id: int,
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    if not is_admin(actor):
        raise HTTPException(403, "Admin only")

    with conn() as c:
        p = ph(c)

        c.execute(
            f"""
            DELETE FROM game_roles
            WHERE telegram_id={p}
            AND role='supervisor'
            """,
            (telegram_id,)
        )

        c.execute(
            f"""
            DELETE FROM supervisor_permissions
            WHERE telegram_id={p}
            """,
            (telegram_id,)
        )

    return {"ok": True}


@app.post("/api/admin/supervisor-permissions")
def permissions(
    body: PermissionBody,
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    if not is_admin(actor):
        raise HTTPException(403, "Admin only")

    with conn() as c:
        p = ph(c)

        vals = (
            body.telegram_id,
            int(body.can_report_names),
            int(body.can_view_reports),
            int(body.can_moderate)
        )

        if hasattr(c, "info"):
            c.execute(
                f"""
                INSERT INTO supervisor_permissions
                (
                    telegram_id,
                    can_report_names,
                    can_view_reports,
                    can_moderate
                )
                VALUES ({p}, {p}, {p}, {p})
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    can_report_names={p},
                    can_view_reports={p},
                    can_moderate={p}
                """,
                vals + (
                    int(body.can_report_names),
                    int(body.can_view_reports),
                    int(body.can_moderate)
                )
            )

        else:
            c.execute(
                f"""
                INSERT OR REPLACE INTO supervisor_permissions
                (
                    telegram_id,
                    can_report_names,
                    can_view_reports,
                    can_moderate
                )
                VALUES ({p}, {p}, {p}, {p})
                """,
                vals
            )

    return {"ok": True}


@app.post("/api/reports")
def create_report(
    body: ReportBody,
    x_telegram_init_data: str = Header(default="")
):
    actor, _ = current_user(x_telegram_init_data)

    with conn() as c:
        p = ph(c)

        role = c.execute(
            f"""
            SELECT role
            FROM game_roles
            WHERE telegram_id={p}
            """,
            (actor,)
        ).fetchone()

        if not is_admin(actor) and not role:
            raise HTTPException(
                403,
                "Report permission required"
            )

        if hasattr(c, "info"):
            row = c.execute(
                """
                INSERT INTO moderation_reports
                (
                    reporter_telegram_id,
                    target_telegram_id,
                    target_name,
                    reason
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    actor,
                    body.target_telegram_id,
                    body.target_name,
                    body.reason
                )
            ).fetchone()

            report_id = row[0]

        else:
            cur = c.execute(
                """
                INSERT INTO moderation_reports
                (
                    reporter_telegram_id,
                    target_telegram_id,
                    target_name,
                    reason
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    actor,
                    body.target_telegram_id,
                    body.target_name,
                    body.reason
                )
            )

            report_id = cur.lastrowid

        for admin_id in ADMIN_TELEGRAM_IDS:
            c.execute(
                f"""
                INSERT INTO admin_notifications
                (
                    admin_telegram_id,
                    title,
                    body
                )
                VALUES ({p}, {p}, {p})
                """,
                (
                    admin_id,
                    "گزارش جدید",
                    f"گزارش #{report_id} برای کاربر "
                    f"{body.target_telegram_id}"
                )
            )

    return {
        "ok": True,
        "report_id": report_id
  }
