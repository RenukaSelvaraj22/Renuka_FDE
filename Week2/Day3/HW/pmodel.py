from pydantic import BaseModel

class Payments(BaseModel):
    invoice_id: int
    paid: float
