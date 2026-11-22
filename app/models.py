
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    DateTime, Numeric, CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Firm(Base):
    __tablename__ = "firms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    transactions = relationship("Transaction", back_populates="firm")


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        UniqueConstraint(
            "firm_id", "idempotency_key",
            name="unique_firm_idempotency"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=False)
    client_ref = Column(String, nullable=False, index=True)

    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    transaction_date = Column(DateTime, nullable=False)

    idempotency_key = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    firm = relationship("Firm", back_populates="transactions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=False)
    transaction_id = Column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
