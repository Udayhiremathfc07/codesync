import eventlet
eventlet.monkey_patch() 

import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_sqlalchemy import SQLAlchemy
import requests

# ----------------- Config -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "codesync.db")

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# Use DATABASE_URL if provided (PostgreSQL on Render) otherwise fallback to SQLite
db_url = os.environ.get("DATABASE_URL") or f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# SocketIO with eventlet for production
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

print("📂 Database will be stored at:", DB_PATH)
print("🔗 Using DB URL:", db_url)

# ----------------- Models -----------------
class Snapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ----------------- In-memory rooms -----------------
rooms = {}    # rooms[room] = {"users": set(), "code": ""}
clients = {}  # clients[sid] = {"username":..., "room":...}

# ----------------- Routes -----------------
# Serve frontend
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory("frontend", path)

# API endpoints
@app.route("/api/snapshots", methods=["POST"])
def save_snapshot():
    data = request.json or {}
    code = data.get("code", "")
    room_id = data.get("room_id", "default")
    username = data.get("username", "Unknown")

    snap = Snapshot(room=room_id, username=username, code=code)
    db.session.add(snap)
    db.session.commit()

    return jsonify({
        "room": room_id,
        "username": username,
        "code": code,
        "status": "saved",
        "id": snap.id,
        "timestamp": snap.timestamp.isoformat()
    }), 201

@app.route("/api/snapshots/<room_id>", methods=["GET"])
def get_snapshots(room_id):
    snaps = Snapshot.query.filter_by(room=room_id).order_by(Snapshot.timestamp.desc()).all()
    return jsonify([{
        "id": s.id,
        "room": s.room,
        "username": s.username,
        "code": s.code,
        "timestamp": s.timestamp.isoformat()
    } for s in snaps])

# ----------------- Socket Events -----------------
@socketio.on("join")
def handle_join(data):
    username = data.get("username")
    room = str(data.get("room"))
    if not username or not room:
        return

    sid = request.sid
    join_room(room)
    clients[sid] = {"username": username, "room": room}

    if room not in rooms:
        rooms[room] = {"users": set(), "code": ""}
    rooms[room]["users"].add(username)

    emit("status", {"msg": f"{username} joined {room}"}, room=room)
    emit("update_users", {"users": list(rooms[room]["users"])}, room=room)

    if rooms[room]["code"]:
        emit("code_update", {"code": rooms[room]["code"]}, room=sid)

@socketio.on("leave")
def handle_leave(data):
    username = data.get("username")
    room = str(data.get("room"))
    if not username or not room:
        return

    sid = request.sid
    leave_room(room)
    if room in rooms and username in rooms[room]["users"]:
        rooms[room]["users"].remove(username)

    clients.pop(sid, None)

    emit("status", {"msg": f"{username} left {room}"}, room=room)
    emit("update_users", {"users": list(rooms.get(room, {"users": set()})["users"])}, room=room)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    info = clients.pop(sid, None)
    if not info:
        return
    username = info.get("username")
    room = info.get("room")
    if room in rooms and username in rooms[room]["users"]:
        rooms[room]["users"].remove(username)

    emit("status", {"msg": f"{username} disconnected"}, room=room)
    emit("update_users", {"users": list(rooms.get(room, {"users": set()})["users"])}, room=room)

@socketio.on("code_change")
def handle_code_change(data):
    room = str(data.get("room"))
    code = data.get("code", "")
    if not room:
        return
    rooms.setdefault(room, {"users": set(), "code": ""})
    rooms[room]["code"] = code
    emit("code_update", {"code": code}, room=room, include_self=False)

@socketio.on("chat_message")
def handle_chat_message(data):
    room = str(data.get("room"))
    username = data.get("username")
    msg = data.get("msg")
    emit("chat_message", {"username": username, "msg": msg}, room=room)

@socketio.on("typing")
def handle_typing(data):
    room = data.get("room")
    username = data.get("username")
    emit("show_typing", {"username": username}, room=room, include_self=False)

@socketio.on("cursor_move")
def handle_cursor_move(data):
    room = data.get("room")
    username = data.get("username")
    position = data.get("position")
    if not room or not username or not position:
        return
    emit("show_cursor", {"username": username, "position": position}, room=room, include_self=False)

@socketio.on("run_code")
def handle_run_code(data):
    room = str(data.get("room"))
    code = data.get("code", "")
    language = data.get("language", "python")

    lang_map = {
        "python": "python3",
        "javascript": "javascript",
        "cpp": "cpp",
        "c": "c",
        "java": "java",
    }
    runtime = lang_map.get(language, "python3")

    payload = {
        "language": runtime,
        "version": "*",
        "files": [{"content": code}]
    }

    try:
        resp = requests.post("https://emkc.org/api/v2/piston/execute", json=payload, timeout=20)
        result = resp.json()
        socketio.emit("run_result", {"output": result}, room=room)
    except Exception as e:
        socketio.emit("run_result", {"error": str(e)}, room=room)

@socketio.on("file_upload")
def handle_file_upload(data):
    room = data.get("room")
    filename = data.get("filename")
    filedata = data.get("data")

    # Safeguard: reject very large files
    if len(filedata) > 2 * 1024 * 1024:  # ~2MB
        emit("chat_message", {"username": "SYSTEM", "msg": f"File {filename} too large."}, room=request.sid)
        return

    emit("file_message", data, room=room)

# ----------------- Run App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
