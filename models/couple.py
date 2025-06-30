from pydantic import BaseModel

class Couple(BaseModel):
    groomName: str
    groomBlank: str
    brideName: str
    brideBlank: str