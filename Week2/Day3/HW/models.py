from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_id: int
    amount: float
    status: str 
    vendor: str = "UNKNOWN"  # Default value for vendor if not provided
    