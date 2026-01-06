from flask import Blueprint, session, request, redirect, url_for, jsonify, current_app, render_template
import requests
import logging
from datetime import datetime
from session_manager import get_sessions_for_user, create_session, delete_session, add_message_to_session

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def index():
    """Main application page - redirects to chat if authenticated, login if not"""
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))

    user = session.get('user', {})
    logger.info(f"[INDEX] User accessing index: {user.get('displayName', 'Unknown')}")

    # Redirect authenticated users to the chat UI
    return render_template('chat.html')

@chat_bp.route('/api/list-agents')
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

@chat_bp.route('/api/sessions')
def get_sessions():
    agent = request.args.get('agent')
    user = request.args.get('user')
    sessions = get_sessions_for_user(agent, user)
    logger.debug(f"Retrieved {len(sessions)} sessions for {agent}:{user}")
    return jsonify(sessions)

@chat_bp.route('/api/create-session', methods=['POST'])
def create_session_route():
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
            create_session(agent, user_id, session_id)
            logger.info(f"Session {session_id} created")
            return jsonify({'status': 'success', 'sessionId': session_id})
        else:
            logger.error(f"Failed to create session: HTTP {response.status_code} - {response.text}")
            return jsonify({'status': 'error', 'message': f'HTTP {response.status_code}'}), response.status_code
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@chat_bp.route('/api/delete-session', methods=['DELETE'])
def delete_session_route():
    data = request.json
    agent = data['agent']
    user_id = data['userId']
    session_id = data['sessionId']
    try:
        adk_api = current_app.config.get('ADK_API', 'http://localhost:8000')
        logger.info(f"Deleting session {session_id}")
        requests.delete(f'{adk_api}/apps/{agent}/users/{user_id}/sessions/{session_id}', timeout=5)
        delete_session(agent, user_id, session_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@chat_bp.route('/api/send-message', methods=['POST'])
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
        response = requests.post(f'{adk_api}/run', json=payload, timeout=600)
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

            add_message_to_session(agent, user_id, session_id, 'assistant', assistant_response)

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