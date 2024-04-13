import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

try:
    with open('users.json', 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    print("Error: users.json file not found.")
    users = []
except json.JSONDecodeError:
    print("Error: users.json file contains invalid JSON data.")
    users = []

try:
    with open('chat_rooms.json', 'r') as f:
        chat_rooms = json.load(f)
except FileNotFoundError:
    print("Error: chat_rooms.json file not found.")
    chat_rooms = []
except json.JSONDecodeError:
    print("Error: chat_rooms.json file contains invalid JSON data.")
    chat_rooms = []

for idx, room in enumerate(chat_rooms):
    room['id'] = f"{idx:04d}"

@app.route('/')
def index():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/get_messages/<int:room_id>')
def get_messages(room_id):
    if room_id < 0 or room_id >= len(chat_rooms):
        return jsonify({'error': 'Room not found'})
    return jsonify(chat_rooms[room_id]['messages'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))

        return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        for user in users:
            if user['username'] == username:
                return render_template('signup.html', error='Username already exists')

        users.append({'username': username, 'password': password})
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        session['username'] = username
        return redirect(url_for('index'))

    return render_template('signup.html')

@app.route('/chat_room_list', methods=['GET', 'POST'])
def chat_room_list():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        command = request.form['command']

        if command.isdigit() and len(command) == 4:
            room_id = int(command)
            if 0 <= room_id < len(chat_rooms):
                return redirect(url_for('chat_room', room_id=room_id))

        for room in chat_rooms:
            if room['name'] == command:
                return redirect(url_for('chat_room', room_id=room['id']))

        if command.lower() == 'back':
            return redirect(url_for('index'))

        return render_template('chat_room_list.html', chat_rooms=chat_rooms, error='Invalid command')

    return render_template('chat_room_list.html', chat_rooms=chat_rooms)

@app.route('/chat_room/<int:room_id>', methods=['GET', 'POST'])
def chat_room(room_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    room = chat_rooms[room_id]

    if request.method == 'POST':
        message = request.form['message']
        room['messages'].append({'username': session['username'], 'message': message})

        with open('chat_rooms.json', 'w') as f:
            json.dump(chat_rooms, f, indent=4)

        socketio.emit('message', {'username': session['username'], 'message': message}, room=room_id)

    return render_template('chat_room.html', room=room, room_id=room_id)

@app.route('/create_chat_room', methods=['GET', 'POST'])
def create_chat_room():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        room_name = request.form['room_name']
        password = request.form['password']

        chat_rooms.append({'name': room_name, 'password': password, 'messages': []})

        with open('chat_rooms.json', 'w') as f:
            json.dump(chat_rooms, f, indent=4)

        chat_rooms[-1]['id'] = f"{len(chat_rooms) - 1:04d}"

        return redirect(url_for('chat_room_list'))

    return render_template('create_chat_room.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app)