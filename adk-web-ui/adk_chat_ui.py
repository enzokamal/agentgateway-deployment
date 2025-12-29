"""
ADK Chat UI - Simple Flask application for Google ADK agents
Features:
- Session management (create, delete, list)
- Multi-agent support
- Persistent chat history
- Properly formatted responses with markdown support
"""

from flask import Flask, render_template_string, request, jsonify
import requests
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# --------------------------
# Configuration via environment variables
# --------------------------
ADK_API_BASE = os.environ.get('ADK_API_BASE', 'http://localhost:8000')
HOST = os.environ.get('ADK_CHAT_UI_HOST', '0.0.0.0')
PORT = int(os.environ.get('ADK_CHAT_UI_PORT', 5000))

# HTML Template with improved formatting
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK Chat Interface</title>
    <!-- Marked.js for markdown rendering -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 90%;
            max-width: 1200px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 280px;
            background: #f7f9fc;
            border-right: 1px solid #e0e0e0;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .sidebar-header h2 {
            font-size: 20px;
            margin-bottom: 10px;
        }
        
        .agent-selector {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }
        
        .sessions-container {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }
        
        .session-item {
            padding: 12px;
            margin-bottom: 8px;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        
        .session-item:hover {
            border-color: #667eea;
            transform: translateX(5px);
        }
        
        .session-item.active {
            background: #667eea;
            color: white;
        }
        
        .session-name {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }
        
        .session-time {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .new-session-btn {
            margin: 15px;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.2s;
        }
        
        .new-session-btn:hover {
            background: #5568d3;
        }
        
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            background: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-header h1 {
            font-size: 22px;
            color: #333;
        }
        
        .delete-btn {
            padding: 8px 16px;
            background: #ff4757;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }
        
        .delete-btn:hover {
            background: #ee5a6f;
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
        
        .message-content {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 18px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }
        
        /* Markdown formatting inside messages */
        .message-content h1, .message-content h2, .message-content h3 {
            margin-top: 10px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .message-content h1 { font-size: 1.4em; }
        .message-content h2 { font-size: 1.2em; }
        .message-content h3 { font-size: 1.1em; }
        
        .message-content p {
            margin-bottom: 10px;
        }
        
        .message-content ul, .message-content ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        .message-content li {
            margin-bottom: 5px;
        }
        
        .message-content code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .message.user .message-content code {
            background: rgba(255,255,255,0.2);
        }
        
        .message-content pre {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 10px 0;
        }
        
        .message-content pre code {
            background: none;
            padding: 0;
        }
        
        .message-content blockquote {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 10px 0;
            color: #666;
        }
        
        .message-content a {
            color: #667eea;
            text-decoration: none;
        }
        
        .message-content a:hover {
            text-decoration: underline;
        }
        
        .message-content strong {
            font-weight: 600;
        }
        
        .message-content em {
            font-style: italic;
        }
        
        .message-time {
            font-size: 11px;
            color: #999;
            margin-top: 5px;
            padding: 0 10px;
        }
        
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-form {
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        .message-input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
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
        
        .send-btn:hover {
            transform: scale(1.05);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: scale(1);
        }
        
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
        
        .empty-state {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>ADK Chat</h2>
                <select class="agent-selector" id="agentSelector">
                    <option value="">Select Agent...</option>
                </select>
            </div>
            <div class="sessions-container" id="sessionsContainer">
                <div class="empty-state" style="padding: 20px; text-align: center;">
                    <p>Select an agent to start</p>
                </div>
            </div>
            <button class="new-session-btn" id="newSessionBtn">+ New Session</button>
        </div>
        
        <div class="chat-area">
            <div class="chat-header">
                <h1 id="chatTitle">Welcome to ADK Chat</h1>
                <button class="delete-btn" id="deleteSessionBtn" style="display: none;">Delete Session</button>
            </div>
            
            <div class="messages" id="messagesContainer">
                <div class="empty-state">
                    <div class="empty-state-icon">💬</div>
                    <h2>Start a conversation</h2>
                    <p>Select an agent and create a new session to begin</p>
                </div>
            </div>
            
            <div class="input-area">
                <form class="input-form" id="messageForm">
                    <input 
                        type="text" 
                        class="message-input" 
                        id="messageInput" 
                        placeholder="Type your message..."
                        disabled
                    >
                    <button type="submit" class="send-btn" id="sendBtn" disabled>Send</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        let currentAgent = '';
        let currentUserId = 'user_' + Date.now();
        let currentSessionId = null;
        let sessions = {};

        // Configure marked for better rendering
        marked.setOptions({
            breaks: true,
            gfm: true
        });

        // Load agents on page load
        async function loadAgents() {
            try {
                const response = await fetch('/api/list-agents');
                const agents = await response.json();
                
                const selector = document.getElementById('agentSelector');
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
            }
        }

        // Render sessions in sidebar
        function renderSessions() {
            const container = document.getElementById('sessionsContainer');
            const sessionIds = Object.keys(sessions);
            
            if (sessionIds.length === 0) {
                container.innerHTML = '<div class="empty-state" style="padding: 20px; text-align: center;"><p>No sessions yet</p></div>';
                return;
            }
            
            container.innerHTML = sessionIds.map(sessionId => `
                <div class="session-item ${sessionId === currentSessionId ? 'active' : ''}" 
                     onclick="selectSession('${sessionId}')">
                    <div class="session-name">Session ${sessionId.substring(0, 8)}</div>
                    <div class="session-time">${new Date(sessions[sessionId].created).toLocaleString()}</div>
                </div>
            `).join('');
        }

        // Select a session
        function selectSession(sessionId) {
            currentSessionId = sessionId;
            renderSessions();
            loadMessages();
            
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('deleteSessionBtn').style.display = 'block';
            document.getElementById('chatTitle').textContent = `${currentAgent} - Session ${sessionId.substring(0, 8)}`;
        }

        // Format message content with markdown
        function formatMessageContent(content) {
            // Parse markdown to HTML
            return marked.parse(content);
        }

        // Load messages for current session
        function loadMessages() {
            if (!currentSessionId || !sessions[currentSessionId]) return;
            
            const container = document.getElementById('messagesContainer');
            const messages = sessions[currentSessionId].messages || [];
            
            if (messages.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👋</div><h2>Start chatting!</h2><p>Send your first message below</p></div>';
                return;
            }
            
            container.innerHTML = messages.map(msg => `
                <div class="message ${msg.role}">
                    <div class="message-content">${formatMessageContent(msg.content)}</div>
                    <div class="message-time">${new Date(msg.timestamp).toLocaleTimeString()}</div>
                </div>
            `).join('');
            
            container.scrollTop = container.scrollHeight;
        }

        // Send message
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !currentSessionId) return;
            
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<span class="loading"></span>';
            input.disabled = true;
            
            try {
                // Add user message to UI
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
                if (data.response) {
                    sessions[currentSessionId].messages.push({
                        role: 'assistant',
                        content: data.response,
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

        // Delete session
        document.getElementById('deleteSessionBtn').addEventListener('click', async () => {
            if (!currentSessionId || !confirm('Delete this session?')) return;
            
            try {
                await fetch('/api/delete-session', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent: currentAgent,
                        userId: currentUserId,
                        sessionId: currentSessionId
                    })
                });
                
                delete sessions[currentSessionId];
                currentSessionId = null;
                
                document.getElementById('messageInput').disabled = true;
                document.getElementById('sendBtn').disabled = true;
                document.getElementById('deleteSessionBtn').style.display = 'none';
                document.getElementById('chatTitle').textContent = 'Welcome to ADK Chat';
                
                renderSessions();
                document.getElementById('messagesContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">💬</div><h2>Start a conversation</h2><p>Select an agent and create a new session to begin</p></div>';
            } catch (error) {
                console.error('Error deleting session:', error);
            }
        });

        // Agent selector change
        document.getElementById('agentSelector').addEventListener('change', (e) => {
            currentAgent = e.target.value;
            currentSessionId = null;
            sessions = {};
            
            document.getElementById('messageInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('deleteSessionBtn').style.display = 'none';
            document.getElementById('chatTitle').textContent = currentAgent ? `${currentAgent} - Select or create a session` : 'Welcome to ADK Chat';
            
            if (currentAgent) {
                loadSessions();
            } else {
                renderSessions();
            }
        });

        // Initialize
        loadAgents();
    </script>
</body>
</html>
'''

# --------------------------
# In-memory session store
# --------------------------
sessions_store = {}

# --------------------------
# Routes
# --------------------------
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

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

@app.route('/api/delete-session', methods=['DELETE'])
def delete_session():
    data = request.json
    agent = data['agent']
    user_id = data['userId']
    session_id = data['sessionId']
    try:
        logger.info(f"Deleting session {session_id}")
        requests.delete(f'{ADK_API_BASE}/apps/{agent}/users/{user_id}/sessions/{session_id}', timeout=5)
        key = f"{agent}:{user_id}"
        if key in sessions_store:
            sessions_store[key].pop(session_id, None)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    agent = data['agent']
    user_id = data['userId']
    session_id = data['sessionId']
    message = data['message']
    logger.info(f"Sending message to agent {agent}, session {session_id}")

    try:
        payload = {
            'appName': agent,
            'userId': user_id,
            'sessionId': session_id,
            'newMessage': {
                'role': 'user',
                'parts': [{'text': message}]
            }
        }
        logger.debug(f"Request payload: {payload}")
        response = requests.post(f'{ADK_API_BASE}/run', json=payload, timeout=240)
        logger.debug(f"Response status: {response.status_code}")

        if response.ok:
            assistant_response = ""
            try:
                response_data = response.json()
                for event in response_data:
                    for part in event.get('content', {}).get('parts', []):
                        assistant_response += part.get('text', '')
            except Exception as e:
                logger.error(f"Failed to parse response JSON: {e}")
                assistant_response = str(response.text)

            key = f"{agent}:{user_id}"
            sessions_store.setdefault(key, {}).setdefault(session_id, {}).setdefault('messages', []).append({
                'role': 'assistant',
                'content': assistant_response,
                'timestamp': datetime.now().isoformat()
            })

            return jsonify({'status': 'success', 'response': assistant_response})
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

# --------------------------
# Run server
# --------------------------
if __name__ == '__main__':
    logger.info("="*60)
    logger.info("ADK Chat UI Server - Enhanced Edition")
    logger.info(f"ADK API Base: {ADK_API_BASE}")
    logger.info(f"Starting server on http://{HOST}:{PORT}")
    logger.info("="*60)
    app.run(debug=True, host=HOST, port=PORT)