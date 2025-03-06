from pydantic import BaseModel

class Drink(BaseModel):
    id: str
    drinkName: str