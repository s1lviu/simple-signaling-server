from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.secret_key = 'random secret key!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Dictionary to store room users
room_users = {}
# Dictionary to map socket ids to room and username
socket_room_user_map = {}

@socketio.on('join')
def join(message):
    username = message['username']
    room = message['room']
    join_room(room)
    session_id = request.sid  # Get socket session id

    # Mapping socket session to room and username
    socket_room_user_map[session_id] = {'room': room, 'username': username}

    # Adding user to the room list in the dictionary
    if room not in room_users:
        room_users[room] = []
    if username not in room_users[room]:
        room_users[room].append(username)

    # Emit the list of users in the room to all users in the room
    emit('user_list', {'users': room_users[room]}, to=room)

    print('RoomEvent: {} has joined the room {}\n'.format(username, room))

@socketio.on('leave')
def leave(message):
    username = message['username']
    room = message['room']
    leave_room(room)

    # Remove user from the room list
    if room in room_users and username in room_users[room]:
        room_users[room].remove(username)
        if not room_users[room]:  # remove the room if empty
            del room_users[room]

    # Emit the updated list of users to remaining users
    emit('user_list', {'users': room_users[room]}, to=room)

    print('RoomEvent: {} has left the room {}\n'.format(username, room))

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in socket_room_user_map:
        user_info = socket_room_user_map[session_id]
        room = user_info['room']
        username = user_info['username']
        
        # Handle as if the user sent a leave event
        leave({'username': username, 'room': room})

        # Clean up map after handling disconnection
        del socket_room_user_map[session_id]

        print('DisconnectEvent: {} has been disconnected from the room {}\n'.format(username, room))

@socketio.on('data')
def transfer_data(message):
    username = message['username']
    room = message['room']
    data = message['data']
    print('DataEvent: {} has sent the data:\n {}\n'.format(username, data))
    emit('data', data, to=room, skip_sid=request.sid)

@socketio.on_error_default
def default_error_handler(e):
    print("Error: {}".format(e))
    socketio.stop()

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5004)
