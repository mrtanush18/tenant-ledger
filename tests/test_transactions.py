import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)
H = {"X-Firm-Id": "firmA", "X-Actor": "tester"}

@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def post_bulk(firm="firmA", txns=None):
    return client.post(f"/firms/{firm}/transactions/bulk",
                       json={"transactions": txns},
                       headers={"X-Firm-Id": firm, "X-Actor": "tester"})

def txn(**kw):
    base = {"client_ref": "c1", "amount": 100, "currency": "USD",
            "txn_type": "deposit", "txn_date": str(date.today())}
    base.update(kw)
    return base

def test_partial_ingest():
    r = post_bulk(txns=[txn(), txn(amount=-5), txn(currency="XXX")])
    j = r.json()
    assert j["accepted"] == 1
    assert len(j["rejected"]) == 2

def test_idempotency_no_double_post():
    post_bulk(txns=[txn(idempotency_key="k1")])
    r2 = post_bulk(txns=[txn(idempotency_key="k1")])
    assert r2.json()["duplicate_skipped"] == 1
    r = client.get("/firms/firmA/clients/c1/balance", headers=H)
    assert r.json()["balance"] == "100.0000"

def test_tenant_isolation():
    post_bulk(firm="firmA", txns=[txn()])
    r = client.get("/firms/firmB/clients/c1/balance",
                   headers={"X-Firm-Id": "firmA"})
    assert r.status_code == 403

def test_balance_as_of():
    post_bulk(txns=[txn(txn_date=str(date.today() - timedelta(days=10)))])
    past = date.today() - timedelta(days=20)
    r = client.get(f"/firms/firmA/clients/c1/balance?as_of={past}", headers=H)
    assert r.json()["balance"] == "0.0000"

def test_reversal_preserves_history():
    post_bulk(txns=[txn()])
    r = client.post("/firms/firmA/transactions/1/reverse", headers=H)
    assert r.status_code == 200
    bal = client.get("/firms/firmA/clients/c1/balance", headers=H).json()["balance"]
    assert bal == "0.0000"
    r2 = client.post("/firms/firmA/transactions/1/reverse", headers=H)
    assert r2.status_code == 400