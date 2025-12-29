"""
ADK Chat UI - Flask application with PERSISTENT memory (SQLite)
"""

from flask import Flask, render_template_string, request, jsonify
import requests
import os
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

ADK_API_BASE = os.environ.get('ADK_API_BASE', 'http://localhost:8000')
DB_PATH = os.environ.get('DB_PATH', 'adk_chat_sessions.db')

# ---------------- Database ---------------- #

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(agent, user_id, session_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT
            )
        """)
        conn.commit()

def session_key(agent, user, session):
    return f"{agent}:{user}:{session}"

def save_session(agent, user, session):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO sessions
            (agent, user_id, session_id, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE(
                (SELECT created_at FROM sessions WHERE agent=? AND user_id=? AND session_id=?),
                ?
            ), ?)
        """, (agent, user, session, agent, user, session, now, now))
        conn.commit()

def save_message(sk, role, content):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO messages (session_key, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sk, role, content, datetime.utcnow().isoformat()))
        conn.commit()

def get_sessions(agent, user):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT session_id, created_at
            FROM sessions
            WHERE agent=? AND user_id=?
            ORDER BY updated_at DESC
        """, (agent, user)).fetchall()

        result = {}
        for r in rows:
            sk = session_key(agent, user, r["session_id"])
            msgs = conn.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE session_key=?
                ORDER BY timestamp
            """, (sk,)).fetchall()

            result[r["session_id"]] = {
                "created": r["created_at"],
                "messages": [dict(m) for m in msgs]
            }
        return result

# ---------------- HTML ---------------- #

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ADK Chat</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
<style>
body { font-family: system-ui; background:#f4f5fa; height:100vh; margin:0; display:flex; }
.sidebar { width:260px; background:#6c5ce7; color:white; padding:15px; display:flex; flex-direction:column; }
.sessions { flex:1; overflow:auto; }
.session { padding:10px; border-radius:8px; cursor:pointer; margin-bottom:6px; background:rgba(255,255,255,.2); }
.session.active { background:white; color:#6c5ce7; font-weight:600; }
.main { flex:1; display:flex; flex-direction:column; }
.messages { flex:1; overflow:auto; padding:20px; background:#fafafa; }
.msg { max-width:70%; padding:12px 16px; border-radius:16px; margin-bottom:10px; }
.msg.user { margin-left:auto; background:#6c5ce7; color:white; }
.msg.assistant { background:white; border:1px solid #ddd; }
.input { display:flex; gap:10px; padding:15px; border-top:1px solid #ddd; }
input { flex:1; padding:12px 16px; border-radius:20px; border:1px solid #ccc; }
button { padding:12px 24px; border:none; border-radius:20px; background:#6c5ce7; color:white; font-weight:600; cursor:pointer; }
</style>
</head>
<body>

<div class="sidebar">
    <select id="agent"></select>
    <div class="sessions" id="sessions"></div>
    <button onclick="newSession()">+ New</button>
</div>

<div class="main">
    <div class="messages" id="messages"></div>
    <form class="input" id="form">
        <input id="input" placeholder="Type a message..." />
        <button>Send</button>
    </form>
</div>

<script>
let agent="", user="user_"+Date.now(), current=null, sessions={};

marked.setOptions({breaks:true});

async function loadAgents(){
    const r = await fetch('/api/list-agents');
    const a = await r.json();
    const sel = document.getElementById('agent');
    sel.innerHTML = '<option value="">Select agent</option>';
    a.forEach(x=>{
        let o=document.createElement('option');
        o.value=o.textContent=x;
        sel.appendChild(o);
    });
}

document.getElementById('agent').onchange = async e=>{
    agent=e.target.value;
    current=null;
    sessions={};
    if(agent){
        const r=await fetch(`/api/sessions?agent=${agent}&user=${user}`);
        sessions=await r.json();
        renderSessions();
    }
};

function renderSessions(){
    const c=document.getElementById('sessions');
    c.innerHTML='';
    Object.keys(sessions).forEach(s=>{
        const d=document.createElement('div');
        d.className='session'+(s===current?' active':'');
        d.textContent=s;
        d.onclick=()=>{
            current=s;
            sessions[s].messages ||= [];
            renderSessions();
            renderMessages();
        };
        c.appendChild(d);
    });
}

function renderMessages(){
    const m=document.getElementById('messages');
    m.innerHTML='';
    if(!current) return;
    sessions[current].messages.forEach(x=>{
        const d=document.createElement('div');
        d.className='msg '+x.role;
        d.innerHTML=marked.parse(x.content);
        m.appendChild(d);
    });
    m.scrollTop=m.scrollHeight;
}

async function newSession(){
    if(!agent) return alert("Select agent");
    const s="s_"+Date.now();
    await fetch('/api/create-session',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({agent,userId:user,sessionId:s})});
    sessions[s]={created:new Date().toISOString(),messages:[]};
    current=s;
    renderSessions();
    renderMessages();
}

document.getElementById('form').onsubmit=async e=>{
    e.preventDefault();
    if(!current) return;
    const input=document.getElementById('input');
    const text=input.value.trim();
    if(!text) return;
    input.value='';
    sessions[current].messages.push({role:'user',content:text});
    renderMessages();
    const r=await fetch('/api/send-message',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({agent,userId:user,sessionId:current,message:text})});
    const d=await r.json();
    if(d.response){
        sessions[current].messages.push({role:'assistant',content:d.response});
        renderMessages();
    }
};

loadAgents();
</script>
</body>
</html>
"""

# ---------------- Routes ---------------- #

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/list-agents")
def list_agents():
    try:
        r=requests.get(f"{ADK_API_BASE}/list-apps",timeout=5)
        return jsonify(r.json() if r.ok else [])
    except:
        return jsonify([])

@app.route("/api/sessions")
def api_sessions():
    return jsonify(get_sessions(request.args["agent"], request.args["user"]))

@app.route("/api/create-session",methods=["POST"])
def create_session():
    d=request.json
    requests.post(f"{ADK_API_BASE}/apps/{d['agent']}/users/{d['userId']}/sessions/{d['sessionId']}",json={})
    save_session(d["agent"],d["userId"],d["sessionId"])
    return jsonify({"ok":True})

@app.route("/api/send-message",methods=["POST"])
def send_message():
    d=request.json
    sk=session_key(d["agent"],d["userId"],d["sessionId"])
    save_message(sk,"user",d["message"])
    save_session(d["agent"],d["userId"],d["sessionId"])

    r=requests.post(f"{ADK_API_BASE}/run",json={
        "appName":d["agent"],
        "userId":d["userId"],
        "sessionId":d["sessionId"],
        "newMessage":{"role":"user","parts":[{"text":d["message"]}]}
    },timeout=240)

    text=""
    if r.ok:
        for e in r.json():
            for p in e.get("content",{}).get("parts",[]):
                text+=p.get("text","")
        if text:
            save_message(sk,"assistant",text)

    return jsonify({"response":text})

# ---------------- Run ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
