from datetime import datetime

# In-memory session store for ADK Chat
sessions_store = {}

def get_sessions_for_user(agent, user_id):
    """Retrieve sessions for a specific agent and user"""
    key = f"{agent}:{user_id}"
    return sessions_store.get(key, {})

def create_session(agent, user_id, session_id):
    """Create a new session"""
    key = f"{agent}:{user_id}"
    sessions_store.setdefault(key, {})[session_id] = {
        'created': datetime.now().isoformat(),
        'messages': []
    }

def delete_session(agent, user_id, session_id):
    """Delete a session"""
    key = f"{agent}:{user_id}"
    if key in sessions_store:
        sessions_store[key].pop(session_id, None)

def add_message_to_session(agent, user_id, session_id, role, content, timestamp=None):
    """Add a message to a session"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    key = f"{agent}:{user_id}"
    sessions_store.setdefault(key, {}).setdefault(session_id, {}).setdefault('messages', []).append({
        'role': role,
        'content': content,
        'timestamp': timestamp
    })