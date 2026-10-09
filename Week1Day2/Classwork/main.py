import importlib
from fastapi import FastAPI 

create_invoice = importlib.import_module("Create_invoices").router
get_invoices = importlib.import_module("Get_invoices").router

app = FastAPI()
app.include_router(create_invoice)
app.include_router(get_invoices)
