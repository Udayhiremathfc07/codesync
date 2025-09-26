from flask import Flask, jsonify, request
from flask_cors import CORS
from models import init_db, SessionLocal, User, Room, Message, CodeSnapshot

# Initialize Flask
app = Flask(__name__)
CORS(app)  # allow frontend requests
init_db()  # create tables

# ---- USERS ----
@app.route("/api/users", methods=["GET"])
def get_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return jsonify([{"id": u.id, "username": u.username} for u in users])

@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    session = SessionLocal()
    new_user = User(username=username)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    session.close()
    return jsonify({"id": new_user.id, "username": new_user.username})

# ---- ROOMS ----
@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    session = SessionLocal()
    rooms = session.query(Room).all()
    session.close()
    return jsonify([{"id": r.id, "room_code": r.room_code} for r in rooms])

@app.route("/api/rooms", methods=["POST"])
def create_room():
    data = request.get_json()
    room_code = data.get("room_code")
    session = SessionLocal()
    new_room = Room(room_code=room_code)
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    session.close()
    return jsonify({"id": new_room.id, "room_code": new_room.room_code})

# ---- MESSAGES ----
@app.route("/api/messages", methods=["GET"])
def get_messages():
    session = SessionLocal()
    messages = session.query(Message).all()
    session.close()
    return jsonify([
        {"id": m.id, "text": m.text, "timestamp": m.timestamp.isoformat(),
         "user_id": m.user_id, "room_id": m.room_id}
        for m in messages
    ])

@app.route("/api/messages", methods=["POST"])
def create_message():
    data = request.get_json()
    text = data.get("text")
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    session = SessionLocal()
    new_message = Message(text=text, user_id=user_id, room_id=room_id)
    session.add(new_message)
    session.commit()
    session.refresh(new_message)
    session.close()
    return jsonify({
        "id": new_message.id,
        "text": new_message.text,
        "timestamp": new_message.timestamp.isoformat(),
        "user_id": new_message.user_id,
        "room_id": new_message.room_id
    })

# ---- CODE SNAPSHOTS ----
@app.route("/api/snapshots", methods=["GET"])
def get_snapshots():
    session = SessionLocal()
    snapshots = session.query(CodeSnapshot).all()
    session.close()
    return jsonify([
        {"id": s.id, "code": s.code, "room_id": s.room_id}
        for s in snapshots
    ])

@app.route("/api/snapshots", methods=["POST"])
def create_snapshot():
    data = request.get_json()
    code = data.get("code")
    room_id = data.get("room_id")
    session = SessionLocal()
    new_snapshot = CodeSnapshot(code=code, room_id=room_id)
    session.add(new_snapshot)
    session.commit()
    session.refresh(new_snapshot)
    session.close()
    return jsonify({"id": new_snapshot.id, "code": new_snapshot.code, "room_id": new_snapshot.room_id})

# ---- RUN APP ----
if __name__ == "__main__":
    app.run(debug=True)
