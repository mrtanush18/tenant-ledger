from datetime import datetime, date
from sqlalchemy import (Column, Integer, String, Date, DateTime, Numeric,
                        ForeignKey, UniqueConstraint, Index)
from app.database import Base

class Firm(Base):
    __tablename__ = "firms"
    id = Column(String, primary_key=True)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    firm_id = Column(String, ForeignKey("firms.id"), nullable=False, index=True)
    client_ref = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("firm_id", "client_ref", name="uq_firm_client"),)

class Transaction(Base):
    """Append-only. No UPDATE, no DELETE."""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    firm_id = Column(String, ForeignKey("firms.id"), nullable=False, index=True)
    client_ref = Column(String, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)   # signed
    currency = Column(String(3), nullable=False)
    txn_type = Column(String, nullable=False)         # deposit|withdrawal|fee|transfer|reversal
    txn_date = Column(Date, nullable=False)
    idempotency_key = Column(String, nullable=True)
    reverses_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("firm_id", "idempotency_key", name="uq_firm_idem"),
        Index("ix_firm_client_date", "firm_id", "client_ref", "txn_date"),
    )

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    firm_id = Column(String, nullable=False, index=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)