from pydantic import BaseModel, constr

# Модель для создания события, без поля `id`, которое будет генерироваться после добавления в базу данных
class UserCreate(BaseModel):
    email: str
    username: str
    email_lower: str
    username_lower: str

# Модель для события с дополнительным полем `id`
class User(UserCreate):
    id: str  # Это поле добавляется, когда событие уже создано в базе данных
