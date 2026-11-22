from datetime import date
from fastapi import FastAPI, Depends, Header, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app import models, schemas, services

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Tenant Ledger")

def tenant_guard(x_firm_id: str = Header(...), firm_id: str = Path(...)):
    if x_firm_id != firm_id:
        raise HTTPException(status_code=403, detail="tenant mismatch")
    return x_firm_id

@app.post("/firms/{firm_id}/transactions/bulk", response_model=schemas.BulkOut)
def bulk(firm_id: str, body: schemas.BulkIn,
         db: Session = Depends(get_db),
         _=Depends(tenant_guard),
         x_actor: str = Header("system")):
    return services.bulk_ingest(db, firm_id, body.transactions, x_actor)

@app.get("/firms/{firm_id}/clients/{client_ref}/balance", response_model=schemas.BalanceOut)
def balance(firm_id: str, client_ref: str, as_of: date | None = None,
            db: Session = Depends(get_db), _=Depends(tenant_guard)):
    d = as_of or date.today()
    bal = services.balance_as_of(db, firm_id, client_ref, d)
    return {"client_ref": client_ref, "as_of": d, "balance": str(bal)}

@app.post("/firms/{firm_id}/transactions/{txn_id}/reverse")
def reverse(firm_id: str, txn_id: int,
            db: Session = Depends(get_db), _=Depends(tenant_guard),
            x_actor: str = Header("system")):
    rev, err = services.reverse(db, firm_id, txn_id, x_actor)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"reversal_id": rev.id, "reverses_id": rev.reverses_id}