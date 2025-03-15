from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models.guest import Guest
from models.user import User
from models.drink import Drink
from models.timing import Timing
from models.visit_sts import VisitSts
from models.couple import Couple
from models.todo import Todo


# Модель для создания события, без поля `id`, которое будет генерироваться после добавления в базу данных
class EventCreate(BaseModel):
    created: datetime
    eventName: str
    eventDate: datetime
    eventTime: str
    eventDesignId: str
    eventLocation: str
    eventDrinks: List[Drink] = []
    eventTiming: List[Timing] = []
    eventCouple: Couple
    guestStatuses: List[VisitSts] = []
    userId: str
    hostId: Optional[str] = ""
    guests: List[str] = []
    todoList: List[Todo] = []
    allowedUsers: List[User] = []

# Модель для события с дополнительным полем `id`
class Event(EventCreate):
    id: str  # Это поле добавляется, когда событие уже создано в базе данных

class EventUpdate(BaseModel):
    eventName: Optional[str]
    eventDate: Optional[datetime]
    eventTime: Optional[str]
    eventDesignId: Optional[str]
    eventLocation: Optional[str]
    eventDrinks: Optional[List[Drink]] = []
    eventTiming: Optional[List[Timing]] = []
    eventCouple: Optional[Couple]
    guestStatuses: Optional[List[VisitSts]] = []
    # guests: Optional[List[str]] = []
    # allowedUsers: Optional[List[User]] = []
    updated: Optional[datetime] = datetime.utcnow  # Дата последнего обновления, по умолчанию текущая дата

    class Config:
        orm_mode = True
        use_enum_values = True