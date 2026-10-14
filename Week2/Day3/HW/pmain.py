

from fastapi import FastAPI, HTTPException

from pmodel import Payments
from pservice import (
    get_payment,
    create_payment,
    update_payment,
    delete_payment
)

app = FastAPI()
@app.get("/payments/{invoice_id}", response_model=Payments)
def read_payment(invoice_id: int):
    try:
        print(f"Fetching payment with ID from main: {invoice_id}")
        return get_payment(invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/payments", response_model=Payments)
def create_new_payment(payment: Payments):
    return create_payment(payment.dict())

@app.put("/payments/{invoice_id}", response_model=Payments)
def update_existing_payment(invoice_id: int, updated_payment: Payments):
    try:
        return update_payment(invoice_id, updated_payment.dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/payments/{invoice_id}")
def delete_existing_payment(invoice_id: int):
    try:
        delete_payment(invoice_id)
        return {"detail": "Payment deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))