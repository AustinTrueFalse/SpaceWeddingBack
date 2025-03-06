from pydantic import BaseModel

class VisitSts(BaseModel):
    id: str
    status: str