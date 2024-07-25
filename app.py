import os
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Lock
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')
socketio = SocketIO(app, cors_allowed_origins=["*"])

# Thread-safe dictionaries
room_users = {}
socket_room_user_map = {}
lock = Lock()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@socketio.on('join')
def join(message):
    try:
        username = message['username']
        room = message['room']
    except KeyError as e:
        logger.error(f"Missing key in join message: {e}")
        return

    join_room(room)
    session_id = request.sid

    with lock:
        socket_room_user_map[session_id] = {'room': room, 'username': username}
        if room not in room_users:
            room_users[room] = set()
        room_users[room].add(username)

    emit('user_list', {'users': list(room_users[room])}, to=room)
    logger.info(f'RoomEvent: {username} has joined the room {room}')

@socketio.on('leave')
def leave(message):
    try:
        username = message['username']
        room = message['room']
    except KeyError as e:
        logger.error(f"Missing key in leave message: {e}")
        return

    leave_room(room)

    with lock:
        if room in room_users and username in room_users[room]:
            room_users[room].remove(username)
            if not room_users[room]:
                del room_users[room]

    if room in room_users:
        emit('user_list', {'users': list(room_users[room])}, to=room)
    logger.info(f'RoomEvent: {username} has left the room {room}')

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    with lock:
        if session_id in socket_room_user_map:
            user_info = socket_room_user_map[session_id]
            room = user_info['room']
            username = user_info['username']
            
            if room in room_users and username in room_users[room]:
                room_users[room].remove(username)
                if not room_users[room]:
                    del room_users[room]

            del socket_room_user_map[session_id]

            if room in room_users:
                emit('user_list', {'users': list(room_users[room])}, to=room)

            logger.info(f'DisconnectEvent: {username} has been disconnected from the room {room}')

@socketio.on('offer')
def handle_offer(message):
    try:
        room = message['room']
        offer = message['offer']
    except KeyError as e:
        logger.error(f"Missing key in offer message: {e}")
        return

    emit('offer', offer, to=room, skip_sid=request.sid)

@socketio.on('answer')
def handle_answer(message):
    try:
        room = message['room']
        answer = message['answer']
    except KeyError as e:
        logger.error(f"Missing key in answer message: {e}")
        return

    emit('answer', answer, to=room, skip_sid=request.sid)

@socketio.on('ice_candidate')
def handle_ice_candidate(message):
    try:
        room = message['room']
        candidate = message['candidate']
    except KeyError as e:
        logger.error(f"Missing key in ice_candidate message: {e}")
        return

    emit('ice_candidate', candidate, to=room, skip_sid=request.sid)

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Error: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5004)
