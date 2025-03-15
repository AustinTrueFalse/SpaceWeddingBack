from pydantic import BaseModel, constr
from datetime import datetime
from typing import Optional, List
from models.drink import Drink


class GuestCreate(BaseModel):
    created: datetime
    eventId: str
    guestName: str
    guestPhone: str
    guestStatus: str
    guestDrinks: List[str] = []

# Модель для события с дополнительным полем `id`
class Guest(GuestCreate):
    id: str  # Это поле добавляется, когда событие уже создано в базе данных

class GuestUpdate(BaseModel):
    guestName: Optional[str]
    guestPhone: Optional[str]
    guestStatus: Optional[str]
    guestDrinks: Optional[List[str]] = []
    updated: Optional[datetime] = datetime.utcnow  # Дата последнего обновления, по умолчанию текущая дата

    class Config:
        orm_mode = True
        use_enum_values = True