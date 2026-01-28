from typing import Dict, Optional, List
from src.models.user import User
from loguru import logger


class UserStorage:
    """Хранилище пользователей чата"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.rooms: Dict[str, List[str]] = {}  # room_name -> list of user_sids
    
    def add_user(self, user: User):
        """Добавить пользователя в хранилище"""
        self.users[user.sid] = user
        logger.info(f"Пользователь {user.name} (SID: {user.sid}) добавлен в хранилище")
    
    def get_user(self, sid: str) -> Optional[User]:
        """Получить пользователя по SID"""
        return self.users.get(sid)
    
    def remove_user(self, sid: str):
        """Удалить пользователя из хранилища"""
        if sid in self.users:
            user = self.users[sid]
            # Удаляем пользователя из комнаты
            if user.room:
                self.remove_user_from_room(sid, user.room)
            del self.users[sid]
            logger.info(f"Пользователь {user.name} (SID: {sid}) удален из хранилища")
    
    def add_user_to_room(self, sid: str, room: str):
        """Добавить пользователя в комнату"""
        if room not in self.rooms:
            self.rooms[room] = []
        
        if sid not in self.rooms[room]:
            self.rooms[room].append(sid)
            logger.info(f"Пользователь {sid} добавлен в комнату {room}")
    
    def remove_user_from_room(self, sid: str, room: str):
        """Удалить пользователя из комнаты"""
        if room in self.rooms and sid in self.rooms[room]:
            self.rooms[room].remove(sid)
            logger.info(f"Пользователь {sid} удален из комнаты {room}")
            
            # Если комната пуста, удаляем её
            if not self.rooms[room]:
                del self.rooms[room]
    
    def get_users_in_room(self, room: str) -> List[User]:
        """Получить список пользователей в комнате"""
        if room not in self.rooms:
            return []
        
        return [
            self.users[sid] 
            for sid in self.rooms[room] 
            if sid in self.users
        ]
    
    def get_room_users_count(self, room: str) -> int:
        """Получить количество пользователей в комнате"""
        return len(self.rooms.get(room, []))
    
    def get_all_rooms(self) -> List[str]:
        """Получить список всех комнат"""
        return list(self.rooms.keys())


# Создаем глобальный экземпляр хранилища
storage = UserStorage()