from pydantic import BaseModel, Field, validator
from typing import Optional, List
from src.models.message import Message


class User(BaseModel):
    """Модель пользователя чата"""
    sid: str = Field(..., description="Socket.IO session ID")
    name: str = Field(..., min_length=1, max_length=50, description="Имя пользователя")
    room: Optional[str] = Field(None, description="Текущая комната")
    messages: List[Message] = Field(default_factory=list, description="История сообщений")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Имя не может быть пустым")
        if len(v.strip()) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа")
        if len(v.strip()) > 50:
            raise ValueError("Имя не должно превышать 50 символов")
        return v.strip()
    
    def join_room(self, room: str):
        """Присоединиться к комнате"""
        self.room = room
    
    def leave_room(self):
        """Покинуть комнату"""
        self.room = None
    
    def add_message(self, message: 'Message'):
        """Добавить сообщение в историю"""
        self.messages.append(message)
    
    def to_dict(self):
        """Преобразовать в словарь для отправки"""
        return {
            'sid': self.sid,
            'name': self.name,
            'room': self.room
        }