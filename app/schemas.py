from pydantic import BaseModel

class TransactionCreate(BaseModel):
    type: str
    amount: int
    description: str
    donor_name: str | None = None

class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: int
    description: str
    donor_name: str | None
    status: str

    model_config = {
        "from_attributes": True 
    }