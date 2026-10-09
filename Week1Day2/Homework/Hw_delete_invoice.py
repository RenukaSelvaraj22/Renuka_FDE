from fastapi import APIRouter, HTTPException
from Data_store import invoices

router = APIRouter()


@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    for index, invoice in enumerate(invoices):
        if invoice["id"] == invoice_id:
            deleted_invoice = invoices.pop(index)
            return {
                "message": "Invoice deleted successfully",
                "invoice": deleted_invoice,
            }
    raise HTTPException(status_code=404, detail="Invoice not found")
