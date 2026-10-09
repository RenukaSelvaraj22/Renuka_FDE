from fastapi import APIRouter
from Data_store import invoices
from Models import Invoice

router = APIRouter()

@router.post("/invoices")
def create_invoice(invoice: Invoice):
    new_invoice = invoice.model_dump()
    invoices.append(new_invoice)
    return {"message": "Invoice created successfully", "invoice": new_invoice}