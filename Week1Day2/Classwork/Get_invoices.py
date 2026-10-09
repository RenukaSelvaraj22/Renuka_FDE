from fastapi import APIRouter
from Data_store import invoices

router = APIRouter()

@router.get("/invoices")
def get_invoices():
    return invoices

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    for invoice in invoices:
        if invoice["id"] == invoice_id:
            return invoice
    return {"error": "Invoice not found"}