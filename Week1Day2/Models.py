from pydantic import BaseModel

class Invoice(BaseModel):
    id: int
    customer: str
    amount: float
    status: str
    vendor: str | None = None

class VendorUpdate(BaseModel):
    vendor: str

class Employee(BaseModel):
    employee_id: int
    name: str
    department: str