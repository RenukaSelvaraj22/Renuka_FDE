import ast
from pathlib import Path
from pprint import pformat


INVOICES_FILE = Path(__file__).resolve().parent.parent / "data" / "invoices.py"


def uppercase_vendors() -> list[dict]:
    with INVOICES_FILE.open("r", encoding="utf-8") as invoices_file:
        invoices = ast.literal_eval(invoices_file.read())

    if not isinstance(invoices, list):
        raise ValueError("Invoice data must be a list.")

    for index in range(len(invoices)):
        if not isinstance(invoices[index], dict):
            raise ValueError(f"Invoice at index {index} must be a dictionary.")
        vendor = invoices[index].get("vendor")
        if not isinstance(vendor, str):
            raise ValueError(f"Invoice at index {index} has no string vendor name.")
        invoices[index]["vendor"] = vendor.upper()

    with INVOICES_FILE.open("w", encoding="utf-8") as invoices_file:
        invoices_file.write(pformat(invoices, sort_dicts=False) + "\n")

    return invoices


if __name__ == "__main__":
    print(pformat(uppercase_vendors(), sort_dicts=False))
