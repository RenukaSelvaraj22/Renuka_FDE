from fastapi import APIRouter, HTTPException
from Data_store import invoices
from Models import VendorUpdate

router = APIRouter()


@router.patch("/invoices/{invoice_id}/vendor")
def update_invoice_vendor(invoice_id: int, vendor_update: VendorUpdate):
    for invoice in invoices:
        if invoice["id"] == invoice_id:
            invoice["vendor"] = vendor_update.vendor
            return {
                "message": "Invoice vendor updated successfully",
                "invoice": invoice,
            }
    raise HTTPException(status_code=404, detail="Invoice not found")
