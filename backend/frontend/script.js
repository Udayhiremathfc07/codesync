// script.js

// ✅ Connect to your Flask-SocketIO backend
// If backend runs at http://127.0.0.1:5000
const socket = io("http://127.0.0.1:5000", {
  transports: ["websocket"], // force WebSocket for stability
});

// --- Connection events ---
socket.on("connect", () => {
  console.log("✅ Connected to Socket.IO server!");
});

socket.on("disconnect", () => {
  console.log("❌ Disconnected from Socket.IO server!");
});

socket.on("connect_error", (err) => {
  console.error("⚠️ Connection error:", err.message);
});

// --- Example: listen for updates from backend ---
socket.on("update", (data) => {
  console.log("📩 Update received from server:", data);
});

// --- Example: send a test message ---
document.addEventListener("DOMContentLoaded", () => {
  const testBtn = document.createElement("button");
  testBtn.textContent = "Send Test Event";
  document.body.appendChild(testBtn);

  testBtn.addEventListener("click", () => {
    socket.emit("test_event", { msg: "Hello from frontend!" });
    console.log("📤 Sent test_event");
  });
});