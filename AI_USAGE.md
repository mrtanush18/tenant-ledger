# AI Usage

Tools: Claude.
Prompts: "FastAPI bulk ingest partial success", "pytest tenant isolation", "append-only ledger reversal".
Corrected/rejected: rejected float money; moved idempotency to DB unique constraint; added tenant guard because path param alone is unsafe; forbid double-reverse.
