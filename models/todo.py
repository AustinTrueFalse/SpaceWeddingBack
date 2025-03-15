from pydantic import BaseModel

class Todo(BaseModel):
    id: str
    name: str
    completed: bool