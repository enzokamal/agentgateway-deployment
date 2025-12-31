from flask import Flask, session, render_template, render_template_string, request, redirect, url_for, current_app, jsonify
from flask_session import Session
import requests
from datetime import datetime
import os
import logging
import base64
import json
from urllib.parse import urlencode, quote

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory session store for ADK Chat
sessions_store = {}

# --------------------------
# HTML Templates
# --------------------------
def get_chat_html_template():
    """Return the HTML template for the chat interface"""
    return '''
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
# Helper Functions
# --------------------------
def setup_app_config(app, config_name):
    """Setup application configuration"""
    from config import config
    app.config.from_object(config[config_name])

    # Ensure session directory exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

def setup_session(app):
    """Initialize Flask-Session"""
    Session(app)

def setup_middleware(app):
    """Setup request middleware"""
    @app.before_request
    def require_auth():
        """Middleware to check authentication before each request"""
        # Allow access to auth routes and static files without authentication
        public_endpoints = ['login', 'login_post', 'auth_callback', 'auth_store_tokens',
                           'auth_manual_token', 'health', 'static']

        # Skip auth check for static files and public endpoints
        if request.endpoint in public_endpoints or request.endpoint is None:
            return

        # Check if user is authenticated
        if not session.get('authenticated'):
            logger.info(f"[AUTH CHECK] Unauthenticated access attempt to: {request.endpoint}")
            return redirect(url_for('login'))

    @app.before_request
    def log_request_info():
        if app.debug:
            print(f"\n{'='*70}")
            print(f"REQUEST: {request.method} {request.path}")
            print(f"Endpoint: {request.endpoint}")
            print(f"Session authenticated: {session.get('authenticated', False)}")
            print(f"{'='*70}\n")

def setup_error_handlers(app):
    """Setup error handlers"""
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(e):
        print(f"Internal error: {str(e)}")
        return {'error': 'Internal server error'}, 500

# --------------------------
# Authentication Helper Functions
# --------------------------
def exchange_code_for_tokens(code):
    """Exchange authorization code for access tokens"""
    tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
    client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
    client_secret = current_app.config.get('AZURE_CLIENT_SECRET', '')
    redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
    scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Prepare token request data
    token_data = {
        'client_id': client_id,
        'scope': scope,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    # Add client secret if available (for confidential clients)
    if client_secret:
        token_data['client_secret'] = client_secret
        logger.info("[TOKEN EXCHANGE] Using client secret authentication")
    else:
        logger.info("[TOKEN EXCHANGE] No client secret - public client flow")

    logger.debug(f"[TOKEN EXCHANGE] URL: {token_url}")
    logger.debug(f"[TOKEN EXCHANGE] Scope: {scope}")
    logger.debug(f"[TOKEN EXCHANGE] Redirect URI: {redirect_uri}")

    # Make token request
    response = requests.post(
        token_url,
        data=token_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    logger.debug(f"[TOKEN EXCHANGE] Response status: {response.status_code}")

    # Handle token exchange errors
    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = json.dumps(error_json, indent=2)
            logger.error(f"[TOKEN EXCHANGE] Error details: {error_detail}")
        except:
            logger.error(f"[TOKEN EXCHANGE] Error response: {error_detail}")

        raise Exception(f"Token exchange failed: {error_detail}")

    tokens = response.json()
    logger.info(f"[TOKEN EXCHANGE] Received tokens: {list(tokens.keys())}")

    return tokens

def render_auth_success_page(tokens):
    """Render success page that posts tokens back to parent window"""
    access_token = tokens.get('access_token', '')
    refresh_token = tokens.get('refresh_token', '')
    id_token = tokens.get('id_token', '')

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
            }}
            .checkmark {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: block;
                stroke-width: 2;
                stroke: #4CAF50;
                stroke-miterlimit: 10;
                margin: 0 auto 20px;
                box-shadow: inset 0px 0px 0px #4CAF50;
                animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
            }}
            .checkmark__circle {{
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                stroke-width: 2;
                stroke-miterlimit: 10;
                stroke: #4CAF50;
                fill: none;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
            }}
            .checkmark__check {{
                transform-origin: 50% 50%;
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
            }}
            @keyframes stroke {{
                100% {{ stroke-dashoffset: 0; }}
            }}
            @keyframes scale {{
                0%, 100% {{ transform: none; }}
                50% {{ transform: scale3d(1.1, 1.1, 1); }}
            }}
            @keyframes fill {{
                100% {{ box-shadow: inset 0px 0px 0px 30px #4CAF50; }}
            }}
            h2 {{ color: #333; margin: 0 0 10px 0; }}
            p {{ color: #666; margin: 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
            <h2>Authentication Successful!</h2>
            <p>Redirecting you back to the application...</p>
        </div>
        <script>
            (function() {{
                try {{
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'auth_success',
                            access_token: '{access_token}',
                            refresh_token: '{refresh_token}',
                            id_token: '{id_token}'
                        }}, '*');
                        // Open chat interface in new window after authentication
                        window.opener.open('/', '_blank');
                        setTimeout(function() {{ window.close(); }}, 1500);
                    }} else {{
                        console.error('No opener window found');
                        setTimeout(function() {{
                            window.location.href = '/';
                        }}, 2000);
                    }}
                }} catch (e) {{
                    console.error('Error posting message:', e);
                    setTimeout(function() {{ window.location.href = '/'; }}, 2000);
                }}
            }})();
        </script>
    </body>
    </html>
    '''

def render_auth_error_page(error, description):
    """Render error page that notifies parent window"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Error</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 500px;
            }}
            .error-icon {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: #f44336;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 48px;
            }}
            h2 {{ color: #333; margin: 0 0 10px 0; }}
            .error-code {{
                color: #f44336;
                font-weight: bold;
                margin: 10px 0;
                font-family: monospace;
            }}
            .error-description {{
                color: #666;
                margin: 10px 0;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 5px;
                word-wrap: break-word;
            }}
            .actions {{
                margin-top: 20px;
                text-align: center;
            }}
            button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">✕</div>
            <h2>Authentication Failed</h2>
            <div class="error-code">Error: {error}</div>
            <div class="error-description">{description}</div>
            <div class="actions">
                <button onclick="tryAgain()">Try Again</button>
            </div>
        </div>
        <script>
            function tryAgain() {{
                if (window.opener) {{
                    window.close();
                    window.opener.location.reload();
                }} else {{
                    window.location.href = '/login';
                }}
            }}

            (function() {{
                try {{
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'auth_error',
                            error: '{error}',
                            description: '{description}'
                        }}, '*');
                    }}
                }} catch (e) {{
                    console.error('Error posting message:', e);
                }}
            }})();
        </script>
    </body>
    </html>
    '''

# --------------------------
# Route Registration Functions
# --------------------------
def register_auth_routes(app):
    """Register authentication-related routes"""
    @app.route('/login')
    def login():
        """Initiate Azure AD OAuth flow"""
        tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
        client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
        redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
        scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

        return render_template("login.html", tenant_id=tenant_id, client_id=client_id, redirect_uri=redirect_uri, scope=scope)

    @app.route("/login", methods=["POST"])
    def login_post():
        """Mock authentication for development/testing"""
        session['authenticated'] = True
        session['user'] = {
            'displayName': 'Test User',
            'name': 'Test User'
        }
        return redirect(url_for('index'))

    @app.route('/auth/callback')
    def auth_callback():
        """Handle OAuth callback from Azure AD"""
        code = request.args.get('code')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        state = request.args.get('state')

        logger.info(f"[AUTH CALLBACK] Code present: {bool(code)}, Error: {error}")

        # Handle OAuth errors
        if error:
            error_msg = error_description or 'No description provided'
            logger.error(f"[AUTH CALLBACK] OAuth error: {error} - {error_msg}")
            return render_auth_error_page(error, error_msg)

        # Handle missing authorization code
        if not code:
            logger.error("[AUTH CALLBACK] No authorization code received")
            return render_auth_error_page('no_code', 'No authorization code received')

        # Exchange authorization code for tokens
        try:
            tokens = exchange_code_for_tokens(code)
            logger.info("[AUTH CALLBACK] Token exchange successful")
            return render_auth_success_page(tokens)
        except Exception as e:
            logger.error(f"[AUTH CALLBACK] Token exchange failed: {str(e)}")
            return render_auth_error_page('token_exchange_failed', str(e))

    @app.route('/auth/store-tokens', methods=['POST'])
    def auth_store_tokens():
        """Store OAuth tokens in session after successful authentication"""
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        id_token = data.get('id_token')

        if not access_token:
            logger.error("[STORE TOKENS] Error: No access token provided")
            return jsonify({'error': 'Access token is required'}), 400

        # Decode ID token to get user info (if available)
        user_info = {'displayName': 'Authenticated User', 'name': 'Authenticated User'}
        if id_token:
            try:
                # Decode JWT payload (without verification for simplicity)
                payload = id_token.split('.')[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))
                user_info = {
                    'displayName': decoded.get('name', 'Authenticated User'),
                    'name': decoded.get('name', 'Authenticated User'),
                    'email': decoded.get('email', decoded.get('preferred_username', '')),
                    'oid': decoded.get('oid', '')
                }
                logger.info(f"[STORE TOKENS] User info from ID token: {user_info['displayName']}")
            except Exception as e:
                logger.error(f"[STORE TOKENS] Could not decode ID token: {e}")

        # Store in session
        session['authenticated'] = True
        session['user'] = {
            **user_info,
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'idToken': id_token
        }

        logger.info(f"[STORE TOKENS] Successfully stored tokens for user: {user_info['displayName']}")
        return jsonify({'success': True, 'message': 'Authentication successful'})

    @app.route('/auth/manual-token', methods=['POST'])
    def auth_manual_token():
        """Manually provide a token for testing purposes"""
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        # Basic JWT format validation
        if token.count('.') != 2:
            return jsonify({'error': 'Invalid token format. Must be a valid JWT.'}), 400

        # Try to decode token to get user info
        user_info = {'displayName': 'Manual Token User', 'name': 'Manual Token User'}
        try:
            payload = token.split('.')[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            user_info = {
                'displayName': decoded.get('name', 'Manual Token User'),
                'name': decoded.get('name', 'Manual Token User'),
                'email': decoded.get('email', decoded.get('preferred_username', ''))
            }
            logger.info(f"[MANUAL TOKEN] Decoded user: {user_info['displayName']}")
        except Exception as e:
            logger.error(f"[MANUAL TOKEN] Could not decode token: {e}")

        session['authenticated'] = True
        session['user'] = {
            **user_info,
            'accessToken': token
        }

        logger.info("[MANUAL TOKEN] Manual token authentication successful")
        return jsonify({'success': True, 'message': 'Manual token authentication successful'})

    @app.route('/logout')
    def logout():
        """Clear session and logout user"""
        user = session.get('user', {})
        logger.info(f"[LOGOUT] User logged out: {user.get('displayName', 'Unknown')}")
        session.clear()
        return redirect(url_for('login'))

def register_chat_routes(app):
    """Register chat-related routes"""
    @app.route('/')
    def index():
        """Main application page - redirects to chat if authenticated, login if not"""
        if not session.get('authenticated'):
            return redirect(url_for('login'))

        user = session.get('user', {})
        logger.info(f"[INDEX] User accessing index: {user.get('displayName', 'Unknown')}")

        # Redirect authenticated users to the chat UI
        return render_template_string(get_chat_html_template())

    @app.route('/api/list-agents')
    def list_agents():
        try:
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Fetching agents from {adk_api}/list-apps")
            response = requests.get(f'{adk_api}/list-apps', timeout=5)
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Creating session {session_id} for agent {agent}")
            response = requests.post(
                f'{adk_api}/apps/{agent}/users/{user_id}/sessions/{session_id}',
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Deleting session {session_id}")
            requests.delete(f'{adk_api}/apps/{agent}/users/{user_id}/sessions/{session_id}', timeout=5)
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
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
            response = requests.post(f'{adk_api}/run', json=payload, timeout=240)
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

def register_health_route(app):
    """Register health check route"""
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'authenticated': session.get('authenticated', False)})

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Setup configuration and components
    setup_app_config(app, config_name)
    setup_session(app)
    setup_middleware(app)
    setup_error_handlers(app)

    # Register routes
    register_auth_routes(app)
    register_chat_routes(app)
    register_health_route(app)

    # Log initialization
    print(f"\n{'='*70}")
    print(f"Flask App Initialized")
    print(f"Configuration: {config_name}")
    print(f"Debug Mode: {app.debug}")
    print(f"Azure Tenant ID: {app.config.get('AZURE_TENANT_ID')}")
    print(f"Azure Client ID: {app.config.get('AZURE_CLIENT_ID')}")
    print(f"Azure Scopes: {app.config.get('AZURE_SCOPES')}")
    print(f"Redirect URI: {app.config.get('REDIRECT_URI')}")
    print(f"Client Secret Set: {bool(app.config.get('AZURE_CLIENT_SECRET'))}")
    print(f"ADK API: {app.config.get('ADK_API', 'http://localhost:8000')}")
    print(f"{'='*70}\n")

    return app

    # Authentication Routes
    @app.route('/login')
    def login():
        """Initiate Azure AD OAuth flow"""
        tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
        client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
        redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
        scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

        return render_template("login.html", tenant_id=tenant_id, client_id=client_id, redirect_uri=redirect_uri, scope=scope)

    @app.route("/login", methods=["POST"])
    def login_post():
        """Mock authentication for development/testing"""
        session['authenticated'] = True
        session['user'] = {
            'displayName': 'Test User',
            'name': 'Test User'
        }
        return redirect(url_for('index'))

    @app.route('/auth/callback')
    def auth_callback():
        """Handle OAuth callback from Azure AD"""
        code = request.args.get('code')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        state = request.args.get('state')

        logger.info(f"[AUTH CALLBACK] Code present: {bool(code)}, Error: {error}")

        # Handle OAuth errors
        if error:
            error_msg = error_description or 'No description provided'
            logger.error(f"[AUTH CALLBACK] OAuth error: {error} - {error_msg}")
            return render_auth_error_page(error, error_msg)

        # Handle missing authorization code
        if not code:
            logger.error("[AUTH CALLBACK] No authorization code received")
            return render_auth_error_page('no_code', 'No authorization code received')

        # Exchange authorization code for tokens
        try:
            tokens = exchange_code_for_tokens(code)
            logger.info("[AUTH CALLBACK] Token exchange successful")
            return render_auth_success_page(tokens)
        except Exception as e:
            logger.error(f"[AUTH CALLBACK] Token exchange failed: {str(e)}")
            return render_auth_error_page('token_exchange_failed', str(e))

    def exchange_code_for_tokens(code):
        """Exchange authorization code for access tokens"""
        tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
        client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
        client_secret = current_app.config.get('AZURE_CLIENT_SECRET', '')
        redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
        scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        # Prepare token request data
        token_data = {
            'client_id': client_id,
            'scope': scope,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        # Add client secret if available (for confidential clients)
        if client_secret:
            token_data['client_secret'] = client_secret
            logger.info("[TOKEN EXCHANGE] Using client secret authentication")
        else:
            logger.info("[TOKEN EXCHANGE] No client secret - public client flow")

        logger.debug(f"[TOKEN EXCHANGE] URL: {token_url}")
        logger.debug(f"[TOKEN EXCHANGE] Scope: {scope}")
        logger.debug(f"[TOKEN EXCHANGE] Redirect URI: {redirect_uri}")

        # Make token request
        response = requests.post(
            token_url,
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        logger.debug(f"[TOKEN EXCHANGE] Response status: {response.status_code}")

        # Handle token exchange errors
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, indent=2)
                logger.error(f"[TOKEN EXCHANGE] Error details: {error_detail}")
            except:
                logger.error(f"[TOKEN EXCHANGE] Error response: {error_detail}")

            raise Exception(f"Token exchange failed: {error_detail}")

        tokens = response.json()
        logger.info(f"[TOKEN EXCHANGE] Received tokens: {list(tokens.keys())}")

        return tokens

    def render_auth_success_page(tokens):
        """Render success page that posts tokens back to parent window"""
        access_token = tokens.get('access_token', '')
        refresh_token = tokens.get('refresh_token', '')
        id_token = tokens.get('id_token', '')

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }}
                .checkmark {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    display: block;
                    stroke-width: 2;
                    stroke: #4CAF50;
                    stroke-miterlimit: 10;
                    margin: 0 auto 20px;
                    box-shadow: inset 0px 0px 0px #4CAF50;
                    animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
                }}
                .checkmark__circle {{
                    stroke-dasharray: 166;
                    stroke-dashoffset: 166;
                    stroke-width: 2;
                    stroke-miterlimit: 10;
                    stroke: #4CAF50;
                    fill: none;
                    animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
                }}
                .checkmark__check {{
                    transform-origin: 50% 50%;
                    stroke-dasharray: 48;
                    stroke-dashoffset: 48;
                    animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
                }}
                @keyframes stroke {{
                    100% {{ stroke-dashoffset: 0; }}
                }}
                @keyframes scale {{
                    0%, 100% {{ transform: none; }}
                    50% {{ transform: scale3d(1.1, 1.1, 1); }}
                }}
                @keyframes fill {{
                    100% {{ box-shadow: inset 0px 0px 0px 30px #4CAF50; }}
                }}
                h2 {{ color: #333; margin: 0 0 10px 0; }}
                p {{ color: #666; margin: 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
                <h2>Authentication Successful!</h2>
                <p>Redirecting you back to the application...</p>
            </div>
            <script>
                (function() {{
                    try {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'auth_success',
                                access_token: '{access_token}',
                                refresh_token: '{refresh_token}',
                                id_token: '{id_token}'
                            }}, '*');
                            // Open chat interface in new window after authentication
                            window.opener.open('/', '_blank');
                            setTimeout(function() {{ window.close(); }}, 1500);
                        }} else {{
                            console.error('No opener window found');
                            setTimeout(function() {{
                                window.location.href = '/';
                            }}, 2000);
                        }}
                    }} catch (e) {{
                        console.error('Error posting message:', e);
                        setTimeout(function() {{ window.location.href = '/'; }}, 2000);
                    }}
                }})();
            </script>
        </body>
        </html>
        '''

    def render_auth_error_page(error, description):
        """Render error page that notifies parent window"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    max-width: 500px;
                }}
                .error-icon {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: #f44336;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 48px;
                }}
                h2 {{ color: #333; margin: 0 0 10px 0; }}
                .error-code {{
                    color: #f44336;
                    font-weight: bold;
                    margin: 10px 0;
                    font-family: monospace;
                }}
                .error-description {{
                    color: #666;
                    margin: 10px 0;
                    padding: 15px;
                    background: #f5f5f5;
                    border-radius: 5px;
                    word-wrap: break-word;
                }}
                .actions {{
                    margin-top: 20px;
                    text-align: center;
                }}
                button {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                button:hover {{
                    background: #5568d3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">✕</div>
                <h2>Authentication Failed</h2>
                <div class="error-code">Error: {error}</div>
                <div class="error-description">{description}</div>
                <div class="actions">
                    <button onclick="tryAgain()">Try Again</button>
                </div>
            </div>
            <script>
                function tryAgain() {{
                    if (window.opener) {{
                        window.close();
                        window.opener.location.reload();
                    }} else {{
                        window.location.href = '/login';
                    }}
                }}

                (function() {{
                    try {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'auth_error',
                                error: '{error}',
                                description: '{description}'
                            }}, '*');
                        }}
                    }} catch (e) {{
                        console.error('Error posting message:', e);
                    }}
                }})();
            </script>
        </body>
        </html>
        '''

    @app.route('/auth/store-tokens', methods=['POST'])
    def auth_store_tokens():
        """Store OAuth tokens in session after successful authentication"""
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        id_token = data.get('id_token')

        if not access_token:
            logger.error("[STORE TOKENS] Error: No access token provided")
            return jsonify({'error': 'Access token is required'}), 400

        # Decode ID token to get user info (if available)
        user_info = {'displayName': 'Authenticated User', 'name': 'Authenticated User'}
        if id_token:
            try:
                # Decode JWT payload (without verification for simplicity)
                payload = id_token.split('.')[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))
                user_info = {
                    'displayName': decoded.get('name', 'Authenticated User'),
                    'name': decoded.get('name', 'Authenticated User'),
                    'email': decoded.get('email', decoded.get('preferred_username', '')),
                    'oid': decoded.get('oid', '')
                }
                logger.info(f"[STORE TOKENS] User info from ID token: {user_info['displayName']}")
            except Exception as e:
                logger.error(f"[STORE TOKENS] Could not decode ID token: {e}")

        # Store in session
        session['authenticated'] = True
        session['user'] = {
            **user_info,
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'idToken': id_token
        }

        logger.info(f"[STORE TOKENS] Successfully stored tokens for user: {user_info['displayName']}")
        return jsonify({'success': True, 'message': 'Authentication successful'})

    @app.route('/auth/manual-token', methods=['POST'])
    def auth_manual_token():
        """Manually provide a token for testing purposes"""
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        # Basic JWT format validation
        if token.count('.') != 2:
            return jsonify({'error': 'Invalid token format. Must be a valid JWT.'}), 400

        # Try to decode token to get user info
        user_info = {'displayName': 'Manual Token User', 'name': 'Manual Token User'}
        try:
            payload = token.split('.')[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            user_info = {
                'displayName': decoded.get('name', 'Manual Token User'),
                'name': decoded.get('name', 'Manual Token User'),
                'email': decoded.get('email', decoded.get('preferred_username', ''))
            }
            logger.info(f"[MANUAL TOKEN] Decoded user: {user_info['displayName']}")
        except Exception as e:
            logger.error(f"[MANUAL TOKEN] Could not decode token: {e}")

        session['authenticated'] = True
        session['user'] = {
            **user_info,
            'accessToken': token
        }

        logger.info("[MANUAL TOKEN] Manual token authentication successful")
        return jsonify({'success': True, 'message': 'Manual token authentication successful'})

    @app.route('/logout')
    def logout():
        """Clear session and logout user"""
        user = session.get('user', {})
        logger.info(f"[LOGOUT] User logged out: {user.get('displayName', 'Unknown')}")
        session.clear()
        return redirect(url_for('login'))

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'authenticated': session.get('authenticated', False)})

    # Chat Routes
    @app.route('/')
    def index():
        """Main application page - redirects to chat if authenticated, login if not"""
        if not session.get('authenticated'):
            return redirect(url_for('login'))

        user = session.get('user', {})
        logger.info(f"[INDEX] User accessing index: {user.get('displayName', 'Unknown')}")

        # Redirect authenticated users to the chat UI
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/list-agents')
    def list_agents():
        try:
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Fetching agents from {adk_api}/list-apps")
            response = requests.get(f'{adk_api}/list-apps', timeout=5)
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Creating session {session_id} for agent {agent}")
            response = requests.post(
                f'{adk_api}/apps/{agent}/users/{user_id}/sessions/{session_id}',
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
            logger.info(f"Deleting session {session_id}")
            requests.delete(f'{adk_api}/apps/{agent}/users/{user_id}/sessions/{session_id}', timeout=5)
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
            adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
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
            response = requests.post(f'{adk_api}/run', json=payload, timeout=240)
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

    print(f"\n{'='*70}")
    print(f"Flask App Initialized")
    print(f"Configuration: {config_name}")
    print(f"Debug Mode: {app.debug}")
    print(f"Azure Tenant ID: {app.config.get('AZURE_TENANT_ID')}")
    print(f"Azure Client ID: {app.config.get('AZURE_CLIENT_ID')}")
    print(f"Azure Scopes: {app.config.get('AZURE_SCOPES')}")
    print(f"Redirect URI: {app.config.get('REDIRECT_URI')}")
    print(f"Client Secret Set: {bool(app.config.get('AZURE_CLIENT_SECRET'))}")
    print(f"ADK API: {app.config.get('ADK_API', 'http://localhost:8000')}")
    print(f"{'='*70}\n")

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)