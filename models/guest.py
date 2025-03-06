from pydantic import BaseModel, constr
from datetime import datetime
from typing import Optional, List
from models.drink import Drink


class GuestCreate(BaseModel):
    created: datetime
    eventId: str
    guestName: str
    guestPhone: str
    guestStatus: int
    guestDrinks: List[str] = []

# Модель для события с дополнительным полем `id`
class Guest(GuestCreate):
    id: str  # Это поле добавляется, когда событие уже создано в базе данных