import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "payments.json"

def load_payments():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_payments(payments):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(payments, f, indent=4)   

def find_payment_by_id(invoice_id):
    print(f"Fetching invoice with ID from repository: {invoice_id}")
    payments = load_payments()
    print(f"Loaded payments: {payments}")
    for payment in payments:
        if payment ["invoice_id"] == invoice_id:
            return payment
    return None 

def add_payment(payment):
    payments = load_payments()
    payments.append(payment)
    save_payments(payments)

def update_payment(invoice_id, updated_payment):    
    payments = load_payments()
    for index, payment in enumerate(payments):
        if payment["invoice_id"] == invoice_id:
            payments[index] = updated_payment
            save_payments(payments)
            return True
    return False  

def delete_payment(invoice_id):
    payments = load_payments()
    for index, payment in enumerate(payments):
        if payment["invoice_id"] == invoice_id:
            del payments[index]
            save_payments(payments)
            return True
    return False        