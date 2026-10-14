import ast
from collections import defaultdict
from pathlib import Path
from pprint import pformat

import repository
from models import Invoice

#INVOICES_FILE = Path(__file__).resolve().parent.parent / "data" / "invoices.py"
#PAYMENTS_FILE = Path(__file__).resolve().parent.parent / "data" / "payments.py"


def get_invoice(invoice_id: int) -> Invoice:
    print(f"Fetching invoice with ID from services: {invoice_id}")
    invoice_data = repository.find_invoice_by_id(invoice_id)
    print(f"Invoice data retrieved: {invoice_data}")
    if invoice_data is None:
        raise ValueError(f"Invoice with ID {invoice_id} not found.")
    return Invoice(**invoice_data)

def create_invoice(invoice_data: dict) -> Invoice:
    new_invoice = Invoice(**invoice_data)
    repository.add_invoice(new_invoice.dict())
    return new_invoice

def update_invoice(invoice_id: int, updated_data: dict) -> Invoice:
    existing_invoice = repository.find_invoice_by_id(invoice_id)
    if existing_invoice is None:
        raise ValueError(f"Invoice with ID {invoice_id} not found.")
    
    updated_invoice = Invoice(**{**existing_invoice, **updated_data})
    repository.update_invoice(invoice_id, updated_invoice.dict())
    return updated_invoice

def delete_invoice(invoice_id: int) -> None:
    existing_invoice = repository.find_invoice_by_id(invoice_id)
    if existing_invoice is None:
        raise ValueError(f"Invoice with ID {invoice_id} not found.")
    
    repository.delete_invoice(invoice_id)


def remove_exact_duplicates() -> tuple[dict[tuple, list[int]], list[dict]]:
    with INVOICES_FILE.open("r", encoding="utf-8") as invoices_file:
        invoices = ast.literal_eval(invoices_file.read())

    if not isinstance(invoices, list):
        raise ValueError("Invoice data must be a list.")

    indexes_by_invoice: dict[tuple, list[int]] = {}
    for index, invoice in enumerate(invoices):
        if not isinstance(invoice, dict):
            raise ValueError(f"Invoice at index {index} must be a dictionary.")
        key = tuple(sorted(invoice.items()))
        indexes_by_invoice.setdefault(key, []).append(index)

    exact_dupes = {
        key: indexes
        for key, indexes in indexes_by_invoice.items()
        if len(indexes) > 1
    }
    duplicate_indexes = {
        index
        for indexes in exact_dupes.values()
        for index in indexes[1:]
    }
    deduplicated_invoices = [
        invoice
        for index, invoice in enumerate(invoices)
        if index not in duplicate_indexes
    ]

    with INVOICES_FILE.open("w", encoding="utf-8") as invoices_file:
        invoices_file.write(pformat(deduplicated_invoices, sort_dicts=False) + "\n")

    return exact_dupes, deduplicated_invoices


def find_suspected_duplicates() -> list[str]:
    with INVOICES_FILE.open("r", encoding="utf-8") as invoices_file:
        invoices = ast.literal_eval(invoices_file.read())

    if not isinstance(invoices, list):
        raise ValueError("Invoice data must be a list.")

    indexes_by_details: dict[tuple, list[str]] = {}
    for index, invoice in enumerate(invoices):
        if not isinstance(invoice, dict):
            raise ValueError(f"Invoice at index {index} must be a dictionary.")
        invoice_id = invoice.get("invoice_id")
        vendor = invoice.get("vendor")
        amount = invoice.get("amount")
        date = invoice.get("date")
        if not isinstance(invoice_id, str):
            raise ValueError(f"Invoice at index {index} has no string invoice ID.")

        key = (vendor, amount, date)
        indexes_by_details.setdefault(key, []).append(invoice_id)

    suspected_dupes = []
    for invoice_ids in indexes_by_details.values():
        distinct_ids = list(dict.fromkeys(invoice_ids))
        for first_index, first_id in enumerate(distinct_ids):
            for second_id in distinct_ids[first_index + 1:]:
                suspected_dupes.append(f"({first_id} ~ {second_id})")

    return suspected_dupes


def process_credit_notes(invoices: list[dict]) -> list[dict]:
    if not isinstance(invoices, list):
        raise ValueError("Invoice data must be a list.")

    for credit_index, credit_invoice in enumerate(invoices):
        if not isinstance(credit_invoice, dict):
            raise ValueError(f"Invoice at index {credit_index} must be a dictionary.")

        amount = credit_invoice.get("amount")
        if amount is None or amount >= 0 or credit_invoice.get("status") == "CANCELLED":
            continue

        partner_found = False
        for positive_index, positive_invoice in enumerate(invoices):
            if not isinstance(positive_invoice, dict):
                raise ValueError(f"Invoice at index {positive_index} must be a dictionary.")

            positive_amount = positive_invoice.get("amount")
            if (
                positive_invoice.get("vendor") == credit_invoice.get("vendor")
                and positive_amount is not None
                and positive_amount > 0
                and positive_amount == abs(amount)
                and positive_invoice.get("status") != "CANCELLED"
            ):
                credit_invoice["status"] = "CANCELLED"
                positive_invoice["status"] = "CANCELLED"
                print(f"{credit_index} <-> {positive_index}")
                partner_found = True
                break

        if not partner_found:
            print(f"No partner found for invoice {credit_invoice.get('invoice_id')}")

    return invoices


def process_credit_notes_from_file() -> list[dict]:
    with INVOICES_FILE.open("r", encoding="utf-8") as invoices_file:
        invoices = ast.literal_eval(invoices_file.read())

    processed_invoices = process_credit_notes(invoices)

    with INVOICES_FILE.open("w", encoding="utf-8") as invoices_file:
        invoices_file.write(pformat(processed_invoices, sort_dicts=False) + "\n")

    return processed_invoices


def reconcile_payments(invoices: list[dict], payments: list[dict]) -> list[dict]:
    if not isinstance(invoices, list) or not isinstance(payments, list):
        raise ValueError("Invoices and payments must both be lists.")

    totals_by_invoice: dict[object, int | float] = defaultdict(int)
    for index, payment in enumerate(payments):
        if not isinstance(payment, dict):
            raise ValueError(f"Payment at index {index} must be a dictionary.")

        invoice_id = payment.get("invoice_id")
        paid_amount = payment.get("paid")
        if invoice_id is None:
            raise ValueError(f"Payment at index {index} has no invoice ID.")
        if not isinstance(paid_amount, (int, float)) or isinstance(paid_amount, bool):
            raise ValueError(f"Payment at index {index} has an invalid paid amount.")
        totals_by_invoice[invoice_id] += paid_amount

    reconciled_invoices = []
    for index, invoice in enumerate(invoices):
        if not isinstance(invoice, dict):
            raise ValueError(f"Invoice at index {index} must be a dictionary.")
        invoice_id = invoice.get("invoice_id")
        if invoice_id is None:
            raise ValueError(f"Invoice at index {index} has no invoice ID.")
        reconciled_invoices.append({
            **invoice,
            "total_paid": totals_by_invoice.get(invoice_id, 0),
        })

    return reconciled_invoices


def reconcile_payments_from_files() -> list[dict]:
    with INVOICES_FILE.open("r", encoding="utf-8") as invoices_file:
        invoices = ast.literal_eval(invoices_file.read())
    with PAYMENTS_FILE.open("r", encoding="utf-8") as payments_file:
        payments = ast.literal_eval(payments_file.read())

    return reconcile_payments(invoices, payments)