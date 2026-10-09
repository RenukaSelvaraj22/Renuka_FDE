from pydantic import BaseModel

class Invoice(BaseModel):
    id: int
    amount: float
    status: str