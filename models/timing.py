from pydantic import BaseModel

class Timing(BaseModel):
    id: str
    time: str
    description: str