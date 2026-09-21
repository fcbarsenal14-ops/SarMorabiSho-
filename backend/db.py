import os
import sqlite3
from contextlib import contextmanager
from .config import DATABASE_URL

SQLITE_PATH = os.getenv("SQLITE_PATH", "/tmp/sarmorabisho.db")

SQLITE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 telegram_id INTEGER PRIMARY KEY, manager_name TEXT NOT NULL,
 team_name TEXT UNIQUE NOT NULL, manager_photo TEXT, team_logo TEXT,
 euros INTEGER NOT NULL DEFAULT 0, diamonds INTEGER NOT NULL DEFAULT 0,
 trophies INTEGER NOT NULL DEFAULT 0, manager_points INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS game_roles (
 telegram_id INTEGER PRIMARY KEY, role TEXT NOT NULL,
 assigned_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS supervisor_permissions (
 telegram_id INTEGER PRIMARY KEY, can_report_names INTEGER NOT NULL DEFAULT 1,
 can_view_reports INTEGER NOT NULL DEFAULT 0, can_moderate INTEGER NOT NULL DEFAULT 0,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS moderation_reports (
 id INTEGER PRIMARY KEY AUTOINCREMENT, reporter_telegram_id INTEGER NOT NULL,
 target_telegram_id INTEGER NOT NULL, target_name TEXT, reason TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_notifications (
 id INTEGER PRIMARY KEY AUTOINCREMENT, admin_telegram_id INTEGER NOT NULL,
 title TEXT NOT NULL, body TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_actions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, actor_telegram_id INTEGER NOT NULL,
 action TEXT NOT NULL, target_telegram_id INTEGER, details TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
'''

PG_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 telegram_id BIGINT PRIMARY KEY, manager_name TEXT NOT NULL,
 team_name TEXT UNIQUE NOT NULL, manager_photo TEXT, team_logo TEXT,
 euros BIGINT NOT NULL DEFAULT 0, diamonds BIGINT NOT NULL DEFAULT 0,
 trophies INTEGER NOT NULL DEFAULT 0, manager_points INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS game_roles (
 telegram_id BIGINT PRIMARY KEY, role TEXT NOT NULL,
 assigned_by BIGINT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS supervisor_permissions (
 telegram_id BIGINT PRIMARY KEY, can_report_names INTEGER NOT NULL DEFAULT 1,
 can_view_reports INTEGER NOT NULL DEFAULT 0, can_moderate INTEGER NOT NULL DEFAULT 0,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS moderation_reports (
 id BIGSERIAL PRIMARY KEY, reporter_telegram_id BIGINT NOT NULL,
 target_telegram_id BIGINT NOT NULL, target_name TEXT, reason TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_notifications (
 id BIGSERIAL PRIMARY KEY, admin_telegram_id BIGINT NOT NULL,
 title TEXT NOT NULL, body TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_actions (
 id BIGSERIAL PRIMARY KEY, actor_telegram_id BIGINT NOT NULL,
 action TEXT NOT NULL, target_telegram_id BIGINT, details TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
'''

@contextmanager
def conn():
    if DATABASE_URL:
        import psycopg
        c = psycopg.connect(DATABASE_URL)
        try:
            yield c
            c.commit()
        finally:
            c.close()
    else:
        c = sqlite3.connect(SQLITE_PATH)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

def init_db():
    with conn() as c:
        schema = PG_SCHEMA if DATABASE_URL else SQLITE_SCHEMA
        for stmt in schema.split(";"):
            stmt = stmt.strip()
            if stmt:
                c.execute(stmt)
