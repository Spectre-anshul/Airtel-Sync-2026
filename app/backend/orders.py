"""Orders + tracker (SQLite). Stage dates are planned from the bundle's install days."""
from __future__ import annotations

import datetime as dt
import json
import secrets
import sqlite3
from contextlib import closing

from .config import RUNTIME_DIR, TODAY
from .privacy import mask_gstin, mask_name

DB = RUNTIME_DIR / "orders.db"
STAGES = ["placed", "kyc_verified", "slot_booked", "engineer_assigned", "installed", "live"]


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, created TEXT, business TEXT, contact_masked TEXT, gstin_masked TEXT,
        bundle_name TEXT, totals TEXT, items TEXT, kyc_verdict TEXT, stage INTEGER, plan TEXT,
        consent_id TEXT, consent_withdrawn INTEGER DEFAULT 0, lang TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS consents (
        id TEXT PRIMARY KEY, created TEXT, purpose TEXT, fields TEXT, lang TEXT, withdrawn TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS handoffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, kind TEXT, business TEXT, detail TEXT)""")
    return c


def _plan(start: dt.date, install_days: int, kyc_ok: bool) -> list[str]:
    d0 = start
    kyc = d0 if kyc_ok else d0 + dt.timedelta(days=1)
    slot = kyc + dt.timedelta(days=1)
    eng = slot + dt.timedelta(days=max(1, install_days // 2))
    inst = d0 + dt.timedelta(days=max(install_days, (eng - d0).days + 1))
    live = inst + dt.timedelta(days=1)
    return [d.isoformat() for d in (d0, kyc, slot, eng, inst, live)]


def record_consent(purpose: str, fields: list[str], lang: str) -> str:
    cid = "C-" + secrets.token_hex(4).upper()
    with closing(_conn()) as c, c:
        c.execute("INSERT INTO consents VALUES (?,?,?,?,?,NULL)",
                  (cid, dt.datetime.now().isoformat(timespec="seconds"), purpose, json.dumps(fields), lang))
    return cid


def withdraw_consent(cid: str) -> bool:
    with closing(_conn()) as c, c:
        n = c.execute("UPDATE consents SET withdrawn=? WHERE id=? AND withdrawn IS NULL",
                      (dt.datetime.now().isoformat(timespec="seconds"), cid)).rowcount
        c.execute("UPDATE orders SET consent_withdrawn=1 WHERE consent_id=?", (cid,))
    return n > 0


def create(quote: dict, business: str, contact_name: str | None, gstin: str | None, kyc_verdict: str,
           consent_id: str | None, lang: str = "en", start: dt.date | None = None) -> dict:
    oid = "UDX-" + secrets.token_hex(3).upper()
    on = [i for i in quote["items"] if i["on"]]
    kyc_ok = kyc_verdict in ("PASS", "AUTO_FIX")
    plan = _plan(start or TODAY, quote["totals"]["install_days"], kyc_ok)
    with closing(_conn()) as c, c:
        c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,?)",
                  (oid, dt.datetime.now().isoformat(timespec="seconds"), business, mask_name(contact_name),
                   mask_gstin(gstin), quote["bundle_name"], json.dumps(quote["totals"]),
                   json.dumps([{k: i[k] for k in ("product_id", "name", "qty", "unit_price")} for i in on]),
                   kyc_verdict, 1 if kyc_ok else 0, json.dumps(plan), consent_id, lang))
        if not kyc_ok:
            c.execute("INSERT INTO handoffs (created, kind, business, detail) VALUES (?,?,?,?)",
                      (dt.datetime.now().isoformat(timespec="seconds"), f"kyc_{kyc_verdict.lower()}", business, oid))
    return get(oid)


def get(oid: str) -> dict | None:
    with closing(_conn()) as c:
        r = c.execute("SELECT * FROM orders WHERE id=?", ((oid or "").strip().upper(),)).fetchone()
    if not r:
        return None
    plan = json.loads(r["plan"])
    stage = r["stage"]
    return {
        "id": r["id"], "business": r["business"], "contact": r["contact_masked"], "gstin": r["gstin_masked"],
        "bundle_name": r["bundle_name"], "totals": json.loads(r["totals"]), "items": json.loads(r["items"]),
        "kyc_verdict": r["kyc_verdict"], "consent_withdrawn": bool(r["consent_withdrawn"]), "consent_id": r["consent_id"],
        "stage_index": stage,
        "stages": [{"key": k, "planned": plan[i], "done": i <= stage, "current": i == stage} for i, k in enumerate(STAGES)],
        "eta": plan[-1],
    }


def advance(oid: str) -> dict | None:
    o = get(oid)
    if not o:
        return None
    with closing(_conn()) as c, c:
        c.execute("UPDATE orders SET stage=MIN(stage+1, ?) WHERE id=?", (len(STAGES) - 1, o["id"]))
    return get(oid)


def log_handoff(kind: str, business: str, detail: str) -> None:
    with closing(_conn()) as c, c:
        c.execute("INSERT INTO handoffs (created, kind, business, detail) VALUES (?,?,?,?)",
                  (dt.datetime.now().isoformat(timespec="seconds"), kind, business, detail))


def backoffice() -> dict:
    with closing(_conn()) as c:
        hand = [dict(r) for r in c.execute("SELECT * FROM handoffs ORDER BY id DESC LIMIT 100")]
        orders = [dict(r) for r in c.execute("SELECT id, created, business, bundle_name, kyc_verdict, stage FROM orders ORDER BY created DESC LIMIT 100")]
    return {"handoffs": hand, "orders": orders}
