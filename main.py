# Import necessary libraries and modules
from flask import Flask, render_template, redirect, request, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
import string

# Configure Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
socketio = SocketIO(app)

# Create a dictionary to store room informations - {room_code: {"username": [], "messages": []}}
rooms = {}

# Only uppercase letters and numbers for the code rooms
data = string.ascii_uppercase + '0123456789'

# Function to generate a random room code
def room_generator(size):

    while True:
        room_name = ''
        for _ in range(size):
            room_name += random.choice(data)
        if room_name not in rooms:
            return room_name


# Define the route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    # Clear the session
    session.clear()

    # Handle POST request
    if request.method == "POST":
        username = request.form.get('username')
        room_code = (request.form.get('room_code')).upper()
        join_room = request.form.get('join', False)
        create_room = request.form.get('create', False)

        # Check for missing username
        if not username:
            return render_template("index.html", error="You forgot to enter a name...", room_code=room_code, username=username)

        # Check for missing room code during join
        if join_room != False and not room_code:
            return render_template("index.html", error="You forgot to enter a room code...", room_code=room_code, username=username)

        # Check for existing room code during room creation
        if create_room != False and room_code in rooms:
            return render_template("index.html", error="This room already exists...", room_code=room_code, username=username)

        # Create a new room
        if create_room != False:
            # Check if the length is 5 and if it has only numbers and letters | else generate the room code
            if len(room_code) != 5 or any(char not in data for char in room_code.upper()):
                room_code = room_generator(5)
            else:
                room_code = room_code.upper()
            # Add the room code in the rooms dict
            rooms[room_code] = {"messages": []}

        # Check if the room code is/isn't in the rooms dict, in order to join a room it has to be already created
        elif room_code not in rooms:
            return render_template("index.html", error="Room does not exist...", room_code=room_code, username=username)

        # Redirect to the room and save the room code and the username in the session
        session["room_code"] = room_code
        session["username"] = username
        return redirect(url_for("room"))

    return render_template('index.html')


# Define the route for the room
@app.route("/room")
def room():
    # Get the room code from the session
    room_code = session.get('room_code')
    # Ensure username and room code are provided before accessing /room
    if room_code is None or session.get("username") is None or room_code not in rooms:
        return redirect(url_for("home"))

    return render_template('room.html', room_code=room_code, message_history=rooms[room_code]["messages"])


# Handle socket.io connection
@socketio.on("connect")
def connect(auth):
    # Get the room code and username from the session
    room_code = session.get("room_code")
    username = session.get("username")

    # Join the specified room
    join_room(room_code)
    # Send a notification message when a user joins the room
    send({"username": username, "message": "has joined the room"}, to=room_code)

# Handle socket.io disconnection
@socketio.on("disconnect")
def disconnect():
    # Get the room code and username from the session
    room_code = session.get("room_code")
    username = session.get("username")

    # Leave the specified room
    leave_room(room)
    # Send a notification message when a user leaves the room
    send({"username": username, "message": "has left the room"}, to=room_code)


# Handle socket.io messages
@socketio.on("message")
def message(message):
    # Get the room code from the session
    room_code = session.get("room_code")
    # Create a content dict with the username and the messages
    content = {
        "username": session.get("username"),
        "message": message["message"]
    }

    # Send the content to the specified room
    send(content, to=room_code)
    # Append the content message to the room's message history
    rooms[room_code]["messages"].append(content)



# Start the Flask app with SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)
