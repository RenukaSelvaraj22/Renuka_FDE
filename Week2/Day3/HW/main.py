from fastapi import FastAPI, HTTPException
from models import Invoice
from service import (
    get_invoice,
    create_invoice,
    update_invoice,
    delete_invoice,
    remove_exact_duplicates,
    find_suspected_duplicates,
    process_credit_notes_from_file,
    reconcile_payments_from_files,
)
from uppercase_vendors import uppercase_vendors
from pprint import pformat

app = FastAPI()

@app.get("/invoices/uppercase")
def uppercase_invoice_vendors():
    invoices = uppercase_vendors()
    print("Invoices with uppercase vendor names:")
    print(pformat(invoices, sort_dicts=False))
    return invoices

@app.post("/invoices/exact-duplicates")
def remove_duplicate_invoices():
    exact_dupes, invoices = remove_exact_duplicates()
    duplicate_details = [
        {"invoice": dict(key), "indexes": indexes}
        for key, indexes in exact_dupes.items()
    ]
    output = {"exact_dupes": duplicate_details, "invoices": invoices}
    print("Exact duplicate invoices and their indexes:")
    print(pformat(duplicate_details, sort_dicts=False))
    print("Invoices after removing duplicate rows:")
    print(pformat(invoices, sort_dicts=False))
    return output

@app.get("/invoices/suspected-duplicates")
def read_suspected_duplicates():
    suspected_dupes = find_suspected_duplicates()
    print("Suspected duplicate invoice pairs:")
    print("\n".join(suspected_dupes) if suspected_dupes else "None found.")
    return {"suspected_duplicates": suspected_dupes}

@app.post("/invoices/credit-notes")
def match_credit_notes():
    invoices = process_credit_notes_from_file()
    credit_notes = [
        invoice
        for invoice in invoices
        if isinstance(invoice.get("amount"), (int, float))
        and invoice["amount"] < 0
    ]
    print("Processed credit notes:")
    print(pformat(credit_notes, sort_dicts=False))
    print("All invoices after matching credit notes:")
    print(pformat(invoices, sort_dicts=False))
    return invoices

@app.get("/payments/reconcile")
def reconcile_invoice_payments():
    invoices = reconcile_payments_from_files()
    print("Invoices reconciled with payment totals:")
    print(pformat(invoices, sort_dicts=False))
    return invoices

@app.get("/invoices/{invoice_id}", response_model=Invoice)
def read_invoice(invoice_id: int):
    try:
        print(f"Fetching invoice with ID from main: {invoice_id}")
        return get_invoice(invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/invoices", response_model=Invoice)
def create_new_invoice(invoice: Invoice):
    return create_invoice(invoice.dict())

@app.put("/invoices/{invoice_id}", response_model=Invoice)
def update_existing_invoice(invoice_id: int, updated_invoice: Invoice):
    try:
        return update_invoice(invoice_id, updated_invoice.dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/invoices/{invoice_id}")
def delete_existing_invoice(invoice_id: int):
    try:
        delete_invoice(invoice_id)
        return {"detail": "Invoice deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))