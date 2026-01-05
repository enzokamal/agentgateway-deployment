"""
ADK Orchestrator Chat UI - Fixed Version
- Multi-agent support
- Session memory (in-browser)
- Markdown rendering
- Reporting-agent chart visualization (Plotly)
- Correct ADK /run endpoint usage
- Proper session management
"""

from flask import Flask, render_template_string, request, jsonify
import requests
import os
import json
import re
import logging
from datetime import datetime
from chart_tool import chart_tool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

ADK_API_BASE = os.environ.get("ADK_API_BASE", "http://localhost:8070")
HOST = os.environ.get("ADK_CHAT_UI_HOST", "0.0.0.0")
PORT = int(os.environ.get("ADK_CHAT_UI_PORT", 5000))

# ------------------------------------------------------------------------------
# In-memory session store (like the working version)
# ------------------------------------------------------------------------------
sessions_store = {}

# ------------------------------------------------------------------------------
# HTML UI - Fixed with proper session handling
# ------------------------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ADK Orchestrator UI</title>

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: #f5f5f5;
    color: #333;
    height: 100vh;
}

.container {
    display: flex;
    height: 100vh;
    max-width: 1400px;
    margin: 0 auto;
    background: white;
}

/* Sidebar */
.sidebar {
    width: 280px;
    background: #f8f9fa;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h2 {
    font-size: 18px;
    margin-bottom: 15px;
    color: #333;
}

#agent {
    width: 100%;
    padding: 10px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    background: white;
    cursor: pointer;
    margin-bottom: 15px;
}

#agent:focus {
    border-color: #667eea;
    outline: none;
}

.new-session-btn {
    width: 100%;
    padding: 12px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 20px;
    transition: background 0.2s;
}

.new-session-btn:hover {
    background: #5568d3;
}

.new-session-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.sessions-container {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
}

.session {
    padding: 12px 15px;
    margin-bottom: 8px;
    background: white;
    border: 2px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.session:hover {
    border-color: #667eea;
    transform: translateX(5px);
}

.session.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.session-id {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 4px;
}

.session-time {
    font-size: 12px;
    opacity: 0.8;
}

/* Chat area */
.chat {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.chat-header {
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
    background: white;
}

.chat-header h1 {
    font-size: 20px;
    color: #333;
}

.messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: #fafbfc;
}

.message {
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
}

.message.user {
    align-items: flex-end;
}

.bubble {
    max-width: 70%;
    padding: 15px 20px;
    border-radius: 18px;
    line-height: 1.5;
    word-wrap: break-word;
}

.message.user .bubble {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.message.assistant .bubble {
    background: white;
    color: #333;
    border: 1px solid #e0e0e0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* Markdown styling */
.bubble h1, .bubble h2, .bubble h3 {
    margin-top: 10px;
    margin-bottom: 8px;
    font-weight: 600;
}

.bubble h1 { font-size: 1.4em; }
.bubble h2 { font-size: 1.2em; }
.bubble h3 { font-size: 1.1em; }

.bubble p {
    margin-bottom: 10px;
}

.bubble ul, .bubble ol {
    margin-left: 20px;
    margin-bottom: 10px;
}

.bubble li {
    margin-bottom: 5px;
}

.bubble code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}

.message.user .bubble code {
    background: rgba(255,255,255,0.2);
}

.bubble pre {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 10px 0;
}

.bubble pre code {
    background: none;
    padding: 0;
}

.bubble blockquote {
    border-left: 4px solid #667eea;
    padding-left: 15px;
    margin: 10px 0;
    color: #666;
}

.bubble a {
    color: #667eea;
    text-decoration: none;
}

.bubble a:hover {
    text-decoration: underline;
}

/* Chart container */
.chart-container {
    margin: 15px 0;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    background: white;
    
}

/* Input area */
.input-area {
    padding: 20px;
    border-top: 1px solid #e0e0e0;
    background: white;
}

.input-form {
    display: flex;
    gap: 10px;
}

#input {
    flex: 1;
    padding: 15px 20px;
    border: 2px solid #e0e0e0;
    border-radius: 25px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}

#input:focus {
    border-color: #667eea;
}

#input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
}

#send {
    padding: 15px 30px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: transform 0.2s;
}

#send:hover:not(:disabled) {
    transform: scale(1.05);
}

#send:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: scale(1);
}

/* Loading indicator */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Empty states */
.empty-state {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #999;
    text-align: center;
    padding: 40px;
}

.empty-state-icon {
    font-size: 48px;
    margin-bottom: 20px;
    opacity: 0.5;
}
</style>
</head>

<body>
<div class="container">

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>ADK Orchestrator</h2>
      <select id="agent">
        <option value="">Select Agent...</option>
      </select>
      <button class="new-session-btn" id="newSessionBtn" disabled>+ New Session</button>
    </div>
    
    <div class="sessions-container" id="sessionsContainer">
      <div class="empty-state">
        <div class="empty-state-icon">💬</div>
        <p>Select an agent to start</p>
      </div>
    </div>
  </div>

  <!-- Chat Area -->
  <div class="chat">
    <div class="chat-header">
      <h1 id="chatTitle">Welcome to ADK Orchestrator</h1>
    </div>
    
    <div class="messages" id="messagesContainer">
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <h3>Start a Conversation</h3>
        <p>Select an agent and create a new session to begin</p>
      </div>
    </div>
    
    <div class="input-area">
      <form class="input-form" id="messageForm">
        <input id="input" placeholder="Type your message..." disabled />
        <button type="submit" id="send" disabled>Send</button>
      </form>
    </div>
  </div>

</div>

<script>
let currentAgent = '';
let currentUserId = 'user_' + Date.now();
let currentSessionId = null;
let sessions = {};

// Configure marked
marked.setOptions({
    breaks: true,
    gfm: true
});

// Load agents on page load
async function loadAgents() {
    try {
        const response = await fetch('/api/list-agents');
        const agents = await response.json();
        
        const selector = document.getElementById('agent');
        selector.innerHTML = '<option value="">Select Agent...</option>';
        
        agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent;
            option.textContent = agent;
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading agents:', error);
    }
}

// Load sessions for current agent
async function loadSessions() {
    if (!currentAgent) return;
    
    try {
        const response = await fetch(`/api/sessions?agent=${currentAgent}&user=${currentUserId}`);
        const data = await response.json();
        sessions = data;
        
        renderSessions();
    } catch (error) {
        console.error('Error loading sessions:', error);
        sessions = {};
        renderSessions();
    }
}

// Render sessions in sidebar
function renderSessions() {
    const container = document.getElementById('sessionsContainer');
    const sessionIds = Object.keys(sessions);
    
    if (sessionIds.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📁</div><p>No sessions yet</p></div>';
        return;
    }
    
    container.innerHTML = sessionIds.map(sessionId => {
        const session = sessions[sessionId];
        return `
            <div class="session ${sessionId === currentSessionId ? 'active' : ''}" 
                 onclick="selectSession('${sessionId}')">
                <div class="session-id">Session ${sessionId.substring(0, 8)}</div>
                <div class="session-time">${new Date(session.created || Date.now()).toLocaleString()}</div>
            </div>
        `;
    }).join('');
}

// Select a session
function selectSession(sessionId) {
    currentSessionId = sessionId;
    renderSessions();
    loadMessages();
    
    document.getElementById('input').disabled = false;
    document.getElementById('send').disabled = false;
    document.getElementById('chatTitle').textContent = `${currentAgent} - Session ${sessionId.substring(0, 8)}`;
}

// Load messages for current session
function loadMessages() {
    if (!currentSessionId || !sessions[currentSessionId]) return;
    
    const container = document.getElementById('messagesContainer');
    const messages = sessions[currentSessionId].messages || [];
    
    if (messages.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👋</div><h3>Start chatting!</h3><p>Send your first message below</p></div>';
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        let content = '';
        
        if (msg.chart) {
            const chartId = `chart-${index}`;
            content = `<div class="chart-container" id="${chartId}"></div>`;
        } else {
            content = marked.parse(msg.content || '');
        }
        
        return `
            <div class="message ${msg.role}">
                <div class="bubble">${content}</div>
            </div>
        `;
    }).join('');
    
    // Render charts after HTML is added
    messages.forEach((msg, index) => {
        if (msg.chart && msg.chart.data) {
            const chartDiv = document.getElementById(`chart-${index}`);
            if (chartDiv) {
                Plotly.newPlot(
                    chartDiv,
                    msg.chart.data,
                    msg.chart.layout || {}
                );
            }
        }
    });
    
    container.scrollTop = container.scrollHeight;
}

// Send message
document.getElementById('messageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('input');
    const message = input.value.trim();
    
    if (!message || !currentSessionId) return;
    
    const sendBtn = document.getElementById('send');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading"></span>';
    input.disabled = true;
    
    try {
        // Add user message to UI
        if (!sessions[currentSessionId].messages) {
            sessions[currentSessionId].messages = [];
        }
        sessions[currentSessionId].messages.push({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
        loadMessages();
        input.value = '';
        
        // Send to API
        const response = await fetch('/api/send-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent: currentAgent,
                userId: currentUserId,
                sessionId: currentSessionId,
                message: message
            })
        });
        
        const data = await response.json();
        
        // Add assistant response
        if (data.response || data.chart) {
            sessions[currentSessionId].messages.push({
                role: 'assistant',
                content: data.response || '',
                chart: data.chart || null,
                timestamp: new Date().toISOString()
            });
            loadMessages();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        input.disabled = false;
        input.focus();
    }
});

// Create new session
document.getElementById('newSessionBtn').addEventListener('click', async () => {
    if (!currentAgent) {
        alert('Please select an agent first');
        return;
    }
    
    const sessionId = 's_' + Date.now();
    
    try {
        const response = await fetch('/api/create-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent: currentAgent,
                userId: currentUserId,
                sessionId: sessionId
            })
        });
        
        if (response.ok) {
            sessions[sessionId] = {
                created: new Date().toISOString(),
                messages: []
            };
            selectSession(sessionId);
        }
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Failed to create session');
    }
});

// Agent selector change
document.getElementById('agent').addEventListener('change', (e) => {
    currentAgent = e.target.value;
    currentSessionId = null;
    
    const newSessionBtn = document.getElementById('newSessionBtn');
    newSessionBtn.disabled = !currentAgent;
    
    document.getElementById('input').disabled = true;
    document.getElementById('send').disabled = true;
    document.getElementById('chatTitle').textContent = currentAgent ? `${currentAgent} - Select or create a session` : 'Welcome to ADK Orchestrator';
    
    if (currentAgent) {
        loadSessions();
    } else {
        sessions = {};
        renderSessions();
        document.getElementById('messagesContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><h3>Start a Conversation</h3><p>Select an agent and create a new session to begin</p></div>';
    }
});

// Initialize
loadAgents();
</script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# Routes - Fixed to match working version
# ------------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route('/api/list-agents')
def list_agents():
    try:
        logger.info(f"Fetching agents from {ADK_API_BASE}/list-apps")
        response = requests.get(f'{ADK_API_BASE}/list-apps', timeout=5)
        if response.ok:
            agents = response.json()
            logger.info(f"Fetched agents: {agents}")
            return jsonify(agents)
        else:
            logger.error(f"Failed to fetch agents: HTTP {response.status_code}")
            return jsonify([]), response.status_code
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions')
def get_sessions():
    agent = request.args.get('agent')
    user = request.args.get('user')
    key = f"{agent}:{user}"
    sessions = sessions_store.get(key, {})
    logger.debug(f"Retrieved {len(sessions)} sessions for {key}")
    return jsonify(sessions)

@app.route('/api/create-session', methods=['POST'])
def create_session():
    data = request.json
    agent = data['agent']
    user_id = data['userId']
    session_id = data['sessionId']
    try:
        logger.info(f"Creating session {session_id} for agent {agent}")
        response = requests.post(
            f'{ADK_API_BASE}/apps/{agent}/users/{user_id}/sessions/{session_id}',
            json={},
            timeout=5
        )
        if response.ok:
            key = f"{agent}:{user_id}"
            sessions_store.setdefault(key, {})[session_id] = {
                'created': datetime.now().isoformat(),
                'messages': []
            }
            logger.info(f"Session {session_id} created")
            return jsonify({'status': 'success', 'sessionId': session_id})
        else:
            logger.error(f"Failed to create session: HTTP {response.status_code} - {response.text}")
            return jsonify({'status': 'error', 'message': f'HTTP {response.status_code}'}), response.status_code
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/api/send-message", methods=["POST"])
def send_message():
    data = request.json
    agent = data["agent"]
    user_id = data["userId"]
    session_id = data["sessionId"]
    message = data["message"]
    
    logger.info(f"Sending message to agent {agent}, session {session_id}")

    try:
        payload = {
            "appName": agent,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}]
            }
        }
        
        logger.debug(f"Request payload: {payload}")
        response = requests.post(f"{ADK_API_BASE}/run", json=payload, timeout=600)
        logger.debug(f"Response status: {response.status_code}")

        assistant_text = ""
        chart = None

        if response.ok:
            try:
                response_data = response.json()
                # Handle both single event and list of events
                if isinstance(response_data, list):
                    for event in response_data:
                        parts = event.get("content", {}).get("parts", [])
                        for part in parts:
                            assistant_text += part.get("text", "")
                else:
                    # Handle single event response
                    parts = response_data.get("content", {}).get("parts", [])
                    for part in parts:
                        assistant_text += part.get("text", "")
                        
                # Extract chart spec if present
                match = re.search(r"<chart_spec>(.*?)</chart_spec>", assistant_text, re.S)

                if match:
                    try:
                        spec = json.loads(match.group(1))

                        # OPTIONAL: attach analysis results if available
                        analysis_context = sessions_store \
                            .get(f"{agent}:{user_id}", {}) \
                            .get(session_id, {}) \
                            .get("analysis", {})

                        chart = chart_tool(spec, analysis_context)

                    except Exception as e:
                        logger.error(f"Chart parse error: {e}")
                        chart = None

                    # Remove chart_spec block from visible text
                    assistant_text = re.sub(
                        r"<chart_spec>.*?</chart_spec>",
                        "",
                        assistant_text,
                        flags=re.S
                    )
                    
            except Exception as e:
                logger.error(f"Failed to parse response JSON: {e}")
                assistant_text = str(response.text)

            # Store in session store
            key = f"{agent}:{user_id}"
            if key in sessions_store and session_id in sessions_store[key]:
                sessions_store[key][session_id].setdefault('messages', []).append({
                    'role': 'assistant',
                    'content': assistant_text,
                    'chart': chart,
                    'timestamp': datetime.now().isoformat()
                })

            return jsonify({'status': 'success', 'response': assistant_text, 'chart': chart})
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Failed to get response: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), response.status_code

    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return jsonify({'status': 'error', 'message': 'Request timed out after 4 minutes'}), 504
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ------------------------------------------------------------------------------
# Run server
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("ADK Orchestrator Chat UI - Fixed Version")
    logger.info(f"ADK API Base: {ADK_API_BASE}")
    logger.info(f"Starting server on http://{HOST}:{PORT}")
    logger.info("="*60)
    app.run(debug=True, host=HOST, port=PORT)