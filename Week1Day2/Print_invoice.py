from fastapi import FastAPI
app = FastAPI()
invoices = [

      {"id": 1, "customer": "ABC corp", "amount": 100.0, "status": "pending"},
        {"id": 2, "customer": "XYZ inc", "amount": 200.0, "status": "paid"},
        {"id": 3, "customer": "123 Ltd", "amount": 150.0, "status": "overdue"},
        {"id": 4, "customer": "DEF Co", "amount": 300.0, "status": "pending"},
        {"id": 5, "customer": "GHI Enterprises", "amount": 250.0, "status": "paid"}
    ]

@app.get("/invoices")
def get_invoices():
 return invoices    