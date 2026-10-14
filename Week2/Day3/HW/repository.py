import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "invoices.json"

def load_invoices():
    with open(DATA_FILE,"r", encoding="utf-8") as f:
        return json.load(f)

def save_invoices(invoices):
    with open(DATA_FILE,"w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=4)   

def find_invoice_by_id(invoice_id):
    print(f"Fetching invoice with ID from repository: {invoice_id}")
    invoices = load_invoices()
    print(f"Loaded invoices: {invoices}")
    for invoice in invoices:
        if invoice["invoice_id"] == invoice_id:
            return invoice
    return None 

def add_invoice(invoice):
    invoices = load_invoices()
    invoices.append(invoice)
    save_invoices(invoices)

def update_invoice(invoice_id, updated_invoice):    
    invoices = load_invoices()
    for index, invoice in enumerate(invoices):
        if invoice["invoice_id"] == invoice_id:
            invoices[index] = updated_invoice
            save_invoices(invoices)
            return True
    return False  

def delete_invoice(invoice_id):
    invoices = load_invoices()
    for index, invoice in enumerate(invoices):
        if invoice["invoice_id"] == invoice_id:
            del invoices[index]
            save_invoices(invoices)
            return True
    return False         
