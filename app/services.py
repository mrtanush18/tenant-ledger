from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
from app.schemas import ALLOWED_CURRENCIES

def _validate(row):
    try:
        amt = Decimal(str(row.amount)).quantize(Decimal("0.0001"))
    except (InvalidOperation, ValueError):
        return None, "amount not numeric"
    if amt <= 0:
        return None, "amount must be positive"
    if row.currency not in ALLOWED_CURRENCIES:
        return None, f"unknown currency {row.currency}"
    if row.txn_date > date.today():
        return None, "future date not allowed"
    if not row.client_ref:
        return None, "missing client_ref"
    signed = -amt if row.txn_type in ("withdrawal", "fee") else amt
    return signed, None

def bulk_ingest(db: Session, firm_id: str, rows, actor: str):
    accepted, rejected, dup = 0, [], 0
    for i, row in enumerate(rows, start=1):
        signed, reason = _validate(row)
        if reason:
            rejected.append({"row": i, "reason": reason})
            continue
        if row.idempotency_key:
            exists = db.query(models.Transaction).filter_by(
                firm_id=firm_id, idempotency_key=row.idempotency_key).first()
            if exists:
                dup += 1
                continue
        db.add(models.Transaction(
            firm_id=firm_id, client_ref=row.client_ref, amount=signed,
            currency=row.currency, txn_type=row.txn_type,
            txn_date=row.txn_date, idempotency_key=row.idempotency_key))
        accepted += 1
    db.add(models.AuditLog(firm_id=firm_id, actor=actor, action="bulk_ingest",
                           detail=f"accepted={accepted} rejected={len(rejected)} dup={dup}"))
    db.commit()
    return {"accepted": accepted, "rejected": rejected, "duplicate_skipped": dup}

def balance_as_of(db: Session, firm_id: str, client_ref: str, as_of: date):
    total = (db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
             .filter(models.Transaction.firm_id == firm_id,
                     models.Transaction.client_ref == client_ref,
                     models.Transaction.txn_date <= as_of).scalar())
    return Decimal(str(total)).quantize(Decimal("0.0001"))

def reverse(db: Session, firm_id: str, txn_id: int, actor: str):
    orig = db.query(models.Transaction).filter_by(
        id=txn_id, firm_id=firm_id).first()
    if not orig:
        return None, "not found"
    if orig.txn_type == "reversal":
        return None, "cannot reverse a reversal"
    already = db.query(models.Transaction).filter_by(reverses_id=orig.id).first()
    if already:
        return None, "already reversed"
    rev = models.Transaction(
        firm_id=firm_id, client_ref=orig.client_ref, amount=-orig.amount,
        currency=orig.currency, txn_type="reversal", txn_date=date.today(),
        reverses_id=orig.id)
    db.add(rev)
    db.add(models.AuditLog(firm_id=firm_id, actor=actor, action="reverse",
                           detail=f"reversed txn {orig.id}"))
    db.commit()
    db.refresh(rev)
    return rev, None