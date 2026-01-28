import eventlet
from eventlet import wsgi
import socketio
from loguru import logger

from src.models.user import User
from src.models.message import Message
from src.storage import storage


ROOMS = ["lobby", "general", "random"]

# Заставляем работать пути к статике
static_files = {'/': 'static/index.html', '/static': './static'}
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio, static_files=static_files)


def send_error(sid, message: str):
    """Отправить ошибку клиенту"""
    sio.emit('error', {'message': message}, room=sid)
    logger.warning(f"Ошибка для пользователя {sid}: {message}")


# Обрабатываем подключение пользователя
@sio.event
def connect(sid, environ):
    logger.info(f"Пользователь {sid} подключился")
    sio.emit('connect', room=sid)


# Отправляем комнаты
@sio.on('get_rooms')
def on_get_rooms(sid, data):
    logger.info(f"Пользователь {sid} запрашивает список комнат")
    sio.emit('rooms', ROOMS, room=sid)


@sio.on('join')
def on_join(sid, data):
    logger.info(f"Пользователь {sid} пытается присоединиться: {data}")
    
    try:
        # Валидация данных
        if not data or not isinstance(data, dict):
            raise ValueError("Неверный формат данных")
        
        room = data.get('room')
        name = data.get('name')
        
        if not room:
            raise ValueError("Не указана комната")
        
        if not name:
            raise ValueError("Не указано имя")
        
        if room not in ROOMS:
            raise ValueError(f"Комната '{room}' не существует. Доступные комнаты: {', '.join(ROOMS)}")
        
        # Создаем пользователя
        user = User(sid=sid, name=name, room=room)
        
        # Добавляем пользователя в хранилище
        storage.add_user(user)
        
        # Добавляем пользователя в комнату Socket.IO
        sio.enter_room(sid, room)
        
        # Добавляем пользователя в комнату в хранилище
        storage.add_user_to_room(sid, room)
        
        # Отправляем событие перемещения
        sio.emit('move', {'room': room}, room=sid)
        
        # Отправляем сообщение о присоединении всем в комнате
        sio.emit('message', {
            'author': 'Система',
            'text': f'Пользователь {name} присоединился к комнате'
        }, room=room)
        
        logger.info(f"Пользователь {name} (SID: {sid}) присоединился к комнате {room}")
        
    except Exception as e:
        send_error(sid, str(e))
        logger.error(f"Ошибка при присоединении пользователя {sid}: {e}")


@sio.on('leave')
def on_leave(sid, data):
    logger.info(f"Пользователь {sid} покидает комнату")
    
    try:
        user = storage.get_user(sid)
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if not user.room:
            raise ValueError("Пользователь не находится в комнате")
        
        # Сохраняем имя комнаты для сообщения
        room_name = user.room
        
        # Отправляем сообщение о выходе всем в комнате
        sio.emit('message', {
            'author': 'Система',
            'text': f'Пользователь {user.name} покинул комнату'
        }, room=room_name)
        
        # Покидаем комнату Socket.IO
        sio.leave_room(sid, room_name)
        
        # Удаляем пользователя из комнаты в хранилище
        storage.remove_user_from_room(sid, room_name)
        
        # Очищаем комнату у пользователя
        user.leave_room()
        
        logger.info(f"Пользователь {user.name} (SID: {sid}) покинул комнату {room_name}")
        
    except Exception as e:
        send_error(sid, str(e))
        logger.error(f"Ошибка при выходе пользователя {sid}: {e}")


# Обрабатываем отправку сообщения
@sio.on('send_message')
def on_message(sid, data):
    logger.info(f"Пользователь {sid} отправляет сообщение: {data}")
    
    try:
        # Валидация данных
        if not data or not isinstance(data, dict):
            raise ValueError("Неверный формат данных")
        
        text = data.get('text')
        
        if not text:
            raise ValueError("Сообщение не может быть пустым")
        
        # Получаем пользователя
        user = storage.get_user(sid)
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if not user.room:
            raise ValueError("Пользователь не находится в комнате")
        
        # Создаем сообщение
        message = Message(text=text, author=user.name, room=user.room)
        
        # Добавляем сообщение в историю пользователя
        user.add_message(message)
        
        # Отправляем сообщение всем в комнате
        sio.emit('message', {
            'author': user.name,
            'text': text
        }, room=user.room)
        
        logger.info(f"Сообщение от {user.name} отправлено в комнату {user.room}")
        
    except Exception as e:
        send_error(sid, str(e))
        logger.error(f"Ошибка при отправке сообщения от пользователя {sid}: {e}")


# Обрабатываем отключение пользователя
@sio.event
def disconnect(sid):
    logger.info(f"Пользователь {sid} отключился")
    
    try:
        user = storage.get_user(sid)
        
        if user and user.room:
            # Отправляем сообщение о выходе всем в комнате
            sio.emit('message', {
                'author': 'Система',
                'text': f'Пользователь {user.name} отключился'
            }, room=user.room)
            
            # Удаляем пользователя из комнаты
            sio.leave_room(sid, user.room)
            storage.remove_user_from_room(sid, user.room)
        
        # Удаляем пользователя из хранилища
        storage.remove_user(sid)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке отключения пользователя {sid}: {e}")


if __name__ == '__main__':
    logger.info("Запуск чат-сервера на порту 8000...")
    logger.info(f"Доступные комнаты: {', '.join(ROOMS)}")
    wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)