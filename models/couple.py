from pydantic import BaseModel

class Couple(BaseModel):
    groomName: str
    brideName: str