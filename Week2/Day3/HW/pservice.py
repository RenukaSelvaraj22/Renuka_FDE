import ast
from collections import defaultdict
from pathlib import Path
from pprint import pformat
from pmodel import Payments
import prepository 


# PAYMENTS_FILE =  "../Day3/data/payments.json"


def get_payment(invoice_id: int) -> Payments:
    print(f"Fetching payment with ID from services: {invoice_id}")
    payment_data = prepository.find_payment_by_id(invoice_id)
    print(f"Payment data retrieved: {payment_data}")
    if payment_data is None:
        raise ValueError(f"Payment with ID {invoice_id} not found.")
    return Payments(**payment_data)

def create_payment(payment_data: dict) -> Payments:
    new_payment = Payments(**payment_data)
    prepository.add_payment(new_payment.dict())
    return new_payment

def update_payment(invoice_id: int, updated_data: dict) -> Payments:
    existing_payment = prepository.find_payment_by_id(invoice_id)
    if existing_payment is None:
        raise ValueError(f"Payment with ID {invoice_id} not found.")
    
    updated_payment = Payments(**{**existing_payment, **updated_data})
    prepository.update_payment(invoice_id, updated_payment.dict())
    return updated_payment

def delete_payment(invoice_id: int) -> None:
    existing_payment = prepository.find_payment_by_id(invoice_id)
    if existing_payment is None:
        raise ValueError(f"Payment with ID {invoice_id} not found.")
    
    prepository.delete_payment(invoice_id)