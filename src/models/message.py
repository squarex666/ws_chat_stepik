from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class Message(BaseModel):
    """Модель сообщения чата"""
    text: str = Field(..., min_length=1, max_length=500, description="Текст сообщения")
    author: str = Field(..., description="Имя автора сообщения")
    room: Optional[str] = Field(None, description="Комната, в которую отправлено сообщение")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время отправки")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Сообщение не может быть пустым")
        if len(v.strip()) > 500:
            raise ValueError("Сообщение не должно превышать 500 символов")
        return v.strip()
    
    @validator('author')
    def validate_author(cls, v):
        if not v.strip():
            raise ValueError("Имя автора не может быть пустым")
        return v.strip()
    
    def to_dict(self):
        """Преобразовать в словарь для отправки"""
        return {
            'text': self.text,
            'author': self.author,
            'room': self.room,
            'timestamp': self.timestamp.isoformat()
        }