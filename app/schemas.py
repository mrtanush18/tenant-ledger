from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field

ALLOWED_CURRENCIES = {"USD", "EUR", "GBP", "INR"}
TxnType = Literal["deposit", "withdrawal", "fee", "transfer"]

class TxnIn(BaseModel):
    client_ref: str = Field(min_length=1)
    amount: float
    currency: str
    txn_type: TxnType
    txn_date: date
    idempotency_key: Optional[str] = None

class BulkIn(BaseModel):
    transactions: list[TxnIn]

class RejectedRow(BaseModel):
    row: int
    reason: str

class BulkOut(BaseModel):
    accepted: int
    rejected: list[RejectedRow]
    duplicate_skipped: int = 0

class BalanceOut(BaseModel):
    client_ref: str
    as_of: date
    balance: str