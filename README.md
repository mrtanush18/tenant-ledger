# Tenant Ledger

Multi-tenant, append-only money-movement ledger for advisory firms.

## Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest -q
```

## API

All routes require header `X-Firm-Id` matching the `{firm_id}` path (else 403).
Write routes accept `X-Actor` for the audit log.

- `POST /firms/{firm_id}/transactions/bulk` — bulk ingest, partial success; body `{"transactions":[...]}`
- `GET /firms/{firm_id}/clients/{client_ref}/balance?as_of=YYYY-MM-DD` — balance as of date
- `POST /firms/{firm_id}/transactions/{txn_id}/reverse` — append a reversal (history is never mutated)

## Design

- Append-only `transactions`: corrections are reversal rows (`reverses_id`), never updates/deletes.
- Money stored as `Numeric(18,4)`, never float.
- Idempotent ingest via `UniqueConstraint(firm_id, idempotency_key)`.
- Every query is scoped by `firm_id`; cross-tenant reads are rejected.
- `audit_log` records actor, action, detail for every write.
