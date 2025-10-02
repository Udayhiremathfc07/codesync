(() => {
  let username = sessionStorage.getItem("codesync_username");
  let room = sessionStorage.getItem("codesync_room");

  if (!username) {
    username = prompt("Enter your name", "User" + Math.floor(Math.random() * 1000)) || "Anonymous";
    sessionStorage.setItem("codesync_username", username);
  }
  if (!room) {
    room = prompt("Enter room name (eg. room1)", "room1") || "room1";
    sessionStorage.setItem("codesync_room", room);
  }

  document.getElementById("roomName").innerText = room;

  const socket = io(window.location.origin, { transports: ["websocket", "polling"] });

  socket.on("connect", () => {
    document.getElementById("statusText").innerText = "Connected";
    socket.emit("join", { username, room });
  });

  socket.on("disconnect", () => {
    document.getElementById("statusText").innerText = "Disconnected";
  });

  // ---------------- Users
  const cursorWidgets = {};
  socket.on("update_users", (data) => {
    const ul = document.getElementById("usersList");
    ul.innerHTML = "";
    (data.users || []).forEach(u => {
      const li = document.createElement("li");
      li.textContent = u;
      ul.appendChild(li);
    });

    const users = data.users || [];
    for (const u in cursorWidgets) {
      if (!users.includes(u)) {
        try { editor.removeContentWidget(cursorWidgets[u]); } catch(e){}
        delete cursorWidgets[u];
      }
    }
  });

  // ---------------- Chat + typing
  socket.on("status", (data) => addChatMessage("SYSTEM", data.msg, true));
  socket.on("chat_message", (d) => addChatMessage(d.username, d.msg, false));
  socket.on("show_typing", (d) => {
    const el = document.getElementById("typingIndicator");
    el.innerText = `${d.username} is typing...`;
    clearTimeout(window._typingClear);
    window._typingClear = setTimeout(() => { el.innerText = ""; }, 1500);
  });

  // ---------------- Monaco Editor
  window.MonacoEnvironment = {
    getWorkerUrl: function(_, label) {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/' };
        importScripts('https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs/base/worker/workerMain.js');`
      )}`;
    },
  };

  require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs" } });

  let editor, applyingRemote = false;

  require(["vs/editor/editor.main"], function () {
    editor = monaco.editor.create(document.getElementById("editor"), {
      language: "python",
      value: `print("Hello from Codesync")\n`,
      theme: "vs-dark",
      automaticLayout: true,
      fontSize: 14,
    });

    const restored = localStorage.getItem("restore_code");
    if (restored) { editor.setValue(restored); localStorage.removeItem("restore_code"); }

    let t;
    editor.onDidChangeModelContent(() => {
      if (applyingRemote) return;
      clearTimeout(t);
      t = setTimeout(() => socket.emit("code_change", { room, code: editor.getValue() }), 150);
      socket.emit("typing", { username, room });
    });

    editor.onDidChangeCursorPosition((e) => socket.emit("cursor_move", { username, room, position: e.position }));

    document.getElementById("themeSwitcher").addEventListener("change", function() {
      monaco.editor.setTheme(this.value);
    });
  });

  socket.on("code_update", (d) => {
    if (!editor) return;
    if (d.code !== editor.getValue()) { applyingRemote = true; editor.setValue(d.code); applyingRemote = false; }
  });

  socket.on("show_cursor", (data) => {
    if (!editor || data.username === username) return;
    const u = data.username;
    const pos = data.position;

    if (cursorWidgets[u]) {
      try { editor.removeContentWidget(cursorWidgets[u]); } catch(e){}
      delete cursorWidgets[u];
    }

    function makeWidget(u,pos) {
      const dom = document.createElement("div");
      dom.className = "cursor-label";
      dom.textContent = u;
      dom.style.background = getColorForUser(u);
      dom.style.color = "#000"; dom.style.padding = "2px 6px";
      dom.style.borderRadius = "4px"; dom.style.fontSize = "11px"; dom.style.fontWeight="600"; dom.style.whiteSpace="nowrap";
      return { getId: () => "cursor.widget." + u, getDomNode: () => dom, getPosition: () => ({ position: pos, preference: [monaco.editor.ContentWidgetPositionPreference.ABOVE] }) };
    }

    const widget = makeWidget(u,pos);
    cursorWidgets[u] = widget;
    editor.addContentWidget(widget);
  });

  socket.on("run_result", (data) => {
    const out = document.getElementById("output");
    if (data.output?.run) { out.textContent = data.output.run.output || data.output.run.stdout || data.output.run.stderr || JSON.stringify(data.output,null,2); }
    else if (data.error) out.textContent = "Error: " + data.error;
    else out.textContent = "Unknown response: " + JSON.stringify(data);
  });

  // ---------------- Helpers
  function addChatMessage(user,msg,isSystem=false){
    const box = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "chat-message";

    const time = new Date().toLocaleTimeString();

    if(isSystem){
      div.innerHTML = `<span class="timestamp">[${time}]</span> <span class="chat-system">[SYSTEM]</span> <span class="text">${msg}</span>`;
    }else{
      const color = getColorForUser(user);
      const initials = user.charAt(0).toUpperCase();
      div.innerHTML = `<div class="chat-avatar" style="background:${color}">${initials}</div>
                       <div class="chat-content">
                         <span class="timestamp">[${time}]</span>
                         <span class="username" style="color:${color}">${user}:</span>
                         <span class="text">${msg}</span>
                       </div>`;
    }
    box.appendChild(div); box.scrollTop = box.scrollHeight;
  }

  function getColorForUser(u){
    const colors = ["#ffcc00","#00ccff","#ff66cc","#66ff66","#ff4444","#cc99ff","#ff9933","#3399ff","#99cc33","#ff6699"];
    let hash=0; for(let i=0;i<u.length;i++) hash=u.charCodeAt(i)+((hash<<5)-hash);
    return colors[Math.abs(hash)%colors.length];
  }

  // ---------------- UI bindings
  document.getElementById("sendBtn").addEventListener("click",()=>{ const input=document.getElementById("chatInput"); const msg=input.value.trim(); if(!msg) return; socket.emit("chat_message",{username,room,msg}); input.value=""; });
  document.getElementById("chatInput").addEventListener("keypress",(e)=>{ if(e.key==="Enter") document.getElementById("sendBtn").click(); });
  document.getElementById("saveBtn").addEventListener("click",async()=>{
    const code = editor ? editor.getValue() : "";
    await fetch(`${window.location.origin}/api/snapshots`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({code, room_id:room, username}) });
    alert(`Snapshot saved for ${username} in room ${room}`);
  });
  document.getElementById("runBtn").addEventListener("click",()=>{
    const code = editor ? editor.getValue() : "";
    const language = document.getElementById("language").value;
    document.getElementById("output").textContent = "Running...";
    socket.emit("run_code",{room,code,language});
  });
  document.getElementById("leaveBtn").addEventListener("click",()=>{
    socket.emit("leave",{username,room}); socket.disconnect();
    document.getElementById("statusText").innerText="Left room";
    addChatMessage("SYSTEM",`You left the room`,true);
    sessionStorage.removeItem("codesync_username"); sessionStorage.removeItem("codesync_room");
  });
  document.getElementById("viewSnapshotsBtn").addEventListener("click",()=>{ window.location.href=`snapshots.html?room=${encodeURIComponent(room)}`; });
  document.getElementById("language").addEventListener("change",function(){ if(editor) monaco.editor.setModelLanguage(editor.getModel(),this.value); });

  // ---------------- Splitter Logic
  const dragY = document.getElementById("dragY");
  const output = document.getElementById("output");
  dragY.addEventListener("mousedown",(e)=>{
    e.preventDefault();
    document.onmousemove=(ev)=>{ const newHeight = window.innerHeight - ev.clientY - 50; output.style.height=newHeight+"px"; };
    document.onmouseup=()=>document.onmousemove=null;
  });

  const dragX = document.getElementById("dragX");
  const chat = document.getElementById("chat");
  dragX.addEventListener("mousedown",(e)=>{
    e.preventDefault();
    document.onmousemove=(ev)=>{ chat.style.width=window.innerWidth-ev.clientX+"px"; };
    document.onmouseup=()=>document.onmousemove=null;
  });
})();
