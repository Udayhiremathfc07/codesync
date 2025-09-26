// Helper function for requests
async function apiRequest(url, method = "GET", body = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(url, options);
  return res.json();
}

// ---- Users ----
document.getElementById("createUserBtn").addEventListener("click", async () => {
  const username = document.getElementById("usernameInput").value;
  const result = await apiRequest("/api/users", "POST", { username });
  document.getElementById("usersOutput").textContent = JSON.stringify(result, null, 2);
});

document.getElementById("getUsersBtn").addEventListener("click", async () => {
  const result = await apiRequest("/api/users");
  document.getElementById("usersOutput").textContent = JSON.stringify(result, null, 2);
});

// ---- Rooms ----
document.getElementById("createRoomBtn").addEventListener("click", async () => {
  const room_code = document.getElementById("roomInput").value;
  const result = await apiRequest("/api/rooms", "POST", { room_code });
  document.getElementById("roomsOutput").textContent = JSON.stringify(result, null, 2);
});

document.getElementById("getRoomsBtn").addEventListener("click", async () => {
  const result = await apiRequest("/api/rooms");
  document.getElementById("roomsOutput").textContent = JSON.stringify(result, null, 2);
});

// ---- Messages ----
document.getElementById("createMessageBtn").addEventListener("click", async () => {
  const text = document.getElementById("messageText").value;
  const user_id = parseInt(document.getElementById("messageUserId").value);
  const room_id = parseInt(document.getElementById("messageRoomId").value);
  const result = await apiRequest("/api/messages", "POST", { text, user_id, room_id });
  document.getElementById("messagesOutput").textContent = JSON.stringify(result, null, 2);
});

document.getElementById("getMessagesBtn").addEventListener("click", async () => {
  const result = await apiRequest("/api/messages");
  document.getElementById("messagesOutput").textContent = JSON.stringify(result, null, 2);
});

// ---- Snapshots ----
document.getElementById("createSnapshotBtn").addEventListener("click", async () => {
  const code = document.getElementById("snapshotCode").value;
  const room_id = parseInt(document.getElementById("snapshotRoomId").value);
  const result = await apiRequest("/api/snapshots", "POST", { code, room_id });
  document.getElementById("snapshotsOutput").textContent = JSON.stringify(result, null, 2);
});

document.getElementById("getSnapshotsBtn").addEventListener("click", async () => {
  const result = await apiRequest("/api/snapshots");
  document.getElementById("snapshotsOutput").textContent = JSON.stringify(result, null, 2);
});
