# Notes
Chose: idempotent bulk ingest (partial success), tenant guard, append-only ledger with reversals, as-of balance, audit log.
Why: money + bad data + multi-tenant leakage break trust fastest.
Risks: float money, cross-tenant reads, duplicate re-sends, history rewrites, race on idempotency.
Handled: Decimal(18,4), X-Firm-Id guard, UniqueConstraint(firm_id,idempotency_key), reversals-not-updates, audit rows.
Skipped: FX, summaries, rate limiting, real auth, suspicious-activity flags.
At 100x: chunked ingest + background worker; pre-aggregated balance table; per-firm rate limits; DB-level row security.