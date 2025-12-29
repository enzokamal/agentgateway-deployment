import requests, os, uuid

ADK_API = os.getenv("ADK_API", "http://localhost:5000")
APP_NAME = os.getenv("ADK_APP_NAME", "my_sample_agent")
USER_ID = os.getenv("ADK_USER_ID", "u_123")

def list_sessions(token):
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers)
    return resp.json() if resp.status_code == 200 else []

def create_session(token):
    sid = "s_" + uuid.uuid4().hex[:8]
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    headers = {'Authorization': f'Bearer {token}'}
    requests.post(url, json={}, headers=headers)
    return sid

def get_session_events(sid, token):
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return []
    return resp.json().get("events", [])

def send_message(sid, message, token):
    payload = {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": sid,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}]
        }
    }
    headers = {'Authorization': f'Bearer {token}'}
    requests.post(f"{ADK_API}/run", json=payload, headers=headers)

def delete_session(sid, token):
    url = f"{ADK_API}/apps/{APP_NAME}/users/{USER_ID}/sessions/{sid}"
    headers = {'Authorization': f'Bearer {token}'}
    requests.delete(url, headers=headers)
