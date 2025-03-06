from pydantic import BaseModel

class Design(BaseModel):
    id: str
    designName: str